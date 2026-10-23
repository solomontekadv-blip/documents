# Brand

The renderer reads the first ```json block below. Everything else in this file is for humans.
Change the values, keep the keys.

```json
{
  "lang": "he",
  "direction": "rtl",
  "fontFamily": "Heebo",
  "fontUrl": "https://fonts.googleapis.com/css2?family=Heebo:wght@500;700;900&display=swap",
  "colors": {
    "text": "#FFFFFF",
    "accent": "#FFD400",
    "card": "rgba(12,12,16,0.88)",
    "stroke": "#000000"
  },
  "captions": {
    "enabled": true,
    "maxWords": 3,
    "size": 76,
    "activeColor": "#FFD400",
    "color": "#FFFFFF"
  },
  "graphics": {
    "textSize": { "xl": 128, "l": 100, "m": 76, "s": 56 },
    "iconRadius": 0.22,
    "screenRadius": 36
  }
}
```

## Notes

- Font: Heebo is a free Hebrew + Latin font. Swap for your own brand font if you have one (any Google Font works by changing `fontFamily` and `fontUrl`).
- `accent` is the colour for the word being spoken in the captions and for highlights in graphics.
- Captions sit between the face and the bottom 400px Instagram covers.
