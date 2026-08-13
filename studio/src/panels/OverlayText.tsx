import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLORS, FONTS} from './../theme';

/**
 * Big kinetic text OVER the fullscreen avatar — the scroll-stopper. Words
 * punch in one by one (top third of frame), hold, then fade out so the
 * face carries the rest of the scene. `accent` marks which word renders
 * violet (default: last word).
 */
export const OverlayText: React.FC<{
  text: string;
  durationInFrames: number;
  holdSec?: number;
}> = ({text, durationInFrames, holdSec = 2.6}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = text.trim().toUpperCase().split(/\s+/).slice(0, 6);
  const holdFrames = Math.min(Math.round(holdSec * fps), durationInFrames - 6);
  const out = interpolate(frame, [holdFrames - 6, holdFrames], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  if (out <= 0) return null;
  const size = words.join(' ').length <= 12 ? 128 : words.join(' ').length <= 20 ? 104 : 84;
  return (
    <div
      style={{
        position: 'absolute',
        top: 210,
        left: 0,
        width: 1080,
        padding: '0 60px',
        display: 'flex',
        flexWrap: 'wrap',
        justifyContent: 'center',
        columnGap: 26,
        rowGap: 4,
        opacity: out,
      }}
    >
      {words.map((w, i) => {
        const p = spring({frame: frame - i * 2, fps, config: {damping: 12, stiffness: 240}});
        const violet = i === words.length - 1;
        return (
          <span
            key={i}
            style={{
              fontFamily: FONTS.display,
              fontWeight: 800,
              fontSize: size,
              lineHeight: 1.04,
              letterSpacing: '-0.02em',
              color: violet ? COLORS.violetLight : COLORS.text,
              opacity: interpolate(p, [0, 0.4], [0, 1], {extrapolateRight: 'clamp'}),
              transform: `scale(${0.5 + p * 0.5}) translateY(${(1 - p) * 20}px)`,
              textShadow:
                '0 4px 30px rgba(0,0,0,0.85), 0 1px 3px rgba(0,0,0,0.9)',
              whiteSpace: 'nowrap',
            }}
          >
            {w}
          </span>
        );
      })}
    </div>
  );
};
