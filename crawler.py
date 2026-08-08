#!/usr/bin/env python3
"""Incrementally crawl donnacoles.home.blog without re-downloading posts.

The crawler scans newest pages first, identifies posts by canonical URL, keeps
existing files when possible, and merges old index entries when a limited run
does not revisit the full archive.

Examples:
    python crawler.py
    python crawler.py --limit 5
    python crawler.py --delay 1.5
    python crawler.py --with-images
"""

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

BASE = "https://donnacoles.home.blog"
UA = "Mozilla/5.0 (compatible; DonnaCrawler/1.0)"

ILLEGAL = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def safe_name(s: str) -> str:
    s = s.strip()
    s = ILLEGAL.sub(" ", s)
    s = re.sub(r"\s+", "_", s)
    return s[:120].rstrip("._ ")


def fetch(url: str, retries: int = 3, backoff: float = 2.0):
    last = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            if e.code == 404:
                raise  # Pagination boundary; do not retry.
            last = e
            print(f"  [retry {attempt}/{retries}] HTTP {e.code} {url}", file=sys.stderr)
        except Exception as e:  # Timeout or connection error.
            last = e
            print(f"  [retry {attempt}/{retries}] {e} {url}", file=sys.stderr)
        if attempt < retries:
            time.sleep(backoff * attempt)
    raise last or RuntimeError("fetch failed")


def parse_list(doc: str):
    """Return ``[(title, link, date_iso), ...]`` from one archive page."""
    blocks = re.findall(r"<article[^>]*id=\"post-\d+\"[^>]*>(.*?)</article>", doc, re.S)
    out = []
    for b in blocks:
        m = re.search(r'<h1 class="entry-title"><a href="([^"]+)"[^>]*>(.*?)</a>', b, re.S)
        if not m:
            m = re.search(r'<h[123] class="entry-title"[^>]*><a href="([^"]+)"[^>]*>(.*?)</a>', b, re.S)
        if not m:
            continue
        link = m.group(1).strip()
        title = html.unescape(re.sub(r"<[^>]+>", "", m.group(2)).strip())
        tm = re.search(r'<time[^>]*datetime="([^"]+)"', b)
        date_iso = tm.group(1) if tm else None
        out.append((title, link, date_iso))
    return out


def parse_content(doc: str):
    """Extract the article entry-content block."""
    m = re.search(
        r'<div class="entry-content"[^>]*>(.*?)(?=<footer class="entry-footer|</article>)',
        doc, re.S,
    )
    return m.group(1).strip() if m else ""


def abs_url(src: str, page_url: str) -> str:
    if src.startswith("http"):
        return src
    return urllib.parse.urljoin(page_url, src)


def download_images(content: str, post_url: str, assets_dir: str) -> str:
    """Download article images and rewrite their ``src`` paths."""
    os.makedirs(assets_dir, exist_ok=True)

    def repl(m):
        tag, src = m.group(0), m.group(1)
        if src.startswith("data:"):
            return tag
        try:
            img_url = abs_url(src, post_url)
            ext = os.path.splitext(urllib.parse.urlparse(img_url).path)[1] or ".png"
            fname = f"img{len(os.listdir(assets_dir))}{ext}"
            data = fetch(img_url)
            if isinstance(data, str):
                data = data.encode("utf-8", "replace")
            with open(os.path.join(assets_dir, fname), "wb") as f:
                f.write(data)
            return tag.replace(src, os.path.join("assets", fname))
        except Exception as e:
            print(f"    image fail {src}: {e}", file=sys.stderr)
            return tag

    return re.sub(r'<img[^>]*src="([^"]+)"[^>]*>', repl, content)


def page_url(n: int) -> str:
    return BASE if n == 1 else f"{BASE}/page/{n}/"


def load_existing_posts(index_path: str) -> list[dict]:
    """Load the previous manifest; a missing or invalid index is an empty one."""
    try:
        with open(index_path, encoding="utf-8") as handle:
            return json.load(handle).get("posts", [])
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return []


def merge_manifest(discovered: list[dict], existing: list[dict]) -> list[dict]:
    """Merge manifests by canonical URL while preferring newly discovered data."""
    by_link = {item.get("link"): item for item in existing if item.get("link")}
    for item in discovered:
        if item.get("link"):
            by_link[item["link"]] = item
    return sorted(
        by_link.values(),
        key=lambda item: (item.get("date", ""), item.get("link", "")),
        reverse=True,
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=os.path.dirname(os.path.abspath(__file__)))
    ap.add_argument("--limit", type=int, default=0, help="Scan only the first N pages (0=all)")
    ap.add_argument("--delay", type=float, default=1.0, help="Delay between requests in seconds")
    ap.add_argument("--with-images", action="store_true", help="Download article images")
    args = ap.parse_args()

    outdir = os.path.join(args.out, "posts")
    os.makedirs(outdir, exist_ok=True)

    index_path = os.path.join(args.out, "index.json")
    existing = load_existing_posts(index_path)
    existing_by_link = {item["link"]: item for item in existing if item.get("link")}
    manifest = []
    seen_links = set()
    page = 1
    while True:
        if args.limit and page > args.limit:
            print(f"Reached --limit before page {page}")
            break
        url = page_url(page)
        print(f"[page {page}] {url}")
        try:
            html = fetch(url)
        except urllib.error.HTTPError as e:
            if e.code == 404:
                print(f"  Page {page} returned 404; archive boundary reached")
                break
            raise
        posts = parse_list(html)
        if not posts:
            print("  No posts found; stopping")
            break
        print(f"  Found {len(posts)} posts")

        for title, link, date_iso in posts:
            try:
                if link in seen_links:
                    continue
                seen_links.add(link)
                date = (date_iso or "")[:10] or "0000-00-00"
                dt = datetime.fromisoformat((date_iso or "1970-01-01T00:00:00+00:00").replace("Z", "+00:00"))
                date = dt.strftime("%Y-%m-%d")
                previous = existing_by_link.get(link, {})
                fname = previous.get("file") or f"{date}-{safe_name(title)}.html"
                fpath = os.path.join(outdir, fname)
                if os.path.exists(fpath):
                    print(f"  skip (exists): {fname}")
                    manifest.append({"title": title, "date": date, "link": link, "file": fname})
                    continue
                phtml = fetch(link)
                content = parse_content(phtml)
                if args.with_images:
                    content = download_images(content, link, os.path.join(outdir, fname + "_assets"))
                html_doc = (
                    f"<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"utf-8\">"
                    f"<title>{title}</title><link rel=\"canonical\" href=\"{link}\"></head>"
                    f"<body><h1>{title}</h1><p><small>Source: <a href=\"{link}\">{link}</a> | "
                    f"Published: {date}</small></p><article>{content}</article></body></html>"
                )
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(html_doc)
                manifest.append({"title": title, "date": date, "link": link, "file": fname})
                print(f"  saved: {fname}")
            except Exception as e:
                print(f"  ERROR {link}: {e}", file=sys.stderr)
            time.sleep(args.delay)

        page += 1
        time.sleep(args.delay)

    manifest = merge_manifest(manifest, existing)
    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(
            {"base": BASE, "crawled_at": datetime.now(timezone.utc).isoformat(),
             "count": len(manifest), "posts": manifest},
            f, ensure_ascii=False, indent=2,
        )
    print(f"\nDone. Indexed {len(manifest)} posts in index.json")


if __name__ == "__main__":
    main()
