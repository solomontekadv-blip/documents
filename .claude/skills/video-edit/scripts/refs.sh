#!/usr/bin/env bash
# Prepare the reference videos for reading: a frame a second (as contact sheets), the transcript,
# and the graphic-change count, per video. Claude then reads them and writes moves.md.
# Usage: bash refs.sh references build/refs [--lang he]
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
src="${1:-references}"; out="${2:-build/refs}"; shift 2 || true
mkdir -p "$out"
shopt -s nullglob nocaseglob
for v in "$src"/*.{mp4,mov,m4v,webm}; do
  name="$(basename "${v%.*}")"; d="$out/$name"; mkdir -p "$d"
  echo "== $name"
  ffmpeg -hide_banner -loglevel error -y -i "$v" -vf "fps=1,scale=216:-2,tile=6x5" "$d/sheet_%02d.png"
  python3 "$here/transcribe.py" "$v" "$d/words.json" "$@"
  python3 -c "import json,sys;d=json.load(open(sys.argv[1]));print(' '.join(w['w'] for w in d['words']))" "$d/words.json" > "$d/transcript.txt"
  python3 "$here/count_changes.py" "$v" --region full | tee "$d/pace.txt"
done
echo "Done. Per reference: sheet_*.png (1 frame/s, 30 per sheet, read left-to-right, top-to-bottom), transcript.txt, pace.txt"
