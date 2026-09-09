import React, {useMemo} from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {groupIntoLines} from '../captions';
import type {KaraokeWord} from '../types';
import {accentFlags, type AccentTest} from './accents';
import {T_CAPTION, T_COLORS, T_FONTS, T_LAYOUT} from './theme';

/**
 * Average glyph advance for Inter Tight at weight 700, as a fraction of the
 * font size. Derived from the reference: the cue "stars today alone."
 * (16 non-space glyphs, 2 word gaps) measures 477px of ink at 1080, so
 * (477 - 2*26) / 16 / 56 = 0.474em.
 *
 * Used only to detect a cue that would overflow the frame, so it can be
 * scaled down instead of running off the edge.
 */
const AVG_ADVANCE = 0.474;

const estimateWidth = (words: string[]) => {
  const glyphs = words.join('').length;
  return (
    glyphs * AVG_ADVANCE * T_CAPTION.size +
    Math.max(words.length - 1, 0) * T_CAPTION.gap
  );
};

type Cue = {
  words: KaraokeWord[];
  startMs: number;
  /** Cues hold until the next one starts, so the caption never blinks out
   *  during a pause — the reference has words on screen throughout. */
  holdMs: number;
};

/**
 * Word captions in the band between the card and the face.
 *
 * Reference geometry (measured across f_014/030/044/058/074/088): baseline
 * pinned at y 906, ink 873..916, centred on x 540, 2-4 words per cue, white
 * bold with the sentence-carrying words in violet.
 *
 * Rendered OUTSIDE the per-scene sequences with absolute word timings, which
 * is what puts captions on every scene including the hook and the CTA.
 */
export const Captions: React.FC<{
  words: KaraokeWord[];
  accent: AccentTest;
}> = ({words, accent}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const nowMs = (frame / fps) * 1000;

  const cues = useMemo<Cue[]>(() => {
    const lines = groupIntoLines(words, T_CAPTION.maxWords).filter(
      (l) => l.length > 0,
    );
    return lines.map((line, i) => ({
      words: line,
      startMs: line[0].startMs,
      holdMs: lines[i + 1]?.[0].startMs ?? line[line.length - 1].endMs + 600,
    }));
  }, [words]);

  const cue = cues.find((c) => nowMs >= c.startMs && nowMs < c.holdMs);
  if (!cue) return null;

  const tokens = cue.words.map((w) => w.word);
  const flags = accentFlags(tokens, accent);
  const estimated = estimateWidth(tokens);
  const scale = Math.min(1, T_CAPTION.maxWidth / Math.max(estimated, 1));

  return (
    <div
      style={{
        position: 'absolute',
        top: T_CAPTION.top,
        left: 0,
        width: T_LAYOUT.width,
        height: T_CAPTION.height,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 20,
        pointerEvents: 'none',
      }}
    >
      <div
        style={{
          display: 'flex',
          gap: T_CAPTION.gap,
          flexWrap: 'nowrap',
          whiteSpace: 'nowrap',
          fontFamily: T_FONTS.body,
          fontWeight: T_CAPTION.weight,
          fontSize: T_CAPTION.size,
          lineHeight: 1,
          letterSpacing: '-0.01em',
          transform: `scale(${scale})`,
        }}
      >
        {tokens.map((token, i) => (
          <span
            key={`${cue.startMs}-${i}`}
            style={{
              color: flags[i] ? T_COLORS.violetLight : T_COLORS.text,
              WebkitTextStroke: T_CAPTION.stroke,
              paintOrder: 'stroke fill',
              textShadow: T_CAPTION.shadow,
            }}
          >
            {token}
          </span>
        ))}
      </div>
    </div>
  );
};
