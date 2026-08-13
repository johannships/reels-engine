import React, {useMemo} from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {groupIntoLines} from './captions';
import {COLORS, FONTS, LAYOUT} from './theme';
import type {KaraokeWord} from './types';

/**
 * Word-by-word karaoke captions. Sits on the seam between the visual canvas
 * and the avatar slot. Shows one line (3-4 words) at a time; the word being
 * spoken is highlighted in violet-light.
 */
export const Karaoke: React.FC<{words: KaraokeWord[]; top?: number}> = ({words, top}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const nowMs = (frame / fps) * 1000;

  const lines = useMemo(() => groupIntoLines(words, 4), [words]);

  const activeLine = lines.find(
    (line) => nowMs >= line[0].startMs && nowMs < line[line.length - 1].endMs,
  );

  return (
    <div
      style={{
        position: 'absolute',
        top: top ?? LAYOUT.captionTop,
        left: 0,
        width: LAYOUT.width,
        height: LAYOUT.captionHeight,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 20,
        pointerEvents: 'none',
      }}
    >
      {activeLine ? (
        <div
          style={{
            display: 'flex',
            gap: 26,
            flexWrap: 'nowrap',
            whiteSpace: 'nowrap',
            fontFamily: FONTS.body,
            fontWeight: 700,
            fontSize: 56,
            lineHeight: 1,
            letterSpacing: '-0.01em',
          }}
        >
          {activeLine.map((w, i) => {
            const active = nowMs >= w.startMs && nowMs < w.endMs;
            return (
              <span
                key={`${w.startMs}-${i}`}
                style={{
                  color: active ? COLORS.violetLight : COLORS.text,
                  transform: active ? 'scale(1.03)' : 'scale(1)',
                  transformOrigin: 'center bottom',
                  WebkitTextStroke: '6px rgba(0, 0, 0, 0.85)',
                  paintOrder: 'stroke fill',
                  textShadow: '0 4px 24px rgba(0, 0, 0, 0.7)',
                }}
              >
                {w.word}
              </span>
            );
          })}
        </div>
      ) : null}
    </div>
  );
};
