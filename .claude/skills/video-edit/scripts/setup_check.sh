#!/usr/bin/env bash
# Checks every tool the video-edit skill needs. Installs nothing; prints the fix for what is missing.
# Usage: bash setup_check.sh [project_dir]
PROJECT="${1:-.}"
missing=0
ok()   { printf '  OK       %s\n' "$1"; }
miss() { printf '  MISSING  %s\n           fix: %s\n' "$1" "$2"; missing=1; }

arch="$(uname -m)"; os="$(uname -s)"
apple_silicon=0; [[ "$os" == "Darwin" && "$arch" == "arm64" ]] && apple_silicon=1

echo "Checking tools ($os $arch)"
if [[ "$os" == "Darwin" ]]; then
  command -v brew >/dev/null 2>&1 && ok "Homebrew" || miss "Homebrew" 'paste the install line from https://brew.sh, then open a new Terminal window'
fi
command -v ffmpeg  >/dev/null 2>&1 && ok "ffmpeg"  || miss "ffmpeg"  "brew install ffmpeg"
command -v ffprobe >/dev/null 2>&1 && ok "ffprobe" || miss "ffprobe" "brew install ffmpeg"
command -v python3 >/dev/null 2>&1 && ok "python3" || miss "python3" "brew install python"
command -v pip3    >/dev/null 2>&1 && ok "pip3"    || miss "pip3"    "brew install python"

if python3 -c "import mlx_whisper" >/dev/null 2>&1; then ok "Whisper (mlx-whisper)"
elif python3 -c "import whisper" >/dev/null 2>&1; then ok "Whisper (openai-whisper)"
elif [[ $apple_silicon == 1 ]]; then miss "Whisper" "pip3 install mlx-whisper"
else miss "Whisper" "pip3 install openai-whisper   (mlx-whisper runs only on Apple Silicon)"
fi

command -v node >/dev/null 2>&1 && ok "Node.js $(node -v)" || miss "Node.js" "brew install node"
if command -v node >/dev/null 2>&1; then
  if (cd "$PROJECT" && node -e "require('puppeteer')" >/dev/null 2>&1); then
    ok "Puppeteer (in $PROJECT)"
    if [[ -z "$PUPPETEER_EXECUTABLE_PATH" ]] && ! (cd "$PROJECT" && node -e "const p=require('puppeteer');require('fs').accessSync(p.executablePath())" >/dev/null 2>&1); then
      miss "Chrome for Puppeteer" "cd $PROJECT && npx puppeteer browsers install chrome"
    fi
  else
    miss "Puppeteer" "cd $PROJECT && npm install puppeteer"
  fi
fi

if [[ $missing == 1 ]]; then
  echo
  echo 'Something is missing. After installing: "command not found"? Open a new Terminal window.'
  exit 1
fi
echo "All set."
