const fs = require('fs');
const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        AlignmentType, LevelFormat, BorderStyle, WidthType, LineRuleType,
        Footer, PageNumber, UnderlineType, PageBreak } = require('docx');

const PAGE_WIDTH = 11906;
const M = 1417;
const CW = PAGE_WIDTH - 2 * M; // 9072
const FONT = "David";
const nb = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: nb, bottom: nb, left: nb, right: nb };
const CASE = "ה\"ט 59722-08-26";
const PREV_CASE = "ה\"ט 9910-03-26";

const run = (text, o = {}) => new TextRun({ text, font: FONT, size: o.size || 24, rightToLeft: true, bold: o.bold, italics: o.italics,
  underline: o.underline ? { type: UnderlineType.SINGLE } : undefined });
const P = (children, o = {}) => new Paragraph({
  bidirectional: true,
  alignment: o.align || AlignmentType.BOTH,
  spacing: { line: 360, lineRule: LineRuleType.AUTO, before: o.before ?? 0, after: o.after ?? 120 },
  ...(o.numbering ? { numbering: { reference: "clauses", level: 0 } } : {}),
  ...(o.indent ? { indent: o.indent } : {}),
  children: Array.isArray(children) ? children : [run(children, o)],
});
const clause = (parts) => P(parts.map(p => typeof p === 'string' ? run(p) : run(p.t, p)), { numbering: true });

const cell = (children, width, align, extra = {}) => new TableCell({
  borders: noBorders, width: { size: width, type: WidthType.DXA },
  margins: { top: 40, bottom: 40, left: 80, right: 80 }, ...extra,
  children: children.map(c => new Paragraph({ bidirectional: true, alignment: align, spacing: { line: 300, lineRule: LineRuleType.AUTO, after: 0 }, children: c })),
});

const header = new Table({
  visuallyRightToLeft: true,
  width: { size: CW, type: WidthType.DXA },
  columnWidths: [CW / 2, CW / 2],
  rows: [new TableRow({ children: [
    cell([[run("בבית המשפט לענייני משפחה ב______________", { bold: true, size: 26 })]], CW / 2, AlignmentType.START),
    cell([[run(CASE, { bold: true, size: 26 })]], CW / 2, AlignmentType.END),
  ]})],
});

const partyRow = (label, lines) => new TableRow({ children: [
  cell([[run(label, { bold: true })]], 1700, AlignmentType.START),
  cell(lines.map(l => [run(l)]), CW - 1700, AlignmentType.START),
]});
const parties = new Table({
  visuallyRightToLeft: true,
  width: { size: CW, type: WidthType.DXA },
  columnWidths: [1700, CW - 1700],
  rows: [
    partyRow("המבקשת:", [
      "______________, ת.ז. ______________",
      "ע\"י ב\"כ עו\"ד סולומון טקה, מ.ר. ______________",
      "מרחוב ______________ ; טל' ______________ ; פקס ______________",
      "דוא\"ל: solomontekadv@gmail.com",
    ]),
    new TableRow({ children: [ cell([[run("- נ ג ד -", { bold: true })]], CW, AlignmentType.CENTER, { columnSpan: 2 }) ] }),
    partyRow("המשיב:", [
      "הבטמו אייסו, ת.ז. ______________",
      "מרחוב ______________",
      "(אינו מיוצג בהליך זה)",
    ]),
  ],
});

const centered = (text, o = {}) => new Paragraph({ bidirectional: true, alignment: AlignmentType.CENTER,
  spacing: { before: o.before ?? 0, after: o.after ?? 80 }, children: [run(text, o)] });

const title = centered("הודעת עדכון מטעם המבקשת", { bold: true, size: 30, underline: true, before: 360 });
const subtitle = centered("ובקשה דחופה למתן החלטה בהסכמה בבקשה להארכת תוקף צו הגנה הדדי", { bold: true, size: 24, after: 60 });
const urgency = centered("(תוקף הצו פוקע ביום 15.09.2026)", { bold: true, size: 24, after: 300 });

const intro = P([
  run("בית המשפט הנכבד מתבקש ליתן, בדחיפות ובטרם פקיעת הצו ביום 15.09.2026, את המבוקש בבקשה להארכת תוקף צו ההגנה ההדדי (להלן: "),
  run("\"הבקשה\"", { bold: true }),
  run("), וזאת בהסכמת המשיב, כמפורט להלן:"),
]);

const quote = new Paragraph({
  bidirectional: true, alignment: AlignmentType.BOTH,
  indent: { left: 850, right: 850 },
  spacing: { line: 300, lineRule: LineRuleType.AUTO, before: 60, after: 200 },
  children: [run("\"בהסתמך על הסכמה קודמת על פיה הוארך תוקפו של צו הגנה הדדי עד ליום 15.09.26, אין התנגדות של הבטמו אייסו להאריכו בשלושה חודשים נוספים, באותה מתכונת קודמת ותוך המשך קיום הסדרי ראייה עם שלושת הקטינים במרכז קשר \"פלא\" בטירת הכרמל\".", { italics: true })],
});

const body = [
  clause(["הבקשה הומצאה ביום 20.08.2026 לעו\"ד ______________, אשר ייצגה את המשיב בהליך הקודם בין הצדדים (" + PREV_CASE + ") ומסרה בשמו את ההסכמה להארכה הקודמת של הצו עד ליום 15.09.2026."]),
  clause(["משהבקשה נפתחה בתיק חדש שבו עו\"ד ______________ אינה רשומה כמייצגת, לא היה באפשרותה להגיש את תגובת המשיב באמצעות מערכת נט המשפט. זו הסיבה היחידה להיעדר תגובה כתובה בתיק."]),
  clause(["ביום ______________ מסרה עו\"ד ______________ לח\"מ, בכתב, את הסכמת המשיב לבקשה, בזו הלשון:"]),
];
const body2 = [
  clause(["העתק ההודעה מצורף ומסומן ", { t: "נספח א'", bold: true }, ". אין אפוא מחלוקת בין הצדדים, והבקשה בשלה למתן החלטה."]),
  clause(["אשר על כן, מתבקש בית המשפט הנכבד להורות, בהסכמת הצדדים, על הארכת תוקף צו ההגנה ההדדי בשלושה חודשים נוספים, מיום 15.09.2026 ועד ליום 15.12.2026, באותה מתכונת שבה עמד בתוקפו עד כה, תוך המשך קיום הסדרי הראייה עם הקטינים במרכז הקשר \"פלא\" בטירת הכרמל; וכן להורות על המצאת ההחלטה למשיב עצמו, שאינו מיוצג בהליך זה."]),
  clause(["העתק מהודעה זו נשלח במקביל לעו\"ד ______________, לשם העברתו למשיב."]),
];

const signature = [
  new Paragraph({ bidirectional: true, alignment: AlignmentType.START, spacing: { before: 400, after: 0 }, children: [run("תאריך: ______________")] }),
  new Paragraph({ bidirectional: true, alignment: AlignmentType.END, spacing: { before: 400, after: 0 }, children: [run("_______________________")] }),
  new Paragraph({ bidirectional: true, alignment: AlignmentType.END, spacing: { after: 0 }, children: [run("סולומון טקה, עו\"ד", { bold: true })] }),
  new Paragraph({ bidirectional: true, alignment: AlignmentType.END, spacing: { after: 0 }, children: [run("ב\"כ המבקשת")] }),
];

const annex = [
  new Paragraph({ children: [new PageBreak()] }),
  centered("נספח א'", { bold: true, size: 32, before: 2000, after: 200 }),
  centered("הודעת ב\"כ המשיב בדבר הסכמת המשיב להארכת תוקף צו ההגנה ההדדי", { bold: true, size: 26, after: 120 }),
  centered("(עו\"ד ______________, מיום ______________)", { size: 24, after: 600 }),
  P("שלום עו\"ד טקה", { align: AlignmentType.START, after: 120 }),
  P("בהסתמך על הסכמה קודמת על פיה הוארך תוקפו של צו הגנה הדדי עד ליום 15.09.26, אין התנגדות של הבטמו אייסו להאריכו בשלושה חודשים נוספים, באותה מתכונת קודמת ותוך המשך קיום הסדרי ראייה עם שלושת הקטינים במרכז קשר \"פלא\" בטירת הכרמל\".", { after: 400 }),
  P("[במקום עמוד זה, או בנוסף לו, יש לצרף צילום מסך של ההודעה המקורית כפי שהתקבלה]", { align: AlignmentType.CENTER, italics: true, size: 20 }),
];

const doc = new Document({
  creator: "עו\"ד סולומון טקה",
  title: "הודעת עדכון מטעם המבקשת ובקשה דחופה למתן החלטה - " + CASE,
  styles: { default: { document: { run: { font: FONT, size: 24, rightToLeft: true } } } },
  numbering: { config: [{
    reference: "clauses",
    levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.START, suffix: "tab",
               style: { paragraph: { indent: { left: 567, hanging: 567 } } } }],
  }] },
  sections: [{
    properties: { page: { size: { width: PAGE_WIDTH, height: 16838 }, margin: { top: M, right: M, bottom: M, left: M } }, bidi: true },
    footers: { default: new Footer({ children: [new Paragraph({ bidirectional: true, alignment: AlignmentType.CENTER,
      children: [new TextRun({ children: [PageNumber.CURRENT], font: FONT, size: 20, rightToLeft: true })] })] }) },
    children: [header, new Paragraph({ spacing: { after: 200 }, children: [] }), parties, title, subtitle, urgency, intro,
               ...body, quote, ...body2, ...signature, ...annex],
  }],
});

Packer.toBuffer(doc).then(buf => {
  // docx-js omits <w:bidi/> from sectPr; inject it so the section itself is RTL.
  fs.writeFileSync("raw.docx", buf);
  console.log("written", buf.length);
});
