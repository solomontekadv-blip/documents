#!/usr/bin/env node
// Capture a real screen of a web app. Opens a visible Chrome window with a profile saved in
// .chrome-profile/, so a login happens once, by the user, in the window - never typed into chat.
//
// Usage (from the project folder):
//   node capture_screen.mjs https://app.example.com assets/screens/dashboard.png [--mobile] [--video 6]
// Log in / navigate in the window, then press Enter in the terminal to capture.
// --mobile   390x844 phone viewport at 3x (fits the top half best)
// --video N  also record N seconds as assets/screens/<name>.webm (scrolls, clicks, typing you do)
import { createRequire } from 'node:module';
import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline/promises';

const [url, outFile] = process.argv.slice(2);
if (!url || !outFile) { console.error('usage: node capture_screen.mjs URL out.png [--mobile] [--video SECONDS]'); process.exit(1); }
const mobile = process.argv.includes('--mobile');
const vi = process.argv.indexOf('--video');
const videoSecs = vi > 0 ? Number(process.argv[vi + 1]) : 0;

const require = createRequire(path.join(process.cwd(), 'package.json'));
const puppeteer = require('puppeteer');
const browser = await puppeteer.launch({
  headless: false, defaultViewport: null, userDataDir: path.resolve('.chrome-profile'),
  executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || undefined,
});
const page = (await browser.pages())[0] || await browser.newPage();
await page.setViewport(mobile ? { width: 390, height: 844, deviceScaleFactor: 3, isMobile: true, hasTouch: true }
                              : { width: 1280, height: 800, deviceScaleFactor: 2 });
await page.goto(url, { waitUntil: 'networkidle2' }).catch(() => {});
const rl = readline.createInterface({ input: process.stdin, output: process.stdout });
await rl.question('Log in and open the exact screen, then press Enter here to capture... ');
fs.mkdirSync(path.dirname(path.resolve(outFile)), { recursive: true });
await page.screenshot({ path: outFile, type: 'png' });
console.log(`saved ${outFile}`);
if (videoSecs > 0) {
  const webm = outFile.replace(/\.png$/i, '.webm');
  await rl.question(`Press Enter to start recording ${videoSecs}s, then do the action in the window... `);
  const rec = await page.screencast({ path: webm });
  await new Promise(r => setTimeout(r, videoSecs * 1000));
  await rec.stop();
  console.log(`saved ${webm}`);
}
rl.close();
await browser.close();
