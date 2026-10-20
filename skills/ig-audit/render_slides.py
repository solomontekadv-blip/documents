"""render_slides.py - export one 1080x1350 PNG per <section> of a carousel HTML file.

Usage: python3 render_slides.py carousel.html   ->  slides/slide-01.png ...
Refuses to render while {{...}} or [לבדיקה] remain, and refuses to export with fallback fonts.
Requires Playwright + Chromium (see ig-carousel SKILL.md). No other network use beyond loading the page fonts.
"""
import pathlib, sys
from playwright.sync_api import sync_playwright

src = pathlib.Path(sys.argv[1]).resolve()
if "{{" in src.read_text(encoding="utf-8") or "[לבדיקה" in src.read_text(encoding="utf-8"):
    sys.exit("נשארו {{...}} או [לבדיקה] בשקופיות. לא מרנדרים.")
out = src.parent / "slides"
out.mkdir(exist_ok=True)
FONTS_OK = """async () => {
  await document.fonts.load('700 40px "Frank Ruhl Libre"', 'א');
  await document.fonts.load('400 40px "Heebo"', 'א');
  const c = document.createElement("canvas").getContext("2d");
  const w = f => { c.font = f; return c.measureText("אבגדהוזחט 3/8").width; };
  return w('700 40px "Frank Ruhl Libre", monospace') !== w('700 40px monospace')
      && w('400 40px "Heebo", monospace') !== w('400 40px monospace');
}"""
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1080, "height": 1350})
    page.goto(src.as_uri(), wait_until="networkidle")
    if not page.evaluate(FONTS_OK):
        browser.close()
        sys.exit("Frank Ruhl Libre או Heebo לא נטענו. לא מייצאים עם גופן חלופי.")
    for i, s in enumerate(page.query_selector_all("section"), 1):
        s.screenshot(path=str(out / f"slide-{i:02d}.png"))
    browser.close()
print(f"נשמר ב-{out}")
