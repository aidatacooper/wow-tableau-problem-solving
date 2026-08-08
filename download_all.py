#!/usr/bin/env python3
"""Incrementally download Tableau Public workbooks and missing views.

Use ``--refresh`` to crawl newly published posts and rebuild the link map
before downloading. Existing non-empty TWBX and PNG files are reused.
"""
import os
import re
import sys
import json
import time
import ssl
import argparse
import subprocess
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

PROJECT = os.path.dirname(os.path.abspath(__file__))
POSTS = os.path.join(PROJECT, "posts")
DASH = os.path.join(PROJECT, "dashboards")
MAPJSON = os.path.join(PROJECT, "public_links_map.json")
MANIFEST = os.path.join(DASH, "manifest.json")

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"


def clean_url(u):
    return u.rstrip(").,;").strip()


def collect():
    with open(MAPJSON, encoding="utf-8") as f:
        data = json.load(f)
    pairs = set()  # (workbook, view)
    article_map = {}  # workbook -> set(articles)
    for it in data["items"]:
        art = it["article"]
        for lk in it["links"]:
            wb = lk.get("workbook")
            view = lk.get("view")
            if not wb:
                continue
            pairs.add((wb, view or wb))
            article_map.setdefault(wb, set()).add(art)
    workbooks = sorted({wb for wb, _ in pairs})
    return workbooks, sorted(pairs), article_map


def refresh_sources():
    """Crawl new posts and rebuild the link map before downloading assets."""
    subprocess.run([sys.executable, os.path.join(PROJECT, "crawler.py")], check=True)
    subprocess.run([sys.executable, os.path.join(PROJECT, "gen_links_map.py")], check=True)


def fetch(url, timeout=60, max_retry=12):
    last = None
    for attempt in range(max_retry):
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": UA, "Referer": "https://public.tableau.com/"},
            )
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as r:
                return r.read(), r.status
        except urllib.error.HTTPError as e:
            if e.code == 429:
                # Respect Retry-After, with a 60-second minimum cooldown.
                wait = 60
                try:
                    rv = int(e.headers.get("Retry-After", "60"))
                    wait = max(60, rv)
                except Exception:
                    pass
                print(f"  [429] {url[:70]} waiting {wait}s ({attempt+1}/{max_retry})", flush=True)
                time.sleep(wait)
                last = e
                continue
            if e.code >= 500:
                time.sleep(min(2 ** attempt, 60))
                last = e
                continue
            raise
        except Exception as e:
            time.sleep(min(2 ** attempt, 60))
            last = e
    if last:
        raise last
    raise RuntimeError("unknown")


def png_url(wb, view):
    seg = wb[:2]
    return f"https://public.tableau.com/static/images/{seg}/{wb}/{view}/4_3_hd.png"


def twb_url(wb):
    return f"https://public.tableau.com/workbooks/{wb}.twb"


def update_manifest(article_map):
    # Recount files from disk so interrupted runs remain recoverable.
    twbx_ok = 0
    png_ok = 0
    wb_dirs = 0
    if os.path.isdir(DASH):
        for name in os.listdir(DASH):
            d = os.path.join(DASH, name)
            if not os.path.isdir(d):
                continue
            wb_dirs += 1
            for fn in os.listdir(d):
                p = os.path.join(d, fn)
                if fn.endswith(".twbx") and os.path.getsize(p) > 0:
                    twbx_ok += 1
                elif fn.endswith(".png") and os.path.getsize(p) > 0:
                    png_ok += 1
    manifest = {
        "unique_workbooks": wb_dirs,
        "twbx_ok": twbx_ok,
        "png_ok": png_ok,
        "workbook_to_articles": {k: sorted(v) for k, v in article_map.items()},
    }
    os.makedirs(DASH, exist_ok=True)
    with open(MANIFEST, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    return manifest


def workbook_complete(wb, views, dash_root=DASH):
    """Return true only when the workbook and every currently known view exist."""
    directory = os.path.join(dash_root, wb)
    twbx = os.path.join(directory, wb + ".twbx")
    if not (os.path.exists(twbx) and os.path.getsize(twbx) > 0):
        return False
    return all(
        os.path.exists(os.path.join(directory, view + ".png"))
        and os.path.getsize(os.path.join(directory, view + ".png")) > 0
        for view in views
    )


def process_workbook(wb, views, delay=1.2):
    time.sleep(delay)  # Keep requests slow enough to avoid repeated 429s.
    d = os.path.join(DASH, wb)
    os.makedirs(d, exist_ok=True)
    # Download the workbook only when missing.
    twbx_path = os.path.join(d, wb + ".twbx")
    twbx_done = os.path.exists(twbx_path) and os.path.getsize(twbx_path) > 0
    if not twbx_done:
        try:
            data, _ = fetch(twb_url(wb))
            with open(twbx_path, "wb") as f:
                f.write(data)
        except Exception as e:
            print(f"  [twbx failed] {wb}: {e}", flush=True)
            return False, len(views)
    # Download only missing views, including views discovered after the TWBX.
    ok = 0
    for v in views:
        p = os.path.join(d, v + ".png")
        if os.path.exists(p) and os.path.getsize(p) > 0:
            ok += 1
            continue
        try:
            data, _ = fetch(png_url(wb, v))
            with open(p, "wb") as f:
                f.write(data)
            ok += 1
        except Exception as e:
            print(f"  [png failed] {wb}/{v}: {e}", flush=True)
        time.sleep(delay * 0.5)
    return True, ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--refresh", action="store_true", help="Crawl new posts and rebuild the link map first")
    ap.add_argument("--max-items", type=int, default=0, help="Maximum workbooks this run (0=all)")
    ap.add_argument("--workers", type=int, default=1, help="Concurrent workers (default 1)")
    ap.add_argument("--delay", type=float, default=1.2, help="Delay before each workbook in seconds")
    args = ap.parse_args()

    if args.refresh:
        refresh_sources()
    workbooks, pairs, article_map = collect()
    wb_views = {}
    for wb, v in pairs:
        wb_views.setdefault(wb, set()).add(v)

    todo = [
        wb
        for wb in workbooks
        if not workbook_complete(wb, wb_views.get(wb, {wb}))
    ]

    if args.max_items > 0:
        todo = todo[: args.max_items]

    print(f"workbooks={len(workbooks)} pending={len(todo)} this_run={len(todo)}", flush=True)

    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(process_workbook, wb, sorted(wb_views.get(wb, {wb})), args.delay): wb for wb in todo}
        for fut in as_completed(futs):
            wb = futs[fut]
            try:
                res = fut.result()
            except Exception as e:
                print(f"  [error] {wb}: {e}", flush=True)
                res = (False, 0)
            done += 1
            if done % 5 == 0 or done == len(todo):
                m = update_manifest(article_map)
                print(f"progress {done}/{len(todo)} | workbooks={m['unique_workbooks']} twbx={m['twbx_ok']} png={m['png_ok']}", flush=True)
    m = update_manifest(article_map)
    print("Done:", json.dumps({k: m[k] for k in ('unique_workbooks','twbx_ok','png_ok')}))


if __name__ == "__main__":
    main()
