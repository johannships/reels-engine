import React from 'react';
import {Easing, interpolate, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLORS, LAYOUT} from './../theme';

const ENTER_FRAMES = 8; // ~267ms at 30fps
const EXIT_FRAMES = 7; // ~233ms at 30fps

/**
 * Full-bleed panel background (ground + subtle violet radial glow) with a
 * quick slide+fade transition on the content. Must be rendered inside a
 * <Sequence> so useCurrentFrame() is scene-local.
 */
export const PanelShell: React.FC<{
  durationInFrames: number;
  children: React.ReactNode;
}> = ({durationInFrames, children}) => {
  const frame = useCurrentFrame();
  useVideoConfig();

  const enter = interpolate(frame, [0, ENTER_FRAMES], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: Easing.out(Easing.cubic),
  });
  const exit = interpolate(
    frame,
    [durationInFrames - EXIT_FRAMES, durationInFrames],
    [1, 0],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.in(Easing.cubic),
    },
  );

  const opacity = Math.min(enter, exit);
  const translateX = (1 - enter) * 64 - (1 - exit) * 48;

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background: COLORS.ground,
        overflow: 'hidden',
      }}
    >
      {/* Subtle violet radial glow on the ground */}
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(90% 60% at 50% 26%, rgba(139, 92, 246, 0.14), rgba(139, 92, 246, 0.04) 55%, transparent 75%)',
          opacity,
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          // Keep panel content clear of the caption band at y ~900.
          padding: '64px 72px 130px',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          opacity,
          transform: `translateX(${translateX}px)`,
        }}
      >
        {children}
      </div>
    </div>
  );
};

export const LAYOUT_CANVAS = LAYOUT;
