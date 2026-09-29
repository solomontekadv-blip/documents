# מערכת המותג: עו״ד סולומון טקה | נתיב האומץ

כל מה שצריך כדי לייצר חומרים עקביים: לוגו וקטורי בכל הגרסאות, צבעים, גופנים, טוקנים לקוד וקומפוננטות UI.
המסמך המלא עם כל הכללים והדוגמאות הוא **`brand-book.html`** (לפתוח בדפדפן).

## מה יש בתיקייה

```
brand/
├── brand-book.html        ספר המותג המלא
├── BRIEF.md               הבריף: המטרה, האסטרטגיה והקריטריונים
├── logo/
│   ├── svg/               וקטור, שקוף (לאתר, למעצבים, ל-Office)
│   ├── png/               תמונה שקופה ברזולוציה גבוהה
│   ├── pdf/               וקטור לבית הדפוס
│   └── favicon/           פביקון ואייקונים לאתר
├── tokens/                tokens.css · tokens.json · tailwind.preset.js
├── ui/                    components.css · ui-kit.html
├── patterns/              קווי גובה וקו הדרך (SVG)
├── proposals/             חמש הצעות ללוגו חדש (טיוטות, עדיין לא בשימוש)
└── source/                הלוגו המקורי (לתיעוד בלבד, לא לשימוש)
```

## איזה לוגו לאיזה שימוש

| שימוש | קובץ |
|---|---|
| כריכה, פוסטר, במה, שקף פתיחה | `netiv-haometz-primary` |
| כותרת אתר, חתימת מייל, מקום צר | `netiv-haometz-horizontal` |
| אתר אישי, כרטיס ביקור, לינקדאין | `solomon-teka-lockup` |
| נייר מכתבים ומסמכי המשרד | `solomon-teka-law` |
| אווטאר ברשתות, חותמת | `netiv-haometz-symbol` |
| פביקון ואפליקציה | `logo/favicon/` · `netiv-haometz-icon` |
| רקע נייבי או כהה | הגרסה עם `-reversed` |
| צבע אחד (הטבעה, רקמה, פקס) | `-mono-navy` · `-mono-white` · `-mono-gold` |

כללים קצרים: לא למתוח, לא לצבוע מחדש, לא להוסיף צל, לא להקליד את השם מחדש בגופן אחר. מרחב מוגן: גובה האות נ מכל צד. מתחת ל-24px משתמשים רק באייקון.

## צבעים

| שם | HEX | CMYK (SWOP) | תפקיד |
|---|---|---|---|
| נייבי פסגה | `#0A2A4B` | 100 84 43 42 | טקסט, כותרות, משטחים |
| כחול רכס | `#1B4775` | 96 77 29 15 | קישורים, מידע |
| זהב הנתיב | `#CA984D` (גרדיאנט `#D9AD69` עד `#BF893A`) | 20 41 82 2 | הדגשה אחת במסך |
| קלף | `#F6EFE1` | 2 4 11 0 | רקע לתוכן ארוך |
| חול | `#EFE3CF` | 5 9 18 0 | משטחים משניים |

זהב הלוגו לא משמש לטקסט על רקע בהיר. לטקסט זהב: `#8D6223`.
לדפוס: לאשר מול הספק בפרופיל FOGRA39 ולבקש הגהת צבע. לכרטיסים ולנייר מכתבים עדיף נייר בגוון שמנת על פני הדפסת רקע קרם.

## גופנים

- **Assistant** (הגופן של הלוגו): כותרות, ממשק, גוף טקסט. https://fonts.google.com/specimen/Assistant
- **Frank Ruhl Libre**: ציטוטים, סיפור, מסמכי המשרד. https://fonts.google.com/specimen/Frank+Ruhl+Libre

שניהם חינמיים. במחשב בלי הגופנים: Arial במקום Assistant, ו-David במקום Frank Ruhl Libre.

## בקוד

```html
<link href="https://fonts.googleapis.com/css2?family=Assistant:wght@400;500;600;700;800&family=Frank+Ruhl+Libre:wght@400;500;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="brand/tokens/tokens.css">
<link rel="stylesheet" href="brand/ui/components.css">

<body class="nv" dir="rtl" lang="he">
  <a class="nv-btn nv-btn--accent" href="#booking">הזמנת הרצאה</a>
</body>
```

- מצב לילה עובד אוטומטית לפי הגדרות המערכת, או עם `data-theme="dark"` על `<html>`.
- `nv-theme-dark` / `nv-theme-light` כופים מצב תאורה על אזור אחד בעמוד.
- Tailwind: `presets: [require('./brand/tokens/tailwind.preset.js')]` יחד עם `tokens.css`.
- כל צירופי הצבע הסמנטיים עומדים ב-WCAG AA בשני המצבים.
- תצוגה של כל הרכיבים: `ui/ui-kit.html`.

## הצעות ללוגו (טיוטות)

בתיקייה `proposals/` יש חמש הצעות ללוגו, כל אחת בצבע ובגרסה לרקע כהה, עם סמל נפרד:
`refined` (המקור, מחודד) · `path-to-name` (הדרך אל השם) · `seal` (החותם) · `line` (קו אחד) · `book` (הספר והפסגה).
ההשוואה וההמלצה ב-`proposals/logo-proposals.pdf`.
אלה טיוטות לבחירה ולא חלק מהמערכת. אחרי הבחירה והליטוש, הלוגו שנבחר יחליף את הקבצים ב-`logo/`.

**סבב ליטוש 1** (`proposals/round-1/`): הכיוון שנבחר, "הדרך אל השם" עם החותם, והשם "עו״ד סולומון טקה" בכל הגרסאות.
חמש גרסאות לפי גודל: `primary` (לוגו ראשי) · `compact` (כותרת אתר, חתימת מייל) · `symbol` (אווטאר) · `seal` (חותם) · `favicon`.
הקבצים עם `-frank` הם אותו לוגו עם השם ב-Frank Ruhl Libre, לבחירה. הסקירה המלאה ב-`round-1/logo-round-1.pdf`.
