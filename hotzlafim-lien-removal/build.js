const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, BorderStyle, WidthType, LineRuleType, UnderlineType,
} = require('docx');
const fs = require('fs');

const PAGE_W = 11906, PAGE_H = 16838;
const M = { top: 1134, right: 1134, bottom: 1134, left: 1134 };
const CW = PAGE_W - M.left - M.right; // 9638
const F = "David";
const nb = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: nb, bottom: nb, left: nb, right: nb };
const LINE = 300; // 1.25 - מרווח מהודק לשמירה על עמוד וחצי

const run = (text, o = {}) => new TextRun({
  text, font: F, size: o.size || 23, rightToLeft: true,
  bold: !!o.bold, italics: !!o.italics,
  ...(o.underline ? { underline: { type: UnderlineType.SINGLE } } : {}),
});

const P = (text, o = {}) => new Paragraph({
  bidirectional: true,
  alignment: o.align || AlignmentType.BOTH,
  spacing: { line: LINE, lineRule: LineRuleType.AUTO, before: o.before || 0, after: o.after === undefined ? 80 : o.after },
  ...(o.indent ? { indent: o.indent } : {}),
  children: Array.isArray(text) ? text : [run(text, o)],
});

const C = (children, o = {}) => new Paragraph({
  bidirectional: true,
  alignment: AlignmentType.BOTH,
  numbering: { reference: "clauses", level: 0 },
  spacing: { line: LINE, lineRule: LineRuleType.AUTO, before: 40, after: o.after === undefined ? 100 : o.after },
  children: Array.isArray(children) ? children : [run(children, o)],
});

const H = (text) => new Paragraph({
  bidirectional: true,
  alignment: AlignmentType.START,
  spacing: { before: 160, after: 70, line: LINE, lineRule: LineRuleType.AUTO },
  children: [run(text, { bold: true, underline: true })],
});

const cell = (children, width, align) => new TableCell({
  borders: noBorders,
  width: { size: width, type: WidthType.DXA },
  margins: { top: 20, bottom: 20, left: 60, right: 60 },
  children: children.map(c => new Paragraph({
    bidirectional: true, alignment: align || AlignmentType.START,
    spacing: { after: 20, line: 260, lineRule: LineRuleType.AUTO },
    children: [c],
  })),
});

const twoCol = (r, l) => new Table({
  visuallyRightToLeft: true,
  width: { size: CW, type: WidthType.DXA },
  columnWidths: [CW / 2, CW / 2],
  rows: [new TableRow({ children: [cell(r, CW / 2, AlignmentType.START), cell(l, CW / 2, AlignmentType.END)] })],
});

const rule = () => new Paragraph({
  bidirectional: true, spacing: { before: 20, after: 100 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "000000", space: 1 } },
  children: [run("")],
});

const children = [];

children.push(twoCol(
  [run("לשכת ההוצאה לפועל - מסלול מזונות, מחוז מרכז", { bold: true, size: 24 }),
   run("דרך השרון 12, כפר סבא 4427125", { size: 20 })],
  [run("תיק הוצל\"פ מס' 542780-03-25", { bold: true, size: 24 }),
   run("בפני כב' הרשמת מרים סגל", { bold: true, size: 22 })]
));
children.push(rule());

children.push(P([run("בעניין: ", { bold: true }), run("מזונות ביטוח לאומי")], { align: AlignmentType.START, after: 50 }));
children.push(P([run("הזוכה: ", { bold: true }), run("המוסד לביטוח לאומי")], { align: AlignmentType.START, after: 50 }));
children.push(P([run("החייב: ", { bold: true }), run("באביי בילילין, ת.ז. 328811385, ע\"י ב\"כ עו\"ד [שם], מ.ר. [___], מרח' [כתובת] | טל' [___] | דוא\"ל [___]")], { align: AlignmentType.START, after: 180 }));

children.push(new Paragraph({
  bidirectional: true, alignment: AlignmentType.CENTER,
  spacing: { before: 100, after: 60, line: LINE, lineRule: LineRuleType.AUTO },
  children: [run("בקשה דחופה למתן הוראות ולהסרת עיקול לאלתר", { bold: true, size: 28, underline: true })],
}));
children.push(new Paragraph({
  bidirectional: true, alignment: AlignmentType.CENTER,
  spacing: { after: 160, line: 280, lineRule: LineRuleType.AUTO },
  children: [run("(עיקול על חשבון הבנק של החייב שנותר על כנו חרף החלטת כב' הרשמת מיום 19.8.2026 בדבר עיכוב ההליכים)", { size: 22 })],
}));

children.push(P([
  run("כב' הרשמת מתבקשת להורות בדחיפות, ובמעמד צד אחד, על "),
  run("הסרת העיקול הרשום על חשבון הבנק של החייב לאלתר", { bold: true }),
  run(", ועל משלוח הודעת ביטול לבנק המחזיק; וכן ליתן הוראות בשאלה "),
  run("מדוע לא בוצעה עד כה החלטת כב' הרשמת מיום 19.8.2026", { bold: true }),
  run(", אף שחלפו למעלה משבועיים ממועד נתינתה."),
], { after: 120 }));

children.push(H("א. העובדות"));

children.push(C([
  run("בתיק שבנדון ננקטו כנגד החייב הליכי אכיפה, ובהם עיקול על חשבון הבנק שלו בבנק "),
  run("[שם הבנק]", { bold: true }), run(", סניף "), run("[___]", { bold: true }),
  run(", חשבון מס' "), run("[___]", { bold: true }), run(" (להלן: \"החשבון\")."),
]));

children.push(C([
  run("ביום 18.8.2026 ניתנה החלטת בית המשפט הנכבד ["), run("ערכאה ומספר הליך"),
  run("], ובעקבותיה הוגשה בקשה מס' 41 (סוג 61 - עיכוב הליך/הליכים). ביום "),
  run("19.8.2026", { bold: true }),
  run(" נעתרה כב' הרשמת לבקשה וקבעה, מפורשות וללא סייג: "),
  run("\"בהתאם להחלטת בית משפט הנכבד מיום 18.8.2026 אני מורה על עיכוב ההליכים בתיק עד למתן החלטה אחרת\"", { bold: true, italics: true }),
  run(" (מצ\"ב "), run("נספח א'", { bold: true }), run(")."),
]));

children.push(C([
  run("חרף האמור, ונכון למועד הגשת בקשה זו - למעלה משבועיים לאחר מתן ההחלטה - "),
  run("העיקול על החשבון טרם הוסר, והוא רשום ופעיל", { bold: true }),
  run(". פנייה לבנק המחזיק העלתה כי לא התקבלה בו כל הודעת ביטול מטעם הלשכה הנכבדה (מצ\"ב "),
  run("נספח ב'", { bold: true }),
  run("), ופניות מקדימות שנעשו ללשכה לא הניבו מענה ענייני."),
]));

children.push(H("ב. הטעמים המשפטיים"));

children.push(C([
  run("החלטת עיכוב ההליכים היא החלטה שיפוטית מחייבת, שנוסחה באופן גורף וללא הבחנה בין סוגי הליכים, ומשמעותה הקפאה מלאה של פעולות האכיפה בתיק. "),
  run("עיקול על חשבון בנק אינו אירוע חד-פעמי הנעצר במועד הטלתו, אלא הליך נמשך ומתחדש מדי יום ביומו", { bold: true }),
  run(" - שכן מדי יום מוסיף הבנק לתפוס את הכספים הנכנסים לחשבון ולהגבילו. משכך, הותרת העיקול על כנו לאחר החלטת העיכוב אינה \"מחדל טכני\" גרידא, אלא המשך נקיטתו בפועל של הליך שעוכב בהחלטה שיפוטית תקפה."),
]));

children.push(C([
  run("פרשנות מצמצמת, שלפיה עיכוב ההליכים חל אך על נקיטת הליכים חדשים ואינו מבטל הליכים קיימים, מרוקנת את ההחלטה מתוכנה ומותירה את החייב במצב זהה למצבו ערב נתינתה. זאת ועוד: כוחו של העיקול לתפוס נכסים בידי צד שלישי יונק מהליכי האכיפה התלויים ועומדים בתיק (סעיף 44 לחוק ההוצאה לפועל, התשכ\"ז-1967); משעוכבו הליכים אלה, נשמט הבסיס להמשך תפיסת הכספים."),
]));

children.push(C([
  run("הנזק יומיומי ומתמשך: כל עוד עומד העיקול בעינו, החייב מנוע מלמשוך את שכרו, מלעמוד בתשלומי מגורים וחשבונות ומלרכוש מזון ותרופות - ובה בעת נמנעת ממנו היכולת לגייס משאבים להסדרת חובו, באופן הפוגע אף באינטרס הזוכה."),
], { after: 140 }));

children.push(H("ג. הסעדים המבוקשים"));

[["א.", "להורות על הסרת העיקול על החשבון לאלתר, ועל משלוח הודעת ביטול לבנק המחזיק באופן מיידי."],
 ["ב.", "להורות למזכירות הלשכה למסור דיווח, בתוך פרק זמן קצר שייקבע, מדוע לא בוצעה החלטת כב' הרשמת מיום 19.8.2026."],
 ["ג.", "להורות על ביטול כלל הליכי האכיפה התלויים ועומדים בתיק, כל עוד עומדת בעינה החלטת עיכוב ההליכים."],
 ["ד.", "להורות על השבת כל סכום שנגבה, נתפס או הועבר מן החשבון החל מיום 19.8.2026 ואילך."],
 ["ה.", "לדון בבקשה בדחיפות ובמעמד צד אחד, לנוכח הנזק המתמשך הנגרם לחייב מדי יום."],
].forEach(([n, t]) => children.push(new Paragraph({
  bidirectional: true, alignment: AlignmentType.BOTH,
  spacing: { after: 80, line: LINE, lineRule: LineRuleType.AUTO },
  indent: { right: 400, hanging: 400 },
  children: [run(n + "\t"), run(t)],
})));

children.push(P("אין באמור כדי לגרוע מכל טענה וזכות של החייב, כולן שמורות לו.", { before: 100, after: 200 }));

children.push(twoCol(
  [run("תאריך: [__].[__].2026")],
  [run("_________________________"), run("[שם עו\"ד], עו\"ד - ב\"כ החייב")]
));

children.push(P([
  run("נספחים: ", { bold: true }),
  run("א' - החלטת כב' הרשמת מיום 19.8.2026 (בקשה מס' 41); ב' - אישור הבנק / פלט מצב החשבון; ג' - החלטת בית המשפט מיום 18.8.2026.", { size: 21 }),
], { before: 140, after: 0 }));

const doc = new Document({
  numbering: {
    config: [{
      reference: "clauses",
      levels: [{
        level: 0, format: LevelFormat.DECIMAL, text: "%1.",
        alignment: AlignmentType.START, suffix: "tab",
        style: { paragraph: { indent: { left: 400, hanging: 400 } } },
      }],
    }],
  },
  sections: [{
    properties: { page: { size: { width: PAGE_W, height: PAGE_H }, margin: M }, bidi: true },
    children,
  }],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync('/home/user/documents/hotzlafim-lien-removal/01_בקשה_דחופה_הסרת_עיקול.docx', b);
  console.log('OK');
});
