#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Legacy Playwright fallback for Tableau Public screenshots.

Prefer ``download_all.py``. This script remains useful when the direct HTTP
preview endpoint cannot capture a specific view.
"""
import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone

PROJECT = os.path.dirname(os.path.abspath(__file__))
POSTS = os.path.join(PROJECT, "posts")
OUT = os.path.join(PROJECT, "dashboards")
LINK_RE = re.compile(r"https?://public\.tableau\.com[^\s\"'<>]+", re.I)


def extract_viz(html):
    out = []
    for raw in LINK_RE.findall(html):
        u = raw.rstrip(").,;")
        m = re.search(r"/vizhome/([^/?#]+)/([^/?#]+)", u)
        if not m:
            continue
        wb, view = m.group(1), m.group(2)
        out.append((wb, view, f"https://public.tableau.com/views/{wb}/{view}"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--try-twbx", action="store_true", help="Try the toolbar TWBX export")
    ap.add_argument("--delay", type=float, default=1.0)
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    tasks = []
    for fn in sorted(os.listdir(POSTS)):
        if not fn.endswith(".html"):
            continue
        stem = fn[:-5]
        html = open(os.path.join(POSTS, fn), encoding="utf-8", errors="replace").read()
        vizzes = extract_viz(html)
        if vizzes:
            tasks.append((stem, vizzes))

    flat = []
    for stem, vizzes in tasks:
        for wb, view, url in vizzes:
            flat.append((stem, wb, view, url))
    if args.limit:
        flat = flat[: args.limit]
    # Deduplicate workbooks referenced by several articles.
    seen = set()
    dedup = []
    for t in flat:
        if t[1] in seen:
            continue
        seen.add(t[1])
        dedup.append(t)
    flat = dedup

    os.makedirs(OUT, exist_ok=True)
    manifest = []
    mpath = os.path.join(OUT, "manifest.json")
    # Resume from either manifest state or an existing PNG.
    done = set()
    if os.path.exists(mpath):
        try:
            old = json.load(open(mpath, encoding="utf-8"))
            for it in old.get("items", []):
                if it.get("png"):
                    done.add(it["workbook"])
        except Exception:
            pass
    for root, _, files in os.walk(OUT):
        for f in files:
            if f.endswith(".png"):
                done.add(f[:-4])
    if done:
        flat = [t for t in flat if t[1] not in done]
        print(f"Resume: skipped {len(done)} completed views; {len(flat)} remain")
    print(f"Views pending: {len(flat)} ({len(seen)} unique workbooks)")

    def save_manifest():
        with open(mpath, "w", encoding="utf-8") as f:
            json.dump({"crawled_at": datetime.now(timezone.utc).isoformat(),
                       "count": len(manifest), "items": manifest}, f, ensure_ascii=False, indent=2)

    LANUNCH_ARGS = ["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu",
                    "--disable-extensions", "--no-first-run", "--disable-background-networking"]

    def new_browser(pw):
        return pw.chromium.launch(headless=True, args=LANUNCH_ARGS)

    with sync_playwright() as pw:
        browser = new_browser(pw)
        for i, (stem, wb, view, url) in enumerate(flat, 1):
            ddir = os.path.join(OUT, stem)
            os.makedirs(ddir, exist_ok=True)
            rec = {"article": stem, "workbook": wb, "view": view, "url": url,
                   "png": None, "twbx": None, "note": ""}
            print(f"[{i}/{len(flat)}] {stem} :: {wb}")
            ctx = None
            try:
                ctx = browser.new_context(viewport={"width": 1280, "height": 900})
                page = ctx.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=60000)
                try:
                    page.wait_for_selector("canvas, .tab-zone", timeout=20000)
                except Exception:
                    pass
                time.sleep(2)
                fr = None
                for f in page.frames:
                    if "viz" in (f.url or ""):
                        fr = f
                        break
                png_path = os.path.join(ddir, f"{wb}.png")
                # Prefer the embedded view body; fall back to the full page.
                try:
                    if fr is not None:
                        fr.locator("body").screenshot(path=png_path, timeout=30000)
                    else:
                        page.screenshot(path=png_path, timeout=30000)
                except Exception:
                    page.screenshot(path=png_path, timeout=30000)
                rec["png"] = os.path.relpath(png_path, PROJECT)
                print(f"   PNG ok -> {rec['png']}")
                rec["note"] = "twbx skipped (author disabled downloads)"
            except Exception as e:
                rec["note"] = (rec["note"] + "; ").strip("; ") + f"failed: {type(e).__name__}: {e}"
                print(f"   ERR {rec['note']}")
                # Recreate the browser after a crash.
                try:
                    if browser is not None:
                        browser.close()
                except Exception:
                    pass
                try:
                    browser = new_browser(pw)
                except Exception:
                    pass
            finally:
                try:
                    if ctx is not None:
                        ctx.close()
                except Exception:
                    pass
                manifest.append(rec)
                save_manifest()  # Persist progress after every item.
                time.sleep(args.delay)

        try:
            browser.close()
        except Exception:
            pass

    ok_png = sum(1 for r in manifest if r["png"])
    ok_twbx = sum(1 for r in manifest if r["twbx"])
    print(f"\nDone. PNG={ok_png} TWBX={ok_twbx}; manifest -> dashboards/manifest.json")


if __name__ == "__main__":
    main()
