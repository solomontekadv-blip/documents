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
const clause = (parts) => para(parts.map(p => typeof p === 'string' ? run(p) : run(p.t, p)), { numbered: true, after: 70 });
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

      clause(["התובע, יליד 16.5.2006, הועסק על ידי הנתבעת, חברה להפקת אירועים, כמלצר באירועים, ברציפות מיום ", { t: "01.05.2022", bold: true }, " ועד ליום ", { t: "28.9.2024", bold: true }, ", שנתיים וחמישה חודשים. תלושי השכר מצורפים כנספח א'."]),
      clause(["במרבית תקופת העבודה היה התובע קטין, והעסקתו כפופה להוראות חוק עבודת הנוער, התשי\"ג-1953."]),
      clause(["שכרו של התובע שולם לפי תעריף שעתי (30 ₪, ומשנת 2024 32.33 ₪) בתוספת תשלום קבוע למשמרת אירוע (250-300 ₪)."]),
      clause(["שכרו הממוצע של התובע בשנים-עשר חודשי העבודה האחרונים, בנטרול דמי הבראה, עמד על ", { t: "3,500 ₪", bold: true }, " לחודש (להלן: \"השכר הקובע\")."]),
      clause(["העסקת התובע הסתיימה ביום 28.9.2024 עקב גיוסו לשירות סדיר בצה\"ל. התפטרות עקב גיוס דינה כפיטורים לעניין פיצויי פיטורים, מכוח סעיף 11(ג) לחוק פיצויי פיטורים, התשכ\"ג-1963."]),
      clause(["הנתבעת לא ערכה לתובע גמר חשבון ולא שילמה לו דבר בגין זכויותיו. פניות התובע אליה נענו בהתעלמות מוחלטת."]),
      clause(["ביום 13.7.2026 שלח ב\"כ התובע לנתבעת מכתב התראה בדואר רשום (נספח ב'). הנתבעת לא השיבה ולא שילמה. תלושי השכר הופקו לראשונה ביום 3.8.2026, כעולה מגוף התלושים עצמם."]),
      clause(["מרישומי הנתבעת עצמה עולה כי התובע הועסק דרך קבע במשמרות שחרגו משמונה שעות, ובחלק מהחודשים (5-6/2023, 12/2023, 1/2024) במשמרות של 12-13 שעות בממוצע. בפועל הועסק התובע במשמרות בנות 11-13 שעות."]),
      clause(["סעיף 20 לחוק עבודת הנוער אוסר להעסיק נער מעבר לשמונה שעות ביום, וסעיף 16 לחוק שעות עבודה ומנוחה, התשי\"א-1951, מחייב גמול של 125% ו-150%. הנתבעת לא שילמה גמול כלשהו."]),
      clause(["הנתבעת לא ניהלה פנקס שעות כדין, ומכוח סעיף 26ב לחוק הגנת השכר, התשי\"ח-1958, נטל ההוכחה בעניין היקף השעות מוטל עליה."]),
      clause(["פיצויי פיטורים לא שולמו לתובע כלל, אף שהועסק למעלה משנתיים וסיום עבודתו מזכה בפיצויים מכוח החוק."]),
      clause(["נער זכאי ל-18 ימי חופשה בשנה (סעיף 27 לחוק עבודת הנוער). תלוש השכר האחרון, לחודש 8/2024, מודה ביתרה של 15.26 ימים בלתי מנוצלים, ואף היא לא נפדתה, בניגוד לסעיף 13 לחוק חופשה שנתית, התשי\"א-1951."]),
      clause(["כעובד שעתי בעל ותק העולה על שלושה חודשים זכאי היה התובע לתשעה ימי חג בשנה מכוח צו ההרחבה הכללי במשק (הסכם המסגרת משנת 2000). לא שולם דבר."]),
      clause(["לא נמסרה לתובע הודעה על תנאי עבודתו, בניגוד לחוק הודעה לעובד ולמועמד לעבודה, התשס\"ב-2002, ותלושי השכר לא נמסרו לו במועדם, בניגוד לסעיף 24 לחוק הגנת השכר. כל אחת מההפרות מקימה זכות לפיצוי לדוגמה ללא הוכחת נזק."]),
      clause(["התובע זכאי לפיצויי פיטורים בסך ", { t: "8,458 ₪", bold: true }, ", לפי 3,500 ₪ × 29/12 חודשי עבודה."]),
      clause(["התובע זכאי לגמול שעות נוספות בסך ", { t: "25,175 ₪", bold: true }, ": 281 משמרות × 3 שעות נוספות למשמרת (שתיים ב-125% ואחת ב-150%, 120 ₪ למשמרת לפי 30 ₪ לשעה) = 33,720 ₪, בניכוי 8,545 ₪ ששולמו כשכר יסוד שעתי."]),
      clause(["החישוב נופל מחזקת 15 השעות הנוספות השבועיות שבסעיף 26ב לחוק הגנת השכר. לחלופין, ולכל הפחות, לפי רישומי הנתבעת עצמה: 475 שעות נוספות, ובסה\"כ 11,049 ₪."]),
      clause(["התובע זכאי לפדיון חופשה בסך ", { t: "6,015 ₪", bold: true }, ", לפי 21 ימים (18 ימים לשנה, באופן יחסי לימי העבודה בפועל) × 286.44 ₪, תעריף יום לפי התלוש."]),
      clause(["התובע זכאי לדמי חגים בסך ", { t: "2,578 ₪", bold: true }, ", לפי 9 ימים × 286.44 ₪."]),
      clause(["התובע זכאי לפיצוי לדוגמה בסך ", { t: "10,000 ₪", bold: true }, ": 5,000 ₪ בגין אי-מסירת הודעה על תנאי עבודה ו-5,000 ₪ בגין אי-מסירת תלושי שכר."]),
      clause([{ t: "סיכום. ", bold: true }, "על הנתבעת לשלם לתובע את הסך ", { t: "52,226 ₪", bold: true }, " בצירוף פיצויי הלנת שכר ופיצויי הלנת פיצויי פיטורים. לחלופין, בצירוף הפרשי הצמדה וריבית מקסימלית כחוק."]),
      clause(["לבית דין נכבד זה הסמכות העניינית מכוח סעיף 24(א)(1) לחוק בית הדין לעבודה, התשכ\"ט-1969, והסמכות המקומית בהיות מקום ביצוע העבודה באזור שיפוטו."]),
      clause(["אין באמור לעיל כדי למצות או לגרוע מכל טענה או זכות העומדת לתובע על פי כל דין, הסכם, נוהג או צו הרחבה, והתובע שומר על זכותו לתקן את כתב התביעה עם קבלת מלוא המסמכים מהנתבעת."]),
      clause(["כמו כן, על הנתבעת לשאת בהוצאות המשפט ובשכר טרחת עו\"ד בתוספת מע\"מ כדין."]),

      para("", { after: 200 }),
      para([run("_________________", {})], { align: AlignmentType.END, after: 0 }),
      para([run("סולומון טקה, עו\"ד", { bold: true })], { align: AlignmentType.END, after: 0, indent: { left: 0, right: 0 } }),
      para("ב\"כ התובע", { align: AlignmentType.END, after: 0 }),
    ]
  }]
});

Packer.toBuffer(doc).then(buf => { fs.writeFileSync("כתב_תביעה_עומר_עלמו.docx", buf); console.log("ok"); });
