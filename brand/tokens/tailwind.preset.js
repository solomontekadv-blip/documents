/** Tailwind preset - Netiv design system (עו״ד סולומון טקה | נתיב האומץ)
 *  Usage: presets: [require('./brand/tokens/tailwind.preset.js')]  +  import tokens.css for the theme variables.
 */
module.exports = {
  darkMode: ['class', '[data-theme="dark"]'],
  theme: {
    extend: {
      colors: {
        "navy": "#0A2A4B",
        "ridge": "#1B4775",
        "parchment": "#F6EFE1",
        "sand": "#EFE3CF",
        "blue": {
          "50": "#F6F8FB",
          "100": "#EBF0F5",
          "200": "#D6DFEA",
          "300": "#B6C6D8",
          "400": "#8FA5C0",
          "500": "#6886A8",
          "600": "#476A92",
          "700": "#1B4775",
          "800": "#143A63",
          "900": "#0A2A4B",
          "950": "#031A33"
        },
        "gold": {
          "50": "#FDF8F0",
          "100": "#F9EFDF",
          "200": "#F2DEC2",
          "300": "#E7C798",
          "400": "#D9AD69",
          "500": "#CA984D",
          "600": "#BF893A",
          "700": "#8D6223",
          "800": "#734E17",
          "900": "#583A0B",
          "950": "#3B2502",
          "DEFAULT": "#CA984D"
        },
        "neutral": {
          "50": "#FCF9F2",
          "100": "#F6EFE1",
          "200": "#EFE3CF",
          "300": "#D7CEC0",
          "400": "#B4AFA7",
          "500": "#8E8C89",
          "600": "#666A6F",
          "700": "#4D535A",
          "800": "#363E47",
          "900": "#222B36",
          "950": "#101A26"
        },
        "bg": "var(--nv-bg)",
        "bg-subtle": "var(--nv-bg-subtle)",
        "surface": "var(--nv-surface)",
        "surface-raised": "var(--nv-surface-raised)",
        "surface-inverse": "var(--nv-surface-inverse)",
        "border-subtle": "var(--nv-border-subtle)",
        "border": "var(--nv-border)",
        "border-strong": "var(--nv-border-strong)",
        "text": "var(--nv-text)",
        "text-secondary": "var(--nv-text-secondary)",
        "text-muted": "var(--nv-text-muted)",
        "text-inverse": "var(--nv-text-inverse)",
        "text-accent": "var(--nv-text-accent)",
        "link": "var(--nv-link)",
        "link-hover": "var(--nv-link-hover)",
        "action": "var(--nv-action)",
        "action-hover": "var(--nv-action-hover)",
        "on-action": "var(--nv-on-action)",
        "accent": "var(--nv-accent)",
        "accent-hover": "var(--nv-accent-hover)",
        "on-accent": "var(--nv-on-accent)",
        "accent-subtle": "var(--nv-accent-subtle)",
        "focus": "var(--nv-focus)",
        "path": "var(--nv-path)",
        "path-track": "var(--nv-path-track)",
        "success": "var(--nv-success)",
        "success-bg": "var(--nv-success-bg)",
        "warning": "var(--nv-warning)",
        "warning-bg": "var(--nv-warning-bg)",
        "danger": "var(--nv-danger)",
        "danger-bg": "var(--nv-danger-bg)",
        "info": "var(--nv-info)",
        "info-bg": "var(--nv-info-bg)"
      },
      fontFamily: {
        sans: ["Assistant", "Segoe UI", "Arial Hebrew", "Arial", "system-ui", "sans-serif"],
        serif: ["Frank Ruhl Libre", "David Libre", "David", "Times New Roman", "serif"],
      },
      fontSize: {
        "display": [
          "clamp(3rem, 2rem + 4vw, 4.625rem)",
          {
            "lineHeight": "1.02",
            "letterSpacing": "-0.015em",
            "fontWeight": "800"
          }
        ],
        "h1": [
          "clamp(2.5rem, 1.9rem + 2.6vw, 3.625rem)",
          {
            "lineHeight": "1.06",
            "letterSpacing": "-0.012em",
            "fontWeight": "800"
          }
        ],
        "h2": [
          "clamp(2rem, 1.6rem + 1.7vw, 2.875rem)",
          {
            "lineHeight": "1.12",
            "letterSpacing": "-0.01em",
            "fontWeight": "700"
          }
        ],
        "h3": [
          "clamp(1.625rem, 1.4rem + 1vw, 2.25rem)",
          {
            "lineHeight": "1.2",
            "letterSpacing": "-0.005em",
            "fontWeight": "700"
          }
        ],
        "h4": [
          "1.875rem",
          {
            "lineHeight": "1.3",
            "letterSpacing": "0",
            "fontWeight": "700"
          }
        ],
        "xl": [
          "1.5rem",
          {
            "lineHeight": "1.45",
            "letterSpacing": "0",
            "fontWeight": "500"
          }
        ],
        "lg": [
          "1.3125rem",
          {
            "lineHeight": "1.6",
            "letterSpacing": "0",
            "fontWeight": "400"
          }
        ],
        "base": [
          "1.125rem",
          {
            "lineHeight": "1.75",
            "letterSpacing": "0",
            "fontWeight": "400"
          }
        ],
        "sm": [
          "0.9375rem",
          {
            "lineHeight": "1.6",
            "letterSpacing": "0",
            "fontWeight": "400"
          }
        ],
        "xs": [
          "0.8125rem",
          {
            "lineHeight": "1.5",
            "letterSpacing": "0.01em",
            "fontWeight": "500"
          }
        ],
        "eyebrow": [
          "0.875rem",
          {
            "lineHeight": "1.4",
            "letterSpacing": "0.06em",
            "fontWeight": "700"
          }
        ],
        "quote": [
          "clamp(1.5rem, 1.2rem + 1.2vw, 2.125rem)",
          {
            "lineHeight": "1.45",
            "letterSpacing": "0",
            "fontWeight": "500"
          }
        ]
      },
      borderRadius: {
        "none": "0",
        "xs": "2px",
        "sm": "4px",
        "md": "6px",
        "lg": "10px",
        "xl": "16px",
        "full": "999px"
      },
      boxShadow: {
        "xs": "var(--nv-shadow-xs)",
        "sm": "var(--nv-shadow-sm)",
        "md": "var(--nv-shadow-md)",
        "lg": "var(--nv-shadow-lg)"
      },
      transitionTimingFunction: { ascent: 'cubic-bezier(0.22, 1, 0.36, 1)', path: 'cubic-bezier(0.65, 0, 0.35, 1)' },
      maxWidth: { container: '1200px', reading: '68ch' },
    },
  },
};
