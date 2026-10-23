---
name: video-edit
description: Turn one raw talking-head take into a finished vertical video (Instagram Reels / TikTok / Shorts, 1080x1920) with word-synced graphics, a hook, captions, music and -14 LUFS export. Use when the user drops a raw take and asks to edit it, cut it, make a reel, "ערוך לי סרטון", "תעשה מזה רילס", or gives a note on a previous edit.
---

# Video edit: one take in, one file out

The deliverable is `final.mp4` + `cut_list.md` in the project folder. A plan, a storyboard or a still is a step, never the deliverable.

## Inputs (ask with AskUserQuestion if any is missing, in one call)

- `RAW_TAKE`: the take (default `raw-take.mov` in the project folder).
- `SECONDS`: target length. Ask every run.
- `AUDIENCE`: default **Hebrew-speaking Israeli audience on Instagram** (Hebrew, RTL, `--lang he`). Confirm if the take sounds different.
- Music file: optional. Ask once; no music is a valid answer.

Talk to the user in Hebrew. Never use the long dashes (U+2013, U+2014) in anything you write; use a plain "-".

## Project folder

```
my-video/
  raw-take.mov     one take, mistakes fine
  references/      5 outlier videos (5x the creator's usual views)
  moves.md         built on the first run from references/
  brand.md         colours, font, captions (machine-readable ```json block)
  notes.md         every note, as a rule
  best.mp4         the edit to beat
  beats.json       the storyboard, written by you
  assets/          real icons and screens
  build/           everything intermediate
```

`SKILL_DIR` below = the folder this SKILL.md is in. Scripts are in `SKILL_DIR/scripts/`. Always run them from the project folder.

## Step 0 - Setup and memory (every run)

1. `bash SKILL_DIR/scripts/setup_check.sh .` - if anything is missing, show the user the fix lines it printed and stop until fixed. Puppeteer must be installed in the project folder (`npm install puppeteer`).
2. Missing `brand.md`, `moves.md` or `notes.md`? Copy from `SKILL_DIR/templates/`. For brand.md, ask for colours and font before the first render.
3. **Read `brand.md`, `moves.md` and `notes.md` in full before any work.** Every rule in notes.md is binding and outranks this file where they conflict.

## Step 1 - References -> moves.md (first run, or when references/ changes)

1. Ask for each reference's views and the creator's usual views. Only keep outliers (>= 5x). Record both numbers in the Sources table; do not invent them.
2. `bash SKILL_DIR/scripts/refs.sh references build/refs --lang he`
3. For each reference read every `sheet_*.png` (1 frame/s, 30 per sheet, left-to-right, top-to-bottom), `transcript.txt` and `pace.txt`.
4. Write down per reference: the hook (first 3s: words + what is on screen), the pace (changes per 10s, longest hold), the layouts.
5. Save to moves.md **only moves seen in 2+ references**, each with "seen in: ...". One-off tricks are not moves.

## Step 2 - Transcribe

`python3 SKILL_DIR/scripts/transcribe.py raw-take.mov build/words.json --lang he`

Whisper's Hebrew is good but not perfect: read the transcript, fix misheard words in `build/words.json` (text only, keep times). If word timing looks off by a lot, say so.

## Step 3 - Cut list (show it, wait for approval)

1. `python3 SKILL_DIR/scripts/cutlist.py raw-take.mov build/words.json build/cut_list.json`
   - Pauses are cut to 0.25s only inside true silence (ffmpeg silencedetect, default -35 dB; use `--noise -30` in a noisy room if pauses are missed).
   - Retakes: a repeated 3-word phrase restarting within 30 words; the earlier attempt is dropped.
   - Words are never cut.
2. Read the "What stays" text yourself. The detector misses short false starts ("אני רצ... אני רוצה") and mid-sentence restarts. Add those to `cuts` in `build/cut_list.json` (`{"start","end","reason":"retake","text"}`, start/end on word edges from words.json), then `--from-json` to rebuild.
3. Compare cut length with `SECONDS`. If it is more than 10% over, propose specific whole sentences to drop (with the reason) - never shorten by speeding up.
4. **Show the cut list (the md table + what stays + the length) and wait for a yes.** Apply the user's changes, show again if they changed anything.
5. `python3 SKILL_DIR/scripts/apply_cuts.py raw-take.mov build/cut_list.json build/words.json build/cut.mov build/words_cut.json`

From here on, all times and word indexes come from `build/words_cut.json`.

## Step 4 - Storyboard (wait for yes before any full render)

Write `beats.json` (format: `SKILL_DIR/templates/beats.example.json`). Rules:

- **Hook**: the first sentence becomes the hook - its key words as big `xl` text, layout `inline`, one object per word on that word's index. Cut filler words from the hook text, keep the words that carry the promise. Use the hook moves from moves.md.
- **A new graphic every 2 seconds** (never hold one beat > 2.5s). Count: beats >= cut length / 2.
- **Each graphic changes on its exact word**: every object's `at` is the index of the word that names it. Several objects in one beat each slam on their own word.
- **Top half only**: graphics live in the zone x 60-890, y 250-940. The face is below. Captions sit under the face.
- **Real things only**: an app is mentioned -> its real icon; a product/site/feature -> a real screen of it. Never a stand-in, emoji, generic shape or AI image of an app.
  - Icons: `python3 SKILL_DIR/scripts/fetch_icon.py "Notion" assets/icons/notion.png --country il` (check the printed name is the right app; `--pick N` otherwise).
  - Screens: `node SKILL_DIR/scripts/capture_screen.mjs URL assets/screens/x.png --mobile [--video 6]`. If it needs a login, ask the user to log in **in the window that opens** (the profile is saved in `.chrome-profile/`, so once). Never ask for a password in chat, never type credentials.
  - Phone-only apps: ask the user for a screen recording or screenshot from their phone.
- Pull layouts and pace from moves.md; follow every rule in notes.md.

Then: `node SKILL_DIR/scripts/render.mjs storyboard --zones` -> look at `build/storyboard.png` and every still in `build/storyboard/` yourself first, fix what is wrong, then show the user the storyboard with one line per beat (time, word, what is on screen). **Wait for a yes.**

## Step 5 - Render and check (loop until clean)

1. `node SKILL_DIR/scripts/render.mjs frames` - renders the transparent graphics layer at 30fps and runs the layout check every 0.25s: Instagram zones (top 220px, bottom 400px, right 130px), graphics below the top half, overlaps, text that overflows, anything cut by the frame. Exit 2 = issues, listed with a screenshot each in `build/qa/`.
2. Fix each issue in beats.json (smaller `h`/`size`, fewer objects per beat, shorter text, split into two beats). Re-run until "no issues". Do not export with open issues.
3. Motion is fixed by design: every object slams in (scale 1.35 -> 1.0 in 0.12s, ease-out, no overshoot) and lands with no bounce. Do not add CSS animations or transitions; animation must stay a function of `seek(t)`.

## Step 6 - Export

`python3 SKILL_DIR/scripts/compose.py build/cut.mov build/gfx final.mp4 --music music.mp3`

H.264 high, 1080x1920, 30fps, AAC 48k, music exactly 12 dB under the voice (by measured LUFS), two-pass loudnorm to -14 LUFS / -1 dBTP. It re-measures the file and prints PASS/FAIL; FAIL means fix and export again. Then copy `build/cut_list.md` to `cut_list.md` next to `final.mp4`.

## Step 7 - Checks on the finished file (run them, never just claim them)

1. `bash SKILL_DIR/scripts/qa_frames.sh final.mp4 build/qa/frames` - a screenshot every 0.25s on contact sheets, red = Instagram-covered, yellow line = top-half limit. **Read every sheet.** Look for overlaps, crops, text on the face, anything in red, a graphic that appears before its word, a held frame. Fix, re-render, check again.
2. `python3 SKILL_DIR/scripts/count_changes.py final.mp4 best.mp4` - same detector on both. Exit 2 (fewer changes than best.mp4) -> add beats, render, export, count again. Also compare changes per 10s when lengths differ.
3. Report to the user in Hebrew: length, number of beats, changes vs best.mp4, LUFS measured, check result, and the paths of `final.mp4` and `cut_list.md`. Say plainly if anything was skipped.

## Notes loop

The user gives one note at a time. For each note:

1. Turn it into a general rule that applies to every future video (not "move the icon at 0:07" but "icons never wider than 300px when a caption is showing"). Append it to notes.md: `- [YYYY-MM-DD] RULE - from note: "..."`. If it contradicts an older rule, rewrite the old line rather than adding a second one.
2. Apply it to this video, re-run Steps 5-7, show the result.
3. Before the next video, all rules apply from the start - the goal is fewer notes each time.

If a note would make the video worse (e.g. a graphic every 5 seconds against moves.md's pace), say so once, with the reason, then do what the user decides.

## Gotchas

- `mlx-whisper` only runs on Apple Silicon. Windows / Intel Mac: `pip3 install openai-whisper` (transcribe.py picks whichever is installed).
- Puppeteer can't find Chrome: `npx puppeteer browsers install chrome` (in the project folder).
- `pip3` missing: `brew install python`. "command not found" right after installing: open a new Terminal window.
- Hebrew in graphics: the renderer is HTML, so RTL and mixed Hebrew/English text are correct. Do not draw text with ffmpeg drawtext (it breaks RTL).
- Screen recordings in beats: use .webm (VP9) or H.264 .mp4; they are seeked frame by frame, so they stay in sync.
- The font must load (render.mjs warns if it falls back). No network = no Google font; install the font locally and drop `fontUrl`.
