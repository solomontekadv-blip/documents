# התקנת סביבת עבודה ל-Claude Code על Windows

סקריפט אחד שמתקין את כל מה שצריך כדי להריץ Claude Code מקומית על מחשב Windows.

## מה מותקן

| כלי | למה צריך אותו |
|---|---|
| Git | Claude Code על Windows דורש Git for Windows (Git Bash). גם לעבודה מול הרפו. |
| Node.js LTS | תשתית ל-Claude Code ולסקילים מבוססי JavaScript (למשל יצירת DOCX). |
| Python 3.12 | סקילים לעיבוד מסמכים (docx, pdf, xlsx) מריצים סקריפטים ב-Python. |
| FFmpeg | אופציונלי. לא נדרש ל-Claude Code עצמו. שימושי לתמלול והמרת קבצי אודיו/וידאו. |
| Claude Code | הכלי עצמו. מותקן דרך המתקין הרשמי, עם גיבוי דרך npm. |

## הרצה

פתח PowerShell בתיקיית הרפו והרץ:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup\setup-windows.ps1
```

בלי FFmpeg:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup\setup-windows.ps1 -SkipFFmpeg
```

הסקריפט בודק מה כבר מותקן ומדלג עליו, כך שאפשר להריץ אותו שוב בכל פעם.

## אחרי ההתקנה

1. סגור ופתח מחדש את הטרמינל כדי ש-PATH יתעדכן.
2. הרץ `claude` מתוך תיקיית הרפו.
3. בהפעלה הראשונה תתבקש להתחבר לחשבון Anthropic דרך הדפדפן.

## בעיות נפוצות

- **winget לא נמצא**: התקן "App Installer" מ-Microsoft Store.
- **python פותח את Microsoft Store**: כבה את "App execution aliases" עבור python ב-Settings > Apps > Advanced app settings, והרץ שוב.
- **כלי הותקן אבל לא מזוהה**: סגור ופתח מחדש את הטרמינל והרץ את הסקריפט שוב.
- **הסקריפט חסום**: ודא שהרצת עם `-ExecutionPolicy Bypass` כמו בדוגמה למעלה.
