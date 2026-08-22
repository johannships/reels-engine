// RepoDrop style tokens. Every number here was measured off a reference reel
// rather than chosen by eye — see docs/REPODROP.md.
export const RD = {
  dark: '#0F0F0F',
  darkPanel: '#121216',
  white: '#FDFDFD',
  ink: '#0B0B0B',
  danger: '#E5484D',
  ok: '#3DD68C',
  teal: '#2BD9C4',
  muted: '#8A8A8A',
  line: '#262626',
} as const;

// Graphic captions: serif, italic, ALL CAPS. Cap-height 87-99px on a 1920-tall
// frame, which is ~116px of Didot.
export const RD_CAP = {
  family: "Didot, 'Bodoni 72', 'Playfair Display', Georgia, serif",
  size: 116,
  spacing: 2,
  maxWidth: 940,
} as const;

export const RD_MONO = "'SF Mono', Menlo, ui-monospace, monospace";
export const RD_SANS = "'Inter Tight', 'Helvetica Neue', Arial, sans-serif";

// The picture-in-picture card: full width, flush to the bottom, top corners only.
export const RD_CARD = {top: 1087, height: 833, radius: 48} as const;
