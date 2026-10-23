#!/usr/bin/env python3
"""Build the cut list: shorten pauses to 0.25s (only inside true silence) and drop retakes.

Words are never cut: every cut stays at least GUARD seconds away from any kept word.
Retakes are found by a repeated 3-word phrase restarting within 30 words; the first
attempt is dropped. Review the list: add or remove cuts by editing cut_list.json and
re-running with --from-json, which only re-renders the .md and keep segments.

Usage:
  python3 cutlist.py raw-take.mov build/words.json build/cut_list.json [--noise -35] [--pause 0.25]
  python3 cutlist.py raw-take.mov build/words.json build/cut_list.json --from-json
Writes cut_list.json (machine) and cut_list.md (for review) next to each other.
"""
import argparse
import json
import os
import re
import subprocess

GUARD = 0.03      # never cut closer than this to a word edge
HEAD = 0.15       # silence kept before the first word
TAIL = 0.30       # silence kept after the last word
NGRAM = 3
RETAKE_WINDOW = 30


def silences(media, noise_db, min_d):
    p = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", media, "-vn", "-af",
                        f"silencedetect=noise={noise_db}dB:d={min_d}", "-f", "null", "-"],
                       capture_output=True, text=True)
    out, starts = [], []
    for line in p.stderr.splitlines():
        m = re.search(r"silence_start: ([\d.]+)", line)
        if m:
            starts.append(float(m.group(1)))
        m = re.search(r"silence_end: ([\d.]+)", line)
        if m and starts:
            out.append((starts.pop(), float(m.group(1))))
    if starts:  # silence runs to the end of the file
        out.append((starts.pop(), float("inf")))
    return out


def norm(w):
    w = re.sub(r"[֑-ׇ]", "", w)          # Hebrew niqqud / cantillation
    return re.sub(r"[^\w]", "", w.lower())


def find_retakes(words, pause):
    n = [norm(w["w"]) for w in words]
    cuts, i = [], 0
    while i < len(words) - NGRAM:
        hit = None
        if all(n[i:i + NGRAM]):
            for j in range(i + 1, min(len(words) - NGRAM + 1, i + RETAKE_WINDOW)):
                if n[j:j + NGRAM] == n[i:i + NGRAM]:
                    hit = j
                    break
        if hit is not None:
            # keep the second attempt: cut from the first attempt's first word up to the second's start
            # keep one natural pause (<= PAUSE) after the previous word, drop the rest up to the second attempt
            start = words[i]["s"] - GUARD
            if i > 0:
                prev_e = words[i - 1]["e"]
                start = max(prev_e, min(start, prev_e + pause))
            cuts.append({"start": round(start, 3), "end": round(words[hit]["s"] - GUARD, 3),
                         "reason": "retake",
                         "text": " ".join(w["w"] for w in words[i:hit])})
            i = hit
        else:
            i += 1
    return cuts


def pause_cuts(words, sil, pause, duration):
    cuts = []
    half = pause / 2

    def cut_inside(lo, hi, reason):
        for ss, se in sil:
            a, b = max(ss, lo), min(se, hi)
            if b - a > pause:
                cuts.append({"start": round(a + half, 3), "end": round(b - half, 3),
                             "reason": reason, "text": f"pause {b - a:.2f}s -> {pause:.2f}s"})

    if words:
        first, last = words[0], words[-1]
        for ss, se in sil:  # head and tail: keep only HEAD / TAIL of silence
            if ss <= 0.05 and min(se, first["s"] - GUARD) > HEAD:
                cuts.append({"start": 0.0, "end": round(min(se, first["s"] - GUARD) - HEAD, 3),
                             "reason": "head", "text": "silence before first word"})
            if se == float("inf") or se >= duration - 0.05:
                a = max(ss, last["e"] + GUARD) + TAIL
                if a < duration:
                    cuts.append({"start": round(a, 3), "end": round(duration, 3),
                                 "reason": "tail", "text": "silence after last word"})
        for a, b in zip(words, words[1:]):
            if b["s"] - a["e"] > pause:
                cut_inside(a["e"], b["s"], "pause")  # half-pause margins (0.125s) already exceed GUARD
    return cuts


def merge(cuts):
    cuts = sorted((c for c in cuts if c["end"] > c["start"]), key=lambda c: c["start"])
    out = []
    for c in cuts:
        if out and c["start"] <= out[-1]["end"]:
            prev = out[-1]
            prev["end"] = max(prev["end"], c["end"])
            if c["reason"] not in prev["reason"].split("+"):
                prev["reason"] += "+" + c["reason"]
            prev["text"] += " | " + c["text"]
        else:
            out.append(dict(c))
    return out


def keeps(cuts, duration):
    segs, t = [], 0.0
    for c in cuts:
        if c["start"] > t:
            segs.append([round(t, 3), round(c["start"], 3)])
        t = max(t, c["end"])
    if t < duration:
        segs.append([round(t, 3), round(duration, 3)])
    return [s for s in segs if s[1] - s[0] > 0.02]


def fmt(t):
    return f"{int(t // 60):02d}:{t % 60:06.3f}"


def write_md(path, data, words):
    kept = sum(e - s for s, e in data["keep"])
    lines = [f"# Cut list - {os.path.basename(data['source'])}", "",
             f"Raw: {data['duration']:.2f}s  ->  Cut: {kept:.2f}s  (removed {data['duration'] - kept:.2f}s)", "",
             "| # | From | To | Length | Why | What |", "|---|------|----|--------|-----|------|"]
    for n, c in enumerate(data["cuts"], 1):
        what = c["text"].replace("|", "/")
        lines.append(f"| {n} | {fmt(c['start'])} | {fmt(c['end'])} | {c['end'] - c['start']:.2f}s | {c['reason']} | {what} |")
    kept_text = " ".join(w["w"] for w in words
                         if any(s <= w["s"] and w["e"] <= e + GUARD for s, e in data["keep"]))
    lines += ["", "## What stays", "", kept_text, ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("words")
    ap.add_argument("out")
    ap.add_argument("--noise", type=float, default=-35.0, help="silence threshold in dB (raise to -30 in a noisy room)")
    ap.add_argument("--pause", type=float, default=0.25)
    ap.add_argument("--from-json", action="store_true", help="keep edited cuts in out, just rebuild keep + md")
    a = ap.parse_args()

    wd = json.load(open(a.words, encoding="utf-8"))
    words, duration = wd["words"], wd["duration"]

    if a.from_json:
        data = json.load(open(a.out, encoding="utf-8"))
        cuts = merge(data["cuts"])
    else:
        sil = silences(a.media, a.noise, a.pause)
        retakes = find_retakes(words, a.pause)
        # a retake cut already leaves one pause of the right length, so pause cuts touching it go
        pauses = [c for c in pause_cuts(words, sil, a.pause, duration)
                  if not any(c["start"] < r["end"] and r["start"] < c["end"] for r in retakes)]
        cuts = merge(pauses + retakes)

    data = {"source": a.media, "duration": duration, "pause": a.pause, "noise_db": a.noise,
            "cuts": cuts, "keep": keeps(cuts, duration)}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    md = os.path.splitext(a.out)[0] + ".md"
    write_md(md, data, words)
    kept = sum(e - s for s, e in data["keep"])
    n_re = sum("retake" in c["reason"] for c in cuts)
    print(f"{len(cuts)} cuts ({n_re} retakes), {duration:.2f}s -> {kept:.2f}s. Review: {md}")


if __name__ == "__main__":
    main()
