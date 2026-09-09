import React from 'react';
import {Easing, interpolate, useCurrentFrame} from 'remotion';
import {T_COLORS, T_LAYOUT} from './theme';

const ENTER_FRAMES = 8; // ~267ms at 30fps
const EXIT_FRAMES = 7; // ~233ms at 30fps

/**
 * The dark ground every Trending scene is drawn on, plus the scene's
 * slide+fade transition.
 *
 * The glow is measured: in f_030 the top of the frame reads rgb(17,14,25) at
 * x 420 (centre) and rgb(12,11,16) at x 20 (edge), and the ground darkens to
 * rgb(8,8,10) by y 600 — i.e. a soft violet radial centred near the top
 * middle, fading out well before the seam.
 *
 * Must be rendered inside a <Sequence> so useCurrentFrame() is scene-local.
 */
export const Shell: React.FC<{
  durationInFrames: number;
  /** `false` for the repo card, which is absolutely positioned instead. */
  center?: boolean;
  children: React.ReactNode;
}> = ({durationInFrames, center = true, children}) => {
  const frame = useCurrentFrame();

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
        background: T_COLORS.ground,
        overflow: 'hidden',
      }}
    >
      {/* Violet radial glow — see the measurement note above. */}
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
          left: 0,
          top: 0,
          width: T_LAYOUT.width,
          height: T_LAYOUT.seam,
          boxSizing: 'border-box',
          opacity,
          transform: `translateX(${translateX}px)`,
          // `center` reproduces the reference's hook/CTA framing: the block
          // is centred in the graphic region inside a 64/72/130 pad, which
          // is what puts the hook eyebrow ink at y 279 and line 1 at y 384.
          // The repo card instead positions itself absolutely (T_CARD.top),
          // so its geometry is fixed rather than content-dependent.
          ...(center
            ? {
                padding: '64px 72px 130px',
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
              }
            : null),
        }}
      >
        {children}
      </div>
    </div>
  );
};
