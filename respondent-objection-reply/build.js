const fs = require('fs');
const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, BorderStyle, WidthType, UnderlineType,
  LineRuleType, Footer, PageNumber, TabStopType
} = require('docx');

const PAGE_W = 11906, PAGE_H = 16838;
const MG = Number(process.env.MG || 1134);              // 2.0 cm
const M = { top: MG, right: MG, bottom: MG, left: MG };
const CW = PAGE_W - M.left - M.right;
const F = "David", SZ = Number(process.env.SZ || 24);
const LN = Number(process.env.LN || 360);               // 1.5
const LINE = { line: LN, lineRule: LineRuleType.AUTO };
const AFTER = Number(process.env.AF || 110);

const nb = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: nb, bottom: nb, left: nb, right: nb };

const r = (text, o = {}) => new TextRun({
  text, font: F, size: o.size || SZ, rightToLeft: true,
  bold: !!o.bold, underline: o.underline ? { type: UnderlineType.SINGLE } : undefined,
});

const clause = (children) => new Paragraph({
  bidirectional: true, alignment: AlignmentType.BOTH,
  spacing: { ...LINE, after: AFTER },
  numbering: { reference: "cl", level: 0 },
  children: Array.isArray(children) ? children : [r(children)],
});

const cap = (kids, o = {}) => new Paragraph({
  bidirectional: true, alignment: o.a || AlignmentType.START,
  spacing: { line: 250, lineRule: LineRuleType.AUTO, after: o.after ?? 0 },
  indent: o.ind,
  tabStops: o.ind ? [{ type: TabStopType.LEFT, position: 1400 }] : undefined,
  children: Array.isArray(kids) ? kids : [r(kids, o)],
});

const doc = new Document({
  numbering: { config: [{ reference: "cl", levels: [{
    level: 0, format: LevelFormat.DECIMAL, text: "%1.",
    alignment: AlignmentType.START, suffix: "tab",
    style: { paragraph: { indent: { left: 420, hanging: 420 } } },
  }]}]},
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: PAGE_H }, margin: M }, bidi: true },
    footers: { default: new Footer({ children: [new Paragraph({
      bidirectional: true, alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: F, size: 20, rightToLeft: true })],
    })] }) },
    children: [
      cap("בבית המשפט לענייני משפחה בראשון לציון", { bold: true }),
      cap('תמ"ש 49199/09/2023', { a: AlignmentType.END, bold: true }),
      cap("בפני כב' השופט/ת: אליהו", { a: AlignmentType.END, after: 200 }),

      cap([r("המבקש:", { bold: true }), r("\tבילילין באביי, ת.ז. 328811385", { bold: true })], { ind: { left: 1400, hanging: 1400 } }),
      cap([r('ע"י ב"כ עו"ד סולומון טקה, פינסקר 214, נתניה')], { ind: { left: 1400 } }),

      new Paragraph({ bidirectional: true, alignment: AlignmentType.CENTER,
        spacing: { before: 110, after: 110 }, children: [r("- נ ג ד -", { bold: true })] }),

      cap([r("המשיב:", { bold: true }), r("\tהמוסד לביטוח לאומי", { bold: true })], { ind: { left: 1400, hanging: 1400 } }),
      cap([r('ע"י ב"כ עו"ד רועי הררי ואח\', ניסנבאום 37, בת ים')], { ind: { left: 1400 } }),

      new Paragraph({ bidirectional: true, alignment: AlignmentType.CENTER,
        spacing: { before: 300, after: 240 },
        children: [r("תגובת המבקש לתשובת המשיב מיום 20.8.26", { bold: true, size: 28, underline: true })] }),

      new Paragraph({ bidirectional: true, alignment: AlignmentType.BOTH,
        spacing: { ...LINE, after: 150 },
        children: [r('בית המשפט הנכבד מתבקש לדחות את טענותיו המקדמיות של המשיב שבתשובתו מיום 20.8.26 (להלן: "התשובה") ולהכריע בבקשה המתוקנת לגופה. ככל שנדרשת רשות להגשת תגובה זו — מתבקש בית המשפט הנכבד ליתן אותה.')] }),

      clause([ r("השיהוי ועיתויו. ", { bold: true }),
        r('ההחלטה מיום 22.7.26 קצבה למשיב חמישה ימים להשיב, וכך אף הבין (סעיף 3 לתשובה). ההמצאה בוצעה ביום 23.7.26, והתשובה הוגשה ביום 20.8.26 — באיחור שהמשיב מודה בו (סעיף 1). לאורך כל אותה תקופה הוסיפו ההליכים בהוצאה לפועל להתנהל נגד המבקש, והמשיב שתק. השינוי היחיד שקדם להגשה הוא החלטה מס\' 11 מיום 18.8.26, שמכוחה נעצרו ההליכים בפועל. התשובה הוגשה יומיים לאחר מכן.') ]),

      clause([ r("טענת אי-ההמצאה אינה נוגעת למסמך שבמחלוקת. ", { bold: true }),
        r('סעיפים 4–6 לתשובה עוסקים בשלושה מסמכים משלבים שהסתיימו: הבקשה שנדחתה בהוצאה לפועל ביום 14.7.26, הבקשה שנדחתה כאן ביום 21.7.26, וההחלטה במזונות זמניים. המסמך היחיד העומד להכרעה הוא הבקשה המתוקנת, שהוגשה מכוח ההחלטה מיום 22.7.26. '),
        r("בשום מקום בתשובה אין המשיב טוען כי הבקשה המתוקנת לא הומצאה לו", { bold: true }),
        r(' — ולא בכדי: היא הומצאה לו בדואר אלקטרוני ובאמצעות אתר המשיב ביום 23.7.26, ובמסירה אישית ביום 4.8.26. מסמכי ההמצאה כבר הוגשו לבית המשפט הנכבד ומצויים בתיק.') ]),

      clause([ r("המסירה קודמת למועד שהמשיב עצמו נוקב בו. ", { bold: true }),
        r('המסירה מיום 4.8.26 קודמת בחמישה ימים ליום 9.8.26, שאותו מציין המשיב כמועד שבו הועברה אליו ההחלטה (סעיף 1). חישוב "18 הימים" שבפתח התשובה נשען, אפוא, על הנחה שמסמכי ההמצאה סותרים. אשר לשתי ההחלטות שתוכנן אינו ידוע לו לטענתו — המשיב הוא הזוכה בתיק ההוצאה לפועל ובעל דין כאן, ושתיהן מצויות בתיקים הפתוחים לעיונו.') ]),

      clause([ r("התשובה סותרת את עצמה. ", { bold: true }),
        r('סעיף 9 טוען כי הבקשה שהוגשה כאן "זהה" לזו שנדחתה בהוצאה לפועל, בעוד סעיפים 4–5 טוענים פעמיים כי "לא ידוע למשיב מה נאמר בבקשה". לא ניתן לטעון לזהות בין מסמכים שהטוען מצהיר כי לא ראה. או שהם בידיו — ואז קורסים סעיפים 4–6; או שאינם בידיו — ואז קורס סעיף 9.') ]),

      clause('סעיף 7 מצהיר כי "לא ניתן כלל להגיב לגופו של עניין", ומיד לאחריו מגיבים סעיפים 8–9 לגופו של עניין — העדר עילה ומסלול דיוני חלופי. בעל דין הטוען כי נבצר ממנו להגיב, ומיד מגיב, מלמד כי המניעה הנטענת אינה קיימת.'),

      clause('סעיף 11 מבקש, לחלופין, כי יורו למבקש למסור את המסמכים שבסעיפים 4–6 וכי יינתן למשיב זמן להשיב. בכך מודה המשיב כי הפגם הנטען ניתן לריפוי במסירת מסמכים. פגם שהטוען לו מציע בעצמו את דרך ריפויו אינו מצדיק דחייה על הסף.'),

      clause([ r("טענת הערעור מתעלמת מהחלטה שיפוטית קיימת. ", { bold: true }),
        r("שאלת המסלול הדיוני הוכרעה ביום 22.7.26, עת הורה בית המשפט הנכבד למבקש להגיש בקשה מתוקנת המכוונת אל המשיב. הבקשה הוגשה מכוח אותה החלטה. בקשת המשיב להפנות כיום את המבקש למסלול אחר משמעה כי בית המשפט הנכבד יתבקש להתעלם מהחלטתו שלו.") ]),

      clause([ r("ולגופה — ", { bold: true }),
        r("אין הבקשה תוקפת את שיקול דעתה של כב' הרשמת. יסודה בעובדה חדשה: ביום 12.5.26 בוטל פסק הדין שעליו נסמך תיק ההוצאה לפועל, ומשבוטל — ניטל מן התיק בסיסו המשפטי. אין זו שאלה ערעורית על ההנמקה, אלא שאלה של עצם קיום בסיס להליך.") ]),

      clause([ r("הסעד החלופי אינו בר-ביצוע לפי חישובו של המשיב. ", { bold: true }),
        r('לפי סעיף 9, תקופת הערעור עמדה לפוג "מחרתיים" מיום ההגשה. המשיב שתק לאורך כל אותה תקופה והעלה את הטענה בשוליה — במועד שבו פעולה על פיה כבר אינה אפשרית. בעל דין אינו רשאי להחריש בעוד המועד רץ ולהיבנות לאחר מכן מחלופו. תוצאתו המעשית היחידה של הסעד המבוקש היא דחיית ההכרעה, בעוד תיק ההוצאה לפועל עומד על כנו.') ]),

      clause('התנהלות זו אינה מתיישבת עם חובת ההגינות הדיונית שבתקנה 3(ב) לתקנות סדר הדין האזרחי, התשע"ט-2018, ובאה בגדר תקנה 4, האוסרת פעולה בהליך שמטרתה או תוצאתה להשהותו. תקנה 42 מסמיכה את בית המשפט למחוק כתב טענות, כולו או מקצתו, מטעם זה בלבד.'),

      clause([ r("אשר על כן", { bold: true }),
        r(", מתבקש בית המשפט הנכבד: (א) לדחות את הטענות המקדמיות שבתשובה ולהורות על מחיקתה, כולה או מקצתה, לפי תקנה 42; (ב) לדחות את הבקשה החלופית שבסעיף 11 לתשובה; (ג) להכריע בבקשה המתוקנת לגופה; (ד) להורות כי עיכוב ההליכים לפי החלטה מס' 11 יעמוד בעינו עד להכרעה; (ה) לחייב את המשיב בהוצאות המבקש, לפי תקנה 151(ג).") ]),

      clause("אין באמור בתגובה זו כדי לגרוע מטענות המבקש, וכולן שמורות לו."),

      new Paragraph({ spacing: { after: 220 }, children: [] }),
      new Paragraph({ bidirectional: true, alignment: AlignmentType.CENTER,
        spacing: { line: 250, lineRule: LineRuleType.AUTO }, children: [r("_______________________")] }),
      new Paragraph({ bidirectional: true, alignment: AlignmentType.CENTER,
        spacing: { line: 250, lineRule: LineRuleType.AUTO }, children: [r('סולומון טקה, עו"ד')] }),
      new Paragraph({ bidirectional: true, alignment: AlignmentType.CENTER,
        spacing: { line: 250, lineRule: LineRuleType.AUTO, after: 260 }, children: [r('ב"כ המבקש')] }),
      new Paragraph({ bidirectional: true, alignment: AlignmentType.START,
        spacing: { line: 250, lineRule: LineRuleType.AUTO }, children: [r("תאריך: ____________")] }),
    ],
  }],
});

Packer.toBuffer(doc).then(b => { fs.writeFileSync(process.argv[2], b); console.log("OK", b.length); });
