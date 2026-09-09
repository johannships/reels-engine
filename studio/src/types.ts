export type IntroScene = {
  type: 'intro';
  durationSec: number;
  text: string;
  /** On-screen overrides (defaults: GITHUB eyebrow, "3 AI REPOS / BLOWING UP TODAY") */
  eyebrow?: string;
  line1?: string;
  line2?: string;
  /** Brand mark badge above the headline: claude|deepseek|github|microsoft|yc */
  logo?: string;
  /** Optional second badge, rendered as "logo × logo2" */
  logo2?: string;
  showGithub?: boolean;
};

export type RepoScene = {
  type: 'repo';
  durationSec: number;
  repo: string;
  stars: number;
  today: number;
  desc: string;
  text: string;
};

export type CtaScene = {
  type: 'cta';
  durationSec: number;
  text: string;
  /** Optional on-screen overrides (defaults: Follow for / tomorrow's 3. / @you) */
  line1?: string;
  line2?: string;
  badge?: string;
};

export type TopicScene = {
  type: 'topic';
  durationSec: number;
  name: string; // topic display name, e.g. "Gemini 3.5 Pro"
  desc: string;
  stat: number; // headline number for the count-up
  statLabel: string; // e.g. "points on Hacker News today"
  pill: string; // e.g. "#1 on r/LocalLLaMA"
  text: string;
};

export type ShotScene = {
  type: 'shot';
  durationSec: number;
  image: string; // data URI (prep.py injects from <episode>/shot.jpg)
  label: string; // source pill, e.g. "github.com/usestrix/strix"
  text: string;
};

export type AvatarScene = {
  type: 'avatar'; // fullscreen talking head — the graphics layer renders
  durationSec: number; // nothing except the optional kinetic text overlay
  text: string;
  /** 3-6 word scroll-stopper punched in over the footage (first ~2.6s) */
  overlayText?: string;
};

export type KineticScene = {
  type: 'kinetic'; // full-frame animated typography (guaranteed visual floor)
  durationSec: number;
  keyText: string;
  text: string;
};

export type IsenScene = {
  type: 'isen'; // premium Isenberg-style motion panel (paper + pills + serif)
  text: string;
  variant: 'levels' | 'faceoff' | 'orgchart';
  half?: boolean; // 50/50 split: panel on top, avatar visible below
  title: string; // *word* marks the coral italic accent
  subtitle?: string;
  doc?: string; // faceoff: document quote, *bold-highlight* markers
  counter?: number; // orgchart: dollar counter target
  items?: {label: string; note?: string; struck?: boolean}[];
  durationSec: number;
};

export type Scene =
  | IntroScene
  | RepoScene
  | TopicScene
  | ShotScene
  | AvatarScene
  | KineticScene
  | IsenScene
  | CtaScene;

export type EpisodeProps = {
  date: string;
  scenes: Scene[];
  /**
   * Optional path/URL of the HeyGen avatar MP4 (1920x1080).
   * When provided it is cropped/scaled to fill the bottom 1080x960 slot.
   */
  avatarSrc?: string;
  /** Source video dimensions (default 1920x1080 landscape). */
  avatarW?: number;
  avatarH?: number;
  /**
   * Vertical focus point of the crop as a fraction of source height (0 = top,
   * 1 = bottom). The crop window is centered on this point. Default 0.5.
   */
  avatarFocusY?: number;
  /**
   * Leave the avatar zone transparent (for ffmpeg compositing) instead of
   * playing the video in the browser. Render with ProRes 4444 + PNG frames.
   */
  avatarTransparent?: boolean;
  /**
   * "split" (default): graphics top 960 / avatar bottom 960.
   * "fullscreen": full-frame scenes — avatar scenes are fully transparent
   * (the real footage shows through), graphic scenes paint the whole frame,
   * captions sit lower-third. Render with ProRes 4444.
   */
  layout?: 'split' | 'fullscreen';
  /**
   * Optional real word timings (e.g. from Whisper), absolute ms from video
   * start. When omitted, placeholder timings are derived from scene text.
   */
  captions?: KaraokeWord[];
  /**
   * Extra caption words to render in the accent colour (Trending style).
   * Numbers, repo names and money words are detected automatically — this is
   * only for words a specific episode wants to punch that the rules miss.
   */
  accentWords?: string[];
};

export type KaraokeWord = {
  word: string;
  startMs: number;
  endMs: number;
};
