#!/usr/bin/env python3
"""
caption.py - lint an Instagram caption and show exactly what the feed shows
before the "... more".

Instagram gives a caption about 125 characters in the feed and hides the rest
behind a tap. Almost every caption that fails, fails there: the hook is in
sentence three, or the first line is a greeting, or the whole thing opens on a
hashtag. This prints the visible window as a box so you can read it the way a
scrolling stranger does, then checks the eight things that are worth checking.

Hebrew: hashtags in Hebrew or mixed (#גירושין, #עורךדין, #דיני_משפחה) are
counted, Hebrew calls to action (כתבו בתגובות, שמרו, שלחו, שתפו, עקבו, לחצו,
הקישור בביו, שלחו הודעה) are counted as asks, and --keywords takes Hebrew
phrases the way Israelis type them ("עורך דין גירושין נתניה"), matched with or
without a prefix. If ethics.py sits in the same folder, the caption is also run
through it in caption context: a one-line summary plus any FAIL/REVIEW codes,
and an ethics FAIL makes the verdict FIX.

The 125-character cut is an approximation. The real number moves with the
device, the font size and where your line breaks fall, which is exactly why
you want a margin rather than a caption engineered to end at 125. Change it
with --truncate if you want to test a tighter one.

Usage
  python3 caption.py caption.txt
  python3 caption.py caption.txt --keywords "proposal software,client contract"
  pbpaste | python3 caption.py -
  python3 caption.py caption.txt --json
"""

import argparse
import json
import os
import re
import sys
import textwrap

import os as _os, sys as _sys
_sys.path.insert(0, _os.path.dirname(_os.path.abspath(__file__)))  # run from any folder, even with python3 -I
import hebtext as he

try:                                     # the compliance gate, when it is here
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import ethics                        # noqa: E402
except Exception:
    ethics = None

LIMIT = 2200             # Instagram's hard caption limit.
TRUNCATE = 125           # Roughly where the feed cuts to "... more".
HASHTAG_LIMIT = 5        # Instagram's cap per post or reel since 18 Dec 2025,
                         # down from 30. Announced by the @Creators account:
                         # "using fewer (up to 5) more targeted hashtags,
                         # rather than many generic ones, can improve both your
                         # content's performance and people's experience".

HASHTAG_RE = re.compile(r"(?:^|\s)(#[A-Za-z0-9_]+)")
# Hebrew or mixed tags: #גירושין #עורךדין #דיני_משפחה #עו"ד is not a tag.
HASHTAG_HE_RE = re.compile(r"(?:^|\s)(#[A-Za-z0-9_\u05d0-\u05ea]*[\u05d0-\u05ea][A-Za-z0-9_\u05d0-\u05ea]*)")
MENTION_RE = re.compile(r"(?:^|\s)(@[A-Za-z0-9_.]+)")
LINK_RE = re.compile(r"https?://\S+|\bwww\.\S+|\b[a-z0-9-]+\.(?:com|co|io|net|org|ai|app)/\S*",
                     re.IGNORECASE)
EMOJI_RE = re.compile(r"[\U0001F300-\U0001FAFF☀-➿←-⇿️]")
CONCRETE_RE = re.compile(r"\$\s?\d|\b\d[\d,.]*\b|(?<!^)\b[A-Z][a-z]{2,}\b", re.MULTILINE)

ASKS = [
    (re.compile(r"(?i)\bcomment (?:the word |\")?[A-Z0-9]{2,}\b"), "comment a keyword"),
    (re.compile(r"(?i)\b(?:dm|message) me\b"), "DM me"),
    (re.compile(r"(?i)\bsave (?:this|it)\b"), "save this"),
    (re.compile(r"(?i)\bshare (?:this|it)\b"), "share this"),
    (re.compile(r"(?i)\bfollow (?:me|for)\b"), "follow"),
    (re.compile(r"(?i)\blink in (?:my )?bio\b"), "link in bio"),
    (re.compile(r"(?i)\b(?:swipe|tap) (?:through|left|right|for|to)\b"), "swipe or tap"),
    (re.compile(r"(?i)\btell me\b|\bwhat would you\b|\bwhich one\b"), "answer a question"),
]

# Hebrew asks. Prefix-aware enough for spoken Hebrew: "ותכתבו", "וכתבו".
_P = r"(?<![\w])(?:ו)?"
ASKS_HE = [
    (re.compile(_P + r"(?:כתבו|תכתבו|הגיבו|תגיבו|כתבי|תכתבי|כתוב|תכתוב)\s+(?:לי\s+)?(?:את\s+(?:ה)?מילה\s+)?"
                r"[\"'״]?[\w\u05d0-\u05ea]{2,}[\"'״]?\s+(?:\S+\s+){0,2}?(?:בתגובות|בתגובה|למטה)"
                r"|" + _P + r"(?:כתבו|תכתבו|הגיבו|תגיבו)\s+(?:\S+\s+){0,3}?(?:בתגובות|בתגובה)"),
     "comment a keyword"),
    (re.compile(_P + r"(?:שלחו|תשלחו|שלחי|תשלחי|כתבו|תכתבו|פנו|תפנו)\s+(?:לי\s+|לנו\s+|אליי\s+|אלינו\s+)?(?:הודעה|הודעת|DM|דיאם|בפרטי|בדיאם|בוואטסאפ|בווטסאפ)"),
     "DM me"),
    (re.compile(_P + r"(?:שמרו|תשמרו|שמרי|תשמרי|שמור|תשמור)(?![\w])"), "save this"),
    (re.compile(_P + r"(?:שתפו|תשתפו|שתפי|תשתפי|שלחו|תשלחו)\s+(?:את\s+)?(?:זה|הפוסט|הסרטון|לחבר|לחברה|למי|עם|ל)"),
     "share this"),
    (re.compile(_P + r"(?:עקבו|תעקבו|עקבי|תעקבי)(?![\w])"), "follow"),
    (re.compile(r"(?:ה)?(?:קישור|לינק)\s+(?:\S+\s+)?(?:בביו|בפרופיל)|(?:לחצו|תלחצו|הקליקו|היכנסו)\s+(?:על|ל|ב)"),
     "link in bio"),
    (re.compile(_P + r"(?:החליקו|תחליקו|גללו\s+ימינה|גללו\s+שמאלה)(?![\w])"), "swipe or tap"),
    (re.compile(r"(?:ספרו|תספרו)\s+לי|(?:מה|איך)\s+(?:אתם|אתן)\s+(?:הייתם|הייתן|הייתם\s+עושים)|איזה\s+(?:מהם|מהן|מה)"),
     "answer a question"),
]

FILLER_TAGS = {"#viral", "#fyp", "#explore", "#explorepage", "#foryou", "#foryoupage",
               "#trending", "#instagood", "#love", "#follow", "#like4like", "#reels",
               "#reelsinstagram", "#viralreels", "#instadaily",
               # Hebrew generic tags: they describe nothing
               "#ויראלי", "#אקספלור", "#טרנד", "#ישראל", "#אינסטגרם", "#רילס", "#לייק",
               "#עוקבים", "#פוריו", "#פיד", "#תוכן"}


def visible_window(text, cut):
    """What the feed shows. Instagram cuts mid-word, so this does too."""
    flat = text.strip()
    return flat if len(flat) <= cut else flat[:cut]


def render_box(window, truncated, out=sys.stdout, width=52):
    print("\n  WHAT THE FEED SHOWS", file=out)
    print("  +" + "-" * (width + 2) + "+", file=out)
    lines = []
    for raw in window.split("\n"):
        lines.extend(textwrap.wrap(raw, width) or [""])
    for line in lines[:8]:
        print(f"  | {line:<{width}} |", file=out)
    tail = "... more" if truncated else "(whole caption fits)"
    print("  +" + "-" * (width + 2 - len(tail) - 2) + f" {tail} " + "+", file=out)


def keyword_found(keyword, text):
    """Hebrew keyword phrases match with or without a prefix on each word
    ("עורך דין גירושין" is found in "לעורך דין גירושין"). Latin stays a substring."""
    if not he.HEB_LETTER.search(keyword):
        return keyword.lower() in text.lower()
    parts = [re.escape(p) for p in keyword.split()]
    rx = he.PREFIX_RX + r"\s+(?:[ובלמשכה]{1,3})?".join(parts) + he.END_RX
    return re.search(rx, text, re.IGNORECASE) is not None


def analyse(text, cut=TRUNCATE, keywords=None, run_ethics=True):
    text = text.rstrip()
    stripped = text.strip()
    hebrew = he.is_hebrew(stripped)
    chars = len(stripped)
    lines = [l for l in stripped.split("\n")]
    first_line = lines[0].strip() if lines else ""
    tags = HASHTAG_RE.findall(stripped)
    if he.HEB_LETTER.search(stripped):  # Hebrew and mixed tags, in order of appearance
        tags = HASHTAG_HE_RE.findall(stripped) + [t for t in tags if t not in
                                                  HASHTAG_HE_RE.findall(stripped)]
        tags = sorted(set(tags), key=lambda t: stripped.find(t))
    mentions = MENTION_RE.findall(stripped)
    links = LINK_RE.findall(stripped)
    emoji = EMOJI_RE.findall(stripped)
    window = visible_window(stripped, cut)
    truncated = chars > cut
    asks = [name for pattern, name in ASKS if pattern.search(stripped)]
    if he.HEB_LETTER.search(stripped):
        asks += [name for pattern, name in ASKS_HE if pattern.search(stripped) and name not in asks]
    filler = [t for t in tags if t.lower() in FILLER_TAGS]
    keywords = [k.strip() for k in (keywords or []) if k.strip()]

    checks = []

    def add(name, status, detail):
        checks.append({"check": name, "status": status, "detail": detail})

    add("LENGTH", "FAIL" if chars > LIMIT else "PASS",
        f"{chars} / {LIMIT} characters" + (f", {chars - LIMIT} over the limit"
                                           if chars > LIMIT else ""))

    if not first_line:
        add("FIRST LINE", "FAIL", "the caption opens on a blank line")
    elif first_line.startswith("#") or first_line.startswith("@"):
        add("FIRST LINE", "FAIL",
            "opens on a hashtag or a mention, which is the one position worth a sentence")
    elif len(first_line) > cut:
        add("FIRST LINE", "WARN",
            f"{len(first_line)} characters, so it gets cut at {cut} mid-thought. "
            "Fine if the cut is a cliffhanger, bad if it is a subordinate clause")
    else:
        add("FIRST LINE", "PASS", f"{len(first_line)} characters, lands whole")

    if hebrew:
        # No capitals in Hebrew: numbers, number words, money, legal nouns, quotes.
        marks = he.concrete_markers(window)
        add("HOOK IS CONCRETE", "PASS" if marks else "WARN",
            f"{len(marks)} number(s), legal term(s) or quote(s) in the visible window"
            + ("" if marks else " - nothing checkable before the tap"))
    else:
        add("HOOK IS CONCRETE", "PASS" if CONCRETE_RE.search(window) else "WARN",
            f"{len(CONCRETE_RE.findall(window))} number(s) or name(s) in the visible window"
            + ("" if CONCRETE_RE.search(window) else " - nothing checkable before the tap"))

    if len(tags) > HASHTAG_LIMIT:
        add("HASHTAGS", "FAIL", f"{len(tags)} tags, over Instagram's cap of {HASHTAG_LIMIT}. "
                                "Tags past the fifth do not count and the block reads as old")
    elif len(tags) == HASHTAG_LIMIT and filler:
        add("HASHTAGS", "WARN", f"{len(tags)} tags, at the cap, and "
                                f"{len(filler)} of them generic. Spend the five on topics")
    elif filler:
        add("HASHTAGS", "WARN", f"{len(tags)} tags, {len(filler)} of them generic "
                                f"({', '.join(filler[:3])}). Those describe nothing")
    else:
        add("HASHTAGS", "PASS", f"{len(tags)} tag(s)" + (f": {' '.join(tags)}" if tags else ""))

    if not tags:
        add("TAG PLACEMENT", "PASS", "no tags to place")
    elif any(re.search(r"(?:^|\s)" + re.escape(t) + r"(?![\w])", window) for t in tags):
        add("TAG PLACEMENT", "WARN", "a hashtag is inside the visible window, "
                                     "spending feed space on a label")
    else:
        add("TAG PLACEMENT", "PASS", "tags are below the fold")

    add("LINKS", "WARN" if links else "PASS",
        f"{len(links)} link(s) in the caption, and captions are not clickable. "
        f"Move it to the bio or the DM" if links else "no dead links in the body")

    if len(asks) == 1:
        add("ONE ASK", "PASS", f"one call to action: {asks[0]}")
    elif not asks:
        add("ONE ASK", "WARN", "no call to action. Decide what this post is for")
    else:
        add("ONE ASK", "WARN", f"{len(asks)} asks ({', '.join(asks)}). "
                               "Two asks is the same as none")

    density = len(emoji) * 100 / max(chars, 1)
    add("EMOJI", "WARN" if density > 4 else "PASS",
        f"{len(emoji)} emoji, {density:.1f} per 100 characters"
        + (" - reads as decoration" if density > 4 else ""))

    if keywords:
        found = [k for k in keywords if keyword_found(k, stripped)]
        missing = [k for k in keywords if not keyword_found(k, stripped)]
        in_window = [k for k in found if keyword_found(k, window)]
        status = "PASS" if not missing else ("WARN" if found else "FAIL")
        add("SEARCH TERMS", status,
            f"{len(found)}/{len(keywords)} present"
            + (f", {len(in_window)} in the visible window" if found else "")
            + (f". Missing: {', '.join(missing)}" if missing else ""))

    fails = sum(1 for c in checks if c["status"] == "FAIL")
    warns = sum(1 for c in checks if c["status"] == "WARN")
    verdict = "FIX" if fails else ("REVIEW" if warns else "READY")

    # The compliance gate: an ethics FAIL is a FIX whatever the lint says, and
    # a REVIEW means the lawyer has to look before it is READY.
    eth = None
    if run_ethics and ethics is not None:
        r = ethics.run(stripped, context="caption")
        eth = {"fail": r["fail"], "review": r["review"],
               "fail_codes": ethics.codes(r, "FAIL"), "review_codes": ethics.codes(r, "REVIEW"),
               "summary": ethics.summary_line(r)}
        if r["fail"]:
            verdict = "FIX"
        elif r["review"] and verdict == "READY":
            verdict = "REVIEW"

    out = {
        "characters": chars, "limit": LIMIT, "truncate_at": cut,
        "visible": window, "truncated": truncated,
        "first_line_chars": len(first_line),
        "hashtags": tags, "mentions": mentions, "links": links,
        "emoji": len(emoji), "asks": asks,
        "checks": checks, "verdict": verdict,
    }
    if eth is not None:
        out["ethics"] = eth
    return out


def render(a, out=sys.stdout):
    head = (f"CAPTION LINT  ·  {a['characters']} / {a['limit']} chars  ·  "
            f"{len(a['hashtags'])} hashtags  ·  {len(a['asks'])} ask(s)")
    print("\n" + head, file=out)
    print("=" * max(len(head), 62), file=out)
    render_box(a["visible"], a["truncated"], out=out)
    print("", file=out)
    for c in a["checks"]:
        print(f"  {c['status']:<5} {c['check']:<17} {c['detail']}", file=out)
    if a.get("ethics"):
        e = a["ethics"]
        status = "FAIL" if e["fail"] else ("WARN" if e["review"] else "PASS")
        codes = "".join([f"  FAIL: {', '.join(e['fail_codes'])}" if e["fail_codes"] else "",
                         f"  REVIEW: {', '.join(e['review_codes'])}" if e["review_codes"] else ""])
        print(f"  {status:<5} {'ETHICS':<17} {e['summary']}{codes}"
              + ("  (details: python3 ethics.py <file> --context caption)" if codes else ""), file=out)
    print("-" * max(len(head), 62), file=out)
    print(f"  VERDICT  {a['verdict']}\n", file=out)


def main():
    ap = argparse.ArgumentParser(description="Lint an Instagram caption.")
    ap.add_argument("input", nargs="?", default="-", help="caption file, or - for stdin")
    ap.add_argument("--truncate", type=int, default=TRUNCATE,
                    help=f"characters shown before '... more' (default {TRUNCATE})")
    ap.add_argument("--keywords", default="", help="comma-separated terms you want to be found for")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    a = analyse(raw, cut=args.truncate, keywords=args.keywords.split(","))
    if args.json:
        print(json.dumps(a, indent=2, ensure_ascii=False))
    else:
        render(a)
    sys.exit(0 if a["verdict"] == "READY" else 1)


if __name__ == "__main__":
    main()
