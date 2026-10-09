#!/usr/bin/env python3
"""Derive a case's identity from one article URL, so a solver needs no brief.

Given an article URL (or a local posts/ filename), print everything
prepare_case.py needs: the iteration id, canonical case id, challenge year,
verified challenge date and URL, and the Tableau Public workbook URL.

The challenge identity is resolved from official sources only:
  1. the local index.json / public_links_map.json archive, and
  2. the Workout Wednesday WordPress REST API (by slug, then by title search).

This is a *read-only* helper. It never edits case metadata, and it never
touches the author workbook.

Usage:
    python scripts/case_intake.py <article-url-or-file>
    python scripts/case_intake.py <article-url> --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[1]
UA = "Mozilla/5.0 (compatible; WowCaseIntake/1.0)"
WP_API = "https://www.workout-wednesday.com/wp-json/wp/v2/posts"


def _load(name: str):
    path = LAB_ROOT / name
    if not path.is_file():
        raise SystemExit(
            f"Missing {name}. Run `python crawler.py && python gen_links_map.py` "
            f"(or `python download_all.py --refresh`) first."
        )
    return json.loads(path.read_text(encoding="utf-8"))


def _slug(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def find_article(reference: str) -> dict:
    """Resolve an article URL or posts/ filename to its index entry."""
    index = _load("index.json")
    posts = index["posts"]
    if reference.startswith("http"):
        url = reference.rstrip("/") + "/"
        match = next((p for p in posts if p["link"].rstrip("/") + "/" == url), None)
        if match is None:
            # Fall back to the path portion, tolerating www./http differences.
            want = urllib.parse.urlparse(url).path.rstrip("/").lower()
            match = next(
                (p for p in posts if urllib.parse.urlparse(p["link"]).path.rstrip("/").lower() == want),
                None,
            )
    else:
        name = Path(reference).name
        match = next((p for p in posts if p["file"] == name), None)
    if match is None:
        raise SystemExit(
            f"Article not found in index.json: {reference}\n"
            "Run `python download_all.py --refresh` to update the archive."
        )
    return match


def find_workbook(article_file: str) -> dict | None:
    """Return the first Tableau Public link recorded for an article."""
    link_map = _load("public_links_map.json")
    stem = article_file[:-5] if article_file.endswith(".html") else article_file
    entry = next((x for x in link_map["items"] if x["article"] == stem), None)
    if not entry or not entry.get("links"):
        return None
    link = entry["links"][0]
    return {
        "workbook": link.get("workbook"),
        "view": link.get("view"),
        "viz_url": link.get("viz_url"),
    }


def _wp_get(params: dict) -> list:
    query = urllib.parse.urlencode(params)
    request = urllib.request.Request(f"{WP_API}?{query}", headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8", "replace"))
    except Exception as exc:  # network is best-effort; identity can stay null
        print(f"  [warn] WordPress lookup failed: {exc}", file=sys.stderr)
        return []


def resolve_challenge(title: str, year: int | None, week: int | None) -> dict:
    """Resolve the official challenge record from the WordPress REST API.

    Prefer the canonical slug (``2026w37tab``), which is exact; fall back to a
    title search when the week is unknown.
    """
    candidates: list[dict] = []
    seen: set = set()

    def collect(posts: list) -> None:
        for post in posts:
            if post.get("id") in seen:
                continue
            seen.add(post.get("id"))
            rendered = re.sub(r"<[^>]+>", "", post.get("title", {}).get("rendered", ""))
            candidates.append(
                {
                    "title": rendered.strip(),
                    "date": (post.get("date") or "")[:10],
                    "link": post.get("link"),
                    "id": post.get("id"),
                }
            )

    if year and week:
        for slug in (f"{year}w{week:02d}tab", f"{year}w{week}tab"):
            collect(_wp_get({"slug": slug, "per_page": 1}))
    collect(_wp_get({"search": re.sub(r"[^\w\s]", " ", title), "per_page": 5}))
    return {"candidates": candidates}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("article", help="Article URL or posts/<file>.html")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument(
        "--command",
        action="store_true",
        help="Print a ready-to-run prepare_case.py command",
    )
    args = parser.parse_args()

    article = find_article(args.article)
    workbook = find_workbook(article["file"])
    date = article["date"]

    # Prefer the week encoded in the workbook name (author convention), else
    # fall back to the official WordPress search.
    year = week = None
    if workbook and workbook.get("workbook"):
        match = re.search(r"(\d{4})[_-]\d{2}[_-]\d{2}[_-]WW[_\s]?(\d{1,2})", workbook["workbook"], re.I)
        if match:
            year, week = int(match.group(1)), int(match.group(2))

    slug_base = _slug(re.sub(r"[^\w\s]", " ", article["title"]))
    iteration_id = f"{date}-ww{week:02d}-{slug_base}" if week else f"{date}-{slug_base}"

    result = {
        "article": {
            "url": article["link"],
            "file": article["file"],
            "title": article["title"],
            "date": date,
        },
        "workbook": workbook,
        "iteration_id": iteration_id,
        "case_id": f"wow-{year}-ww{week:02d}-{slug_base}" if (year and week) else None,
        "challenge_year": year,
        "challenge_week": week,
    }

    official = resolve_challenge(article["title"], year, week)
    result["challenge_candidates"] = official["candidates"]
    top = official["candidates"][0] if official["candidates"] else None
    if top:
        result["challenge_date"] = top["date"]
        result["challenge_url"] = top["link"]

    if args.command:
        viz = (workbook or {}).get("viz_url")
        lines = ["python scripts/prepare_case.py"]
        lines.append(f'  --workbook-url "{viz}"' if viz else "  --source <path/to/author.twbx>")
        lines.append(f"  --iteration-id {iteration_id}")
        lines.append(f"  --challenge-year {year}" if year else "  --challenge-year <YYYY>")
        if result.get("challenge_date"):
            lines.append(f"  --challenge-date {result['challenge_date']}")
        if result.get("challenge_url"):
            lines.append(f'  --challenge-url "{result["challenge_url"]}"')
        lines.append(f'  --post "posts/{article["file"]}"')
        print("\n".join(lines))
        return

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    print(f"article      {article['link']}")
    print(f"  file       {article['file']}")
    print(f"  date       {date}")
    print(f"workbook     {(workbook or {}).get('viz_url') or '(no Tableau Public link found)'}")
    print(f"iteration_id {iteration_id}")
    print(f"case_id      {result['case_id'] or '(confirm the challenge week)'}")
    print()
    print("Official challenge record (confirm date + url before prepare_case):")
    for candidate in official["candidates"][:3]:
        print(f"  {candidate['date']}  {candidate['title'][:60]}")
        print(f"             {candidate['link']}")
    if not official["candidates"]:
        print("  (none found; confirm the challenge week from the article)")


if __name__ == "__main__":
    main()
