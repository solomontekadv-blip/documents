#!/usr/bin/env python3
"""render_slides.py - export one 1080x1350 PNG per <section> of a carousel HTML file.

Usage
  python3 render_slides.py carousel.html                 ->  slides/slide-01.png ...
  python3 render_slides.py carousel.html --out ~/slides
  python3 render_slides.py carousel.html --chromium /path/to/chrome

Refuses to render while {{...}} or [לבדיקה] remain, and refuses to export with
fallback fonts. Requires Playwright + Chromium (see ig-carousel SKILL.md); with
no Playwright it says so and exits 3, so the skill can hand over the HTML
instead. No network use beyond loading the page fonts.
"""
import argparse
import os
import pathlib
import sys

FONTS_OK = """async () => {
  await document.fonts.load('700 40px "Frank Ruhl Libre"', 'א');
  await document.fonts.load('400 40px "Heebo"', 'א');
  const c = document.createElement("canvas").getContext("2d");
  const w = f => { c.font = f; return c.measureText("אבגדהוזחט 3/8").width; };
  return w('700 40px "Frank Ruhl Libre", monospace') !== w('700 40px monospace')
      && w('400 40px "Heebo", monospace') !== w('400 40px monospace');
}"""


def main():
    ap = argparse.ArgumentParser(description="Export a carousel HTML file as 1080x1350 PNG slides.")
    ap.add_argument("html", help="the carousel HTML file, one <section> per slide")
    ap.add_argument("--out", help="folder for the PNGs (default: slides/ next to the HTML)")
    ap.add_argument("--chromium", default=os.environ.get("CHROMIUM_PATH"),
                    help="a Chromium or Chrome binary, if Playwright's own is not installed")
    args = ap.parse_args()

    src = pathlib.Path(args.html).expanduser().resolve()
    if not src.is_file():
        sys.exit(f"אין קובץ כזה: {src}")
    text = src.read_text(encoding="utf-8")
    if "{{" in text or "[לבדיקה" in text:
        sys.exit("נשארו {{...}} או [לבדיקה] בשקופיות. לא מרנדרים.")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Playwright לא מותקן, אז אין ייצוא ל-PNG. להתקנה:\n"
              "  pip install playwright && python3 -m playwright install chromium\n"
              "בינתיים קובץ ה-HTML מוכן: פתח אותו בדפדפן וצלם כל שקופית.", file=sys.stderr)
        sys.exit(3)

    out = pathlib.Path(args.out).expanduser() if args.out else src.parent / "slides"
    out.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        launch = {"executable_path": args.chromium} if args.chromium else {}
        browser = p.chromium.launch(**launch)
        page = browser.new_page(viewport={"width": 1080, "height": 1350})
        page.goto(src.as_uri(), wait_until="networkidle")
        if not page.evaluate(FONTS_OK):
            browser.close()
            sys.exit("Frank Ruhl Libre או Heebo לא נטענו. לא מייצאים עם גופן חלופי.")
        sections = page.query_selector_all("section")
        if not sections:
            browser.close()
            sys.exit("אין <section> בקובץ, אז אין שקופיות לייצא.")
        for i, s in enumerate(sections, 1):
            s.screenshot(path=str(out / f"slide-{i:02d}.png"))
        browser.close()
    print(f"נשמרו {len(sections)} שקופיות ב-{out}")


if __name__ == "__main__":
    main()
