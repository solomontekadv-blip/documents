#!/usr/bin/env python3
"""
humanize.py - strip the machine fingerprint out of a draft.

Three passes, in this order:

  1. INVISIBLE   delete or normalise the characters a human keyboard never
                 produces: zero-width joiners, word joiners, soft hyphens,
                 BOMs, Unicode tag characters, non-breaking and narrow spaces.
                 These survive copy-paste and are the most mechanical tell in
                 any generated text.
  2. TYPOGRAPHIC em dash -> spaced hyphen " - " (the user's preference), en
                 dash -> hyphen, curly quotes -> straight, ellipsis -> three
                 dots, bullet -> hyphen, Hebrew gershayim and geresh -> " and '.
                 The Hebrew maqaf is left alone.
  3. LEXICAL     replace the slop lexicon in slop.json with plain words,
                 preserving capitalisation and leaving URLs untouched. Hebrew
                 entries match with or without a prefix (ובעולם של היום) and
                 the deletion clean-up keeps the Hebrew grammatical: no
                 dangling ש or ו, no double space, no orphan punctuation.

Bidi marks: LRM and RLM (U+200E, U+200F) keep mixed Hebrew/English text in the
right order, so they are KEPT and reported; --strip-bidi removes them too. All
other bidi embeddings, overrides and isolates are removed with the rest of the
invisible characters.

Legal disclaimers ("אין באמור ייעוץ משפטי") are never touched: they are good
practice, not slop.

Structural tells (rule-of-three, "not just X, it's Y", hashtag walls, and the
Hebrew ones: "זה לא X, זה Y", "התוצאה?") are REPORTED, never auto-rewritten -
rewriting a sentence's shape needs judgement, so that is the model's job, not a
regex's. Ambiguous Hebrew words (מסע, חוויה, קסם) are reported as flagged.

Usage
  python3 humanize.py draft.txt
  python3 humanize.py draft.txt --report
  pbpaste | python3 humanize.py - --report
  python3 humanize.py draft.txt --json
  python3 humanize.py draft.txt -o clean.txt
  python3 humanize.py draft.txt --strip-bidi    # also remove LRM / RLM
"""

import argparse
import json
import os
import re
import sys
import unicodedata

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))  # run from any folder, even with python3 -I
import hebtext as he

HERE = os.path.dirname(os.path.abspath(__file__))
LEX = os.path.join(HERE, "slop.json")

URL_RE = re.compile(r"https?://\S+|www\.\S+|\S+@\S+\.\S+")
SENT_RE = re.compile(r"[^.!?\n]+[.!?]*")
EM, EN = "\u2014", "\u2013"
BIDI_MARKS = "\u200e\u200f"             # LRM, RLM: kept unless --strip-bidi
# Legal disclaimers sit out the lexical pass: nothing inside them is rewritten.
# A disclaimer runs to the end of its clause (". , ;" or a spaced hyphen).
_DIS_TAIL = r"(?:(?!\s-\s)[^.,;\n])*"
DISCLAIMER_RE = re.compile(
    r"(?:אין\s+(?:ב|ל)?(?:אמור|כתוב|תוכן|מידע|פוסט|סרטון|דברים)[^.\n]{0,40}"
    r"(?:ייעוץ|יעוץ|חוות\s+דעת)\s+משפטי" + _DIS_TAIL +
    r"|(?:ה)?(?:מידע|תוכן|אמור)\s+(?:כאן|בפוסט|בסרטון|לעיל)?\s*(?:הוא\s+)?(?:מידע\s+)?כללי[^.\n]{0,60}"
    r"(?:ייעוץ|יעוץ)\s+משפטי" + _DIS_TAIL + ")")


def is_he_entry(entry):
    return entry.get("lang") == "he"


def load_lexicon(path=LEX):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _cp(spec):
    """'U+200B' -> '\\u200b';  'U+E0000-U+E007F' -> (start, end)."""
    if "-" in spec:
        a, b = spec.split("-")
        return (int(a[2:], 16), int(b[2:], 16))
    return int(spec[2:], 16)


def protect_urls(text):
    """Swap URLs for placeholders so no pass rewrites inside a link."""
    found = []

    def stash(m):
        found.append(m.group(0))
        return f"\x00URL{len(found) - 1}\x00"

    return URL_RE.sub(stash, text), found


def protect_disclaimers(text):
    """Legal disclaimers sit out the lexical pass (their typography is still fixed)."""
    found = []

    def stash(m):
        found.append(m.group(0))
        return f"\x00DIS{len(found) - 1}\x00"

    return DISCLAIMER_RE.sub(stash, text), found


def restore_disclaimers(text, found):
    for i, d in enumerate(found):
        text = text.replace(f"\x00DIS{i}\x00", d)
    return text


def restore_urls(text, found):
    for i, url in enumerate(found):
        text = text.replace(f"\x00URL{i}\x00", url)
    return text


def pass_invisible(text, lex, strip_bidi=False):
    """Delete or space-normalise invisible characters. Returns (text, hits, kept).

    LRM / RLM are kept and reported in `kept`, unless strip_bidi is set.
    """
    hits, kept = [], []
    for entry in lex["invisible"]:
        cp = _cp(entry["cp"])
        if isinstance(cp, tuple):
            pattern = "[" + re.escape(chr(cp[0])) + "-" + re.escape(chr(cp[1])) + "]"
        else:
            pattern = re.escape(chr(cp))
        n = len(re.findall(pattern, text))
        if not n:
            continue
        action = entry["action"]
        if action == "keep" and not strip_bidi:
            kept.append({"name": entry["cp"] + " " + entry["name"], "count": n,
                         "action": "kept (bidi mark, --strip-bidi removes it)"})
            continue
        action = "delete" if action == "keep" else action
        hits.append({"name": entry["cp"] + " " + entry["name"], "count": n, "action": action})
        text = re.sub(pattern, "" if action == "delete" else " ", text)
    # Any remaining Cf (format) character is invisible by definition, except
    # the bidi marks we chose to keep.
    keep = "" if strip_bidi else BIDI_MARKS
    stray = [c for c in text if unicodedata.category(c) == "Cf" and c not in keep]
    if stray:
        hits.append({"name": "other invisible format chars", "count": len(stray),
                     "action": "delete"})
        text = "".join(c for c in text if unicodedata.category(c) != "Cf" or c in keep)
    return text, hits, kept


def pass_typographic(text, lex):
    hits = []
    for entry in lex["typographic"]:
        ch = entry["from"]
        n = text.count(ch)
        if not n:
            continue
        hits.append({"name": f"{ch} {entry['name']}", "count": n, "to": entry["to"].strip() or "(space)"})
        if ch == EM:
            # The user's preference: an em dash becomes a spaced hyphen.
            # "word - word", "word-word" alike; a dash that ends a clause
            # before punctuation or a line break just goes.
            text = re.sub(r"[ \t]*" + EM + r"[ \t]*(?=[,.;:!?\n]|$)", "", text)
            text = re.sub(r"(?m)^([ \t]*)" + EM + r"[ \t]*", r"\1- ", text)
            text = re.sub(r"[ \t]*" + EM + r"[ \t]*", " - ", text)
        elif ch == EN:
            text = re.sub(r"\s*" + EN + r"\s*(?=\d)", "-", text)      # 5-10 ranges
            text = re.sub(r"[ \t]+" + EN + r"[ \t]+", " - ", text)     # used as em dash
            text = text.replace(EN, "-")
        else:
            text = text.replace(ch, entry["to"])
    # A comma inserted before existing punctuation reads wrong.
    text = re.sub(r",\s*([,.;:!?])", r"\1", text)
    text = re.sub(r",\s*\n", "\n", text)
    return text, hits


def _match_case(src, repl):
    if not repl:
        return repl
    if src.isupper() and len(src) > 1:
        return repl.upper()
    if src[0].isupper():
        return repl[0].upper() + repl[1:]
    return repl


def pass_lexical(text, lex):
    """Replace slop words and phrases. Longest first so phrases win."""
    hits = []
    entries = sorted([e for e in lex["phrases"] + lex["words"] if not is_he_entry(e)],
                     key=lambda e: len(e["find"]), reverse=True)
    for entry in entries:
        find = entry["find"]
        pattern = re.compile(r"\b" + re.escape(find).replace(r"\ ", r"\s+") + r"\b",
                             re.IGNORECASE)
        found = pattern.findall(text)
        if not found:
            continue
        hits.append({"find": find, "replace": entry["replace"] or "(deleted)",
                     "count": len(found), "family": entry["family"]})
        text = pattern.sub(lambda m: _match_case(m.group(0), entry["replace"]), text)
    # Clean up after deletions. Deleting a whole clause leaves orphaned
    # punctuation behind ("system. ." or a line that now opens on a comma),
    # and that reads worse than the slop did.
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"(?m)^[ \t]*(?:[,.;:]+[ \t]*)+", "", text)
    text = re.sub(r"(?m)^[ \t](?=\S)", "", text)       # one space left by a deletion.
                                                      # Deeper indents are deliberate.
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r",\s*([,.;:!?])", r"\1", text)      # an em dash became a comma,
                                                      # then the clause after it went
    text = text.replace("...", "\x00ELL\x00")          # protect real ellipses
    text = re.sub(r"\.\s*\.+", ".", text)
    text = re.sub(r"([!?])\s*\.", r"\1", text)
    text = text.replace("\x00ELL\x00", "...")
    text = re.sub(r"(?m)^[ \t]+$", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    # An em dash that became a comma, followed by a sentence connective, leaves
    # a splice ("is important, also, it's proof"). Promote it to a full stop.
    text = re.sub(r",\s*(also|so|still|basically|in the end)\s*,\s*",
                  lambda m: ". " + m.group(1)[0].upper() + m.group(1)[1:] + ", ", text)
    return text, hits


# Marks a prefix left behind by a Hebrew deletion ("ו" of "ובעולם של היום"),
# so the clean-up can glue it to the next word instead of leaving it alone.
# Distinct open and close marks, so a match can never span two deletions.
GLUE, GLUE_END = "\x01", "\x02"


def pass_lexical_he(text, lex):
    """Hebrew slop. Prefix-aware, longest first, and grammatical afterwards."""
    hits = []
    entries = sorted([e for e in lex["phrases"] + lex["words"] if is_he_entry(e)],
                     key=lambda e: len(e["find"]), reverse=True)
    for entry in entries:
        pattern = he.lex_regex(entry)
        count = [0]

        def sub(m, entry=entry, count=count):
            count[0] += 1
            pre = m.group("pre") or ""
            repl = m.expand(entry["replace"]) if entry.get("regex") else entry["replace"]
            if repl:
                return pre + repl
            # Deleted: a conjunction prefix (ו, ש, כש) belongs to whatever
            # comes next; a preposition (ב, ל, מ) went with the phrase.
            keep = re.match(r"(?:ו|ש|כש|וכש|וש)?", pre).group(0)
            return GLUE + keep + GLUE_END

        new = pattern.sub(sub, text)
        if count[0]:
            hits.append({"find": he.lex_label(entry), "replace": entry["replace"] or "(deleted)",
                         "count": count[0], "family": entry["family"]})
            text = new
    if not hits:
        return text, hits
    # Two deletions in a row ("ובסופו של יום, ללא ספק, ...") merge, so the
    # first one's ו still reaches the word after both.
    pair = GLUE + r"([^" + GLUE + GLUE_END + r"]*)" + GLUE_END
    prev = None
    while prev != text:
        prev = text
        text = re.sub(pair + r"[ \t]*,?[ \t]*" + pair, GLUE + r"\1\2" + GLUE_END, text)
    # Glue a kept prefix to the next word, across any comma the deletion left.
    text = re.sub(pair + r"[ \t]*,?[ \t]*(?=[\w\"'])", lambda m: m.group(1), text)
    text = re.sub(pair, "", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"(?m)^[ \t]*(?:[,.;:]+[ \t]*)+", "", text)       # line opens on punctuation
    text = re.sub(r"([.!?:])[ \t]*,[ \t]*", r"\1 ", text)             # ". , next" -> ". next"
    text = re.sub(r"[ \t]+([,.;:!?])", r"\1", text)
    text = re.sub(r",\s*([,.;:!?])", r"\1", text)
    text = re.sub(r"([.!?])[ \t]*[:;]", r"\1", text)                  # "!:" after an emptied clause
    text = re.sub(r"\.[!?]+", ".", text)                              # ".!" left by a deleted CTA
    text = re.sub(r"(?<![\w])([ושה])[ \t]+(?=[\u05d0-\u05ea])", r"\1", text)  # dangling ש / ו
    text = re.sub(r"(?m)^[ \t]+(?=\S)", "", text)
    text = re.sub(r"(?m)[ \t]+$", "", text)
    text = re.sub(r"(?m)^[ \t]*-[ \t]*$\n?", "", text)                  # a hyphen left alone
    text = re.sub(r"(?m)^[ \t]*[.,;:!?][ \t]*$\n?", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text, hits


def scan_flagged(text, lex):
    """Ambiguous Hebrew words: reported for a decision, never replaced."""
    flags = []
    for entry in lex.get("flagged", []):
        n = sum(1 for t in he.tokens(text) if he.lookup(t, {entry["find"]}))
        if n:
            flags.append({"find": entry["find"], "count": n, "note": entry["note"]})
    return flags


def scan_structures(text, lex):
    flags = []
    for s in lex["structures"]:
        if is_he_entry(s) and not he.HEB_LETTER.search(text):
            continue
        try:
            pattern = re.compile(s["regex"], re.MULTILINE)
        except re.error:
            continue
        found = pattern.findall(text)
        if found:
            flags.append({"name": s["name"], "count": len(found), "fix": s["fix"]})
    # Sentence-length uniformity is structural too.
    lens = [len(s.split()) for s in SENT_RE.findall(text) if len(s.split()) > 2]
    if len(lens) >= 4:
        mean = sum(lens) / len(lens)
        var = sum((n - mean) ** 2 for n in lens) / len(lens)
        cv = (var ** 0.5) / mean if mean else 0
        if cv < 0.35:
            flags.append({
                "name": f"Uniform sentence length (variation {cv:.2f})",
                "count": len(lens),
                "fix": "Break one sentence in half. Let another run long. Machines write even.",
            })
    return flags


def restore_capitals(original, text):
    """Deleting an opener leaves the next word lower case.

    Only fix it for writers who capitalise their sentences in the first place:
    a deliberately lower-case voice is a style, not an artefact, and shouting
    over it would be exactly the kind of thing this script exists to stop.
    """
    starts = re.findall(r"(?:^|[.!?]\s+|\n)\s*([A-Za-z])", original)
    if not starts or sum(1 for c in starts if c.isupper()) * 2 < len(starts):
        return text
    return re.sub(r"(?:^|(?<=[.!?] )|(?<=[.!?]\n)|(?<=\n))\s*([a-z])",
                  lambda m: m.group(0)[:-1] + m.group(1).upper(), text)


def humanize(text, lex, strip_bidi=False):
    raw_for_case = text
    text, urls = protect_urls(text)
    text, inv, kept = pass_invisible(text, lex, strip_bidi)
    text, typo = pass_typographic(text, lex)
    text, lexi = pass_lexical(text, lex)
    if he.HEB_LETTER.search(text):
        text, disc = protect_disclaimers(text)
        text, lexi_he = pass_lexical_he(text, lex)
        text = restore_disclaimers(text, disc)
        lexi += lexi_he
    text = restore_capitals(raw_for_case, text)
    text = restore_urls(text, urls)
    report = {
        "invisible": inv,
        "typographic": typo,
        "lexical": lexi,
        "structures": scan_structures(text, lex),
    }
    # New keys only when they have something in them, so English reports keep
    # their original shape.
    flagged = scan_flagged(text, lex) if he.HEB_LETTER.search(text) else []
    if flagged:
        report["flagged"] = flagged
    if kept:
        report["kept"] = kept
    return text.strip() + "\n", report


def render_report(report, out=sys.stderr):
    def head(title):
        print(f"\n{title}\n" + "-" * len(title), file=out)

    total = sum(h["count"] for h in report["invisible"]) \
        + sum(h["count"] for h in report["typographic"]) \
        + sum(h["count"] for h in report["lexical"])

    head("HUMANIZE REPORT")
    print(f"{total} machine artefacts removed, "
          f"{len(report['structures'])} structural tells flagged for rewrite", file=out)
    if report.get("kept"):
        print("Kept on purpose: " + ", ".join(f"{h['count']}x {h['name']}" for h in report["kept"])
              + ". They hold mixed Hebrew/English in order; --strip-bidi removes them.", file=out)

    if report["invisible"]:
        head("1. INVISIBLE CHARACTERS")
        for h in report["invisible"]:
            print(f"  {h['count']:>3}x  {h['name']}  -> {h['action']}", file=out)
    if report["typographic"]:
        head("2. TYPOGRAPHY")
        for h in report["typographic"]:
            print(f"  {h['count']:>3}x  {h['name']}  -> {h['to']}", file=out)
    if report["lexical"]:
        head("3. SLOP LEXICON")
        for h in report["lexical"]:
            print(f"  {h['count']:>3}x  {h['find']}  -> {h['replace']}   [{h['family']}]", file=out)
    if report["structures"]:
        head("4. STRUCTURAL TELLS  (not auto-fixed - rewrite these yourself)")
        for h in report["structures"]:
            print(f"  {h['count']:>3}x  {h['name']}\n        {h['fix']}", file=out)
    if report.get("flagged"):
        head("5. FLAGGED WORDS  (often fine - decide, nothing was changed)")
        for h in report["flagged"]:
            print(f"  {h['count']:>3}x  {h['find']}  {h['note']}", file=out)
    if not any(v for k, v in report.items() if k != "kept"):
        head("CLEAN")
        print("  Nothing to strip.", file=out)
    print("", file=out)


def main():
    ap = argparse.ArgumentParser(description="Strip the machine fingerprint out of a draft.")
    ap.add_argument("input", nargs="?", default="-", help="file, or - for stdin")
    ap.add_argument("-o", "--out", help="write cleaned text here instead of stdout")
    ap.add_argument("--report", action="store_true", help="print what changed, to stderr")
    ap.add_argument("--json", action="store_true", help="emit {text, report} as JSON")
    ap.add_argument("--lexicon", default=LEX, help="path to slop.json")
    ap.add_argument("--strip-bidi", action="store_true",
                    help="also remove LRM / RLM marks (kept by default)")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    lex = load_lexicon(args.lexicon)
    clean, report = humanize(raw, lex, strip_bidi=args.strip_bidi)

    if args.json:
        print(json.dumps({"text": clean, "report": report}, indent=2, ensure_ascii=False))
        return
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(clean)
        print(f"wrote {args.out}", file=sys.stderr)
    else:
        sys.stdout.write(clean)
    if args.report:
        render_report(report)


if __name__ == "__main__":
    main()
