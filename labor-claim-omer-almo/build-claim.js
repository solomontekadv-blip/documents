const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        AlignmentType, LevelFormat, BorderStyle, WidthType, LineRuleType, UnderlineType } = require('docx');

const PAGE_WIDTH = 11906;
const M = { top: 1134, right: 1247, bottom: 1020, left: 1247 };
const CW = PAGE_WIDTH - M.left - M.right;
const FONT = "David";
const SZ = 23;
const nb = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: nb, bottom: nb, left: nb, right: nb };

const run = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || SZ, rightToLeft: true, bold: o.bold, underline: o.underline ? { type: UnderlineType.SINGLE } : undefined });
const para = (children, o = {}) => new Paragraph({
  bidirectional: true, alignment: o.align || AlignmentType.BOTH,
  spacing: { line: o.line || 276, lineRule: LineRuleType.AUTO, before: o.before || 0, after: o.after == null ? 80 : o.after },
  ...(o.numbered ? { numbering: { reference: "legal-clauses", level: 0 } } : {}),
  ...(o.indent ? { indent: o.indent } : {}),
  children: Array.isArray(children) ? children : [run(children, o)]
});
const clause = (parts) => para(parts.map(p => typeof p === 'string' ? run(p) : run(p.t, p)), { numbered: true, after: 100 });
const cell = (paras, width) => new TableCell({ borders: noBorders, width: { size: width, type: WidthType.DXA }, margins: { top: 40, bottom: 40, left: 60, right: 60 }, children: paras });

const partiesTable = new Table({
  visuallyRightToLeft: true, width: { size: CW, type: WidthType.DXA }, columnWidths: [1500, CW - 1500],
  rows: [
    new TableRow({ children: [
      cell([para([run("התובע:", { bold: true })], { align: AlignmentType.START, after: 0 })], 1500),
      cell([
        para([run("עומר אלמו (בתלושי השכר: \"אלמטה עומר\"), ת\"ז 329502223", { bold: true })], { align: AlignmentType.START, after: 0 }),
        para("מרחוב האגמון 8, חדרה 3836822", { align: AlignmentType.START, after: 0 }),
        para("ע\"י ב\"כ עו\"ד סולומון טקה, רישיון מס' 4545", { align: AlignmentType.START, after: 0 }),
        para("מרחוב פינסקר 21, נתניה; טל': 052-3700918", { align: AlignmentType.START, after: 0 }),
      ], CW - 1500),
    ]}),
    new TableRow({ children: [
      cell([para("", { after: 0 })], 1500),
      cell([para([run("- נגד -", { bold: true })], { align: AlignmentType.START, before: 80, after: 80 })], CW - 1500),
    ]}),
    new TableRow({ children: [
      cell([para([run("הנתבעת:", { bold: true })], { align: AlignmentType.START, after: 0 })], 1500),
      cell([
        para([run("ד.ע משי ארועים בעמק בע\"מ, ח.פ. 516510633", { bold: true })], { align: AlignmentType.START, after: 0 }),
        para("מאזור תעשייה עמק חפר, עפולה", { align: AlignmentType.START, after: 0 }),
      ], CW - 1500),
    ]}),
  ]
});

const headTable = new Table({
  visuallyRightToLeft: true, width: { size: CW, type: WidthType.DXA }, columnWidths: [CW / 2, CW / 2],
  rows: [new TableRow({ children: [
    cell([para([run("בבית הדין האזורי לעבודה", { bold: true, size: 26 })], { align: AlignmentType.START, after: 0 }),
          para([run("בחיפה", { bold: true, size: 26 })], { align: AlignmentType.START, after: 0 })], CW / 2),
    cell([para([run("ס\"ע ________________", { bold: true })], { align: AlignmentType.END, after: 0 }),
          para("תאריך: 09.09.2026", { align: AlignmentType.END, after: 0 })], CW / 2),
  ]})]
});

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: SZ, rightToLeft: true } } } },
  numbering: { config: [{ reference: "legal-clauses", levels: [{
    level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.START, suffix: "tab",
    style: { paragraph: { indent: { left: 567, hanging: 567 } }, run: { font: FONT, size: SZ, bold: true } }
  }]}]},
  sections: [{
    properties: { page: { size: { width: PAGE_WIDTH, height: 16838 }, margin: M }, bidi: true },
    children: [
      headTable,
      para("", { after: 60 }),
      partiesTable,
      para("", { after: 40 }),
      para([run("מהות התביעה: ", { bold: true }), run("פיצויי פיטורים, גמול שעות נוספות, פדיון חופשה, דמי חגים ופיצוי לדוגמה (עובד קטין).")], { after: 40 }),
      para([run("סכום התביעה: ", { bold: true }), run("52,226 ₪.")], { after: 40 }),
      para([run("אגרה: ", { bold: true }), run("בהתאם לתקנות בית הדין לעבודה (אגרות), התשס\"ח-2008, לפי התוספת.")], { after: 40 }),

      para([run("כתב תביעה", { bold: true, size: 30, underline: true })], { align: AlignmentType.CENTER, before: 120, after: 160 }),

      para([run("א. הצדדים ותקופת העבודה", { bold: true, underline: true })], { align: AlignmentType.START, after: 60 }),
      clause(["התובע, יליד ", { t: "16.5.2006", bold: true }, ", הועסק על ידי הנתבעת, חברה להפקת אירועים, כמלצר באירועים, ברציפות מיום ", { t: "01.05.2022", bold: true }, " ועד ליום ", { t: "28.9.2024", bold: true }, ", שנתיים וחמישה חודשים. במרבית תקופת העבודה היה התובע קטין, והעסקתו כפופה להוראות חוק עבודת הנוער, התשי\"ג-1953. תלושי השכר מצורפים כנספח א'."]),
      clause(["שכרו של התובע שולם לפי תעריף שעתי (30 ₪, ומשנת 2024 32.33 ₪) בתוספת תשלום קבוע למשמרת אירוע (250-300 ₪). שכרו הממוצע בשנים-עשר חודשי העבודה האחרונים, בנטרול דמי הבראה, עמד על ", { t: "3,500 ₪", bold: true }, " לחודש (להלן: \"השכר הקובע\")."]),
      clause(["העסקת התובע הסתיימה ביום 28.9.2024 עקב גיוסו לשירות סדיר בצה\"ל. התפטרות עקב גיוס דינה כפיטורים לעניין פיצויי פיטורים, מכוח סעיף 11(ג) לחוק פיצויי פיטורים, התשכ\"ג-1963. הנתבעת לא ערכה לתובע גמר חשבון ולא שילמה לו דבר בגין זכויותיו."]),
      clause(["פניות התובע לנתבעת נענו בהתעלמות מוחלטת. ביום ", { t: "13.7.2026", bold: true }, " שלח ב\"כ התובע לנתבעת מכתב התראה בדואר רשום (נספח ב'). הנתבעת לא השיבה ולא שילמה. תלושי השכר הופקו על ידי הנתבעת לראשונה ביום 3.8.2026, כעולה מהמצוין בגוף התלושים עצמם."]),

      para([run("ב. הפרת זכויות התובע", { bold: true, underline: true })], { align: AlignmentType.START, before: 60, after: 60 }),
      clause([{ t: "שעות נוספות: ", bold: true }, "מרישומי הנתבעת עצמה בתלושים עולה כי התובע הועסק דרך קבע במשמרות שחרגו משמונה שעות, ובחלק מהחודשים (5-6/2023, 12/2023, 1/2024) במשמרות של 12-13 שעות בממוצע. בפועל הועסק התובע דרך קבע במשמרות אירועים בנות 11-13 שעות, ורישומי הנתבעת משקפים רק חלק מהן. סעיף 20 לחוק עבודת הנוער אוסר להעסיק נער מעבר לשמונה שעות ביום, וסעיף 16 לחוק שעות עבודה ומנוחה, התשי\"א-1951, מחייב גמול של 125% ו-150%. הנתבעת לא ניהלה פנקס שעות כדין, ומכוח סעיף 26ב לחוק הגנת השכר, התשי\"ח-1958, נטל ההוכחה בעניין היקף השעות מוטל עליה."]),
      clause([{ t: "פיצויי פיטורים: ", bold: true }, "לא שולמו כלל, אף שהתובע הועסק למעלה משנתיים וסיום עבודתו מזכה בפיצויים מכוח החוק."]),
      clause([{ t: "חופשה: ", bold: true }, "נער זכאי ל-18 ימי חופשה בשנה (סעיף 27 לחוק עבודת הנוער). תלוש השכר האחרון, לחודש 8/2024, מודה ביתרה של 15.26 ימים בלתי מנוצלים, ואף יתרה זו לא נפדתה, בניגוד לסעיף 13 לחוק חופשה שנתית, התשי\"א-1951."]),
      clause([{ t: "דמי חגים: ", bold: true }, "כעובד שעתי בעל ותק העולה על שלושה חודשים זכאי היה התובע לתשלום בגין תשעה ימי חג בשנה מכוח צו ההרחבה הכללי במשק (הסכם המסגרת משנת 2000). לא שולם דבר."]),
      clause([{ t: "הודעה על תנאי עבודה ותלושי שכר: ", bold: true }, "לא נמסרה לתובע הודעה על תנאי עבודתו, בניגוד לחוק הודעה לעובד ולמועמד לעבודה, התשס\"ב-2002, ותלושי השכר לא נמסרו לו במועדם בניגוד לסעיף 24 לחוק הגנת השכר. כל אחת מההפרות מקימה זכות לפיצוי לדוגמה ללא הוכחת נזק."]),

      para([run("ג. הסעדים", { bold: true, underline: true })], { align: AlignmentType.START, before: 60, after: 60 }),
      clause([{ t: "פיצויי פיטורים: ", bold: true }, "3,500 ₪ × 29/12 חודשי עבודה = ", { t: "8,458 ₪", bold: true }, "."]),
      clause([{ t: "גמול שעות נוספות: ", bold: true }, "281 משמרות לפי התלושים × 3 שעות נוספות למשמרת (משמרת ממוצעת של 11 שעות): שתי שעות ב-125% ושעה ב-150%, 120 ₪ למשמרת לפי 30 ₪ לשעה, = 33,720 ₪, בניכוי 8,545 ₪ ששולמו כשכר יסוד שעתי, ובסה\"כ ", { t: "25,175 ₪", bold: true }, ". החישוב נופל מחזקת 15 השעות הנוספות השבועיות שבסעיף 26ב לחוק הגנת השכר. לחלופין, ולכל הפחות, לפי רישומי הנתבעת עצמה בתלושים: 475 שעות נוספות, ובסה\"כ 11,049 ₪."]),
      clause([{ t: "פדיון חופשה: ", bold: true }, "21 ימים (18 ימים לשנה, באופן יחסי לימי העבודה בפועל) × 286.44 ₪, תעריף יום לפי התלוש, ובסה\"כ ", { t: "6,015 ₪", bold: true }, "."]),
      clause([{ t: "דמי חגים: ", bold: true }, "9 ימים × 286.44 ₪ = ", { t: "2,578 ₪", bold: true }, "."]),
      clause([{ t: "פיצוי לדוגמה: ", bold: true }, "5,000 ₪ בגין אי-מסירת הודעה על תנאי עבודה ו-5,000 ₪ בגין אי-מסירת תלושי שכר, ובסה\"כ ", { t: "10,000 ₪", bold: true }, "."]),
      clause(["סך הכל על הנתבעת לשלם לתובע ", { t: "52,226 ₪", bold: true }, ", בצירוף הפרשי הצמדה וריבית כחוק ממועד סיום העבודה ועד התשלום בפועל. לחלופין, ובכפוף לשיקול דעת בית הדין הנכבד, בצירוף פיצויי הלנת שכר והלנת פיצויי פיטורים לפי חוק הגנת השכר."]),
      clause(["לבית דין נכבד זה הסמכות העניינית לדון בתביעה מכוח סעיף 24(א)(1) לחוק בית הדין לעבודה, התשכ\"ט-1969, והסמכות המקומית נתונה לו בהיות מקום ביצוע העבודה באזור שיפוטו."]),
      clause(["התובע שומר על זכותו לתקן את כתב התביעה ולהוסיף עליו עם קבלת מלוא המסמכים מהנתבעת, ואין באמור לעיל כדי לגרוע מכל זכות העומדת לו על פי כל דין, הסכם, נוהג או צו הרחבה."]),
      clause(["אשר על כן מתבקש בית הדין הנכבד להזמין את הנתבעת לדין, לחייבה בתשלום הסכומים המפורטים לעיל, וכן לחייבה בהוצאות המשפט ובשכר טרחת עו\"ד בתוספת מע\"מ כדין."]),

      para("", { after: 200 }),
      para([run("_________________", {})], { align: AlignmentType.END, after: 0 }),
      para([run("סולומון טקה, עו\"ד", { bold: true })], { align: AlignmentType.END, after: 0, indent: { left: 0, right: 0 } }),
      para("ב\"כ התובע", { align: AlignmentType.END, after: 0 }),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => { fs.writeFileSync("כתב_תביעה_עומר_עלמו.docx", buf); console.log("ok"); });
