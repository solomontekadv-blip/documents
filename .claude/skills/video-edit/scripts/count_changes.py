#!/usr/bin/env python3
"""Count graphic changes in videos with the same detector, so the numbers compare fairly.

A change = a scene-score jump in the region (default: the top half graphics zone).
Hits closer than 0.3s merge into one (a slam is several frames, not several changes).

Usage: python3 count_changes.py final.mp4 best.mp4 [--region top|full] [--threshold 0.12]
The first file is the candidate, the second is the edit to beat. Exit 2 if the candidate has fewer.
With one file it just prints the count (use it on references for moves.md).
"""
import argparse
import re
import subprocess

MERGE = 0.3


def changes(path, region, th):
    # crop as a fraction of the frame so references of any size work: top zone = y 220..960 / 1920, x 0..950 / 1080
    crop = "crop=iw*950/1080:ih*740/1920:0:ih*220/1920," if region == "top" else ""
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-an", "-vf",
                        f"{crop}scale=270:-2,select='gt(scene\\,{th})',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True)
    times = [float(t) for t in re.findall(r"pts_time:([\d.]+)", p.stderr)]
    merged = []
    for t in times:
        if not merged or t - merged[-1] > MERGE:
            merged.append(t)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
                               capture_output=True, text=True).stdout.strip())
    return merged, dur


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("videos", nargs="+")
    ap.add_argument("--region", choices=["top", "full"], default="top")
    ap.add_argument("--threshold", type=float, default=0.12)
    a = ap.parse_args()

    res = []
    for v in a.videos:
        ts, dur = changes(v, a.region, a.threshold)
        gaps = [b - x for x, b in zip([0.0] + ts, ts + [dur])]
        res.append((v, len(ts), dur))
        print(f"{v}: {len(ts)} changes in {dur:.1f}s = {len(ts) / dur * 10:.1f} per 10s, "
              f"longest hold {max(gaps):.1f}s")
    if len(res) >= 2:
        (cv, cn, cd), (bv, bn, bd) = res[0], res[1]
        if cn < bn:
            print(f"FEWER: {cv} has {cn}, {bv} has {bn}. Add at least {bn - cn} beats and render again.")
            raise SystemExit(2)
        print(f"OK: {cn} >= {bn}")


if __name__ == "__main__":
    main()
