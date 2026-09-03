const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, LevelFormat, BorderStyle, WidthType, LineRuleType, UnderlineType,
} = require('docx');
const fs = require('fs');

const PAGE_W = 11906, PAGE_H = 16838;
const M = { top: 1417, right: 1417, bottom: 1417, left: 1417 };
const CW = PAGE_W - M.left - M.right; // 9072
const F = "David";
const nb = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: nb, bottom: nb, left: nb, right: nb };

const run = (text, o = {}) => new TextRun({
  text, font: F, size: o.size || 24, rightToLeft: true,
  bold: !!o.bold, italics: !!o.italics,
  ...(o.underline ? { underline: { type: UnderlineType.SINGLE } } : {}),
});

// פסקה רגילה
const P = (text, o = {}) => new Paragraph({
  bidirectional: true,
  alignment: o.align || AlignmentType.BOTH,
  spacing: { line: 360, lineRule: LineRuleType.AUTO, before: o.before || 0, after: o.after === undefined ? 120 : o.after },
  ...(o.indent ? { indent: o.indent } : {}),
  children: Array.isArray(text) ? text : [run(text, o)],
});

// סעיף ממוספר אוטומטית
const C = (children, o = {}) => new Paragraph({
  bidirectional: true,
  alignment: AlignmentType.BOTH,
  numbering: { reference: "clauses", level: 0 },
  spacing: { line: 360, lineRule: LineRuleType.AUTO, before: o.before || 60, after: o.after === undefined ? 120 : o.after },
  children: Array.isArray(children) ? children : [run(children, o)],
});

// כותרת ביניים
const H = (text) => new Paragraph({
  bidirectional: true,
  alignment: AlignmentType.START,
  spacing: { before: 300, after: 140, line: 360, lineRule: LineRuleType.AUTO },
  children: [run(text, { bold: true, underline: true })],
});

const cell = (children, width, align) => new TableCell({
  borders: noBorders,
  width: { size: width, type: WidthType.DXA },
  margins: { top: 40, bottom: 40, left: 60, right: 60 },
  children: children.map(c => new Paragraph({
    bidirectional: true,
    alignment: align || AlignmentType.START,
    spacing: { after: 40, line: 300, lineRule: LineRuleType.AUTO },
    children: [c],
  })),
});

const twoCol = (rightRuns, leftRuns) => new Table({
  visuallyRightToLeft: true,
  width: { size: CW, type: WidthType.DXA },
  columnWidths: [CW / 2, CW / 2],
  rows: [new TableRow({
    children: [cell(rightRuns, CW / 2, AlignmentType.START), cell(leftRuns, CW / 2, AlignmentType.END)],
  })],
});

const rule = () => new Paragraph({
  bidirectional: true,
  spacing: { before: 60, after: 160 },
  border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "000000", space: 1 } },
  children: [run("")],
});

// ---- תוכן ----
const children = [];

children.push(twoCol(
  [run("לשכת ההוצאה לפועל", { bold: true, size: 26 }),
   run("מסלול מזונות - מחוז מרכז", { bold: true, size: 26 }),
   run("דרך השרון 12, כפר סבא 4427125", { size: 22 })],
  [run("תיק הוצל\"פ מס' 542780-03-25", { bold: true, size: 26 }),
   run("בפני כב' הרשמת מרים סגל", { bold: true, size: 24 })]
));
children.push(rule());

children.push(P([run("בעניין:", { bold: true, underline: true }), run("   מזונות ביטוח לאומי")], { align: AlignmentType.START, after: 160 }));

children.push(P([run("הזוכה:", { bold: true }), run("   המוסד לביטוח לאומי")], { align: AlignmentType.START, after: 60 }));
children.push(P([run("החייב:", { bold: true }), run("   באביי בילילין, ת.ז. 328811385")], { align: AlignmentType.START, after: 40 }));
children.push(P("ע\"י ב\"כ עו\"ד [שם מלא], מ.ר. [___]", { align: AlignmentType.START, after: 40, indent: { right: 700 } }));
children.push(P("מרח' [כתובת המשרד] | טל': [___] | פקס: [___] | דוא\"ל: [___]", { align: AlignmentType.START, after: 240, indent: { right: 700 } }));

children.push(new Paragraph({
  bidirectional: true, alignment: AlignmentType.CENTER,
  spacing: { before: 240, after: 100, line: 360, lineRule: LineRuleType.AUTO },
  children: [run("בקשה דחופה למתן הוראות ולהסרת עיקול לאלתר", { bold: true, size: 30, underline: true })],
}));
children.push(new Paragraph({
  bidirectional: true, alignment: AlignmentType.CENTER,
  spacing: { after: 300, line: 340, lineRule: LineRuleType.AUTO },
  children: [run("(עיקול על חשבון הבנק של החייב שנותר על כנו חרף החלטת כב' הרשמת מיום 19.8.2026 בדבר עיכוב ההליכים בתיק)", { size: 24 })],
}));

children.push(P([
  run("כב' הרשמת מתבקשת בזאת, בדחיפות ובמעמד צד אחד, להורות על "),
  run("הסרה מיידית של העיקול הרשום על חשבון הבנק של החייב", { bold: true }),
  run(", ועל משלוח הודעת ביטול לבנק המחזיק לאלתר; וכן ליתן הוראות בשאלה "),
  run("מדוע לא בוצעה עד כה החלטת כב' הרשמת מיום 19.8.2026", { bold: true }),
  run(", המורה על עיכוב ההליכים בתיק שבנדון עד למתן החלטה אחרת - וזאת אף שחלפו למעלה משבועיים ממועד נתינתה."),
], { after: 200 }));

children.push(H("א. השתלשלות העניינים"));

children.push(C("התיק שבנדון הוא תיק הוצאה לפועל במסלול מזונות ביטוח לאומי, המתנהל בלשכת מחוז מרכז, אשר בגדרו ננקטו כנגד החייב הליכי אכיפה שונים."));

children.push(C([
  run("בין הליכי האכיפה שננקטו נמנה עיקול על חשבון הבנק של החייב, המתנהל בבנק "),
  run("[שם הבנק]", { bold: true }), run(", סניף "), run("[מס' הסניף]", { bold: true }),
  run(", חשבון מס' "), run("[מס' החשבון]", { bold: true }),
  run(" (להלן: "), run("\"החשבון\"", { bold: true }), run(")."),
]));

children.push(C([
  run("ביום "), run("18.8.2026", { bold: true }),
  run(" ניתנה החלטת בית המשפט הנכבד ["), run("ציון הערכאה ומספר ההליך"),
  run("], אשר בעקבותיה הוגשה בו ביום בקשה מטעם החייב בתיק ההוצאה לפועל - בקשה מס' 41, מסוג 61 (עיכוב הליך/הליכים)."),
]));

children.push(C([
  run("ביום "), run("19.8.2026", { bold: true }),
  run(" נעתרה כב' הרשמת מרים סגל לבקשה, וקבעה בהחלטתה, מפורשות וללא כל סייג, כדלקמן:"),
]));

children.push(new Paragraph({
  bidirectional: true, alignment: AlignmentType.BOTH,
  spacing: { before: 120, after: 160, line: 320, lineRule: LineRuleType.AUTO },
  indent: { right: 900, left: 500 },
  border: { right: { style: BorderStyle.SINGLE, size: 12, color: "666666", space: 12 } },
  children: [run("\"בהתאם להחלטת בית משפט הנכבד מיום 18.8.2026 אני מורה על עיכוב ההליכים בתיק עד למתן החלטה אחרת.\"", { italics: true })],
}));

children.push(C([
  run("העתק החלטת כב' הרשמת מיום 19.8.2026 מצורף לבקשה זו ומסומן "),
  run("נספח א'", { bold: true }), run("."),
]));

children.push(H("ב. חרף ההחלטה - העיקול על החשבון עומד בעינו"));

children.push(C([
  run("על אף האמור, ונכון למועד הגשת בקשה זו - "), run("[__].[__].2026", { bold: true }),
  run(", היינו למעלה משבועיים לאחר מתן ההחלטה - העיקול על החשבון "),
  run("טרם הוסר, והוא רשום ופעיל", { bold: true }), run("."),
]));

children.push(C([
  run("החייב פנה לבנק המחזיק ביום "), run("[__].[__].2026", { bold: true }),
  run(", ונמסר לו כי לא התקבלה בבנק כל הודעה בדבר ביטול העיקול מטעם לשכת ההוצאה לפועל, וכי החשבון מוגבל כמימים ימימה. אישור הבנק / פלט מצב החשבון מצורף ומסומן "),
  run("נספח ב'", { bold: true }), run("."),
]));

children.push(C([
  run("פניות מקדימות שנעשו ללשכה הנכבדה ["), run("בטלפון / באמצעות האזור האישי / בפנייה בכתב מיום [__].[__].2026"),
  run("] לא הניבו מענה ענייני, ולא הועברה לחייב כל הודעה בדבר הטעם שבשלו לא בוצעה ההחלטה."),
]));

children.push(H("ג. הטעמים המשפטיים לבקשה"));

children.push(C([
  run("החלטה על עיכוב הליכים היא החלטה שיפוטית מחייבת, החלה על "),
  run("כלל ההליכים בתיק", { bold: true }),
  run(". החלטת כב' הרשמת נוסחה באופן גורף, ללא הסתייגות וללא הבחנה בין סוגי הליכים, ומשמעותה הקפאה מלאה של פעולות האכיפה בתיק."),
]));

children.push(C([
  run("עיקול על חשבון בנק אינו אירוע חד-פעמי הנעצר במועד הטלתו, אלא "),
  run("הליך נמשך ומתחדש מדי יום ביומו", { bold: true }),
  run(" כל עוד לא בוטל: מדי יום מוסיף הבנק לתפוס את הכספים הנכנסים לחשבון ולהגבילו. משכך, הותרתו של העיקול על כנו לאחר החלטת העיכוב אינה בגדר \"מחדל טכני\" גרידא, אלא המשך נקיטתו בפועל של הליך אשר עוכב בהחלטה שיפוטית."),
]));

children.push(C("פרשנות מצמצמת, שלפיה עיכוב ההליכים חל אך על נקיטת הליכים חדשים ואינו מבטל הליכים קיימים, מרוקנת את ההחלטה מתוכנה ומותירה את החייב במצב זהה לחלוטין למצבו ערב נתינתה - תוצאה שאין הדעת סובלתה, ואשר בוודאי לא לה כיוונו בית המשפט הנכבד וכב' הרשמת."));

children.push(C([
  run("יתרה מזאת, כוחו של העיקול לתפוס נכסים בידי צד שלישי יונק מהליכי האכיפה התלויים ועומדים בתיק (סעיף 44 לחוק ההוצאה לפועל, התשכ\"ז-1967). משעוכבו הליכים אלה, נשמט הבסיס להמשך תפיסת הכספים, והמשך החזקתם המוגבלת בידי הבנק נעשה בהיעדר הרשאה."),
]));

children.push(C([
  run("למעלה מן הצורך יצוין, כי מדובר בחשבון שאליו מועברים "),
  run("[משכורתו של החייב / קצבאות המשולמות לו]"),
  run(", ובגדרו כספים שחלקם אינו בר-עיקול על פי דין. גם מטעם זה נדרשת בחינה מחודשת ומיידית של העיקול."),
]));

children.push(H("ד. הנזק המתמשך הנגרם לחייב"));

children.push(C("כל עוד עומד העיקול בעינו, החייב מנוע מלמשוך את שכרו, מלעמוד בתשלומי שכר דירה, חשבונות חשמל ומים, ומלרכוש מזון ותרופות עבורו ועבור בני משפחתו. מדובר בפגיעה קשה ויומיומית בזכות הקניין ובכבוד האדם, אשר מתעצמת והולכת מדי יום שחולף."));

children.push(C("למעלה מכך, ומן הבחינה המעשית: דווקא הותרת החשבון מעוקל היא שמונעת מן החייב לגייס את המשאבים הדרושים להסדרת חובו ולעמידה בחיוביו העתידיים - ובכך פוגעת אף באינטרס הזוכה עצמו."));

children.push(C("כל יום נוסף שבו נותר העיקול על כנו, בניגוד להחלטה שיפוטית תקפה, מעמיק את הנזק ומחייב מתן סעד דחוף."));

children.push(H("ה. הסעדים המבוקשים"));

children.push(P("אשר על כן, מתבקשת כב' הרשמת להורות כדלקמן:", { after: 140 }));

const relief = [
  ["א.", "להורות על הסרת העיקול הרשום על חשבון החייב לאלתר, ועל משלוח הודעת ביטול העיקול לבנק המחזיק באופן מיידי."],
  ["ב.", "להורות למזכירות הלשכה הנכבדה למסור דיווח, בתוך פרק זמן קצר שייקבע, מדוע לא בוצעה עד כה החלטת כב' הרשמת מיום 19.8.2026, ומדוע לא הוסרו הליכי האכיפה מכוחה."],
  ["ג.", "להורות על ביטולם של כלל הליכי האכיפה התלויים ועומדים בתיק - לרבות עיקולי צד שלישי, עיקולי רכב והגבלות - כל עוד עומדת בעינה החלטת עיכוב ההליכים."],
  ["ד.", "להורות על השבת כל סכום אשר נגבה, נתפס או הועבר מן החשבון החל מיום 19.8.2026 ואילך."],
  ["ה.", "לדון בבקשה זו בדחיפות ובמעמד צד אחד, לנוכח הנזק המתמשך והבלתי הפיך הנגרם לחייב מדי יום."],
];
relief.forEach(([n, t]) => children.push(new Paragraph({
  bidirectional: true, alignment: AlignmentType.BOTH,
  spacing: { after: 120, line: 360, lineRule: LineRuleType.AUTO },
  indent: { right: 420, hanging: 420 },
  children: [run(n + "\t"), run(t)],
})));

children.push(P("בקשה זו נתמכת בהחלטות המצורפות ובמסמכי התיק, ואין בה כדי לגרוע מכל טענה וזכות של החייב, כולן שמורות לו.", { before: 240, after: 300 }));

children.push(twoCol(
  [run("תאריך: [__].[__].2026", { bold: false })],
  [run("_________________________"), run("[שם עו\"ד], עו\"ד"), run("ב\"כ החייב")]
));

children.push(H("רשימת נספחים"));
[["נספח א'", "החלטת כב' הרשמת מרים סגל מיום 19.8.2026 (בקשה מס' 41) בדבר עיכוב ההליכים בתיק."],
 ["נספח ב'", "אישור הבנק / פלט מצב החשבון, המעיד כי העיקול עודנו רשום ופעיל."],
 ["נספח ג'", "החלטת בית המשפט הנכבד מיום 18.8.2026."]].forEach(([n, t]) =>
  children.push(new Paragraph({
    bidirectional: true, alignment: AlignmentType.BOTH,
    spacing: { after: 100, line: 340, lineRule: LineRuleType.AUTO },
    indent: { right: 900, hanging: 900 },
    children: [run(n + "\t", { bold: true }), run(t)],
  })));

const doc = new Document({
  numbering: {
    config: [{
      reference: "clauses",
      levels: [{
        level: 0, format: LevelFormat.DECIMAL, text: "%1.",
        alignment: AlignmentType.START, suffix: "tab",
        style: { paragraph: { indent: { left: 420, hanging: 420 } } },
      }],
    }],
  },
  sections: [{
    properties: {
      page: { size: { width: PAGE_W, height: PAGE_H }, margin: M },
      bidi: true,
    },
    children,
  }],
});

Packer.toBuffer(doc).then(b => {
  fs.writeFileSync('/home/user/documents/out/בקשה_דחופה_הסרת_עיקול_542780-03-25.docx', b);
  console.log('OK');
});
