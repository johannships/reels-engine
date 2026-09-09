/**
 * Trending style tokens — the "3 AI repos blowing up today" format.
 *
 * ─── HOW EVERY NUMBER IN THIS FILE WAS PRODUCED ────────────────────────────
 * Measured off the reference reel (Johann's best performer, 5,411 likes):
 *   /Users/johannsathianathen/reels/three-repos/ref.mp4
 *   52.77s, 720x1280, 30fps.
 *
 * The reference is 720 wide and we render 1080 wide, so every measurement is
 * quoted as "<ink px measured @720> -> <token value @1080>" (scale x1.5).
 *
 * Frames were extracted at 2fps (`ffmpeg -vf fps=2`) and measured by
 * luminance-thresholding each row/column and reading off the ink extents, so
 * the measured numbers are *glyph ink* bounds. Font sizes are back-solved
 * from ink height using the metric ratios of the two bundled faces
 * (x-height ~0.55em, ascender ~0.75em, cap-height ~0.727em) and were then
 * confirmed against a render.
 *
 * Frames referenced below:
 *   f_030 = t 14.5s — repo card 1/3 ("usestrix/strix", 35,615, +1,910 today)
 *   f_090 = t  3.0s — hook ("3 AI REPOS / BLOWING UP TODAY")
 *   f_1540 = t 51.3s — CTA ("Follow for tomorrow's 3." + @handle pill)
 *
 * The one DELIBERATE deviation from the reference is `CARD.top` — see the
 * comment on it. Everything else reproduces the reference geometry.
 */

/** Colours. Sampled as the median of the brightest 1% of each glyph's ink
 *  (a plain single-pixel sample lands on antialiasing and reads too dark). */
export const T_COLORS = {
  /** f_030 background, left of the card @(20,300) = rgb(11,10,15). The
   *  graphic area darkens toward the seam (rgb(8,8,10) @y600), which the
   *  radial glow in Shell.tsx reproduces. */
  ground: '#0A0A0D',
  /** f_030 card interior @(400,270) = rgb(20,19,24) — measured exactly. */
  card: '#141318',
  /** Hairline divider above the stars row. Sits ~1 luminance step above the
   *  card fill, invisible at 720p but it separates the row at 1080. */
  border: '#232028',
  /** f_030 repo name ink peak = rgb(255,255,255). */
  text: '#FFFFFF',
  /** f_030 owner ink #B3B2BB, desc ink #B5B3BC, "1/3" #BAB9BF, GitHub mark
   *  #B2B0BA — one grey for all four. */
  muted: '#A49FB3',
  /** f_090 hook underline rule ink #936DF0; f_1540 CTA handle pill fill
   *  rgb(51,37,87) is this colour at low alpha over the ground. */
  violet: '#8B5CF6',
  /** f_030 "TRENDING #1" ink #B3A5F2, star glyph #AE9AFB, caption accent
   *  #AE9BFA, f_090 hook line 2 #AE99FC, f_1540 CTA line 2 #AE98FB — the
   *  single accent colour used everywhere. */
  violetLight: '#A78BFA',
  /** f_030 chip text ink #75C55A. */
  green: '#67D243',
  /** f_030 chip fill @(440,440) = rgb(29,43,26) — the green above at ~12%
   *  over the card fill. */
  greenFill: 'rgba(103, 210, 67, 0.12)',
  /** f_030 chip has a visible 1px lighter-green rim. */
  greenLine: 'rgba(103, 210, 67, 0.4)',
} as const;

export const T_FONTS = {
  /** Repo name, star count, hook lines, CTA lines. */
  display: "'Bricolage Grotesque', 'Helvetica Neue', Arial, sans-serif",
  /** Labels, owner, description, chip, captions. */
  body: "'Inter Tight', 'Helvetica Neue', Arial, sans-serif",
} as const;

/** Frame + region geometry. */
export const T_LAYOUT = {
  width: 1080,
  height: 1920,
  /** f_030: the footage's top edge is a hard horizontal step at y 639 @720
   *  -> 958.5. The pipeline's split composite uses `crop=1080:960:0:0` on the
   *  canvas, so 960 is exact and the reference agrees to 1.5px. Everything
   *  this style draws lives in y 0..960; rows below are discarded by ffmpeg. */
  seam: 960,
  /** Instagram crops the top and bottom of a 1080x1920 reel in some
   *  surfaces. Nothing meaning-carrying may sit above/below these lines. */
  safeTop: 220,
  safeBottom: 1620,
} as const;

/** The repo card panel. */
export const T_CARD = {
  /** f_030 card edges x 48..671 @720 -> 72..1006, i.e. 934 wide with 72/74px
   *  side margins. 936 is the width that reproduces those margins exactly on
   *  a 1080 frame (72 + 936 + 72 = 1080). */
  width: 936,
  /** f_030 top-left corner: the arc closes ~11px @720 below the top edge,
   *  which after antialiasing is a 24px radius at 1080. */
  radius: 24,
  /** f_030 ink starts at x 136..141 @1080 against a card left edge of 72,
   *  so the horizontal inset is 64-69px; 64 with the glyphs' own left side
   *  bearing lands on the measurement. */
  padX: 64,
  /** f_030 card top 130, GitHub-mark ink top 189 -> 59px; a 58px pad plus
   *  the mark's 1px of antialiasing gives 189 exactly. */
  padY: 58,
  /** f_030 vertical gaps between the header / name / desc / divider / stars
   *  blocks all measure 30px at 1080. */
  gap: 30,
  /**
   * DELIBERATE DEVIATION FROM THE REFERENCE.
   * The reference card sits at y 130..764 (measured 87..509 @720). At that
   * position the "TRENDING #N" label's ink top lands at y 189 — above the
   * y=220 Instagram-crop safe line, so the label can get clipped.
   * We keep the card's internal geometry byte-for-byte and slide the whole
   * panel down 38px: top 168 puts the label ink at y 227 (7px of margin) and
   * the card bottom at ~800, still clear of the caption band at 826.
   */
  top: 168,
} as const;

/** Type inside the card. Sizes are back-solved from measured ink heights. */
export const T_CARD_TYPE = {
  /** f_030 GitHub mark ink 38x40 @1080 (x 136..172, y 189..231); the glyph
   *  box that produces that ink is 44. */
  markSize: 44,
  /** f_030 "TRENDING #1" cap-height 22 @1080 (ink y 200..220) -> 22/0.727 = 30. */
  labelSize: 30,
  /** f_030 "TRENDING #1" glyph advance is 25.5 @1080 ("T" at x 198, "R" at
   *  223.5) against a 30px body, i.e. ~7px of extra tracking = 0.24em. */
  labelTracking: '0.24em',
  /** f_030 gap between the mark's right edge (172) and the "T" ink (198). */
  labelGap: 18,
  /** f_030 "1/3" digit height 21 @1080 -> 21/0.727 = 29; 26 plus its 0.12em
   *  tracking matches the measured 40px total ink width (x 898..938). */
  rankSize: 26,
  rankTracking: '0.12em',
  /** f_030 "usestrix/" x-height 21 @1080 (ink y 270..302 incl. the slash's
   *  overshoot) -> 21/0.55 = 38; 36 in Inter Tight, whose x-height runs a
   *  little tall, reproduces the measured ink. */
  ownerSize: 36,
  /** f_030 gap between the owner baseline and the name's ascender. */
  ownerGap: 6,
  /** f_030 "strix" x-height 63 and i-dot ascender 89 @1080 (ink y 321..411)
   *  -> 63/0.55 = 115 and 89/0.75 = 119. 116 is the value that renders both. */
  nameSize: 116,
  /** f_030 name ink 321..411 spans 90px; at lineHeight 1.02 a 116px body
   *  occupies 118px. Reserved as a FIXED block so that shorter/longer repo
   *  names (which take a smaller size, see nameSizeFor) never change the
   *  card's height — that keeps the safe-zone budget constant. */
  nameBlock: 118,
  nameLineHeight: 1.02,
  nameTracking: '-0.02em',
  /** f_030 desc ink line 1 y 471..502 and line 2 y 518..550: 33px tall
   *  (cap-to-descender = 0.967em -> 34) on a 47px baseline-to-baseline
   *  rhythm -> 33px body at lineHeight 1.42. */
  descSize: 33,
  descLineHeight: 1.42,
  /** The reference desc is always exactly 2 lines (ink x 136..880 @1080).
   *  We reserve 2 lines and clamp, so the card height never grows into the
   *  caption band on repos with long descriptions. */
  descLines: 2,
  /** f_030 star glyph ink 44x40 @1080 (x 141..183, y 639..678); the glyph
   *  box that produces it is 52. */
  starSize: 52,
  /** f_030 gap between the star glyph's right edge and the "3" ink. */
  starGap: 20,
  /** f_030 "35,615" digit height 62 @1080 (ink y 628..690, comma to 700)
   *  -> 62/0.727 = 85; the measured 288px ink width for 5 digits + comma
   *  confirms 88 in Bricolage's wider figures. */
  countSize: 88,
} as const;

/** The green "+N today" chip. */
export const T_CHIP = {
  /** f_030 chip fill bounds y 624..694 @1080 = 72 tall (x 644..944 = 302
   *  wide); 14px of vertical padding around a 32px body gives 72. */
  padY: 14,
  padX: 26,
  /** f_030: magnifying the chip shows a fully-round pill, so radius = h/2. */
  radius: 999,
  /** f_030 "+1,910 today" digit height 24 @1080 -> 24/0.727 = 33. */
  textSize: 32,
  /** f_030 flame ink 21x26 @1080 (x 676..697); glyph box 30. */
  flameSize: 30,
  /** f_030 gap between the flame's right edge and the "+" ink. */
  gap: 12,
} as const;

/** Word captions between the card and the face. Present on EVERY scene. */
export const T_CAPTION = {
  /** Measured across f_014/030/044/058/074/088: the caption baseline is
   *  rock-steady at y 604 @720 -> 906, x-height top y 582 -> 873, descender
   *  bottom y 611 -> 916. A 120px band starting at 826 centres a 56px line
   *  on exactly that baseline. */
  top: 826,
  height: 120,
  /** f_030 caption x-height 33 and ascender 44 @1080 -> 33/0.58 = 57 and
   *  44/0.75 = 59 in Inter Tight. */
  size: 56,
  weight: 700,
  /** f_030 "stars"/"today" ink gap 27 @1080 (x 285 -> 303 @720). */
  gap: 26,
  /** Widest caption measured across the six sampled frames was 842 @1080
   *  (f_058); 900 leaves 90px of margin each side and cues wider than this
   *  are scaled down rather than allowed to touch the frame edge. */
  maxWidth: 900,
  /** Captions sit over the dark ground in the reference, but on the last
   *  ~30px they can overlap footage after the crop moves, so they keep the
   *  reference's black stroke + shadow. */
  stroke: '6px rgba(0, 0, 0, 0.85)',
  shadow: '0 4px 24px rgba(0, 0, 0, 0.7)',
  /** 2-4 words per cue in the reference ("three AI repos", "are blowing up",
   *  "on GitHub today.", "And number two is", "stars today alone."). */
  maxWords: 4,
} as const;

/** Full-frame hook (scene 1) and CTA (last scene) title treatment. */
export const T_TITLE = {
  /** f_090 eyebrow ink y 279..312, cap-height 22 -> 30, tracked like the
   *  card's TRENDING label. */
  eyebrowSize: 30,
  eyebrowTracking: '0.22em',
  /** f_090 "3 AI REPOS" cap-height 93 @1080 (ink y 384..476) -> 93/0.727
   *  = 128; 132 in Bricolage at lineHeight 1.02 renders that ink. */
  hookLine1: 132,
  /** f_090 "BLOWING UP TODAY" cap-height 58 @1080 (ink y 516..573)
   *  -> 58/0.727 = 80. */
  hookLine2: 84,
  /** f_090 purple rule ink y 624..630 (6 tall), x 484..594 (110 wide). */
  ruleW: 110,
  ruleH: 6,
  /** f_1540 "Follow for" / "tomorrow's 3." ascender height 75 @1080
   *  (ink y 280..354 and 387..460) -> 75/0.75 = 100. */
  ctaLine: 100,
  /** f_1540 handle pill 399x87 @1080, fully round, purple with a soft glow;
   *  22/44 padding around a 44px body gives 87 tall. */
  badgeSize: 44,
  badgePadY: 22,
  badgePadX: 44,
  /** f_090/f_1540 vertical rhythm: the stacked blocks are 36-48px apart. */
  gap: 36,
  ctaGap: 48,
} as const;

/**
 * Repo names are usually far longer than the reference's "strix" (5 chars),
 * so the name is set as large as fits the card's text column, capped at the
 * measured 116.
 *
 * The text column is 936 - 2*64 = 808px. The per-character advance was
 * measured off a render: "camofox-browser" (15 chars) at 78px occupies 663px
 * of ink, i.e. 0.567em per character. 0.62em is used here as the working
 * figure so that name-heavy strings (capitals are wider than lowercase)
 * still land inside the column.
 */
const NAME_COLUMN = T_CARD.width - 2 * T_CARD.padX; // 808
const NAME_ADVANCE = 0.62;

export const nameSizeFor = (name: string): number => {
  const fits = Math.floor(NAME_COLUMN / Math.max(name.length, 1) / NAME_ADVANCE);
  // Never below 44 — past that a name is better wrapped than shrunk, and the
  // fixed name block (see T_CARD_TYPE.nameBlock) centres whatever it gets.
  return Math.max(Math.min(T_CARD_TYPE.nameSize, fits), 44);
};

/**
 * The reference descriptions are short enough to set at 33px on two lines.
 * Longer ones step down so more of the sentence survives the 2-line clamp.
 */
export const descSizeFor = (desc: string): number => {
  const n = desc.length;
  if (n <= 110) return T_CARD_TYPE.descSize; // the measured case
  if (n <= 150) return 30;
  return 28;
};
