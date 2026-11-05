"""Rebuild the article backlog using verified case metadata and local link data."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def url_key(value: str) -> str:
    parts = urlsplit(value)
    return parts.netloc.lower() + unquote(parts.path).rstrip("/")


def backlog() -> tuple[list[dict], dict]:
    index = json.loads((ROOT / "index.json").read_text(encoding="utf-8"))
    catalogue = json.loads((ROOT / "usage/case-index.json").read_text(encoding="utf-8"))
    links = json.loads((ROOT / "public_links_map.json").read_text(encoding="utf-8"))
    solved = [c for c in catalogue["cases"]
              if c["functional_status"] == "replicated"
              and c.get("verification_status") in {"verified", "historical"}]
    urls, files = set(), set()
    for case in solved:
        article = case.get("source", {}).get("article", {})
        if article.get("url"):
            urls.add(url_key(article["url"]))
        if article.get("path"):
            files.add(Path(article["path"]).name)
    link_counts = {item["html_file"]: item["link_count"] for item in links["items"]}
    pending = [dict(p, link_count=link_counts.get(p["file"], 0))
               for p in index["posts"]
               if url_key(p["link"]) not in urls and p["file"] not in files]
    summary = {
        "archive_crawled_at": index.get("crawled_at"),
        "articles": len(index["posts"]),
        "replicated_cases": len(solved),
        "remaining_articles": len(pending),
        "remaining_with_workbook_links": sum(p["link_count"] > 0 for p in pending),
        "remaining_without_workbook_links": sum(p["link_count"] == 0 for p in pending),
    }
    return pending, summary


def main() -> None:
    pending, summary = backlog()
    lines = ["# 未解决的 post（解题 backlog）", "",
             "由本地 `index.json`、`usage/case-index.json` 与 `public_links_map.json` 生成。",
             "只将 `functional_status: replicated` 且验收为 `verified` / `historical` 的案例计为已解决；优先按文章 URL 匹配，兼容仅有文章路径的历史记录。",
             "重新生成：`python scripts/refresh_unsolved_posts.py`。", "",
             f"- 文章归档时间：{summary['archive_crawled_at']}",
             f"- 目录文章总数：{summary['articles']}",
             f"- 已复现 case：{summary['replicated_cases']}",
             f"- 尚未解决的文章：{summary['remaining_articles']}",
             f"- 其中带 Tableau Public 链接：{summary['remaining_with_workbook_links']}",
             f"- 其中没有工作簿链接：{summary['remaining_without_workbook_links']}", "",
             "有链接不保证工作簿仍可下载；没有链接也不代表文章一定不是挑战。以上为本地归档口径，未检查新发布文章。", ""]
    counts = Counter(p["date"][:4] for p in pending)
    for year in sorted(counts, reverse=True):
        lines += [f"## {year}（{counts[year]}）", ""]
        for post in sorted((p for p in pending if p["date"].startswith(year)), key=lambda p: p["date"], reverse=True):
            suffix = "（无工作簿链接）" if not post["link_count"] else ""
            lines.append(f"- {post['date']} — [{post['title']}]({post['link']}){suffix}")
        lines.append("")
    (ROOT / "docs/unsolved-posts.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
