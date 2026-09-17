import localFont from "next/font/local";

/**
 * Thamanya Sans — the practical UI family. Everything the user reads and interacts
 * with (body copy, navigation, forms, buttons, dashboard) uses this.
 */
export const thmanyahSans = localFont({
  src: [
    { path: "../fonts/thmanyah-sans-Light.otf", weight: "300", style: "normal" },
    { path: "../fonts/thmanyah-sans-Regular.otf", weight: "400", style: "normal" },
    { path: "../fonts/thmanyah-sans-Medium.otf", weight: "500", style: "normal" },
    { path: "../fonts/thmanyah-sans-Bold.otf", weight: "700", style: "normal" },
    { path: "../fonts/thmanyah-sans-Black.otf", weight: "900", style: "normal" },
  ],
  variable: "--font-thmanyah",
  display: "swap",
  fallback: ["system-ui", "seguiemj", "sans-serif"],
  preload: true,
  adjustFontFallback: false,
});

/** Hayah — display family for important headings and section titles. */
export const hayah = localFont({
  src: [
    { path: "../fonts/Hayah-Regular.otf", weight: "400", style: "normal" },
  ],
  variable: "--font-hayah",
  display: "swap",
  fallback: ["var(--font-thmanyah)", "serif"],
  // Used for a handful of headlines only — not worth a preload slot.
  preload: false,
  adjustFontFallback: false,
});

/**
 * Aviny — the signature Arabic calligraphic face. Reserved for a few hero-level
 * brand moments so it keeps its impact. Never used for body text or UI controls.
 */
export const aviny = localFont({
  src: [
    { path: "../fonts/Aviny-Regular.ttf", weight: "400", style: "normal" },
  ],
  variable: "--font-aviny",
  display: "swap",
  fallback: ["var(--font-hayah)", "serif"],
  preload: false,
  adjustFontFallback: false,
});

export const fontVariables = [
  thmanyahSans.variable,
  hayah.variable,
  aviny.variable,
].join(" ");
