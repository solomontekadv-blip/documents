#!/usr/bin/env python3
"""
ethics.py - a deterministic compliance linter for an Israeli lawyer's posts.

Checks a draft against the detectable parts of compliance.md (codes C1-C23):
superlatives, "מומחה", promises, case results and amounts, client stories,
pending cases, testimonials, fees and "free", unsolicited DMs, DM invitations
in comments, gifts and coupons, sponsored content, video rules, links, "as
seen on", lectures used for recruiting, mediation details, rabbinical court
details. Every rule lives in ethics.json (code, level, contexts, prefix-aware
regex patterns, Hebrew message, Hebrew fix, source), so the rules can be read
and edited without touching code.

What this is:  a regex linter with a few proximity conditions. It catches the
words and shapes that the rules are about, with a bias towards REVIEW where a
word is ambiguous. FAIL = must be fixed before it goes out. REVIEW = the
lawyer decides.

What this is NOT:  legal advice or a substitute for the lawyer reading the
post (C18). It cannot see the video, the image, the client's consent or who
wrote to whom first. A clean run means "nothing detectable", not "compliant".
C17 (archiving), C18 (personal review) and C19 (retroactive cleanup) are
duties, not text patterns, and no run of this script checks them.

Usage
  python3 ethics.py draft.txt
  python3 ethics.py draft.txt --context caption
  python3 ethics.py dm.txt --context dm
  python3 ethics.py post.txt --sponsored
  pbpaste | python3 ethics.py - --context comment
  python3 ethics.py draft.txt --json

Exit code 1 if any FAIL, else 0. The last line is always
  COMPLIANCE  <n> FAIL  <m> REVIEW
(with --json, stdout is pure JSON carrying the same line as "summary", and the
line is also printed to stderr).
"""

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RULES = os.path.join(HERE, "ethics.json")
CONTEXTS = ["general", "caption", "script", "story", "comment", "reply", "dm", "bio", "carousel"]
MACRO_RE = re.compile(r"<<([A-Z_]+)>>")


def load_rules(path=RULES):
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    macros = data.get("macros", {})

    def expand(rx):
        # Macros may use other macros; three rounds is plenty.
        for _ in range(3):
            rx = MACRO_RE.sub(lambda m: macros[m.group(1)], rx)
        return rx

    def comp(patterns):
        return [re.compile(expand(p), re.MULTILINE) for p in patterns]

    rules = []
    for r in data["rules"]:
        c = dict(r)
        c["_patterns"] = comp(r["patterns"])
        c["_near"] = [dict(n, _p=comp(n["patterns"])) for n in r.get("near", [])]
        c["_unless_before"] = comp(r.get("unless_before", []))
        c["_unless_after"] = comp(r.get("unless_after", []))
        c["_unless_text"] = comp(r.get("unless_text", []))
        if r.get("downgrade"):
            c["_down"] = dict(r["downgrade"], _p=comp(r["downgrade"]["patterns"]))
        if r.get("alt_message"):
            c["_alt"] = dict(r["alt_message"], _p=re.compile(expand(r["alt_message"]["when"])))
        rules.append(c)
    allowed = [d.lower() for d in data.get("allowed_domains", []) if not d.startswith("{{")]
    return rules, allowed


def _line_of(text, pos):
    return text.count("\n", 0, pos) + 1


def _snippet(text, start, end, pad=18):
    """The match with a little context, never crossing into another line."""
    ls = text.rfind("\n", 0, start) + 1
    le = text.find("\n", end)
    le = len(text) if le == -1 else le
    a = max(ls, start - pad)
    b = min(le, end + pad)
    s = text[a:b].strip()
    return ("..." if a > ls else "") + s + ("..." if b < le else "")


def _domain(url):
    u = re.sub(r"^[a-z]+://", "", url.lower())
    u = re.sub(r"^www\.", "", u)
    return re.split(r"[/?#:]", u, maxsplit=1)[0].rstrip(".,;:!?)")


def _near_ok(text, start, end, near):
    """Every near-condition must find a match within its window."""
    for cond in near:
        a = max(0, start - cond.get("before", 60))
        b = min(len(text), end + cond.get("after", 60))
        window = text[a:start] + " \x00 " + text[end:b]
        if not any(p.search(window) for p in cond["_p"]):
            return False
    return True


def _applies(rule, context, sponsored):
    ctx = rule.get("contexts", ["*"])
    if "*" not in ctx and context not in ctx:
        return False
    need = rule.get("requires")
    if need == "sponsored" and not sponsored:
        return False
    if need == "not_sponsored" and sponsored:
        return False
    return True


def run(text, context="general", sponsored=False, rules_path=RULES):
    """Lint `text`. Returns {"findings": [...], "fail": n, "review": m, "context": ...}.

    caption.py imports this. Findings are sorted by line, then code.
    """
    rules, allowed = load_rules(rules_path)
    # Hashtags: "#עורך_דין_מומחה" must be read as words. "_" -> " " keeps every
    # offset and line number, so findings still point at the original text.
    text = re.sub(r"#\w+", lambda m: m.group(0).replace("_", " "), text)
    findings = []
    seen = set()
    for rule in rules:
        if not _applies(rule, context, sponsored):
            continue
        if any(p.search(text) for p in rule["_unless_text"]):
            continue
        if rule.get("mode") == "absent":
            if not any(p.search(text) for p in rule["_patterns"]):
                findings.append(_finding(rule, rule["level"], rule["message"], text, 0, 0, ""))
            continue
        for pattern in rule["_patterns"]:
            for m in pattern.finditer(text):
                start, end = m.span()
                if start == end:
                    continue
                if rule.get("url_allowlist"):
                    dom = _domain(m.group(0))
                    if any(dom == d or dom.endswith("." + d) for d in allowed):
                        continue
                if rule["_near"] and not _near_ok(text, start, end, rule["_near"]):
                    continue
                before = text[max(0, start - 40):start]
                after = text[end:end + 40]
                if any(p.search(before) for p in rule["_unless_before"]):
                    continue
                if any(p.search(after) for p in rule["_unless_after"]):
                    continue
                level, message = rule["level"], rule["message"]
                if "_down" in rule:
                    d = rule["_down"]
                    win = text[max(0, start - d.get("before", 30)):start] + " \x00 " + \
                        text[end:end + d.get("after", 30)]
                    if any(p.search(win) for p in d["_p"]):
                        level, message = d["level"], d["message"]
                if "_alt" in rule and rule["_alt"]["_p"].search(text):
                    message = rule["_alt"]["message"]
                key = (rule["code"], _line_of(text, start), m.group(0).strip())
                if key in seen:
                    continue
                seen.add(key)
                findings.append(_finding(rule, level, message, text, start, end, m.group(0)))

    # Glued hashtags ("#עורךדיןמומחה") have no word breaks to match on, so they
    # get a plain substring check against a short list in ethics.json.
    with open(rules_path, encoding="utf-8") as fh:
        subs = json.load(fh).get("hashtag_substrings", [])
    for m in re.finditer(r"#\w+", text):
        body = m.group(0)[1:].replace(" ", "").lower()
        for entry in subs:
            if entry["sub"] in body:
                rule = {"code": entry["code"], "id": entry["code"] + "-hashtag",
                        "fix": entry["fix"], "source": entry["source"]}
                key = (entry["code"], _line_of(text, m.start()), m.group(0))
                if key in seen:
                    continue
                seen.add(key)
                findings.append(_finding(rule, entry["level"], entry["message"],
                                         text, m.start(), m.end(), m.group(0)))

    # One code, one line, one verdict: a FAIL on a line hides a REVIEW of the
    # same code on that line (C1 "מספר 1" and C1 "המוביל" are one problem),
    # and several matches of one code on one line become one finding.
    worst = {}
    for f in findings:
        k = (f["code"], f["line"])
        if f["level"] == "FAIL":
            worst[k] = "FAIL"
        else:
            worst.setdefault(k, "REVIEW")
    merged = {}
    for f in findings:
        k = (f["code"], f["line"])
        if f["level"] != worst[k]:
            continue
        if k not in merged:
            merged[k] = dict(f, rules=[f["rule"]])
            continue
        m = merged[k]
        if f["rule"] not in m["rules"]:
            m["rules"].append(f["rule"])
        parts = m["match"].split(" | ")
        if f["match"] and not any(f["match"] in x for x in parts):
            # keep the longer of two overlapping matches ("הטוב ביותר בדיני")
            parts = [x for x in parts if x not in f["match"]] + [f["match"]]
            m["match"] = " | ".join(parts)
    findings = list(merged.values())
    findings.sort(key=lambda f: (f["line"], _code_num(f["code"]), f["level"] != "FAIL"))
    return {
        "context": context,
        "sponsored": sponsored,
        "findings": findings,
        "fail": sum(1 for f in findings if f["level"] == "FAIL"),
        "review": sum(1 for f in findings if f["level"] == "REVIEW"),
    }


def _code_num(code):
    return int(re.sub(r"\D", "", code) or 0)


def _finding(rule, level, message, text, start, end, match):
    return {
        "code": rule["code"],
        "rule": rule["id"],
        "level": level,
        "line": _line_of(text, start) if match else 0,
        "match": match.strip(),
        "snippet": _snippet(text, start, end) if match else "",
        "message": message,
        "fix": rule["fix"],
        "source": rule["source"],
    }


def summary_line(result):
    return f"COMPLIANCE  {result['fail']} FAIL  {result['review']} REVIEW"


def codes(result, level):
    return sorted({f["code"] for f in result["findings"] if f["level"] == level}, key=_code_num)


def render(result, out=sys.stdout):
    head = f"ETHICS LINT  ·  context: {result['context']}" + ("  ·  sponsored" if result["sponsored"] else "")
    print("\n" + head, file=out)
    print("=" * max(len(head), 62), file=out)
    if not result["findings"]:
        print("  Nothing detectable. The lawyer still reads it before it goes out (C18).", file=out)
    for f in result["findings"]:
        where = f"line {f['line']}" if f["line"] else "whole text"
        print(f"\n  {f['level']:<6} {f['code']:<4} {where}", file=out)
        if f["match"]:
            print(f"         match:   \"{f['match']}\"   in: {f['snippet']}", file=out)
        print(f"         {f['message']}", file=out)
        print(f"         תיקון:  {f['fix']}", file=out)
        print(f"         מקור:   {f['source']}", file=out)
    print("-" * max(len(head), 62), file=out)
    print(summary_line(result), file=out)


def main():
    ap = argparse.ArgumentParser(description="Lint a draft against compliance.md (C1-C23).")
    ap.add_argument("input", nargs="?", default="-", help="draft file, or - for stdin")
    ap.add_argument("--context", default="general", choices=CONTEXTS,
                    help="where the text will appear (default general)")
    ap.add_argument("--sponsored", action="store_true",
                    help="the post is paid or sponsored: the word פרסומת becomes mandatory")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--rules", default=RULES, help="path to ethics.json")
    args = ap.parse_args()

    raw = sys.stdin.read() if args.input == "-" else open(args.input, encoding="utf-8").read()
    result = run(raw, context=args.context, sponsored=args.sponsored, rules_path=args.rules)
    if args.json:
        # stdout stays valid JSON; the summary line goes to stderr as well.
        result["summary"] = summary_line(result)
        print(json.dumps(result, indent=2, ensure_ascii=False))
        sys.stdout.flush()
        print(summary_line(result), file=sys.stderr)
    else:
        render(result)
    sys.exit(1 if result["fail"] else 0)


if __name__ == "__main__":
    main()
