#!/usr/bin/env python3
"""Download a real app icon (1024px) from the Apple App Store. Never draw a stand-in.

Usage: python3 fetch_icon.py "Notion" assets/icons/notion.png [--country il] [--pick N]
Prints the matches; saves the first one (or --pick N). Check the printed name is the right app.
"""
import argparse
import json
import os
import sys
import urllib.parse
import urllib.request


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("app")
    ap.add_argument("out")
    ap.add_argument("--country", default="us")
    ap.add_argument("--pick", type=int, default=0)
    a = ap.parse_args()

    q = urllib.parse.urlencode({"term": a.app, "entity": "software", "limit": 5, "country": a.country})
    with urllib.request.urlopen(f"https://itunes.apple.com/search?{q}", timeout=20) as r:
        results = json.load(r)["results"]
    if not results:
        sys.exit(f"No App Store match for '{a.app}'. Try the exact app name, or --country il.")
    for n, app in enumerate(results):
        print(f"  [{n}] {app['trackName']} - {app.get('sellerName', '')}")
    app = results[a.pick]
    url = app["artworkUrl512"].replace("512x512bb", "1024x1024bb").replace(".jpg", ".png")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    urllib.request.urlretrieve(url, a.out)
    print(f"saved [{a.pick}] {app['trackName']} -> {a.out}")


if __name__ == "__main__":
    main()
