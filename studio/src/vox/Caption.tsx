import React from 'react';
import {useCurrentFrame} from 'remotion';
import {CUES, FPS, INK, YELLOW} from './data';
import {FONT} from './fonts';
import {ease} from './kit';

// Highlight onsets: the frame the highlighted word is actually spoken, taken
// from words.json. Keyed by cue `from`. Where absent, the highlight wipes in
// at the cue start (the cue already begins on that word).
const HI_AT: Record<string, number> = {
  '0': 0.54, // killed
  '1.16': 2.16, // entirely
  '3.79': 3.95, // graphics
  '4.68': 4.86, // made
  '9.74': 10.04, // entirely
  '11.12': 11.68, // amazing
  '13.95': 14.15, // Hyperframes
  '25.16': 25.59, // EDIT
  '26.65': 27.02, // DMs
};

const FS = 62;

const Seg: React.FC<{text: string; hi: boolean; p: number}> = ({text, hi, p}) => {
  if (!hi) return <span style={{whiteSpace: 'pre'}}>{text}</span>;
  return (
    <span style={{position: 'relative', display: 'inline-block'}}>
      <span style={{visibility: 'hidden', whiteSpace: 'pre'}}>{text}</span>
      <span
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          right: 0,
          bottom: 0,
          whiteSpace: 'pre',
          color: '#fff',
        }}
      >
        {text}
      </span>
      <span
        style={{
          position: 'absolute',
          left: -11,
          top: -5,
          right: -11,
          bottom: -5,
          padding: '5px 11px',
          background: YELLOW,
          color: INK,
          whiteSpace: 'pre',
          clipPath: `inset(0 ${(1 - p) * 100}% 0 0)`,
        }}
      >
        {text}
      </span>
    </span>
  );
};

export const Caption: React.FC = () => {
  const frame = useCurrentFrame();
  const t = frame / FPS;
  const cue = CUES.find((c) => t >= c.from && t < c.to);
  if (!cue) return null;

  const start = Math.round(cue.from * FPS);
  const hiSec = HI_AT[String(cue.from)] ?? cue.from;
  const wipe = ease(frame, Math.round(hiSec * FPS), 6);
  const inT = start === 0 ? 1 : ease(frame, start, 3);

  const parts = cue.text.split(/(\{[^}]*\})/).filter(Boolean);

  return (
    <div
      style={{
        position: 'absolute',
        left: 70,
        right: 70,
        bottom: 320,
        textAlign: 'center',
        fontFamily: FONT,
        fontWeight: 700,
        fontSize: FS,
        lineHeight: 1.18,
        color: '#fff',
        letterSpacing: '-0.012em',
        textShadow:
          '0 2px 4px rgba(0,0,0,0.75), 0 6px 22px rgba(0,0,0,0.66), 0 0 2px rgba(0,0,0,0.9)',
        opacity: inT,
      }}
    >
      {parts.map((p, i) =>
        p.startsWith('{') ? (
          <Seg key={i} text={p.slice(1, -1)} hi p={wipe} />
        ) : (
          <Seg key={i} text={p} hi={false} p={1} />
        ),
      )}
    </div>
  );
};
