/**
 * Design tokens for JS consumers (Recharts, Framer Motion, inline styles).
 * Keep in sync with tailwind.config.js / index.css.
 */

export const colors = {
  surface: {
    950: '#06080a',
    900: '#0b0f12',
    800: '#12181d',
    700: '#1a2229',
    600: '#243039',
  },
  brand: {
    DEFAULT: '#14b8a6',
    300: '#5eead4',
    400: '#2dd4bf',
    500: '#14b8a6',
    600: '#0d9488',
    700: '#0f766e',
    emerald: '#34d399',
    glow: 'rgba(20, 184, 166, 0.35)',
    soft: 'rgba(20, 184, 166, 0.12)',
  },
  platform: {
    mynavi: '#3b82f6',
    careercross: '#f59e0b',
    wantedly: '#f43f5e',
    gaijinpot: '#22c55e',
  },
  white: {
    full: '#ffffff',
    90: 'rgba(255,255,255,0.9)',
    70: 'rgba(255,255,255,0.7)',
    50: 'rgba(255,255,255,0.5)',
    30: 'rgba(255,255,255,0.3)',
    10: 'rgba(255,255,255,0.1)',
    6: 'rgba(255,255,255,0.06)',
  },
};

/** Brand gradient stops for Recharts / SVG */
export const brandGradientStops = [
  { offset: '0%', color: colors.brand[700] },
  { offset: '45%', color: colors.brand[500] },
  { offset: '100%', color: colors.brand.emerald },
];

/** Score → color helper for match badges */
export function scoreColor(score) {
  if (score == null) return colors.white[30];
  if (score >= 80) return colors.brand.emerald;
  if (score >= 60) return colors.brand[500];
  if (score >= 40) return '#f59e0b';
  return '#f43f5e';
}

/** Normalize platform name → badge color */
export function platformColor(platform = '') {
  const key = String(platform).toLowerCase().replace(/\s+/g, '');
  if (key.includes('mynavi')) return colors.platform.mynavi;
  if (key.includes('career')) return colors.platform.careercross;
  if (key.includes('wantedly')) return colors.platform.wantedly;
  if (key.includes('gaijin')) return colors.platform.gaijinpot;
  return colors.brand[500];
}

/** Shared Framer Motion presets */
export const motionPresets = {
  fadeUp: {
    initial: { opacity: 0, y: 16 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -8 },
    transition: { duration: 0.35, ease: [0.22, 1, 0.36, 1] },
  },
  page: {
    initial: { opacity: 0, y: 12 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: -8 },
    transition: { duration: 0.28, ease: [0.22, 1, 0.36, 1] },
  },
  hoverLift: {
    whileHover: { scale: 1.02, y: -2 },
    whileTap: { scale: 0.98 },
    transition: { duration: 0.18 },
  },
  stagger: {
    animate: { transition: { staggerChildren: 0.08 } },
  },
};
