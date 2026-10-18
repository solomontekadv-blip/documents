// Measures the end-card lines at their spec sizes and lists the fonts Chromium actually used.
import { chromium } from 'playwright';
import path from 'node:path';
import fs from 'node:fs';
const root = path.resolve(import.meta.dirname, '..');
const lines = [
  { id: 'line1', text: 'האומץ לא נולד איתך.', font: "500 66px 'Heebo'" },
  { id: 'tail', text: 'הוא נבנה בדרך.', font: "500 72px 'Frank Ruhl Libre'" },
  { id: 'badge', text: 'נתיב האומץ', font: "500 28px 'Heebo'" },
  { id: 'cta', text: '79 ₪ | sefer.tekalaw.co.il', font: "500 40px 'Heebo'" },
];
const html = `<!doctype html><html dir="rtl" lang="he"><head><meta charset="utf-8">
<link rel="stylesheet" href="../fonts/fonts.css"></head><body>
${lines.map(l => `<p><span id="${l.id}" style="font:${l.font};white-space:nowrap">${l.text}</span></p>`).join('')}
</body></html>`;
const browser = await chromium.launch();
const page = await browser.newPage();
const tmp = path.join(root, 'scripts', '_measure.html');
fs.writeFileSync(tmp, html);
await page.goto('file://' + tmp);
await page.evaluate(() => document.fonts.ready);
const client = await page.context().newCDPSession(page);
await client.send('DOM.enable'); await client.send('CSS.enable');
const { root: doc } = await client.send('DOM.getDocument');
for (const l of lines) {
  const w = await page.$eval('#' + l.id, e => e.getBoundingClientRect().width);
  const { nodeId } = await client.send('DOM.querySelector', { nodeId: doc.nodeId, selector: '#' + l.id });
  const { fonts } = await client.send('CSS.getPlatformFontsForNode', { nodeId });
  console.log(`${l.id.padEnd(6)} ${w.toFixed(0).padStart(4)}px  ${fonts.map(f => `${f.familyName}${f.isCustomFont ? '' : ' (SYSTEM FALLBACK)'} x${f.glyphCount}`).join(', ')}`);
}
await browser.close();
fs.unlinkSync(tmp);
