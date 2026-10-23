#!/usr/bin/env python3
"""Word-level transcript with Whisper.

Uses mlx-whisper on Apple Silicon, openai-whisper everywhere else.
Writes JSON: {"source", "language", "duration", "words": [{"i", "w", "s", "e"}]}

Usage: python3 transcribe.py raw-take.mov build/words.json [--lang he] [--model NAME]
"""
import argparse
import json
import subprocess
import sys

MLX_DEFAULT = "mlx-community/whisper-large-v3-turbo"
OPENAI_DEFAULT = "turbo"


def duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", path],
        capture_output=True, text=True, check=True).stdout.strip()
    return float(out)


def run_mlx(path, lang, model):
    import mlx_whisper
    return mlx_whisper.transcribe(path, path_or_hf_repo=model or MLX_DEFAULT,
                                  word_timestamps=True, language=lang,
                                  condition_on_previous_text=False)


def run_openai(path, lang, model):
    import whisper
    m = whisper.load_model(model or OPENAI_DEFAULT)
    return m.transcribe(path, word_timestamps=True, language=lang,
                        condition_on_previous_text=False)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("out")
    ap.add_argument("--lang", default=None, help="he, en ... (default: auto-detect)")
    ap.add_argument("--model", default=None)
    a = ap.parse_args()

    try:
        import mlx_whisper  # noqa: F401
        result = run_mlx(a.media, a.lang, a.model)
    except ImportError:
        try:
            result = run_openai(a.media, a.lang, a.model)
        except ImportError:
            sys.exit("No Whisper found. Apple Silicon: pip3 install mlx-whisper. Otherwise: pip3 install openai-whisper")

    words = []
    for seg in result.get("segments", []):
        for w in seg.get("words", []):
            text = w["word"].strip()
            if not text:
                continue
            words.append({"i": len(words), "w": text,
                          "s": round(float(w["start"]), 3), "e": round(float(w["end"]), 3)})

    data = {"source": a.media, "language": result.get("language", a.lang),
            "duration": duration(a.media), "words": words}
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"{len(words)} words, language={data['language']}, {data['duration']:.2f}s -> {a.out}")


if __name__ == "__main__":
    main()
