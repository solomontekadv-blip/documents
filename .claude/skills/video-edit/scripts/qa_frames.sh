#!/usr/bin/env bash
# Screenshot the finished video every 0.25s, with Instagram's covered zones tinted red,
# and tile them into contact sheets (8x4 = 32 frames = 8 seconds per sheet) to look at.
# Usage: bash qa_frames.sh final.mp4 build/qa/frames
set -euo pipefail
in="$1"; out="${2:-build/qa/frames}"
rm -rf "$out"; mkdir -p "$out"
ffmpeg -hide_banner -loglevel error -i "$in" -vf "fps=4,\
drawbox=x=0:y=0:w=1080:h=220:color=red@0.30:t=fill,\
drawbox=x=0:y=1520:w=1080:h=400:color=red@0.30:t=fill,\
drawbox=x=950:y=220:w=130:h=1300:color=red@0.30:t=fill,\
drawbox=x=0:y=959:w=950:h=3:color=yellow@0.8:t=fill,\
scale=270:480,pad=276:486:3:3:white,tile=8x4" "$out/sheet_%02d.png"
n=$(ls "$out" | wc -l | tr -d ' ')
echo "$n sheet(s) in $out. Sheet k, row r, column c = time ((k-1)*32 + r*8 + c) * 0.25s (r, c from 0). Red = covered by Instagram, yellow line = top-half limit."
