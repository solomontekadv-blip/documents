const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        AlignmentType, LevelFormat, BorderStyle, WidthType, LineRuleType, UnderlineType } = require('docx');
const PAGE_WIDTH = 11906; const M = { top: 900, right: 1247, bottom: 800, left: 1247 };
const CW = PAGE_WIDTH - M.left - M.right; const FONT = "David"; const SZ = 23;
const nb = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" }; const noBorders = { top: nb, bottom: nb, left: nb, right: nb };
const run = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || SZ, rightToLeft: true, bold: o.bold, underline: o.underline ? { type: UnderlineType.SINGLE } : undefined });
const para = (children, o = {}) => new Paragraph({ bidirectional: true, alignment: o.align || AlignmentType.BOTH,
  spacing: { line: 276, lineRule: LineRuleType.AUTO, before: o.before || 0, after: o.after == null ? 80 : o.after },
  ...(o.numbered ? { numbering: { reference: "cl", level: 0 } } : {}),
  children: Array.isArray(children) ? children : [run(children, o)] });
const clause = (parts) => para(parts.map(p => typeof p === 'string' ? run(p) : run(p.t, p)), { numbered: true, after: 50 });
const cell = (paras, width) => new TableCell({ borders: noBorders, width: { size: width, type: WidthType.DXA }, margins: { top: 40, bottom: 40, left: 60, right: 60 }, children: paras });

const sig = new Table({ visuallyRightToLeft: true, width: { size: CW, type: WidthType.DXA }, columnWidths: [CW/2, CW/2],
  rows: [new TableRow({ children: [
    cell([para("_____________________", { align: AlignmentType.CENTER, after: 0 }), para([run("סולומון טקה, עו\"ד", { bold: true })], { align: AlignmentType.CENTER, after: 0 })], CW/2),
    cell([para("_____________________", { align: AlignmentType.CENTER, after: 0 }), para([run("עומר אלמו, הלקוח", { bold: true })], { align: AlignmentType.CENTER, after: 0 })], CW/2),
  ]})]});

const doc = new Document({
  styles: { default: { document: { run: { font: FONT, size: SZ, rightToLeft: true } } } },
  numbering: { config: [{ reference: "cl", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.START, suffix: "tab",
    style: { paragraph: { indent: { left: 567, hanging: 567 } }, run: { font: FONT, size: SZ, bold: true } } }]}]},
  sections: [{ properties: { page: { size: { width: PAGE_WIDTH, height: 16838 }, margin: M }, bidi: true }, children: [
    para([run("הסכם שכר טרחה", { bold: true, size: 32, underline: true })], { align: AlignmentType.CENTER, after: 60 }),
    para("שנערך ונחתם בנתניה ביום ____________", { align: AlignmentType.CENTER, after: 200 }),
    para([run("בין: ", { bold: true }), run("עו\"ד סולומון טקה, רישיון מס' 4545, מרחוב פינסקר 21, נתניה, טל' 052-3700918 (להלן: \"עורך הדין\")")], { after: 60 }),
    para([run("לבין: ", { bold: true }), run("עומר אלמו, ת\"ז 329502223, מרחוב האגמון 8, חדרה (להלן: \"הלקוח\")")], { after: 200 }),

    clause(["הלקוח מבקש מעורך הדין לייצג אותו בתביעה נגד מעסיקתו לשעבר, ד.ע משי ארועים בעמק בע\"מ, ח.פ. 516510633, בבית הדין האזורי לעבודה, בגין זכויותיו מתקופת עבודתו בחודשים 5/2022 עד 9/2024 (להלן: \"התיק\")."]),
    clause(["הטיפול בתיק כולל: הכנת כתב התביעה והגשתו, ניהול ההליך בבית הדין האזורי לעבודה על כל שלביו, ניהול משא ומתן לפשרה מול המעסיקה, וגביית הכסף שייפסק או שיוסכם. ערעור, אם יהיה, אינו כלול, ויסוכם בנפרד."]),
    clause(["הלקוח לא משלם שכר טרחה מראש. שכר הטרחה ישולם רק בסוף ההליך, ורק מתוך כסף שיתקבל בפועל מהמעסיקה."]),
    clause(["שכר הטרחה הוא ", { t: "20% בתוספת מע\"מ", bold: true }, " מכל סכום שיתקבל מהמעסיקה בקשר לתיק, בין בפסק דין ובין בפשרה, ובין אם יתקבל דרך עורך הדין ובין אם ישירות אצל הלקוח. לדוגמה: אם יתקבלו 50,000 ₪, שכר הטרחה יהיה 10,000 ₪ בתוספת מע\"מ."]),
    clause(["אם התיק יסתיים בלי שיתקבל כסף מהמעסיקה, הלקוח לא ישלם שכר טרחה כלל."]),
    clause(["הוצאות ושכר טרחת עורך דין שייפסקו על ידי בית הדין לחובת המעסיקה, אם ייפסקו, שייכים לעורך הדין, בנוסף לשכר הטרחה שבסעיף 4. הם לא ייכללו בסכום שממנו מחושבים ה-20%."]),
    clause(["הכסף שיתקבל מהמעסיקה יועבר לחשבון הנאמנות של עורך הדין. עורך הדין ינכה ממנו את שכר הטרחה ואת ההוצאות המגיעות לו לפי הסכם זה, יעביר ללקוח את היתרה בתוך 14 ימים, וימסור לו חשבונית וקבלה ופירוט בכתב של החישוב."]),
    clause(["אם הכסף יתקבל ישירות אצל הלקוח, הלקוח ישלם לעורך הדין את שכר הטרחה בתוך 7 ימים מיום קבלתו."]),
    clause(["הוצאות ההליך, כגון אגרת בית הדין (כ-1% מסכום התביעה), מסירות, שליחויות והזמנת עדים, חלות על הלקוח. עורך הדין רשאי לשלם אותן מראש במקום הלקוח, ולנכות אותן מהכסף שיתקבל, לפני חישוב שכר הטרחה."]),
    clause(["הלקוח מבין שעורך הדין אינו מבטיח תוצאה, לא לגבי הזכייה בתיק ולא לגבי הסכום שייפסק, וכי ההחלטה נתונה לבית הדין."]),
    clause(["כל הצעת פשרה שתתקבל מהמעסיקה תובא ללקוח, וההחלטה אם לקבל אותה היא של הלקוח בלבד, לאחר שיקבל מעורך הדין את הסברו והמלצתו."]),
    clause(["הלקוח מתחייב למסור לעורך הדין מידע נכון ומלא, להעביר כל מסמך או הודעה שיגיעו אליו בקשר לתיק, להתייצב לדיונים ולעדות כשיידרש, ולהודיע מראש על תקופות שבהן לא יהיה זמין בשל שירותו הצבאי."]),
    clause(["הלקוח מתחייב לא לפנות למעסיקה ולא לסכם איתה דבר בקשר לתיק בלי ידיעת עורך הדין. סכום שיתקבל בדרך זו ייחשב כסכום שהתקבל בקשר לתיק, ושכר הטרחה יחול עליו."]),
    clause(["הלקוח רשאי להפסיק את הייצוג בכל עת בהודעה בכתב. במקרה כזה, אם בהמשך יתקבל כסף מהמעסיקה בקשר לתיק, ישלם הלקוח לעורך הדין את שכר הטרחה לפי סעיף 4, לפי חלקה של העבודה שבוצעה עד להפסקת הייצוג. עורך הדין ימסור ללקוח את כל מסמכי התיק."]),
    clause(["עורך הדין רשאי להפסיק את הייצוג בהודעה בכתב מראש, אם הלקוח לא ישתף פעולה, אם יתברר שהמידע שנמסר לו אינו נכון, או מכל טעם המותר לפי כללי לשכת עורכי הדין, ובלבד שלא ייגרם ללקוח נזק דיוני."]),
    clause(["עורך הדין ישמור בסוד כל מידע שיימסר לו על ידי הלקוח, ויעדכן את הלקוח על כל התפתחות מהותית בתיק."]),
    clause(["הלקוח מאשר כי קרא הסכם זה, כי הוסבר לו תוכנו בשפה המובנת לו, וכי ניתנה לו הזדמנות לשאול שאלות לפני החתימה."]),
    para("", { after: 120 }),
    para([run("ולראיה באו הצדדים על החתום:", { bold: true })], { align: AlignmentType.CENTER, after: 200 }),
    sig,
  ]}]
});
Packer.toBuffer(doc).then(b => { fs.writeFileSync("הסכם_שכר_טרחה_עומר_אלמו.docx", b); console.log("ok"); });
