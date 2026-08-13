// Brand tokens — must match the Reels Engine brand exactly.
export const COLORS = {
  ground: '#0A0A0D',
  card: '#141318',
  border: '#232028',
  text: '#FFFFFF',
  muted: '#A49FB3',
  violet: '#8B5CF6',
  violetLight: '#A78BFA',
  green: '#67D243',
} as const;

export const FONTS = {
  display: "'Bricolage Grotesque', sans-serif",
  body: "'Inter Tight', sans-serif",
} as const;

// Layout constants for the 1080x1920 vertical frame.
export const LAYOUT = {
  width: 1080,
  height: 1920,
  canvasHeight: 960, // visual canvas: y 0-960
  captionTop: 826, // caption band sits just above the seam: y 826-946
  captionHeight: 120,
  avatarTop: 960, // avatar slot: y 960-1920
  avatarHeight: 960,
} as const;
