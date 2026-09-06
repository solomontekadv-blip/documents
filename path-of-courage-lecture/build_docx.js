const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, LevelFormat, PageBreak, Footer, PageNumber, TabStopType,
} = require("docx");

const src = fs.readFileSync(process.argv[2], "utf8").split("\n");
const out = process.argv[3];

const FONT = { ascii: "David", hAnsi: "David", cs: "David", eastAsia: "David" };
const GRAY = "666666";
const STAGE = "8A5A00";

function runs(text, base = {}) {
  // inline **bold**, *italic*, `code`
  const parts = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) parts.push({ t: text.slice(last, m.index) });
    const s = m[0];
    if (s.startsWith("**")) parts.push({ t: s.slice(2, -2), bold: true });
    else if (s.startsWith("`")) parts.push({ t: s.slice(1, -1), code: true });
    else parts.push({ t: s.slice(1, -1), italics: true });
    last = m.index + s.length;
  }
  if (last < text.length) parts.push({ t: text.slice(last) });
  return parts.map(p => new TextRun({
    text: p.t,
    font: FONT,
    rightToLeft: true,
    size: base.size || 26, sizeComplexScript: base.size || 26,
    bold: !!(p.bold || base.bold), boldComplexScript: !!(p.bold || base.bold),
    italics: !!(p.italics || base.italics), italicsComplexScript: !!(p.italics || base.italics),
    color: base.color,
    shading: p.code ? { type: ShadingType.CLEAR, fill: "EEEEEE" } : undefined,
  }));
}

function para(text, opts = {}) {
  return new Paragraph({
    bidirectional: true,
    alignment: opts.alignment || AlignmentType.START,
    heading: opts.heading,
    spacing: opts.spacing || { after: 140, line: 330 },
    indent: opts.indent,
    shading: opts.shading,
    border: opts.border,
    numbering: opts.numbering,
    keepNext: opts.keepNext,
    children: runs(text, opts.run || {}),
  });
}

const children = [];
let i = 0;
let bulletInst = 0, numInst = 0;

function flushTable(rows) {
  const body = rows.filter(r => !/^\|\s*-+/.test(r)).map(r =>
    r.replace(/^\||\|$/g, "").split("|").map(c => c.trim()));
  const cols = Math.max(...body.map(r => r.length));
  const total = 9360;
  const w = Math.floor(total / cols);
  const widths = Array(cols).fill(w);
  widths[cols - 1] = total - w * (cols - 1);
  const trs = body.map((cells, ri) => new TableRow({
    tableHeader: ri === 0,
    children: widths.map((cw, ci) => new TableCell({
      width: { size: cw, type: WidthType.DXA },
      shading: ri === 0 ? { type: ShadingType.CLEAR, fill: "D9E2F3" } : undefined,
      margins: { top: 60, bottom: 60, left: 100, right: 100 },
      children: [para(cells[ci] || "", { spacing: { after: 0, line: 280 }, run: { size: 22, bold: ri === 0 } })],
    })),
  }));
  children.push(new Table({
    visuallyRightToLeft: true,
    width: { size: total, type: WidthType.DXA },
    columnWidths: widths,
    rows: trs,
  }));
  children.push(para("", { spacing: { after: 120 } }));
}

while (i < src.length) {
  let line = src[i];
  const trimmed = line.trim();

  if (trimmed.startsWith("|")) {
    const rows = [];
    while (i < src.length && src[i].trim().startsWith("|")) { rows.push(src[i].trim()); i++; }
    flushTable(rows);
    continue;
  }
  if (trimmed.startsWith("> ") || trimmed === ">") {
    const q = [];
    while (i < src.length && (src[i].trim().startsWith(">"))) { q.push(src[i].trim().replace(/^>\s?/, "")); i++; }
    q.forEach(t => children.push(para(t, {
      indent: { start: 500 },
      shading: { type: ShadingType.CLEAR, fill: "FFF4D6" },
      spacing: { after: 80, line: 300 },
      run: { size: 24 },
    })));
    children.push(para("", { spacing: { after: 100 } }));
    continue;
  }
  if (trimmed === "") { i++; continue; }
  if (trimmed === "---") {
    children.push(new Paragraph({ bidirectional: true, spacing: { after: 200 }, border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: "999999", space: 4 } }, children: [] }));
    i++; continue;
  }
  if (trimmed.startsWith("# ")) {
    children.push(para(trimmed.slice(2), { heading: HeadingLevel.TITLE, alignment: AlignmentType.CENTER, run: { size: 44, bold: true } }));
    i++; continue;
  }
  if (trimmed.startsWith("## ")) {
    // new chapter -> page break before (except first)
    if (children.length > 12) children.push(new Paragraph({ children: [new PageBreak()] }));
    children.push(para(trimmed.slice(3), { heading: HeadingLevel.HEADING_1, keepNext: true, run: { size: 36, bold: true, color: "1F3864" }, spacing: { before: 200, after: 200 } }));
    i++; continue;
  }
  if (trimmed.startsWith("### ")) {
    const t = trimmed.slice(4);
    if (t.includes("=====")) {
      children.push(para(t.replace(/=====/g, "").trim(), { heading: HeadingLevel.HEADING_2, keepNext: true, shading: { type: ShadingType.CLEAR, fill: "FFE699" }, run: { size: 28, bold: true, color: "7F0000" }, spacing: { before: 200, after: 120 } }));
    } else {
      children.push(para(t, { heading: HeadingLevel.HEADING_2, keepNext: true, run: { size: 30, bold: true, color: "2E5395" }, spacing: { before: 240, after: 120 } }));
    }
    i++; continue;
  }
  if (/^\[.*\]$/.test(trimmed)) {
    children.push(para(trimmed, { alignment: AlignmentType.CENTER, run: { size: 22, italics: true, color: STAGE }, spacing: { after: 160, line: 300 } }));
    i++; continue;
  }
  if (/^\[/.test(trimmed) && /\]$/.test(trimmed) === false && /^\[[^\]]+\]/.test(trimmed)) {
    // "[גשר]" followed by text on next line is handled by the pure [..] case; fallthrough
  }
  if (/^- /.test(trimmed)) {
    bulletInst++;
    while (i < src.length && /^- /.test(src[i].trim())) {
      children.push(para(src[i].trim().slice(2), { numbering: { reference: "bullets", level: 0, instance: bulletInst }, spacing: { after: 80, line: 300 } }));
      i++;
    }
    continue;
  }
  if (/^\d+\. /.test(trimmed)) {
    numInst++;
    while (i < src.length && /^\d+\. /.test(src[i].trim())) {
      children.push(para(src[i].trim().replace(/^\d+\. /, ""), { numbering: { reference: "nums", level: 0, instance: numInst }, spacing: { after: 80, line: 300 } }));
      i++;
    }
    continue;
  }
  // normal paragraph (speech text): larger, comfortable line spacing
  children.push(para(trimmed, { run: { size: 28 }, spacing: { after: 180, line: 360 } }));
  i++;
}

const doc = new Document({
  creator: "סולומון טקה",
  title: "נתיב האומץ - נוסח בימה",
  styles: {
    default: { document: { run: { font: FONT, size: 26, rightToLeft: true } } },
    paragraphStyles: [
      { id: "Title", name: "Title", basedOn: "Normal", run: { font: FONT, size: 44, bold: true, color: "1F3864" }, paragraph: { alignment: AlignmentType.CENTER, spacing: { after: 240 } } },
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 36, bold: true, color: "1F3864" }, paragraph: { spacing: { before: 240, after: 200 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true, run: { font: FONT, size: 30, bold: true, color: "2E5395" }, paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.START, style: { paragraph: { indent: { start: 720, hanging: 360 } } } }] },
      { reference: "nums", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.START, style: { paragraph: { indent: { start: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: { margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } },
      bidi: true,
    },
    footers: {
      default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER, bidirectional: true, children: [new TextRun({ children: ["עמוד ", PageNumber.CURRENT], font: FONT, size: 20, rightToLeft: true })] })] }),
    },
    children,
  }],
});

Packer.toBuffer(doc).then(buf => { fs.writeFileSync(out, buf); console.log("wrote", out, buf.length); });
