#!/usr/bin/env python3
"""
run_tests.py - regression tests for the tools in shared/, Hebrew and English.

  python3 tests/run_tests.py

Stdlib only. Runs against shared/ (the source), so run it before build.py.
Each test names the bug it pins down; a failure prints what came back.
"""

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SHARED = os.path.join(ROOT, "shared")
sys.path.insert(0, SHARED)

import caption        # noqa: E402
import detect         # noqa: E402
import ethics         # noqa: E402
import hebtext as he  # noqa: E402
import hookscore      # noqa: E402
import humanize       # noqa: E402
import swipe          # noqa: E402
import beats          # noqa: E402

LEX = json.load(open(os.path.join(SHARED, "slop.json"), encoding="utf-8"))
ZW, SHY = "​", "­"
RESULTS = []


def test(name):
    def wrap(fn):
        try:
            fn()
            RESULTS.append((name, None))
        except AssertionError as e:
            RESULTS.append((name, str(e) or "assertion failed"))
        except Exception as e:                       # a crash is a failure too
            RESULTS.append((name, f"{type(e).__name__}: {e}"))
        return fn
    return wrap


def eq(got, want):
    assert got == want, f"got {got!r}, want {want!r}"


def cli(tool, *args, stdin=None):
    p = subprocess.run([sys.executable, "-I", os.path.join(SHARED, tool), *args],
                       input=stdin, capture_output=True, text=True, encoding="utf-8")
    return p.returncode, p.stdout + p.stderr


def codes(text, **kw):
    r = ethics.run(text, **kw)
    return ethics.codes(r, "FAIL"), ethics.codes(r, "REVIEW")


def humanized(text):
    return humanize.humanize(text, LEX)[0].strip()


# ------------------------------------------------------------------ ethics

PLAIN = "אני מומחה בדיני משפחה, ייעוץ ראשון חינם"
NIQQUD = "אני מוּמְחֶה בדיני משפחה, ייעוץ ראשון חִינָּם"


@test("ethics: plain 'מומחה' and 'חינם' fail C2 and C9")
def _():
    eq(codes(PLAIN)[0], ["C2", "C9"])


@test("ethics: niqqud does not hide a FAIL (was 0 FAIL)")
def _():
    eq(codes(NIQQUD)[0], ["C2", "C9"])


@test("ethics: a zero-width space inside a word does not hide a FAIL (was 0 FAIL)")
def _():
    eq(codes("אני מו" + ZW + "מחה בדיני משפחה, ייעוץ ראשון חי" + ZW + "נם")[0], ["C2", "C9"])


@test("ethics: a soft hyphen inside a word does not hide a FAIL")
def _():
    eq(codes("אני מומ" + SHY + "חה בדיני משפחה")[0], ["C2"])


@test("ethics: line numbers still point at the draft after cleaning")
def _():
    r = ethics.run("שורה ראשונה נקייה\nאני מוּמְחֶה" + ZW + " בדיני משפחה")
    eq([f["line"] for f in r["findings"] if f["code"] == "C2"], [2])


@test("ethics: the report says what was cleaned")
def _():
    r = ethics.run(NIQQUD)
    eq(r["cleaned"], {"niqqud": 6, "invisible": 0})


@test("ethics: a neutral sentence passes")
def _():
    eq(codes("שלושה דברים שכדאי לבדוק בהסכם ממון לפני החתימה")[0], [])


@test("ethics: --sponsored without the word פרסומת is flagged")
def _():
    r = ethics.run("שלושה דברים שכדאי לבדוק בהסכם ממון", sponsored=True)
    assert r["fail"] + r["review"] >= 1, r


@test("ethics: a price next to a service fails C9 (was clean)")
def _():
    for t in ['הסכם ממון ב-5,000 ש"ח בלבד', "פגישת ייעוץ 500 ₪", "עריכת צוואה החל מ-2,000 שקלים",
              "רק 1,500 ₪ לפגישה", 'שכר טרחה: 5,000 ש"ח']:
        assert "C9" in codes(t)[0], (t, codes(t))


@test("ethics: amounts that are legal information are not a price")
def _():
    for t in ['המזונות הממוצעים הם 3,000 ש"ח לילד', 'חוב של 50,000 ש"ח עלול להוביל לעיקול',
              'בהסכם הממון נקבע שהדירה שווה 2,000,000 ש"ח', 'מזונות של 2,500 ש"ח בחודש נקבעו בהסכם']:
        assert "C9" not in codes(t)[0] + codes(t)[1], (t, codes(t))


@test("ethics: a domain in ~/.claude/instagram/allowed_domains.txt is not a C16 REVIEW")
def _():
    with tempfile.TemporaryDirectory() as home:
        draft = "פרטים באתר https://example-law.co.il/prenup"
        env = dict(os.environ, HOME=home)
        run = lambda: subprocess.run([sys.executable, "-I", os.path.join(SHARED, "ethics.py"), "-"],
                                     input=draft, capture_output=True, text=True, env=env).stdout
        assert "C16" in run(), run()
        os.makedirs(os.path.join(home, ".claude", "instagram"))
        open(os.path.join(home, ".claude", "instagram", "allowed_domains.txt"), "w").write(
            "example-law.co.il   # landing page\n")
        assert "C16" not in run(), run()


# ------------------------------------------------------------------ caption

@test("caption: 'שלחו לי הודעה' is one ask, not DM + share (was two)")
def _():
    eq(caption.analyse("מה בודקים בהסכם ממון? שלחו לי הודעה", run_ethics=False)["asks"], ["DM me"])


@test("caption: 'תשלחו לנו הודעה בוואטסאפ' is one ask (was two)")
def _():
    eq(caption.analyse("מה בודקים בהסכם ממון? תשלחו לנו הודעה בוואטסאפ",
                       run_ethics=False)["asks"], ["DM me"])


@test("caption: 'שתפו לחברה' is still a share")
def _():
    eq(caption.analyse("מה בודקים בהסכם ממון? שתפו לחברה שמתחתנת", run_ethics=False)["asks"],
       ["share this"])


@test("caption: 'שלחו את זה לחבר' is still a share")
def _():
    eq(caption.analyse("מה בודקים בהסכם ממון? שלחו את זה לחבר", run_ethics=False)["asks"],
       ["share this"])


@test("caption: niqqud in the caption still trips the ethics gate (verdict FIX)")
def _():
    eq(caption.analyse(NIQQUD + "\n\nשמרו את הפוסט")["verdict"], "FIX")


@test("caption: --sponsored reaches the ethics gate")
def _():
    a = caption.analyse("שלושה דברים שכדאי לבדוק בהסכם ממון. שמרו", sponsored=True)
    b = caption.analyse("שלושה דברים שכדאי לבדוק בהסכם ממון. שמרו", sponsored=False)
    assert a["ethics"]["fail"] + a["ethics"]["review"] > b["ethics"]["fail"] + b["ethics"]["review"], (a["ethics"], b["ethics"])


@test("caption: CLI accepts --sponsored")
def _():
    rc, out = cli("caption.py", "-", "--sponsored", stdin="שלושה דברים שכדאי לבדוק בהסכם ממון. שמרו")
    assert "ETHICS" in out and "unrecognized" not in out, out


@test("caption: keywords are found through niqqud")
def _():
    a = caption.analyse("עוֹרֵךְ דִּין גירושין בנתניה מסביר", keywords=["עורך דין גירושין"], run_ethics=False)
    eq([c["status"] for c in a["checks"] if c["check"] == "SEARCH TERMS"], ["PASS"])


# ------------------------------------------------------------------ hookscore

@test("hookscore: a hook with niqqud scores like the same hook without (was 12 vs 100)")
def _():
    plain = "אל תחתמו על הסכם ממון לפני שאתם בודקים את סעיף 4"
    pointed = "אַל תַּחְתְּמוּ עַל הֶסְכֵּם מָמוֹן לִפְנֵי שֶׁאַתֶּם בּוֹדְקִים אֶת סָעִיף 4"
    eq(round(hookscore.run(pointed)[1], 1), round(hookscore.run(plain)[1], 1))


@test("hookscore: English scores are unchanged from the original (85.6 / 81.4 / 54.4 / 9.6)")
def _():
    hooks = ["Nobody tells you that your first 30 reels are supposed to flop.",
             "I lost $18,000 because of one missing contract.",
             "Stop scrolling if you want to grow on Instagram in 2026 🔥",
             "Hey guys, today I wanted to talk about content strategy"]
    eq([round(hookscore.run(h)[1], 1) for h in hooks], [85.6, 81.4, 54.4, 9.6])


@test("hookscore: 'גירושין' counts as a concrete legal term (was SPECIFICITY 15)")
def _():
    assert hookscore.run("מה קורה עם הדירה אחרי הגירושין?")[0]["SPECIFICITY"][0] >= 70


@test("hookscore: 'טעיתי' is a stakes word (was STAKES 20)")
def _():
    assert hookscore.run("טעיתי בהסכם הממון הראשון שכתבתי")[0]["STAKES"][0] >= 70


@test("hookscore: Hebrew formula classification reads through niqqud")
def _():
    plain = hookscore.classify_he("אל תחתמו על הסכם ממון לפני שאתם בודקים את סעיף 4")
    pointed = hookscore.classify_he("אַל תַּחְתְּמוּ עַל הֶסְכֵּם מָמוֹן לִפְנֵי שֶׁאַתֶּם בּוֹדְקִים אֶת סָעִיף 4")
    eq(pointed, plain)


# ------------------------------------------------------------------ beats

@test("beats: a script with niqqud is timed like the same script without (was 15.4s vs 4.3s)")
def _():
    plain = "אל תחתמו על הסכם ממון לפני שאתם בודקים את סעיף 4.\nזה הסעיף שעולה הכי הרבה כסף."
    pointed = "אַל תַּחְתְּמוּ עַל הֶסְכֵּם מָמוֹן לִפְנֵי שֶׁאַתֶּם בּוֹדְקִים אֶת סָעִיף 4.\nזה הסעיף שעולה הכי הרבה כסף."
    eq(beats.analyse(pointed)["total_seconds"], beats.analyse(plain)["total_seconds"])


# ------------------------------------------------------------------ humanize

@test("humanize: a single letter the writer typed is not glued to the next word (was 'המתייחס')")
def _():
    out = humanized("סעיף קטן ה מתייחס לזה. בעולם של היום הכל ברור.")
    assert "סעיף קטן ה מתייחס" in out, out


@test("humanize: a conjunction left by a deleted phrase still glues on ('והכל')")
def _():
    out = humanized("זה המצב, ובסופו של יום הכל ברור.")
    assert "והכל ברור" in out, out


@test("humanize: slop with niqqud is found (was 'Nothing to strip')")
def _():
    out = humanized("וּבְסוֹפוֹ שֶׁל יוֹם הכל ברור.")
    assert "סוֹפוֹ" not in out, out


@test("humanize: a regex slop entry with niqqud is found")
def _():
    out = humanized("בְּעוֹלָם שֶׁל הַיּוֹם, ההסכם מחייב.")
    assert "עוֹלָם" not in out and "ההסכם מחייב" in out, out


@test("humanize: niqqud the writer put on other words is kept")
def _():
    out = humanized("בעולם של היום, הַהֶסְכֵּם מחייב.")
    assert "הַהֶסְכֵּם" in out, out


@test("humanize: every Hebrew lexicon entry compiles")
def _():
    for e in LEX["phrases"] + LEX["words"]:
        if e.get("lang") == "he":
            he.lex_regex(e)


@test("hebtext: niqqud_tolerant keeps a quantifier on its letter")
def _():
    import re
    rx = re.compile(he.niqqud_tolerant("ה?בית"))
    assert rx.fullmatch("בית") and rx.fullmatch("הַבַּיִת") and rx.fullmatch("הבית"), rx.pattern


@test("hebtext: analysis_text keeps line breaks and counts what it removed")
def _():
    t = "שׁוּרָה\nשו" + ZW + "רה"
    eq(he.analysis_text(t), "שורה\nשורה")
    eq(he.hidden_marks(t), (3, 1))


@test("humanize: bidi marks go in English text (as in the original) and stay in Hebrew")
def _():
    assert "\u200e" not in humanized("Sign the contract\u200e today."), "English kept LRM"
    assert "\u200f" in humanized("חתמו על ההסכם\u200f היום ABC."), "Hebrew lost RLM"


# ------------------------------------------------------------------ detect

@test("detect: niqqud does not change the Hebrew human score")
def _():
    plain = "חתמתי על הסכם ממון ב-2019. שנתיים אחר כך גיליתי שסעיף 4 לא שווה כלום. אז מה עושים?"
    pointed = "חָתַמְתִּי עַל הֶסְכֵּם מָמוֹן ב-2019. שנתיים אחר כך גיליתי שסעיף 4 לא שווה כלום. אז מה עושים?"
    eq(round(detect.run(pointed, LEX)[1], 1), round(detect.run(plain, LEX)[1], 1))


# ------------------------------------------------------------------ swipe

TSV = ("account\tfollowers\tmedian\tviews\thook\tflag\n"
       "@a\t9000\t2000\t40000\tאל תחתמו על הסכם ממון לפני שאתם בודקים את סעיף 4\tC15\n"
       "@b\t9000\t2000\t30000\tאף אחד לא מספר לכם מה קורה ביום הראשון אחרי הגירושין\t\n"
       "@c\t9000\t2000\t2000\tהיום רציתי לדבר על משהו\t\n")


def _swipe(tsv):
    with tempfile.TemporaryDirectory() as tmp:
        src, out = os.path.join(tmp, "c.tsv"), os.path.join(tmp, "swipe.md")
        open(src, "w", encoding="utf-8").write(tsv)
        rc, txt = cli("swipe.py", src, "--out", out)
        return rc, txt, open(out, encoding="utf-8").read() if os.path.exists(out) else ""


@test("swipe: a compliance flag reaches swipe.md (was dropped)")
def _():
    rc, txt, md = _swipe(TSV)
    assert "[FLAG C15]" in md and "FLAG C15" in txt, md + txt


@test("swipe: a flagged reel is left out of 'what is working'")
def _():
    rc, txt, md = _swipe(TSV)
    assert "compliance flags:      1 of 3" in txt, txt


@test("swipe: the Hebrew header 'ציות' is read as the flag column")
def _():
    rc, txt, md = _swipe(TSV.replace("\tflag\n", "\tציות\n", 1))
    assert "[FLAG C15]" in md, md


# ------------------------------------------------------------------ render_slides

@test("render_slides: refuses a file with {{...}} left in it")
def _():
    with tempfile.TemporaryDirectory() as tmp:
        p = os.path.join(tmp, "c.html")
        open(p, "w", encoding="utf-8").write("<section>{{כותרת}}</section>")
        rc, out = cli("render_slides.py", p)
        assert rc != 0 and "לא מרנדרים" in out, out


@test("render_slides: --help works and a missing file is a clear message (was a traceback)")
def _():
    rc, out = cli("render_slides.py", "--help")
    eq(rc, 0)
    rc, out = cli("render_slides.py", "/nonexistent/c.html")
    assert rc != 0 and "Traceback" not in out, out


# ------------------------------------------------------------------ build

@test("build: shared/ and the 13 skill copies are in sync")
def _():
    p = subprocess.run([sys.executable, "-I", os.path.join(ROOT, "build.py"), "--check"],
                       capture_output=True, text=True)
    assert p.returncode == 0, p.stdout + p.stderr


def main():
    width = max(len(n) for n, _ in RESULTS)
    for name, err in RESULTS:
        print(f"  {'PASS' if err is None else 'FAIL'}  {name}")
        if err:
            print(f"        {err}")
    failed = sum(1 for _, e in RESULTS if e)
    print("-" * min(width + 8, 100))
    print(f"{len(RESULTS) - failed} passed, {failed} failed")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
