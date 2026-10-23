#!/usr/bin/env node
// Graphics layer renderer + layout checker. Run from the project folder (my-video/),
// where `npm install puppeteer` was run.
//
//   node render.mjs storyboard   one still per beat over the cut video  -> build/storyboard/ + storyboard.png
//   node render.mjs check        every 0.25s: safe zones, overlaps, crops -> build/qa/check.json (exit 2 on issues)
//   node render.mjs frames       transparent PNG per frame (30fps) + the check -> build/gfx/
//
// Options: --beats beats.json --words build/words_cut.json --brand brand.md --video build/cut.mov
//          --out build --fps 30 --zones (draw Instagram zones on storyboard stills)
import { createRequire } from 'node:module';
import { execFileSync } from 'node:child_process';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const HERE = path.dirname(fileURLToPath(import.meta.url));
const W = 1080, H = 1920;
const ZONE = { top: 220, bottom: H - 400, right: W - 130 };   // Instagram UI covers outside these
const FACE_TOP = 960;                                          // graphics stay in the top half
const SLAM = 0.12;

const args = process.argv.slice(2);
const mode = args[0];
const opt = (k, d) => { const i = args.indexOf('--' + k); return i > 0 ? args[i + 1] : d; };
const flag = k => args.includes('--' + k);
if (!['storyboard', 'check', 'frames'].includes(mode)) {
  console.error('usage: node render.mjs storyboard|check|frames [--beats beats.json] [--words build/words_cut.json] [--brand brand.md] [--video build/cut.mov] [--out build] [--fps 30] [--zones]');
  process.exit(1);
}
const project = process.cwd();
const out = path.resolve(opt('out', 'build'));
const fps = Number(opt('fps', 30));
const words = JSON.parse(fs.readFileSync(opt('words', 'build/words_cut.json'), 'utf8'));
const beatsDoc = JSON.parse(fs.readFileSync(opt('beats', 'beats.json'), 'utf8'));
const brandMd = fs.readFileSync(opt('brand', 'brand.md'), 'utf8');
const brandJson = brandMd.match(/^```json[ \t]*$([\s\S]*?)^```/m);
if (!brandJson) { console.error('brand.md has no ```json block'); process.exit(1); }
const brand = JSON.parse(brandJson[1]);
const video = path.resolve(opt('video', 'build/cut.mov'));
const duration = words.duration;

for (const b of beatsDoc.beats) for (const o of b.objects) {
  if (o.at != null && !words.words[o.at]) { console.error(`beat ${b.id}: word index ${o.at} does not exist`); process.exit(1); }
  if (o.src) {
    const p = path.resolve(project, o.src);
    if (!fs.existsSync(p)) { console.error(`beat ${b.id}: missing asset ${o.src}`); process.exit(1); }
    o.url = pathToFileURL(p).href;
  }
}

const require = createRequire(path.join(project, 'package.json'));
let puppeteer;
try { puppeteer = require('puppeteer'); }
catch { console.error(`Puppeteer not found in ${project}. Run: npm install puppeteer`); process.exit(1); }

const browser = await puppeteer.launch({
  headless: true,
  executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || undefined,
  args: ['--allow-file-access-from-files', '--force-color-profile=srgb', '--hide-scrollbars',
         ...(process.getuid?.() === 0 ? ['--no-sandbox'] : [])],   // root only happens in containers
});
const page = await browser.newPage();
await page.setViewport({ width: W, height: H, deviceScaleFactor: 1 });
page.on('pageerror', e => console.error('page error:', e.message));
await page.goto(pathToFileURL(path.join(HERE, 'composition.html')).href);
const info = await page.evaluate(d => window.setup(d), { beats: beatsDoc.beats, words: words.words, brand, duration });
if (info.failed.length) { console.error('could not load:', info.failed.join(', ')); await browser.close(); process.exit(1); }
if (!info.fontOk) console.warn(`warning: font "${brand.fontFamily}" did not load, falling back. Check fontUrl / network.`);

const seek = t => page.evaluate(t => window.seek(t), t);
const shot = (file, transparent = true) => page.screenshot({ path: file, omitBackground: transparent, type: 'png' });

// ---------- layout check ----------
async function check(t) {
  await seek(t);
  const items = await page.evaluate(() => window.inspect());
  const issues = [];
  for (const it of items) {
    const r = { x1: it.x, y1: it.ink.y, x2: it.x + it.w, y2: it.ink.y + it.ink.h };
    if (r.x1 < 0 || r.y1 < 0 || r.x2 > W || r.y2 > H) issues.push(['cropped by frame', it.id]);
    if (r.y1 < ZONE.top) issues.push(['in top 220px', it.id]);
    if (r.y2 > ZONE.bottom) issues.push(['in bottom 400px', it.id]);
    if (r.x2 > ZONE.right) issues.push(['in right 130px button column', it.id]);
    if (it.kind === 'graphic' && r.y2 > FACE_TOP) issues.push(['graphic below top half (covers face)', it.id]);
    if (it.textCrop) issues.push(['text overflows its box', it.id]);
  }
  for (let i = 0; i < items.length; i++) for (let j = i + 1; j < items.length; j++) {
    const a = items[i], b = items[j];
    const ix = Math.min(a.x + a.w, b.x + b.w) - Math.max(a.x, b.x);
    const iy = Math.min(a.y + a.h, b.y + b.h) - Math.max(a.y, b.y);
    if (ix > 2 && iy > 2) issues.push(['overlap', `${a.id} x ${b.id}`]);
  }
  return issues;
}

async function runCheck() {
  const qa = path.join(out, 'qa');
  fs.rmSync(qa, { recursive: true, force: true });
  fs.mkdirSync(qa, { recursive: true });
  const found = new Map();
  for (let t = 0; t < duration; t += 0.25) {
    for (const [what, id] of await check(t)) {
      const k = `${what}|${id}`;
      if (!found.has(k)) {
        const file = path.join(qa, `issue_${String(found.size + 1).padStart(2, '0')}_${t.toFixed(2)}s.png`);
        await page.evaluate(() => { window.showZones(true); document.body.style.background = '#333'; });
        await shot(file, false);
        await page.evaluate(() => { window.showZones(false); document.body.style.background = 'transparent'; });
        found.set(k, { what, id, first: t, last: t, screenshot: path.relative(project, file) });
      } else found.get(k).last = t;
    }
  }
  const issues = [...found.values()];
  fs.writeFileSync(path.join(qa, 'check.json'), JSON.stringify({ samples: Math.ceil(duration / 0.25), issues }, null, 1));
  if (!issues.length) console.log(`check: ${Math.ceil(duration / 0.25)} samples every 0.25s, no issues`);
  else {
    console.log(`check: ${issues.length} issue(s):`);
    for (const i of issues) console.log(`  ${i.first.toFixed(2)}-${i.last.toFixed(2)}s  ${i.what}  [${i.id}]  ${i.screenshot}`);
  }
  return issues.length;
}

// ---------- modes ----------
let exitCode = 0;
if (mode === 'storyboard') {
  const dir = path.join(out, 'storyboard');
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  const beats = beatsDoc.beats.map(b => {
    const ts = b.objects.map(o => o.t != null ? o.t : words.words[o.at].s);
    return { id: b.id, t0: Math.min(...ts), last: Math.max(...ts) };
  }).sort((a, b) => a.t0 - b.t0);
  if (flag('zones')) await page.evaluate(() => window.showZones(true));
  for (const [i, b] of beats.entries()) {
    const t1 = i + 1 < beats.length ? beats[i + 1].t0 : duration;
    const t = Math.min(t1 - 1 / fps, b.last + SLAM + 0.05);
    const bg = path.join(dir, `bg_${i}.jpg`);
    if (fs.existsSync(video)) {
      execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-ss', String(t), '-i', video, '-frames:v', '1', '-q:v', '3', bg]);
      await page.evaluate(u => window.setBackground(u), pathToFileURL(bg).href);
    }
    await seek(t);
    await shot(path.join(dir, `${String(i + 1).padStart(2, '0')}_${b.id}.png`), false);
    fs.rmSync(bg, { force: true });
    console.log(`  still ${i + 1}: ${b.id} @ ${t.toFixed(2)}s (${(t1 - b.t0).toFixed(2)}s on screen)`);
  }
  const cols = Math.min(6, beats.length), rows = Math.ceil(beats.length / cols);
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-framerate', '1', '-pattern_type', 'glob', '-i', path.join(dir, '[0-9]*.png'),
    '-vf', `scale=270:480,pad=280:490:5:5:white,tile=${cols}x${rows}`, '-frames:v', '1', path.join(out, 'storyboard.png')]);
  console.log(`storyboard: ${beats.length} beats -> ${path.relative(project, path.join(out, 'storyboard.png'))}`);
} else if (mode === 'check') {
  exitCode = (await runCheck()) ? 2 : 0;
} else {
  const dir = path.join(out, 'gfx');
  fs.rmSync(dir, { recursive: true, force: true });
  fs.mkdirSync(dir, { recursive: true });
  const n = Math.ceil(duration * fps);
  const t0 = Date.now();
  for (let f = 0; f < n; f++) {
    await seek(f / fps);
    await shot(path.join(dir, `${String(f).padStart(5, '0')}.png`));
    if (f % (fps * 5) === 0) process.stdout.write(`\r  frame ${f}/${n}`);
  }
  console.log(`\r  ${n} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s -> ${path.relative(project, dir)}`);
  exitCode = (await runCheck()) ? 2 : 0;
}
await browser.close();
process.exit(exitCode);
