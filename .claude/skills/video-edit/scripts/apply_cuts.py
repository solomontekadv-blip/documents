#!/usr/bin/env python3
"""Apply cut_list.json: render build/cut.mov (1080x1920, 30fps) and remap word times.

Segment edges are snapped outward to the 30fps frame grid so audio and video stay in
sync over many cuts, and each segment gets an 8ms audio fade so cuts never click.

The voice stays lossless PCM until the final mix, so the output is a .mov (mp4 cannot hold PCM).

Usage: python3 apply_cuts.py raw-take.mov build/cut_list.json build/words.json build/cut.mov build/words_cut.json
"""
import argparse
import json
import math
import os
import subprocess
import tempfile

FPS = 30
W, H = 1080, 1920
FADE = 0.008


def snap(segs, duration):
    out = []
    for s, e in segs:
        s = math.floor(s * FPS) / FPS
        e = min(math.ceil(e * FPS) / FPS, duration)
        if out and s <= out[-1][1]:
            out[-1][1] = max(out[-1][1], e)
        elif e - s >= 1 / FPS:
            out.append([s, e])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("cut_list")
    ap.add_argument("words")
    ap.add_argument("out_video")
    ap.add_argument("out_words")
    a = ap.parse_args()
    if not a.out_video.endswith(".mov"):
        ap.error("out_video must be a .mov (lossless PCM voice)")

    cl = json.load(open(a.cut_list, encoding="utf-8"))
    wd = json.load(open(a.words, encoding="utf-8"))
    segs = snap(cl["keep"], wd["duration"])
    n = len(segs)

    f = [f"[0:v]fps={FPS},scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,split={n}"
         + "".join(f"[vs{i}]" for i in range(n)) + ";",
         f"[0:a]aresample=48000,asplit={n}" + "".join(f"[as{i}]" for i in range(n)) + ";"]
    for i, (s, e) in enumerate(segs):
        d = e - s
        f.append(f"[vs{i}]trim=start={s:.4f}:end={e:.4f},setpts=PTS-STARTPTS[v{i}];")
        f.append(f"[as{i}]atrim=start={s:.4f}:end={e:.4f},asetpts=PTS-STARTPTS,"
                 f"afade=t=in:d={FADE},afade=t=out:st={max(0, d - FADE):.4f}:d={FADE}[a{i}];")
    f.append("".join(f"[v{i}][a{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v][a]")

    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as tf:
        tf.write("\n".join(f))
        script = tf.name
    os.makedirs(os.path.dirname(os.path.abspath(a.out_video)), exist_ok=True)
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", a.media,
                    "-filter_complex_script", script, "-map", "[v]", "-map", "[a]",
                    "-c:v", "libx264", "-preset", "fast", "-crf", "14", "-pix_fmt", "yuv420p",
                    "-c:a", "pcm_s16le", "-ar", "48000", a.out_video], check=True)
    os.unlink(script)

    words, offset = [], 0.0
    for s, e in segs:
        for w in wd["words"]:
            if w["s"] >= s - 0.01 and w["e"] <= e + 0.05:
                words.append({"i": len(words), "w": w["w"], "src": w["i"],
                              "s": round(offset + max(0.0, w["s"] - s), 3),
                              "e": round(offset + min(e, w["e"]) - s, 3)})
        offset += e - s
    with open(a.out_words, "w", encoding="utf-8") as fh:
        json.dump({"source": a.out_video, "language": wd.get("language"), "duration": round(offset, 3),
                   "words": words}, fh, ensure_ascii=False, indent=1)
    dropped = len(wd["words"]) - len(words)
    print(f"{n} segments -> {a.out_video} ({offset:.2f}s), {len(words)} words kept, {dropped} dropped -> {a.out_words}")


if __name__ == "__main__":
    main()
