#!/usr/bin/env python3
"""
hebtext.py - the small amount of Hebrew every tool in this folder needs.

Imported by hookscore.py, beats.py, caption.py, humanize.py, detect.py,
ethics.py and swipe.py. Stdlib only, no network.

Nothing here rewrites the user's text. The prefix stripper exists for lexicon
lookups ("is ובהסכם the word הסכם?") and is never used to change what was written.

  is_hebrew(text)         majority script: Hebrew letters vs Latin letters
  tokens(text)            spoken words: keeps עו"ד, ש"ח, צ'קליסט, ב-2024, 40,000
  variants(word)          the word, then the word minus a conservative prefix
  lookup(word, lexicon)   first variant found in a lexicon, or None
  sentences(text)         split on . ! ? and line breaks, never inside 2.5
  concrete_markers(text)  numbers, number words, money, legal nouns, quoted terms
  person_counts(text)     first / second person markers, for ADDRESS and VOICE
  lex_regex(entry)        prefix-aware regex for a Hebrew slop.json entry
  analysis_text(text)     niqqud and invisible characters removed, for checks only
"""

import re
import unicodedata

HEB = "א-ת"                     # alef to tav, final forms included
HEB_LETTER = re.compile("[" + HEB + "]")
LAT_LETTER = re.compile("[A-Za-z]")

# Hebrew glues prepositions, the article and conjunctions onto the word
# (ובבית = "and in the house") and possessives onto the end, so the same
# sentence has roughly 15-20% fewer words than in English. 0.83 is the
# midpoint. It is a heuristic, used to scale word-count bands and the
# "per 100 words" densities so Hebrew is judged on the same footing.
WORD_RATIO = 0.83


# ---------------------------------------------------------------- language

def hebrew_share(text):
    """Share of Hebrew letters among all Hebrew + Latin letters (0.0 - 1.0)."""
    h = len(HEB_LETTER.findall(text))
    l = len(LAT_LETTER.findall(text))
    return h / (h + l) if (h + l) else 0.0


def is_hebrew(text):
    # Majority script decides. A tie, or no letters at all, stays English so
    # the original English behaviour is the default.
    return hebrew_share(text) > 0.5


def lang(text):
    return "he" if is_hebrew(text) else "en"


# ---------------------------------------------------------------- marks

# Niqqud and cantillation: every combining mark in U+0591-U+05C7. The
# punctuation that shares the block stays: maqaf U+05BE, paseq U+05C0, sof
# pasuq U+05C3, nun hafukha U+05C6. Without this, "מוּמְחֶה" is not the word
# "מומחה" to any lexicon or rule, and the tokenizer splits it into letters.
NIQQUD = "֑-ׇֽֿׁׂׅׄ"
NIQQUD_RE = re.compile("[" + NIQQUD + "]")
NQ = "[" + NIQQUD + "]*"            # optional niqqud after a letter, in patterns


def strip_niqqud(text):
    return NIQQUD_RE.sub("", text)


def strip_invisible(text):
    """Drop format characters (category Cf): zero-width space and joiners,
    soft hyphen, word joiner, BOM, bidi marks and embeddings. A zero-width
    space inside "מו​מחה" hides the word from every pattern."""
    return "".join(c for c in text if unicodedata.category(c) != "Cf")


def analysis_text(text):
    """The text the checks read: no niqqud, no invisible characters.

    Never shown to the user as a rewrite. Line breaks are untouched, so line
    numbers in a report still point at the original text.
    """
    return strip_invisible(strip_niqqud(text))


def hidden_marks(text):
    """(niqqud marks, invisible characters) in `text`, for a report note."""
    return (len(NIQQUD_RE.findall(text)),
            sum(1 for c in text if unicodedata.category(c) == "Cf"))


# ---------------------------------------------------------------- tokens

# Quote marks that can sit inside a Hebrew word: ASCII and Hebrew geresh /
# gershayim. עו"ד, ש״ח, צ'קליסט, ג׳ירפה. A trailing geresh is an
# abbreviation (מס', סע').
_INNER = "\"'׳״"
HEB_WORD = "[" + HEB + "]+(?:[" + _INNER + "][" + HEB + "]+)*['׳]?"
TOKEN_RE = re.compile(
    # a prefix glued with a hyphen to a number or a Latin word: ב-2024, ה-DM
    r"(?:[" + HEB + r"]{1,3}-)?(?:[$₪]?\d+(?:[.,]\d+)*%?₪?|[A-Za-z][A-Za-z0-9'’]*(?:-[A-Za-z0-9]+)*)"
    r"|" + HEB_WORD +
    r"|₪"
)


def tokens(text):
    """Spoken-word tokens. "40,000" is one word when it is spoken, so it is one here."""
    return TOKEN_RE.findall(re.sub(r"(?<=\d),(?=\d)", "", text))


def token_spans(text):
    """[(token, start, end)] on the text as given (commas in numbers kept)."""
    rx = re.compile(r"(?:[" + HEB + r"]{1,3}-)?[$₪]?\d[\d,]*(?:\.\d+)?%?₪?|" + TOKEN_RE.pattern)
    return [(m.group(0), m.start(), m.end()) for m in rx.finditer(text)]


def norm(word):
    """Normalise quote marks and drop a trailing geresh or quote, for lookups."""
    w = word.replace("״", '"').replace("׳", "'").replace("’", "'")
    return w.rstrip("'\"")


# ---------------------------------------------------------------- prefixes

# One-letter clitics ו ה ב ל מ ש כ and the common combinations, at most three
# letters. Tried shortest first.
PREFIXES = (
    "ו", "ה", "ב", "ל", "מ", "ש", "כ",
    "וה", "וב", "ול", "ומ", "וש", "וכ", "שה", "שב", "של", "שמ", "שכ",
    "מה", "כש", "לכ", "בה",
    "וכש", "ושה", "ושב", "ושל", "ומה", "כשה", "כשב", "כשל",
)
# A two-letter stem is where stripping goes wrong: מלא is not מ + לא, כלא is
# not כ + לא, ברק is not ב + רק. A two-letter stem only loses a conjunction,
# unless it is a short noun that really does take every prefix (בצו, הגט).
CONJ_PREFIXES = {"ו", "ש", "וש", "כש", "וכש"}
SHORT_NOUNS = {"גט", "צו", "שש"}


def variants(word, min_stem=2):
    """[word, word minus a 1-, 2- or 3-letter prefix], the stem never under 2 letters."""
    w = norm(word)
    out = [w]
    for p in sorted(PREFIXES, key=len):
        if not w.startswith(p):
            continue
        stem = w[len(p):]
        if len(stem) < min_stem or not HEB_LETTER.match(stem):
            continue
        if len(stem) == 2 and p not in CONJ_PREFIXES and stem not in SHORT_NOUNS:
            continue
        if stem not in out:
            out.append(stem)
    return out


def lookup(word, lexicon):
    """The first variant of `word` that is in `lexicon`, or None. Lookups only."""
    for v in variants(word):
        if v in lexicon:
            return v
    return None


# Regex fragments for prefix-aware patterns: an optional run of up to three
# prefix letters, not glued to a previous word; an end not followed by a letter.
PREFIX_RX = r"(?<![\w])(?:[ובלמשכה]{1,3})?"
END_RX = r"(?![\w])"


# ---------------------------------------------------------------- numbers & money

# Spoken numbers. אחד/אחת are deliberately absent, like "one" in English:
# they are filler far more often than a quantity. שני is absent too, because
# השני ("the other one") is far more common than "two".
NUMBER_WORDS = {
    "שניים", "שלושה", "ארבעה", "חמישה", "שישה", "שבעה", "שמונה", "תשעה", "עשרה",
    "שתיים", "שתי", "שלוש", "ארבע", "חמש", "שש", "שבע", "תשע", "עשר",
    "שלושת", "ארבעת", "חמשת", "ששת", "שבעת", "שמונת", "תשעת", "עשרת",
    "עשרים", "שלושים", "ארבעים", "חמישים", "שישים", "שבעים", "שמונים", "תשעים",
    "מאה", "מאתיים", "מאות", "אלף", "אלפיים", "אלפים", "אלפי", "רבבה",
    "מיליון", "מיליונים", "מיליוני", "מיליארד", "עשרות",
    "חצי", "רבע", "שליש", "פעמיים", "כפול", "תריסר", "שנתיים", "חודשיים", "יומיים",
}
MONEY_WORDS = {
    "₪", 'ש"ח', "שקל", "שקלים", "אגורה", "אגורות", "דולר", "דולרים", "יורו",
    "אחוז", "אחוזים", "משכורת", "משכורות", "משכנתא", "משכנתה", "שכר",
}

NUMBER_RE = re.compile(r"[$₪]?\d[\d,]*(?:\.\d+)?\s?(?:%|₪)?")
PLACEHOLDER_RE = re.compile(r"\{\{[^}]*\}\}")


# ---------------------------------------------------------------- legal nouns

# Concrete legal-domain nouns. Hebrew has no capital letters, so a proper-noun
# check is impossible; in a family-law account these nouns do the job a name
# does in English: they make the line about something you can check.
LEGAL_WORDS = {
    "סעיף", "סעיפים", "תקנה", "תקנות", "חוק", "חוקים",
    "מזונות", "משמורת", "צו", "צווים", "עיקול", "עיקולים",
    "ירושה", "ירושות", "צוואה", "צוואות", "גט", "כתובה",
    "הסכם", "הסכמים", "הסכמי", "תביעה", "תביעות", "ערעור", "גישור", "בוררות",
    "אפוטרופסות", "אפוטרופוס", "תסקיר", 'עו"ד', 'בימ"ש', 'ביהמ"ש',
    "גירושין", "גירושים", "נישואין", "אימוץ", "אבהות", "פונדקאות",
    'הוצל"פ', 'תמ"ש', 'פס"ד', "פסיקה", "פסיקת",
}
LEGAL_PHRASES = [
    "בית הדין הרבני", "בית דין רבני",
    "בית המשפט לענייני משפחה", "בית משפט לענייני משפחה", "בית המשפט",
    "הוצאה לפועל", "רשם הירושות",
    "הסכם ממון", "הסכמי ממון", "הסכם גירושין", "הסכם יחסי ממון", "חוק יחסי ממון",
    "הסדרי שהות", "הסדרי ראייה", "משמורת משותפת",
    "צו הגנה", "צו עיכוב יציאה", "צו מניעה", "צו ירושה", "צו קיום צוואה",
    "איזון משאבים", "חלוקת רכוש", "פסק דין", "כתב תביעה",
    "תביעת מזונות", "סרבנות גט", "ייפוי כוח מתמשך", "פקיד סעד", "פקידת סעד",
    "יישוב סכסוך", "תקנות סדר הדין", "ידועים בציבור", "ידועה בציבור",
]


def _phrase_rx(phrase):
    """'הסכם ממון' -> prefix-aware regex that also accepts 'הסכם הממון'."""
    parts = [re.escape(p).replace('"', '["״]') for p in phrase.split()]
    body = parts[0] + "".join(r"\s+ה?" + p for p in parts[1:])
    return PREFIX_RX + body + END_RX


LEGAL_PHRASE_RE = re.compile("|".join(
    _phrase_rx(p) for p in sorted(LEGAL_PHRASES, key=len, reverse=True)))

QUOTED_RE = re.compile(
    r"(?:(?<=\s)|^)[\"“”״]([^\"“”״\n]{2,40})[\"“”״](?![" + HEB + r"])",
    re.MULTILINE)


def concrete_markers(text):
    """[(kind, surface, start)] for every checkable thing in `text`.

    kinds: number, number-word, money, legal, quoted, placeholder. A phrase
    like "בית המשפט לענייני משפחה" counts once, not once per word inside it.
    A {{placeholder}} counts: it stands for a real number the user will fill in.
    """
    found = []
    taken = []

    def free(pos):
        return not any(a <= pos < b for a, b in taken)

    for m in PLACEHOLDER_RE.finditer(text):
        found.append(("placeholder", m.group(0), m.start()))
        taken.append(m.span())
    for m in LEGAL_PHRASE_RE.finditer(text):
        if free(m.start()):
            found.append(("legal", m.group(0).strip(), m.start()))
            taken.append(m.span())
    for m in QUOTED_RE.finditer(text):
        if free(m.start()):
            found.append(("quoted", m.group(0), m.start()))
            taken.append(m.span())
    for m in NUMBER_RE.finditer(text):
        if m.group(0).strip() and free(m.start()):
            found.append(("number", m.group(0).strip(), m.start()))
            taken.append(m.span())
    for m in re.finditer("₪", text):
        if free(m.start()):
            found.append(("money", "₪", m.start()))
    for tok, start, _ in token_spans(text):
        if not free(start) or re.search(r"\d", tok) or not HEB_LETTER.match(tok):
            continue
        if lookup(tok, NUMBER_WORDS):
            found.append(("number-word", tok, start))
        elif lookup(tok, MONEY_WORDS):
            found.append(("money", tok, start))
        elif lookup(tok, LEGAL_WORDS):
            found.append(("legal", tok, start))
    return sorted(found, key=lambda f: f[2])


# ---------------------------------------------------------------- sentences

def sentences(text):
    """Split on . ! ? … and line breaks. A decimal point is not a sentence end."""
    t = re.sub(r"(?<=\d)\.(?=\d)", "\x00", text)
    parts = re.findall(r"[^.!?…\n]+[.!?…]*", t)
    return [p.replace("\x00", ".").strip() for p in parts if p.strip()]


# ---------------------------------------------------------------- person

FIRST_PERSON = {
    "אני", "לי", "שלי", "אותי", "איתי", "ממני", "אליי", "עליי", "בשבילי", "אצלי",
    "כמוני", "אנחנו", "אנו", "לנו", "שלנו", "אותנו", "איתנו", "מאיתנו", "אלינו",
    "עלינו", "בשבילנו", "אצלנו",
}
# "את" is left out on purpose: it is far more often the object marker than "you".
SECOND_PERSON = {
    "אתה", "אתם", "אתן", "לך", "לכם", "לכן", "שלך", "שלכם", "שלכן", "אותך",
    "אתכם", "אתכן", "אותכם", "איתך", "איתכם", "ממך", "מכם", "אליך", "אלייך",
    "אליכם", "עליך", "עלייך", "עליכם", "בשבילך", "בשבילכם", "אצלך", "אצלכם",
    "כמוך", "בך", "בכם",
}
# Imperatives and 2nd-person future forms that open hooks and CTAs.
IMPERATIVES = {
    "תחתמו", "תבדקו", "תשאלו", "תקראו", "תעשו", "תגידו", "תדעו", "תזכרו",
    "תשמרו", "תכתבו", "תשלחו", "תשתפו", "תעקבו", "תחכו", "תבואו", "תביאו",
    "תתחילו", "תפסיקו", "תנסו", "תקחו", "תיקחו", "תחשבו", "תבינו", "תפנו",
    "תחליטו", "תוודאו", "תגישו", "תצרפו", "תדברו", "תספרו", "תוותרו",
    "תסכימו", "תעתיקו", "תגנבו", "תראו", "תסתכלו", "תצפו", "תשמעו", "תקשיבו",
    "תמחקו", "תעצרו", "תגללו", "תחתום", "תבדוק", "תשאל", "תקרא", "תעשה",
    "תגיד", "תדע", "תזכור", "תפסיק", "תחכה", "תשים", "תחתמי", "תבדקי",
    "תשאלי", "תקראי", "תעשי", "תגידי", "תדעי", "תזכרי", "תפסיקי",
    "חתמו", "בדקו", "שאלו", "קראו", "עשו", "דעו", "זכרו", "שמרו", "כתבו",
    "שלחו", "שתפו", "עקבו", "חכו", "בואו", "הביאו", "התחילו", "הפסיקו",
    "נסו", "קחו", "חשבו", "הבינו", "פנו", "החליטו", "ודאו", "וודאו", "הגישו",
    "צרפו", "דברו", "ספרו", "תנו", "שימו", "לכו", "ראו", "שמעו", "הקשיבו",
    "העתיקו", "גנבו", "צפו", "הסתכלו", "מחקו", "עצרו", "שמור", "בדוק", "קח",
    "נסה", "דע", "זכור", "עצור", "חכה", "שים", "שאל", "קרא", "תן", "שמרי",
    "בדקי", "קחי", "נסי", "דעי", "זכרי", "חכי", "שימי", "שאלי", "קראי", "תני",
}
# Common 2nd-person-plural past verbs. -תם is also "their" on feminine nouns
# (זכותם, משפחתם), so the suffix alone is not trusted.
SECOND_PAST = {
    "חתמתם", "קיבלתם", "שילמתם", "התגרשתם", "נפרדתם", "הגשתם", "ידעתם",
    "שאלתם", "ראיתם", "שמעתם", "חשבתם", "עשיתם", "הבנתם", "קראתם", "בדקתם",
    "הסכמתם", "החלטתם", "פניתם", "נכנסתם", "יצאתם", "התחתנתם", "עברתם",
    "הייתם", "רציתם", "ניסיתם", "שכחתם", "טעיתם", "פספסתם", "ויתרתם",
    "הגעתם", "התחלתם", "סיימתם", "דחיתם", "שלחתם", "כתבתם", "אמרתם",
    "חיכיתם", "הפסדתם", "השארתם", "קניתם", "מכרתם", "עזבתם", "ביקשתם",
    "נתתם", "לקחתם", "שמתם", "תכננתם", "התכוונתם", "מצאתם", "שכחתן",
    "חתמת", "קיבלת", "שילמת", "התגרשת",
}
# Adjectives and nouns that end in -תי without being "I did".
NOT_FIRST_PAST = {
    "משפחתי", "חברתי", "תרבותי", "אמיתי", "שנתי", "ממשלתי", "מהותי",
    "בריאותי", "כיתתי", "איכותי", "כמותי", "סמכותי", "עובדתי", "חוקתי",
    "תחתי", "זמני", "אישי",
}


def _is_first_past(w):
    return len(w) >= 4 and w.endswith("תי") and w not in NOT_FIRST_PAST


def _is_second_verb(w):
    if w in IMPERATIVES or w in SECOND_PAST:
        return True
    # generic 2nd-person plural future: ת...ו, five letters or more (תתגרשו)
    return len(w) >= 5 and w.startswith("ת") and w.endswith("ו")


def person_counts(text):
    """{"first": n, "second": n, "second_verbs": n, "opener": kind or None}.

    opener is "imperative" when the line opens on a 2nd-person verb, or on
    אל + verb ("אל תחתמו"), which is how Hebrew gives an order.
    """
    toks = [norm(t) for t in tokens(text) if HEB_LETTER.match(t)]
    first = second = second_verbs = 0
    for t in toks:
        vs = variants(t)
        stem = vs[1] if len(vs) > 1 and t[0] in "וש" else t   # strip ו / ש only
        if any(v in SECOND_PERSON for v in (t, stem)):
            second += 1
        elif any(_is_second_verb(v) for v in (t, stem)):
            second_verbs += 1
        elif any(v in FIRST_PERSON for v in (t, stem)) or any(_is_first_past(v) for v in (t, stem)):
            first += 1
    # "את" is "you" (f.) when it opens the line and the next word is not
    # definite: "את חייבת לדעת" yes, "את ההסכם" no.
    if len(toks) > 1 and toks[0] == "את" and not toks[1].startswith("ה"):
        second += 1
    opener = None
    if toks:
        t0 = toks[0][1:] if toks[0].startswith("ו") and len(toks[0]) > 3 else toks[0]
        if _is_second_verb(t0) or (t0 in ("אל", "לעולם") and len(toks) > 1
                                     and _is_second_verb(toks[1] if t0 == "אל" else toks[-1])):
            opener = "imperative"
    return {"first": first, "second": second, "second_verbs": second_verbs, "opener": opener}


# ---------------------------------------------------------------- register

# Spoken Hebrew. A caption or a script that sounds like a person has some of
# these; a generated one has almost none.
SPOKEN_MARKERS = {
    "אז", "כאילו", "בעצם", "פשוט", "ממש", "נו", "וואלה", "יאללה", "סתם",
    "תכלס", "בקיצור", "בטח", "ככה", "כזה", "כזאת", "עזבו", "תשמעו", "תקשיבו",
    "רגע", "האמת", "באמת", "אוקיי", "זהו", "שנייה", "בסדר", "הכי", "די",
}
# Written, formal register. Fine in a contract, a tell in a caption.
FORMAL_MARKERS = {
    "אשר", "הינו", "הינה", "הינם", "הנו", "אינו", "אינה", "אינם", "אינן",
    "כאשר", "לפיכך", "אולם", "אך", 'הנ"ל', "באמצעות", "לרבות", "כגון",
    "בנוסף", "ניתן", "עשוי", "עשויה", "עשויים", "מהווה", "מהווים", "מהוות",
    "יתרה", "במסגרת", "אודות", "בטרם", "מאחר", "ביותר", "הנכם", "הינכם",
}


def register_counts(text):
    """(spoken, formal) marker counts; prefix-aware lookups."""
    spoken = formal = 0
    for t in tokens(text):
        if not HEB_LETTER.match(t):
            continue
        if lookup(t, SPOKEN_MARKERS):
            spoken += 1
        elif lookup(t, FORMAL_MARKERS):
            formal += 1
    formal += len(re.findall(r"(?<![\w])(?:ו)?(?:על מנת|כמו כן|יש ל[" + HEB + r"]+)(?![\w])", text))
    return spoken, formal


# ---------------------------------------------------------------- stopwords

# Function words that cannot carry a loop between the first and last beat.
STOPWORDS = {
    "של", "את", "על", "עם", "זה", "זאת", "זו", "הוא", "היא", "הם", "הן",
    "אני", "אתה", "אתם", "אתן", "אנחנו", "לא", "כן", "יש", "אין", "גם", "רק",
    "כל", "מה", "מי", "איך", "למה", "כי", "אם", "או", "אבל", "אז", "עוד",
    "כבר", "היה", "הייתה", "היו", "להיות", "יהיה", "תהיה", "שלי", "שלך", "שלו",
    "שלה", "שלנו", "שלכם", "שלהם", "לי", "לך", "לו", "לה", "לנו", "לכם",
    "להם", "אותו", "אותה", "אותם", "אותי", "אותך", "אתכם", "כמו", "כך", "ככה",
    "פה", "כאן", "שם", "אחד", "אחת", "הזה", "הזאת", "האלה", "אלה", "אלו",
    "מאוד", "הכי", "יותר", "פחות", "אחרי", "לפני", "בין", "עד", "תוך", "בלי",
    "אצל", "אל", "מן", "בגלל", "כדי", "אפילו", "עכשיו", "היום", "טוב", "רוצה",
    "רוצים", "צריך", "צריכה", "צריכים", "יכול", "יכולה", "יכולים", "אפשר",
    "דבר", "דברים", "משהו", "הנה", "נכון", "ממש", "בעצם", "אחר", "אחרת",
    "תמיד", "אף", "פעם", "עליו", "עליה", "בו", "בה", "בהם", "ממנו", "ממנה",
    "אשר", "כאשר", "אצלי", "איתי", "איתך", "בשביל", "כמה", "איזה", "איזו",
    "מכם", "מהם", "מכן", "ממני", "אליו", "אליה", "אליי", "אלינו", "אתכם",
    "איתכם", "שלכן", "לכן", "אותנו", "עלינו", "עליכם", "כאלה", "כזה", "כזאת",
}


def is_stopword(word):
    return any(v in STOPWORDS for v in variants(word))


def content_keys(text):
    """Loop keys for beats.py: every prefix-stripped content word, digits normalised.

    "ההסכם" and "הסכם" share the key "הסכם"; "40,000" and "40000" share "40000".
    Returns {key: surface}.
    """
    keys = {}
    for t in tokens(text):
        digits = re.sub(r"[^\d.]", "", t)
        if re.search(r"\d", t):
            keys.setdefault(digits.strip("."), t)
            continue
        if not HEB_LETTER.match(t):
            if t.lower() not in STOPWORDS:
                keys.setdefault(t.lower(), t)
            continue
        if is_stopword(t):
            continue
        for v in variants(t):
            if len(v) >= 3:
                keys.setdefault(v, t)
    return keys


# ---------------------------------------------------------------- lexicon regex

_HEB_CHAR = re.compile("[" + HEB + "]")


def niqqud_tolerant(rx):
    """Let optional niqqud follow every Hebrew letter or Hebrew class in `rx`.

    "ה?" becomes "(?:ה<NQ>)?", not "ה<NQ>?", so a quantifier still applies to
    the letter; "[א-ת]+" becomes "(?:[א-ת]<NQ>)+". Escapes are copied as they are.
    """
    out, i, n = [], 0, len(rx)
    while i < n:
        c = rx[i]
        if c == "\\":
            out.append(rx[i:i + 2])
            i += 2
            continue
        if c == "[":
            j = i + 1
            if j < n and rx[j] == "^":
                j += 1
            if j < n and rx[j] == "]":
                j += 1
            while j < n and rx[j] != "]":
                j += 2 if rx[j] == "\\" else 1
            atom, i = rx[i:j + 1], j + 1
            hebrew = bool(_HEB_CHAR.search(atom)) and not atom.startswith("[^")
        else:
            atom, i = c, i + 1
            hebrew = bool(_HEB_CHAR.match(c))
        if not hebrew:
            out.append(atom)
        elif i < n and rx[i] in "?*+{":
            out.append("(?:" + atom + NQ + ")")
        else:
            out.append(atom + NQ)
    return "".join(out)


def lex_regex(entry):
    """Prefix-aware regex for one Hebrew slop.json entry (humanize, detect).

    - an optional prefix (group `pre`, up to 3 letters) may sit in front of the
      entry: "ובעולם של היום" matches "בעולם של היום";
    - words are separated by any whitespace;
    - when the entry ends in a lone prefix letter ("חשוב לזכור ש"), or has
      "glued": true, that letter is glued to the next word: it matches
      "חשוב לזכור שהחוזה" (and "חשוב לזכור, שהחוזה") and consumes nothing of
      the next word;
    - an entry with "regex": true is used as written inside the same frame.
    """
    find = entry["find"]
    glued = bool(entry.get("glued"))
    if entry.get("regex"):
        body = "(?:" + find + ")"
    else:
        parts = find.split()
        glued = glued or (len(parts) > 1 and len(parts[-1]) == 1 and parts[-1] in "ובלמשכה")
        if glued and len(parts[-1]) == 1:
            body = r"\s+".join(re.escape(p) for p in parts[:-1])
            body += r"\s*,?\s*" + re.escape(parts[-1])
        else:
            body = r"\s+".join(re.escape(p) for p in parts)
    # Niqqud may sit on any letter: "בְּעוֹלָם שֶׁל הַיּוֹם" is still the
    # phrase, and a deleted phrase takes its marks with it.
    body = niqqud_tolerant(body)
    tail = r"(?=[" + HEB + r"\"'])" if glued else END_RX
    return re.compile(r"(?<![\w])(?P<pre>(?:[ובלמשכה]" + NQ + r"){0,3}?)" + body + tail)


def lex_label(entry):
    """What a report calls an entry: its label, else its find string."""
    return entry.get("label") or entry["find"]
