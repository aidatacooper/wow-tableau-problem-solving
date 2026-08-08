"""Fetch the freshest render of a view via REST (maxage=0) and report the
row-background colours of the table, so fidelity can be verified without
eyeballing a PNG.

Usage:
    python pixel_check.py <view_id> [out.png]
"""
import hashlib
import re
import sys

import requests
from dotenv import dotenv_values
from PIL import Image

ENV = dotenv_values(r"C:/Users/imgwho/Desktop/projects/20260227-cwtwb/.env")
API = "3.18"


def signin():
    r = requests.post(
        f"{ENV['TABLEAU_SERVER']}/api/{API}/auth/signin",
        json={"credentials": {
            "personalAccessTokenName": ENV["TABLEAU_PAT_NAME"],
            "personalAccessTokenSecret": ENV["TABLEAU_PAT_SECRET"],
            "site": {"contentUrl": ENV["TABLEAU_SITE"]}}},
        headers={"Accept": "application/json"}, timeout=60)
    r.raise_for_status()
    c = r.json()["credentials"]
    return c["token"], c["site"]["id"]


def fetch(view_id, out_path):
    token, site_id = signin()
    url = (f"{ENV['TABLEAU_SERVER']}/api/{API}/sites/{site_id}"
           f"/views/{view_id}/image?maxage=0&resolution=high")
    r = requests.get(url, headers={"X-Tableau-Auth": token}, timeout=180)
    r.raise_for_status()
    with open(out_path, "wb") as fh:
        fh.write(r.content)
    print(f"  saved {out_path}  {len(r.content)} bytes  "
          f"md5={hashlib.md5(r.content).hexdigest()}")
    return out_path


def hexof(px):
    return "#%02x%02x%02x" % px[:3]


def row_profile(path, x_frac=0.16, label=""):
    """Walk down a vertical line and report each contiguous colour band."""
    img = Image.open(path).convert("RGB")
    w, h = img.size
    x = int(w * x_frac)
    print(f"--- {label or path}  size={w}x{h}  scanning x={x} ---")
    bands = []
    prev = None
    start = 0
    for y in range(h):
        c = img.getpixel((x, y))
        if c != prev:
            if prev is not None and y - start >= 6:
                bands.append((start, y - 1, prev))
            prev = c
            start = y
    if prev is not None and h - start >= 6:
        bands.append((start, h - 1, prev))
    for a, b, c in bands:
        print(f"   y {a:5d}-{b:5d} ({b - a + 1:4d}px)  {hexof(c)}")
    return bands


if __name__ == "__main__":
    view_id = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else "evidence/pixel_check.png"
    fetch(view_id, out)
    row_profile(out, label=out)
