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
        para([run("עומר עלמו (בתלושי השכר: \"אלמטה עומר\"), ת\"ז 329502223", { bold: true })], { align: AlignmentType.START, after: 0 }),
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
          para([run("בנצרת", { bold: true, size: 26 })], { align: AlignmentType.START, after: 0 })], CW / 2),
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
      para([run("מהות התביעה: ", { bold: true }), run("פיצויי פיטורים, דמי הודעה מוקדמת, הפרשות לפנסיה, פדיון חופשה ופיצוי בגין פיטורים שלא כדין.")], { after: 40 }),
      para([run("סכום התביעה: ", { bold: true }), run("27,901 ₪.")], { after: 40 }),
      para([run("אגרה: ", { bold: true }), run("בהתאם לתקנות בית הדין לעבודה (אגרות), התשס\"ח-2008, לפי התוספת.")], { after: 40 }),

      para([run("כתב תביעה", { bold: true, size: 30, underline: true })], { align: AlignmentType.CENTER, before: 120, after: 160 }),

      para([run("א. הצדדים ותקופת העבודה", { bold: true, underline: true })], { align: AlignmentType.START, after: 60 }),
      clause(["התובע הועסק אצל הנתבעת, חברה העוסקת בהפקת אירועים, כעובד שעתי ברציפות מיום ", { t: "01.05.2022", bold: true }, " ועד לחודש ", { t: "אוגוסט 2024", bold: true }, ", תקופה של שנתיים וארבעה חודשים, עת הופסקה עבודתו על ידי הנתבעת. תלושי השכר לתקופת העבודה מצורפים כנספח א'."]),
      clause(["שכרו של התובע שולם לפי תעריף שעתי (30 ₪ ובהמשך 32.33 ₪ לשעה) בתוספת תשלום קבוע בגין כל משמרת אירוע (250-300 ₪ למשמרת). שכרו הממוצע של התובע בשנים-עשר חודשי העבודה האחרונים, בנטרול דמי הבראה, עמד על סך ", { t: "3,500 ₪", bold: true }, " לחודש (להלן: \"השכר הקובע\")."]),
      clause(["בחודשים האחרונים להעסקתו צמצמה הנתבעת באופן חד-צדדי את היקף המשמרות שהוקצו לתובע, עד כדי משמרת אחת או שתיים בחודש, ובחודש אוגוסט 2024 הופסקה העסקתו כליל. הפסקת העבודה נעשתה כלאחר יד, בלא הודעה מוקדמת בכתב, בלא שימוע ובלא שניתנה לתובע כל הזדמנות להשמיע את טענותיו."]),
      clause(["עם סיום העבודה לא ערכה הנתבעת לתובע גמר חשבון, ולא שולם לו דבר בגין זכויותיו הסוציאליות. פניות התובע לנתבעת בדרישה לקבל את זכויותיו לא נענו."]),

      para([run("ב. הפרת זכויות התובע", { bold: true, underline: true })], { align: AlignmentType.START, before: 60, after: 60 }),
      clause([{ t: "אי-הפרשה לפנסיה: ", bold: true }, "מתלושי השכר עולה כי לאורך כל תקופת העבודה לא הפרישה הנתבעת ולו שקל אחד לביטוח פנסיוני עבור התובע. בכל התלושים מופיע ברכיב \"קופ\"ג מעסיק\" וברכיב \"פיצויים מעסיק\" הסכום 0.00. זאת בניגוד לצו ההרחבה לביטוח פנסיוני מקיף במשק, המחייב מעסיק להפריש לקופת גמל לקצבה בשיעור 6.5% משכר העובד, לכל המאוחר מתום ששת חודשי העבודה הראשונים."]),
      clause([{ t: "אי-תשלום פיצויי פיטורים: ", bold: true }, "התובע הועסק למעלה משנה ופוטר על ידי הנתבעת, ועל כן זכאי הוא לפיצויי פיטורים מכוח סעיף 1 לחוק פיצויי פיטורים, התשכ\"ג-1963. משלא בוצעה כל הפרשה לרכיב הפיצויים, חב המעסיק במלוא הפיצויים."]),
      clause([{ t: "אי-מתן הודעה מוקדמת: ", bold: true }, "הנתבעת לא נתנה לתובע הודעה מוקדמת לפיטורים כנדרש בחוק הודעה מוקדמת לפיטורים ולהתפטרות, התשס\"א-2001. התובע, עובד בשכר בעל ותק העולה על שנתיים, זכאי להודעה מוקדמת של חודש ימים."]),
      clause([{ t: "אי-פדיון חופשה: ", bold: true }, "על פי תלוש השכר האחרון (8/2024) שהנפיקה הנתבעת עצמה, עמדה לזכות התובע יתרת חופשה צבורה ובלתי מנוצלת של ", { t: "15.26 ימים", bold: true }, ", אשר לא נפדתה עם סיום העבודה, בניגוד לסעיף 13 לחוק חופשה שנתית, התשי\"א-1951."]),
      clause([{ t: "פיטורים שלא כדין: ", bold: true }, "הפסקת העבודה נעשתה ללא שימוע וללא הודעה, תוך הפרת חובת תום הלב וכללי הצדק הטבעי החלים על מעסיק, ומזכה את התובע בפיצוי כספי."]),

      para([run("ג. הסעדים", { bold: true, underline: true })], { align: AlignmentType.START, before: 60, after: 60 }),
      clause([{ t: "פיצויי פיטורים: ", bold: true }, "3,500 ₪ × 28/12 חודשי עבודה = ", { t: "8,167 ₪", bold: true }, "."]),
      clause([{ t: "דמי הודעה מוקדמת: ", bold: true }, "חודש שכר קובע = ", { t: "3,500 ₪", bold: true }, "."]),
      clause([{ t: "הפרשות לפנסיה (חלק מעסיק): ", bold: true }, "6.5% מהשכר ששולם מחודש 11/2022 ועד 8/2024, בסך 74,818 ₪, ובסה\"כ ", { t: "4,863 ₪", bold: true }, ". התובע שומר על זכותו לתבוע הפרשות ממועד תחילת העבודה, ככל שיתברר כי היה מבוטח בביטוח פנסיוני קודם."]),
      clause([{ t: "פדיון חופשה: ", bold: true }, "15.26 ימים × 286.44 ₪, תעריף יום לפי התלוש, ובסה\"כ ", { t: "4,371 ₪", bold: true }, "."]),
      clause([{ t: "פיצוי בגין פיטורים ללא שימוע: ", bold: true }, "בשיעור שתי משכורות = ", { t: "7,000 ₪", bold: true }, "."]),
      clause(["סך הכל על הנתבעת לשלם לתובע ", { t: "27,901 ₪", bold: true }, ", בצירוף הפרשי הצמדה וריבית כחוק ממועד סיום העבודה ועד התשלום בפועל. לחלופין, ובכפוף לשיקול דעת בית הדין הנכבד, בצירוף פיצויי הלנת פיצויי פיטורים לפי סעיף 20 לחוק הגנת השכר, התשי\"ח-1958."]),
      clause(["לבית דין נכבד זה הסמכות העניינית לדון בתביעה מכוח סעיף 24(א)(1) לחוק בית הדין לעבודה, התשכ\"ט-1969, והסמכות המקומית נתונה לו בהיות מקום מושבה של הנתבעת בעפולה."]),
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
