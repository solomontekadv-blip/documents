#!/usr/bin/env python3
"""
detect.py - a five-check panel that scores how machine-written a draft looks.

What this is:  five local heuristics modelled on the signals public AI
detectors actually measure - sentence-length variation, concreteness, stock
vocabulary, typographic fingerprint, and voice. Every score is computed on
your machine from the text alone. Nothing is uploaded.

What this is NOT:  GPTZero, Originality, Copyleaks, Winston or Turnitin.
It does not call their APIs and it cannot promise their verdict. It catches
the things they all key on, which is why fixing them tends to move their
numbers too - but the only honest claim is the one on this line.

Each check returns a HUMAN score from 0 to 100. Higher is better.

Hebrew text (majority of letters) takes a Hebrew path through the same five
checks and the same verdict formula: SPECIFICITY counts numbers, number words,
money, legal nouns and quoted terms (hebtext.py); SLOP DENSITY uses the Hebrew
block of slop.json, prefix-aware; VOICE looks for first/second person and a
spoken register instead of English contractions; FINGERPRINT counts em/en
dashes, Hebrew gershayim/geresh and invisible characters. LRM/RLM bidi marks
are not penalised: Hebrew needs them in mixed text.

Usage
  python3 detect.py draft.txt
  pbpaste | python3 detect.py -
  python3 detect.py draft.txt --json
  python3 detect.py before.txt after.txt      # compare two drafts
"""

import argparse
import json
import os
import re
import statistics
import sys
import unicodedata

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))  # run from any folder, even with python3 -I
import hebtext as he

HERE = os.path.dirname(os.path.abspath(__file__))
LEX = os.path.join(HERE, "slop.json")

SENT_RE = re.compile(r"[^.!?\n]+[.!?]*")
WORD_RE = re.compile(r"[A-Za-z']+")
CONTRACTIONS = re.compile(r"\b\w+'(?:s|t|re|ve|ll|d|m)\b", re.IGNORECASE)
PRONOUNS = re.compile(r"\b(i|me|my|mine|we|us|our|you|your)\b", re.IGNORECASE)
NUMBERS = re.compile(r"\b\d[\d,.]*%?\b|\$\d")
PROPER = re.compile(r"(?<![.!?]\s)(?<!^)\b[A-Z][a-z]{2,}\b", re.MULTILINE)


def en_lexicon(lex):
    """The English view of slop.json: Hebrew entries and tells left out, so
    English scores are exactly what they were before Hebrew was added."""
    return {k: ([e for e in v if not (isinstance(e, dict) and e.get("lang") == "he")]
                if isinstance(v, list) else v) for k, v in lex.items()}


def clamp(n):
    return max(0.0, min(100.0, n))


def scale(value, human, machine):
    """Map value onto 0-100 where `human` -> 100 and `machine` -> 0."""
    if human == machine:
        return 50.0
    return clamp((value - machine) / (human - machine) * 100)


def sentences(text):
    return [s.strip() for s in SENT_RE.findall(text) if len(s.split()) > 2]


def words(text):
    return WORD_RE.findall(text)


def check_burstiness(text):
    """Humans vary sentence length hard. Models write even."""
    lens = [len(s.split()) for s in sentences(text)]
    if len(lens) < 4:
        return 50.0, "too short to judge"
    mean = statistics.mean(lens)
    cv = statistics.pstdev(lens) / mean if mean else 0
    score = scale(cv, human=0.70, machine=0.22)
    return score, f"variation {cv:.2f} across {len(lens)} sentences (want 0.55+)"


def check_specificity(text):
    """Numbers, names and concrete nouns. Slop is abstract."""
    w = words(text)
    if len(w) < 25:
        return 50.0, "too short to judge"
    per100 = 100 / len(w)
    hits = len(NUMBERS.findall(text)) + len(set(PROPER.findall(text)))
    density = hits * per100
    score = scale(density, human=6.0, machine=0.5)
    return score, f"{hits} concrete markers, {density:.1f} per 100 words (want 4+)"


def check_slop(text, lex):
    """Stock vocabulary density against the lexicon."""
    w = words(text)
    if not w:
        return 50.0, "empty"
    hits, found = 0, []
    for entry in lex["words"] + lex["phrases"]:
        pattern = re.compile(r"\b" + re.escape(entry["find"]).replace(r"\ ", r"\s+") + r"\b",
                             re.IGNORECASE)
        n = len(pattern.findall(text))
        if n:
            hits += n
            found.append(entry["find"])
    density = hits * 100 / len(w)
    score = scale(density, human=0.0, machine=4.0)
    detail = f"{hits} stock terms, {density:.1f} per 100 words"
    if found:
        detail += " (" + ", ".join(sorted(found)[:4]) + (", ..." if len(found) > 4 else "") + ")"
    return score, detail


def check_fingerprint(text):
    """Characters a phone keyboard does not produce."""
    invisible = sum(1 for c in text if unicodedata.category(c) == "Cf")
    em = text.count("\u2014")
    curly = sum(text.count(c) for c in "‘’“”")
    ellip = text.count("…")
    nbsp = sum(text.count(c) for c in "   ")
    total = invisible * 4 + em * 2 + curly + ellip + nbsp
    per1k = total * 1000 / max(len(text), 1)
    score = scale(per1k, human=0.0, machine=12.0)
    detail = (f"{invisible} invisible, {em} em dash, {curly} curly quote, "
              f"{ellip} ellipsis, {nbsp} hard space")
    return score, detail


def check_voice(text, lex):
    """Contractions, person, and the shapes models default to."""
    w = words(text)
    if len(w) < 25:
        return 50.0, "too short to judge"
    per100 = 100 / len(w)
    contractions = len(CONTRACTIONS.findall(text)) * per100
    person = len(PRONOUNS.findall(text)) * per100
    tells = 0
    names = []
    for s in lex["structures"]:
        try:
            n = len(re.compile(s["regex"], re.MULTILINE).findall(text))
        except re.error:
            continue
        if n:
            tells += n
            names.append(s["id"])
    bullets = [len(b.split()) for b in re.findall(r"(?m)^\s*[-*•]\s+(.+)$", text)]
    uniform = (len(bullets) >= 3 and statistics.pstdev(bullets) < 1.6)
    score = (scale(contractions, human=3.0, machine=0.0) * 0.35
             + scale(person, human=8.0, machine=1.0) * 0.35
             + clamp(100 - tells * 22) * 0.30)
    if uniform:
        score -= 12
        names.append("uniform-bullets")
    detail = (f"{contractions:.1f} contractions, {person:.1f} personal pronouns "
              f"per 100 words, {tells} structural tell(s)")
    if names:
        detail += " [" + ", ".join(names[:4]) + "]"
    return clamp(score), detail


# ------------------------------------------------------------------ Hebrew

def he_lexicon(lex):
    return [e for e in lex["words"] + lex["phrases"] if e.get("lang") == "he"]


def he_structures(lex, text):
    """Structural tells that apply to Hebrew text: the Hebrew ones, plus the
    language-neutral English ones (emoji, hashtag wall, emoji bullets)."""
    neutral = {"rocket", "hashtag-wall", "emoji-bullets"}
    tells, names = 0, []
    for s in lex["structures"]:
        if s.get("lang") != "he" and s["id"] not in neutral:
            continue
        try:
            n = len(re.compile(s["regex"], re.MULTILINE).findall(text))
        except re.error:
            continue
        if n:
            tells += n
            names.append(s["id"])
    return tells, names


def he_words(text):
    return he.tokens(text)


def he_per100(text):
    """Per-100-words factor, on an English-equivalent word count.

    Hebrew has ~17% fewer words for the same text (hebtext.WORD_RATIO), so a
    raw per-100-words density would read Hebrew as denser than it is. Dividing
    by the English-equivalent count keeps the English human/machine anchors.
    """
    return 100 / (len(he_words(text)) / he.WORD_RATIO)


def check_burstiness_he(text):
    lens = [len(he.tokens(x)) for x in he.sentences(text)]
    lens = [n for n in lens if n > 2]
    if len(lens) < 4:
        return 50.0, "too short to judge"
    mean = statistics.mean(lens)
    cv = statistics.pstdev(lens) / mean if mean else 0
    score = scale(cv, human=0.70, machine=0.22)
    return score, f"variation {cv:.2f} across {len(lens)} sentences (want 0.55+)"


def check_specificity_he(text):
    """Numbers, number words, money, legal nouns, quoted terms. No capitals in Hebrew."""
    w = he_words(text)
    if len(w) < 21:                      # 25 English words, scaled
        return 50.0, "too short to judge"
    hits = len(he.concrete_markers(text))
    density = hits * he_per100(text)
    score = scale(density, human=6.0, machine=0.5)
    return score, f"{hits} concrete markers, {density:.1f} per 100 words (want 4+)"


def check_slop_he(text, lex):
    w = he_words(text)
    if not w:
        return 50.0, "empty"
    hits, found = 0, []
    for entry in he_lexicon(lex):
        n = len(he.lex_regex(entry).findall(text))
        if n:
            hits += n
            found.append(he.lex_label(entry))
    # English entries still count in a Hebrew text ("game-changer", "hack").
    for entry in lex["words"] + lex["phrases"]:
        if entry.get("lang") == "he":
            continue
        pattern = re.compile(r"\b" + re.escape(entry["find"]).replace(r"\ ", r"\s+") + r"\b",
                             re.IGNORECASE)
        n = len(pattern.findall(text))
        if n:
            hits += n
            found.append(entry["find"])
    density = hits * he_per100(text)
    score = scale(density, human=0.0, machine=4.0)
    detail = f"{hits} stock terms, {density:.1f} per 100 words"
    if found:
        detail += " (" + ", ".join(sorted(found)[:4]) + (", ..." if len(found) > 4 else "") + ")"
    return score, detail


def check_fingerprint_he(text):
    """Characters a phone keyboard does not produce. LRM/RLM are not counted."""
    invisible = sum(1 for c in text if unicodedata.category(c) == "Cf"
                    and c not in "‎‏")
    em = text.count("\u2014")
    en = text.count("\u2013")
    hebq = text.count("״") + text.count("׳")      # gershayim, geresh
    curly = sum(text.count(c) for c in "‘’“”")
    ellip = text.count("…")
    nbsp = sum(text.count(c) for c in "   ")
    total = invisible * 4 + em * 2 + en + hebq + curly + ellip + nbsp
    per1k = total * 1000 / max(len(text), 1)
    score = scale(per1k, human=0.0, machine=12.0)
    detail = (f"{invisible} invisible, {em} em dash, {en} en dash, {hebq} gershayim/geresh, "
              f"{curly} curly quote, {ellip} ellipsis, {nbsp} hard space")
    return score, detail


def check_voice_he(text, lex):
    """Person and spoken register, minus structural tells.

    Hebrew has no contractions, so that third of the English check becomes
    register: spoken markers (אז, בעצם, תכלס, ממש...) against written ones
    (הינו, אשר, על מנת, לפיכך...). Person counts I/we and you, singular or
    plural, plus imperatives, which is how Hebrew talks to one viewer.
    """
    w = he_words(text)
    if len(w) < 21:
        return 50.0, "too short to judge"
    per100 = he_per100(text)
    p = he.person_counts(text)
    person = (p["first"] + p["second"] + p["second_verbs"]) * per100
    spoken, formal = he.register_counts(text)
    register = (spoken - formal) * per100
    tells, names = he_structures(lex, text)
    bullets = [len(b.split()) for b in re.findall(r"(?m)^\s*[-*•]\s+(.+)$", text)]
    uniform = (len(bullets) >= 3 and statistics.pstdev(bullets) < 1.6)
    score = (scale(register, human=2.0, machine=-1.0) * 0.35
             + scale(person, human=8.0, machine=1.0) * 0.35
             + clamp(100 - tells * 22) * 0.30)
    if uniform:
        score -= 12
        names.append("uniform-bullets")
    detail = (f"{spoken} spoken / {formal} formal register markers, {person:.1f} "
              f"first/second person per 100 words, {tells} structural tell(s)")
    if names:
        detail += " [" + ", ".join(names[:4]) + "]"
    return clamp(score), detail


CHECKS = ["BURSTINESS", "SPECIFICITY", "SLOP DENSITY", "FINGERPRINT", "VOICE"]


def run(text, lex):
    results = {}
    if he.is_hebrew(text):               # majority script decides
        # Niqqud is read past; invisible characters stay for FINGERPRINT.
        text = he.strip_niqqud(text)
        results["BURSTINESS"] = check_burstiness_he(text)
        results["SPECIFICITY"] = check_specificity_he(text)
        results["SLOP DENSITY"] = check_slop_he(text, lex)
        results["FINGERPRINT"] = check_fingerprint_he(text)
        results["VOICE"] = check_voice_he(text, lex)
    else:
        results["BURSTINESS"] = check_burstiness(text)
        results["SPECIFICITY"] = check_specificity(text)
        results["SLOP DENSITY"] = check_slop(text, en_lexicon(lex))
        results["FINGERPRINT"] = check_fingerprint(text)
        results["VOICE"] = check_voice(text, en_lexicon(lex))
    scores = [results[c][0] for c in CHECKS]
    # The weakest check drags the verdict: a detector only needs one signal.
    overall = statistics.mean(scores) * 0.6 + min(scores) * 0.4
    verdict = "PASS" if overall >= 70 and min(scores) >= 55 else (
        "REVIEW" if overall >= 50 else "FLAGGED")
    return results, overall, verdict


def bar(score, width=24):
    filled = round(score / 100 * width)
    return "#" * filled + "." * (width - filled)


def render(results, overall, verdict, label=None, out=sys.stdout):
    title = "AI DETECTION PANEL" + (f"  -  {label}" if label else "")
    print("\n" + title, file=out)
    print("=" * max(len(title), 62), file=out)
    for name in CHECKS:
        score, detail = results[name]
        print(f"  {name:<13} {bar(score)} {score:5.1f}", file=out)
        print(f"  {'':<13} {detail}", file=out)
    print("-" * 62, file=out)
    print(f"  {'HUMAN SCORE':<13} {bar(overall)} {overall:5.1f}   {verdict}", file=out)
    if verdict != "PASS":
        weakest = min(CHECKS, key=lambda c: results[c][0])
        print(f"\n  Weakest signal: {weakest}. Fix that first.", file=out)
    print("", file=out)


def main():
    ap = argparse.ArgumentParser(description="Score how machine-written a draft looks.")
    ap.add_argument("input", nargs="?", default="-", help="file, or - for stdin")
    ap.add_argument("compare", nargs="?", help="second file, to show before/after")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--lexicon", default=LEX)
    args = ap.parse_args()

    lex = json.load(open(args.lexicon, encoding="utf-8"))
    read = lambda p: sys.stdin.read() if p == "-" else open(p, encoding="utf-8").read()

    targets = [(args.input, read(args.input))]
    if args.compare:
        targets.append((args.compare, read(args.compare)))

    payload = []
    for name, text in targets:
        results, overall, verdict = run(text, lex)
        payload.append({
            "source": name,
            "checks": {k: {"score": round(v[0], 1), "detail": v[1]} for k, v in results.items()},
            "human_score": round(overall, 1),
            "verdict": verdict,
        })

    if args.json:
        print(json.dumps(payload if args.compare else payload[0], indent=2,
                         ensure_ascii=not any(he.HEB_LETTER.search(t) for _, t in targets)))
        return

    for (name, text), p in zip(targets, payload):
        results, overall, verdict = run(text, lex)
        render(results, overall, verdict, label=os.path.basename(name) if args.compare else None)
    if args.compare:
        a, b = payload
        delta = b["human_score"] - a["human_score"]
        print(f"  {a['human_score']:.1f} {a['verdict']}  ->  "
              f"{b['human_score']:.1f} {b['verdict']}   ({delta:+.1f})\n")

    sys.exit(0 if payload[-1]["verdict"] == "PASS" else 1)


if __name__ == "__main__":
    main()
