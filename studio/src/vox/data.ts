// All timings are seconds, taken from Whisper word onsets in
// /Users/johannsathianathen/reels/dji-vox/words.json. Nothing here is guessed.
// Caption TEXT is the corrected script (Whisper mis-heard Claude/Codex/ChatGPT).

export const FPS = 30;
export const W = 1080;
export const H = 1920;
export const DUR_S = 976 / 30; // 32.5333s — matches base30.mp4 exactly
export const YELLOW = '#F5E11B';

// Star counts, verified against the GitHub API on the render date. These appear
// in three places (s5b receipt bars, s8 burst receipt/badge, s8 stats chip) and
// must never diverge - read them from here, never retype a literal.
export const STARS = {remotion: 58699, hyperframes: 48191};
export const INK = '#111111';

export const s = (sec: number) => Math.round(sec * FPS);

// ---------------------------------------------------------------- safe zone
export const SAFE = {top: 220, bottom: 1620, left: 60, right: 1020};

// ---------------------------------------------------------------- shots
export type ShotKind =
  | 'full'
  | 'montageA'
  | 'montageB'
  | 'montageC'
  | 'sites'
  | 'guide'
  | 'pip'
  | 'burst';

export type Shot = {
  id: string;
  kind: ShotKind;
  from: number;
  to: number;
  // talking-head punch-in: scale about origin, in source px
  scale?: number;
  ox?: number;
  oy?: number;
};

export const SHOTS: Shot[] = [
  {id: 's1a', kind: 'full', from: 0.0, to: 0.54, scale: 1.0, ox: 560, oy: 880},
  {id: 's1b', kind: 'full', from: 0.54, to: 2.9, scale: 1.07, ox: 560, oy: 880},
  {id: 's2a', kind: 'montageA', from: 2.9, to: 4.62},
  {id: 's2b', kind: 'montageB', from: 4.62, to: 6.03},
  {id: 's2c', kind: 'montageC', from: 6.03, to: 7.63},
  {id: 's3', kind: 'full', from: 7.63, to: 8.88, scale: 1.09, ox: 490, oy: 860},
  {id: 's4a', kind: 'full', from: 8.88, to: 10.73, scale: 1.03, ox: 520, oy: 880},
  {id: 's4b', kind: 'full', from: 10.73, to: 11.62, scale: 1.1, ox: 520, oy: 880},
  {id: 's5a', kind: 'full', from: 11.62, to: 13.42, scale: 1.045, ox: 545, oy: 890},
  {id: 's5b', kind: 'sites', from: 13.42, to: 15.2},
  {id: 's6a', kind: 'guide', from: 15.2, to: 19.55, scale: 1.05, ox: 520, oy: 860},
  {id: 's6b', kind: 'pip', from: 19.55, to: 23.86},
  {id: 's7a', kind: 'full', from: 23.86, to: 25.16, scale: 1.0, ox: 520, oy: 880},
  {id: 's7b', kind: 'full', from: 25.16, to: 28.24, scale: 1.06, ox: 520, oy: 880},
  {id: 's8', kind: 'burst', from: 28.24, to: 30.05},
  {id: 's9a', kind: 'full', from: 30.05, to: 30.93, scale: 1.02, ox: 560, oy: 780},
  {id: 's9b', kind: 'full', from: 30.93, to: DUR_S, scale: 1.08, ox: 560, oy: 780},
];

// ---------------------------------------------------------------- captions
// {curly} marks the highlighter box. Text is the corrected script.
export type Cue = {from: number; to: number; text: string};

export const CUES: Cue[] = [
  {from: 0.0, to: 1.16, text: 'AI just {killed}'},
  {from: 1.16, to: 2.9, text: 'video editors {entirely}'},
  {from: 2.9, to: 3.79, text: 'As you see,'},
  {from: 3.79, to: 4.68, text: 'all these {graphics} on screen'},
  {from: 4.68, to: 6.03, text: 'are {made with AI}'},
  {from: 6.03, to: 6.94, text: '{100% automated}'},
  {from: 6.94, to: 7.63, text: 'no editor'},
  {from: 7.63, to: 8.88, text: 'touched this video'},
  {from: 8.88, to: 9.74, text: 'And you can get this'},
  {from: 9.74, to: 11.12, text: 'done {entirely for free}'},
  {from: 11.12, to: 12.17, text: 'using two {amazing}'},
  {from: 12.17, to: 13.42, text: "software, it's called"},
  {from: 13.42, to: 13.95, text: '{Remotion}'},
  {from: 13.95, to: 15.12, text: 'and {Hyperframes}'},
  {from: 15.12, to: 15.75, text: 'If you want the'},
  {from: 15.75, to: 16.42, text: '{full guide}'},
  {from: 16.42, to: 17.04, text: 'I made it a'},
  {from: 17.04, to: 17.8, text: '{breakdown}'},
  {from: 17.8, to: 18.58, text: 'so that you can get it'},
  {from: 18.58, to: 19.55, text: 'set up with any'},
  {from: 19.55, to: 20.29, text: '{AI agent}'},
  {from: 20.29, to: 21.17, text: '{Claude Code}'},
  {from: 21.17, to: 21.7, text: '{Codex}'},
  {from: 21.7, to: 22.44, text: '{ChatGPT}'},
  {from: 22.44, to: 22.72, text: '{Claude}'},
  {from: 22.72, to: 23.86, text: 'whatever it might be'},
  {from: 23.86, to: 25.16, text: 'And all you have to do is'},
  {from: 25.16, to: 25.92, text: 'comment {EDIT}'},
  {from: 25.92, to: 26.65, text: "and I'll send it"},
  {from: 26.65, to: 27.15, text: 'to your {DMs}'},
  {from: 27.15, to: 28.24, text: '{entirely for free}'},
  {from: 28.24, to: 28.84, text: 'so you can have'},
  {from: 28.84, to: 29.6, text: '{amazing graphics}'},
  {from: 29.6, to: 30.15, text: '{like this}'},
  {from: 30.15, to: 30.93, text: 'without having an'},
  {from: 30.93, to: 31.26, text: '{editor}'},
  {from: 31.26, to: DUR_S, text: 'ever touch your videos'},
];

// ---------------------------------------------------------------- beats
export const BEATS = {
  nameIn: 0.6,
  nameOut: 2.80,
  stat100: 6.03,
  stat0: 6.94,
  remotionCard: 13.42,
  hyperframesCard: 14.15,
  guideHeader: 15.2,
  slotsIn: 19.55,
  chips: [20.29, 21.17, 21.7, 22.44],
  pillIn: 25.59, // "edit"
  guideCard: 15.75, // "full"
  burstIn: 28.35,
  burstOut: 29.5,
  endCard: 31.2,
};

// Measured hand position during "graphics like this" (facedet picked the hand
// up as a box at t=29.20: x 621-1057, y 1128-1644 -> centre 839,1386; the
// gridded frame at 28.3s reads ~765,1409). Burst origin:
export const HAND = {x: 812, y: 1372};

// Right-hand clear column for the burst elements. Face right edge over
// 28.32-29.42 maxes at 680px (measured every 0.1s), so x >= 705 never touches
// the head; x <= 1020 keeps it inside the platform safe zone.
export const BURST_COL = {left: 705, right: 1015};
