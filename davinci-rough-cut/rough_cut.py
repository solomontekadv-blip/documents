#!/usr/bin/env python3
"""Rough cut for DaVinci Resolve Studio.

Transcribes the clip(s) on the current timeline, keeps the last complete take of
every sentence, removes silences, fillers and stutters, and builds the result as
a NEW timeline. The original timeline is never touched, and every clip in the
new timeline is a sub-range of the original media, so any cut can be trimmed
back open in the editor.
"""

import argparse
import glob
import hashlib
import json
import os
import re
import sys
from difflib import SequenceMatcher

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_MODEL = "ivrit-ai/whisper-large-v3-turbo-ct2"

# Nudges Whisper to write fillers out instead of silently dropping them.
FILLER_PROMPT = "אממ, אה, כן. אז, אה, היום אני, אממ, רוצה לדבר על..."

NIQQUD_RE = re.compile(r"[\u0591-\u05C7]")
PUNCT_RE = re.compile(r"[^\w]", re.UNICODE)
FINALS = str.maketrans("ךםןףץ", "כמנפצ")

# Checked on the raw word, before final letters are folded: a non-final mem
# ("אמ", "אממ") marks a filler, while "אם" (if) and "הם" (they) stay.
FILLER_RE = re.compile(
    r"^(א+ה+|א+ה*מ+|ה+מ+|מ+|אהם|אום|u+m+|u+h+|a+h+|e+h+|e+r+m*|h+m+|m+)$"
)

# Doubled words that are real Hebrew, not stutters ("לאט לאט", "מאוד מאוד").
DOUBLE_OK = {"מאוד", "לאט", "כנ", "לא", "רגע", "טוב", "שוב", "עוד", "הרבה", "יחד"}

MAX_BACK_WORDS = 80   # how far back a retake may reach, in words
MAX_BACK_SEC = 90.0   # and in seconds


class Params:
    def __init__(self, args):
        self.silence = args.silence
        self.pad_before = args.pad_before
        self.pad_after = args.pad_after
        self.min_len = 0.12
        self.coverage = 0.6
        self.stop_pause = 0.5


# ---------------------------------------------------------------- Resolve

def connect_resolve():
    try:
        import DaVinciResolveScript as dvr
    except ImportError:
        api = os.environ.get("RESOLVE_SCRIPT_API") or os.path.expandvars(
            r"%PROGRAMDATA%\Blackmagic Design\DaVinci Resolve\Support\Developer\Scripting")
        lib = os.environ.get("RESOLVE_SCRIPT_LIB") or \
            r"C:\Program Files\Blackmagic Design\DaVinci Resolve\fusionscript.dll"
        os.environ["RESOLVE_SCRIPT_API"] = api
        os.environ["RESOLVE_SCRIPT_LIB"] = lib
        sys.path.append(os.path.join(api, "Modules"))
        try:
            import DaVinciResolveScript as dvr
        except ImportError:
            die("Could not load the DaVinci Resolve scripting module. "
                "Is DaVinci Resolve Studio installed in the default location?")
    resolve = dvr.scriptapp("Resolve")
    if resolve is None:
        die("Could not connect to DaVinci Resolve. Make sure it is open and that "
            "Preferences > System > General > External scripting using = Local.")
    return resolve


def parse_fps(value):
    try:
        return float(str(value).split()[0])
    except (ValueError, IndexError):
        return None


def source_range(item):
    """Source in/out of a timeline item, in frames from the start of the media."""
    try:
        start = item.GetSourceStartFrame()  # Resolve 19+
    except Exception:
        start = None
    if start is None:
        start = item.GetLeftOffset()
    return int(start), int(start) + int(item.GetDuration())


def unique_timeline_name(project, base):
    names = {project.GetTimelineByIndex(i).GetName()
             for i in range(1, project.GetTimelineCount() + 1)}
    name, n = base, 2
    while name in names:
        name, n = f"{base} {n}", n + 1
    return name


# ---------------------------------------------------------------- Audio

def add_cuda_dll_dirs():
    """GPU libraries installed with pip are not on PATH on Windows."""
    if os.name != "nt":
        return
    for d in glob.glob(os.path.join(sys.prefix, "Lib", "site-packages", "nvidia", "*", "bin")):
        os.add_dll_directory(d)
        os.environ["PATH"] = d + os.pathsep + os.environ["PATH"]


def transcribe(path, model_name, language, force):
    st = os.stat(path)
    key = hashlib.sha1(f"{os.path.abspath(path)}|{st.st_size}|{st.st_mtime}|"
                       f"{model_name}|{language}".encode()).hexdigest()[:16]
    cache = os.path.join(HERE, "cache", key + ".json")
    if not force and os.path.exists(cache):
        print("  Using cached transcript.")
        with open(cache, encoding="utf-8") as f:
            return json.load(f)

    add_cuda_dll_dirs()
    import ctranslate2
    from faster_whisper import WhisperModel

    devices = ["cuda", "cpu"] if ctranslate2.get_cuda_device_count() > 0 else ["cpu"]
    for device in devices:
        try:
            print(f"  Transcribing on {device.upper()} with {model_name} "
                  "(first run downloads the model)...")
            model = WhisperModel(model_name, device=device,
                                 compute_type="float16" if device == "cuda" else "int8")
            segments, info = model.transcribe(
                path, language=language, word_timestamps=True, beam_size=5,
                vad_filter=True, vad_parameters={"min_silence_duration_ms": 500},
                condition_on_previous_text=False, initial_prompt=FILLER_PROMPT)
            words = []
            for seg in segments:
                for w in seg.words or []:
                    words.append({"w": w.word.strip(), "s": round(w.start, 3),
                                  "e": round(w.end, 3), "p": round(w.probability, 3)})
                print(f"\r  {seg.end / max(info.duration, 1):6.1%}", end="", flush=True)
            print()
            break
        except RuntimeError as e:
            if device == "cpu":
                raise
            print(f"\n  GPU failed ({e}); falling back to CPU.")

    os.makedirs(os.path.dirname(cache), exist_ok=True)
    with open(cache, "w", encoding="utf-8") as f:
        json.dump(words, f, ensure_ascii=False)
    return words


def load_energy(path):
    """Loudness in dB per 10 ms frame, or None if the audio can't be decoded."""
    try:
        import numpy as np
        from faster_whisper import decode_audio
        audio = decode_audio(path, sampling_rate=16000)
    except Exception as e:
        print(f"  Could not analyse audio levels ({e}); cutting on word timing only.")
        return None
    n = len(audio) // 160
    frames = audio[:n * 160].reshape(n, 160)
    return 20 * np.log10(np.sqrt((frames ** 2).mean(axis=1)) + 1e-9)


def silence_threshold(db):
    import numpy as np
    floor, speech = np.percentile(db, 10), np.percentile(db, 90)
    return floor + max(6.0, (speech - floor) * 0.25)


# ---------------------------------------------------------------- Edit decisions

def clean(text):
    return PUNCT_RE.sub("", NIQQUD_RE.sub("", text)).lower()


def norm(text):
    return clean(text).translate(FINALS)


def same_word(a, b):
    if a == b:
        return True
    if min(len(a), len(b)) < 3:
        return False
    return SequenceMatcher(None, a, b).ratio() >= 0.8


def fuzzy_lcs(a, b):
    prev = [0] * (len(b) + 1)
    for x in a:
        cur = [0]
        for j, y in enumerate(b):
            cur.append(prev[j] + 1 if same_word(x, y) else max(prev[j + 1], cur[j]))
        prev = cur
    return prev[-1]


def prefix_len(a, b):
    n = 0
    while n < len(a) and n < len(b) and same_word(a[n], b[n]):
        n += 1
    return n


def find_removals(words, p):
    """Returns (reason per word or None, list of (word indices, reason) for takes)."""
    n = len(words)
    N = [norm(w["w"]) for w in words]
    reason = [None] * n

    for i, w in enumerate(words):
        c = clean(w["w"])
        if not c or FILLER_RE.match(c):
            reason[i] = "filler"

    alive = [i for i in range(n) if reason[i] is None]
    for a, b in zip(alive, alive[1:]):
        if words[b]["s"] - words[a]["e"] > 0.6:
            continue
        if (N[a] == N[b] and N[a] not in DOUBLE_OK) or \
                (len(N[a]) <= 2 and len(N[b]) > len(N[a]) and N[b].startswith(N[a])):
            reason[a] = "stutter"

    # Walk forward. Whenever the next few words repeat words said shortly before,
    # the speaker restarted: drop the earlier attempt if the new one covers it,
    # or drop the new one if it stops short (an aborted retake of a finished line).
    seq = [i for i in range(n) if reason[i] is None]
    kept, takes = [], []
    pos = 0
    while pos < len(seq):
        y = seq[pos]
        accepted, false_start = False, None
        for k in (4, 3, 2):
            if pos + k > len(seq):
                continue
            probe = [N[seq[pos + t]] for t in range(k)]
            lo = max(0, len(kept) - MAX_BACK_WORDS)
            for xi in range(len(kept) - k, lo - 1, -1):
                if words[y]["s"] - words[kept[xi]]["s"] > MAX_BACK_SEC:
                    break
                if not all(same_word(N[kept[xi + t]], probe[t]) for t in range(k)):
                    continue
                span = [N[i] for i in kept[xi:]]
                after = [N[i] for i in seq[pos:pos + len(span) + 3]]
                if fuzzy_lcs(span, after) / len(span) >= p.coverage:
                    takes.append((kept[xi:], "retake"))
                    for i in kept[xi:]:
                        reason[i] = "retake"
                    del kept[xi:]
                    accepted = True
                    break
                if false_start is None:
                    false_start = prefix_len(span, [N[i] for i in seq[pos:]])
            if accepted:
                break

        if not accepted and false_start and false_start >= 2 and pos + false_start < len(seq):
            last, nxt = seq[pos + false_start - 1], seq[pos + false_start]
            if words[nxt]["s"] - words[last]["e"] >= p.stop_pause:
                group = seq[pos:pos + false_start]
                takes.append((group, "false start"))
                for i in group:
                    reason[i] = "false start"
                pos += false_start
                continue

        kept.append(y)
        pos += 1

    return reason, takes


def build_intervals(words, reason, db, thr, rng, p):
    """Seconds to keep, as sorted (start, end) pairs inside rng."""
    INF = float("inf")
    runs = []
    for i, r in enumerate(reason):
        if r is not None:
            continue
        if runs and i == runs[-1][-1] + 1 and words[i]["s"] - words[i - 1]["e"] < p.silence:
            runs[-1].append(i)
        else:
            runs.append([i])

    def loud(t):
        i = int(t * 100)
        return db is not None and 0 <= i < len(db) and db[i] > thr

    out = []
    for run in runs:
        first, last = run[0], run[-1]
        lo = words[first - 1]["e"] if first > 0 and reason[first - 1] else 0.0
        hi = words[last + 1]["s"] if last + 1 < len(words) and reason[last + 1] else INF
        s, e = words[first]["s"], words[last]["e"]
        # Whisper word edges drift; follow the actual sound a little further.
        t = s
        while t > s - 0.25 and t - 0.01 > lo and loud(t - 0.01):
            t -= 0.01
        s = max(t - p.pad_before, lo, rng[0])
        t = e
        while t < e + 0.35 and t + 0.01 < hi and loud(t):
            t += 0.01
        e = min(t + p.pad_after, hi, rng[1])
        if e > s:
            out.extend(split_on_silence(s, e, db, thr, p))

    merged = []
    for s, e in sorted(out):
        if merged and s - merged[-1][1] < 0.05:
            merged[-1][1] = max(merged[-1][1], e)
        else:
            merged.append([s, e])
    return [(s, e) for s, e in merged if e - s >= p.min_len]


def split_on_silence(s, e, db, thr, p):
    """Cut pauses inside a span that Whisper stretched words over."""
    if db is None:
        return [(s, e)]
    a, b = int(s * 100), min(int(e * 100), len(db))
    pieces, cur, i = [], s, a
    while i < b:
        if db[i] <= thr:
            j = i
            while j < b and db[j] <= thr:
                j += 1
            if (j - i) / 100 >= p.silence and i > a and j < b:
                cut_s, cut_e = i / 100 + p.pad_after, j / 100 - p.pad_before
                if cut_e > cut_s:
                    pieces.append((cur, cut_s))
                    cur = cut_e
            i = j
        else:
            i += 1
    pieces.append((cur, e))
    return pieces


# ---------------------------------------------------------------- Report

def tc(sec):
    sec = max(sec, 0)
    return f"{int(sec // 3600):02d}:{int(sec % 3600 // 60):02d}:{sec % 60:05.2f}"


def write_report(path, timeline_name, new_name, clips, p, dry_run):
    orig = sum(c["rng"][1] - c["rng"][0] for c in clips)
    new = sum(e - s for c in clips for s, e in c["keep"])
    lines = [
        f"חיתוך ראשון: {timeline_name}",
        "",
        "בדיקה בלבד, לא נוצר טיימליין." if dry_run else f"טיימליין חדש: {new_name}",
        "הטיימליין המקורי לא שונה.",
        f"אורך מקורי: {tc(orig)}   אורך אחרי חיתוך: {tc(new)}   ({new / max(orig, 1e-9):.0%})",
        f"הגדרות: שתיקה מעל {p.silence} שנ' נחתכת, מרווח לפני {p.pad_before} / אחרי {p.pad_after} שנ'",
        "",
    ]
    for c in clips:
        if len(clips) > 1:
            lines += [f"=== {os.path.basename(c['path'])} ===", ""]
        counts = {}
        for r in c["reason"]:
            if r:
                counts[r] = counts.get(r, 0) + 1
        heb = {"retake": "טייק קודם", "false start": "התחלה שנקטעה",
               "filler": "מילת מילוי", "stutter": "גמגום"}
        lines.append("מילים שהוסרו: " + ", ".join(
            f"{heb[k]} {v}" for k, v in counts.items()) if counts else "לא הוסרו מילים.")
        lines += ["", "טייקים שהוסרו (הזמן מתחילת קובץ המקור, וגם מרקר כחול בטיימליין החדש):", ""]
        for idx, why in c["takes"]:
            text = " ".join(c["words"][i]["w"] for i in idx)
            lines.append(f"[{tc(c['words'][idx[0]]['s'])}] {heb[why]}: {text}")
        if not c["takes"]:
            lines.append("אין.")
        lines += ["", "התמליל של החיתוך:", ""]
        kept = [w["w"] for w, r in zip(c["words"], c["reason"]) if r is None]
        lines += [" ".join(kept), ""]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8-sig") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------- Main

def die(msg):
    print("ERROR: " + msg)
    sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--silence", type=float, default=0.4,
                    help="cut pauses longer than this, in seconds (default 0.4)")
    ap.add_argument("--pad-before", type=float, default=0.10,
                    help="breathing room kept before speech (default 0.10)")
    ap.add_argument("--pad-after", type=float, default=0.15,
                    help="breathing room kept after speech (default 0.15)")
    ap.add_argument("--model", default=DEFAULT_MODEL,
                    help=f"Whisper model (default {DEFAULT_MODEL})")
    ap.add_argument("--language", default="he")
    ap.add_argument("--retranscribe", action="store_true",
                    help="ignore the cached transcript")
    ap.add_argument("--dry-run", action="store_true",
                    help="write the report only, don't build a timeline")
    ap.add_argument("--no-markers", action="store_true",
                    help="don't mark removed takes on the new timeline")
    args = ap.parse_args()
    p = Params(args)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")

    resolve = connect_resolve()
    project = resolve.GetProjectManager().GetCurrentProject()
    timeline = project and project.GetCurrentTimeline()
    if not timeline:
        die("Open the timeline you want to cut, then run again.")
    tl_name = timeline.GetName()
    tl_fps = parse_fps(timeline.GetSetting("timelineFrameRate"))
    items = timeline.GetItemListInTrack("video", 1) or timeline.GetItemListInTrack("audio", 1)
    if not items:
        die("Track V1 of the current timeline is empty.")
    print(f'Timeline "{tl_name}": {len(items)} clip(s) on track 1.')

    clips = []
    for n, item in enumerate(items, 1):
        mpi = item.GetMediaPoolItem()
        path = mpi and mpi.GetClipProperty("File Path")
        if not path or not os.path.exists(path):
            print(f"Clip {n}: no media file found, skipped.")
            continue
        fps = parse_fps(mpi.GetClipProperty("FPS")) or tl_fps
        if tl_fps and abs(fps - tl_fps) > 0.01:
            print(f"  Warning: clip is {fps} fps but the timeline is {tl_fps} fps.")
        f_in, f_out = source_range(item)
        rng = (f_in / fps, f_out / fps)
        print(f"Clip {n}: {os.path.basename(path)}  [{tc(rng[0])} - {tc(rng[1])}]")

        words = [w for w in transcribe(path, args.model, args.language, args.retranscribe)
                 if w["e"] > rng[0] and w["s"] < rng[1]]
        if not words:
            print("  No speech found, clip skipped.")
            continue
        db = load_energy(path)
        thr = None
        if db is not None:
            used = db[int(rng[0] * 100):int(rng[1] * 100)]
            thr = silence_threshold(used if len(used) else db)
        reason, takes = find_removals(words, p)
        keep = build_intervals(words, reason, db, thr, rng, p)
        clips.append({"item": item, "mpi": mpi, "path": path, "fps": fps, "rng": rng,
                      "words": words, "reason": reason, "takes": takes, "keep": keep})
        print(f"  {len(takes)} takes removed, {len(keep)} pieces kept.")

    if not clips:
        die("Nothing to cut.")

    safe = re.sub(r'[\\/:*?"<>|]', "_", tl_name)
    report = os.path.join(HERE, "output", f"{safe} - rough cut report.txt")
    new_name = None if args.dry_run else unique_timeline_name(project, f"{tl_name} - Rough Cut")
    write_report(report, tl_name, new_name, clips, p, args.dry_run)
    if args.dry_run:
        print(f"Dry run. Report: {report}")
        return

    media_pool = project.GetMediaPool()
    new_tl = media_pool.CreateEmptyTimeline(new_name)
    if not new_tl:
        die("Could not create the new timeline.")
    project.SetCurrentTimeline(new_tl)

    infos, markers, pos = [], [], 0
    for c in clips:
        fps, ti = c["fps"], 0
        takes = sorted(c["takes"], key=lambda t: c["words"][t[0][0]]["s"])
        for s, e in c["keep"]:
            while ti < len(takes) and c["words"][takes[ti][0][0]]["s"] < e:
                idx, why = takes[ti]
                text = " ".join(c["words"][i]["w"] for i in idx)
                markers.append((pos, why, text))
                ti += 1
            a, b = int(round(s * fps)), int(round(e * fps)) - 1
            if b >= a:
                infos.append({"mediaPoolItem": c["mpi"], "startFrame": a, "endFrame": b})
                pos += b - a + 1
        for idx, why in takes[ti:]:
            markers.append((max(pos - 1, 0), why, " ".join(c["words"][i]["w"] for i in idx)))

    if not media_pool.AppendToTimeline(infos):
        die("DaVinci Resolve refused to add the clips to the new timeline.")
    if not args.no_markers:
        by_frame = {}
        for frame, why, text in markers:
            by_frame.setdefault(frame, []).append(text)
        for frame, texts in by_frame.items():
            new_tl.AddMarker(frame, "Blue", "Removed take", " | ".join(texts)[:500], 1)

    print(f'Done. New timeline "{new_name}" with {len(infos)} pieces.')
    print(f"Report: {report}")


if __name__ == "__main__":
    main()
