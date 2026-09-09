import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Shell} from './Shell';
import {T_COLORS, T_FONTS, T_TITLE} from './theme';

/**
 * Last scene: card-less. Two display lines (second in the accent colour) and
 * the handle pill — plus the captions, which the composition draws over
 * every scene.
 *
 * Reference (f_1540, t 51.3s): "Follow for" ink y 280..354 white,
 * "tomorrow's 3." ink y 387..460 violet, handle pill 399x87 centred on
 * x 540 at y 570..656 with a violet glow.
 */
export const TrendingCta: React.FC<{
  durationInFrames: number;
  line1?: string;
  line2?: string;
  badge?: string;
}> = ({
  durationInFrames,
  line1 = 'Follow for',
  line2 = "tomorrow's 3.",
  badge = '@you',
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();

  const headlineIn = spring({
    frame: frame - 2,
    fps,
    config: {damping: 16, stiffness: 140},
  });
  const handleIn = spring({
    frame: frame - 12,
    fps,
    config: {damping: 12, stiffness: 170},
  });

  return (
    <Shell durationInFrames={durationInFrames}>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: T_TITLE.ctaGap,
          textAlign: 'center',
        }}
      >
        <div
          style={{
            fontFamily: T_FONTS.display,
            fontWeight: 800,
            fontSize: T_TITLE.ctaLine,
            lineHeight: 1.06,
            letterSpacing: '-0.02em',
            color: T_COLORS.text,
            opacity: interpolate(headlineIn, [0, 0.6], [0, 1], {
              extrapolateRight: 'clamp',
            }),
            transform: `translateY(${(1 - headlineIn) * 44}px)`,
          }}
        >
          {line1}
          <br />
          <span style={{color: T_COLORS.violetLight}}>{line2}</span>
        </div>

        <div
          style={{
            padding: `${T_TITLE.badgePadY}px ${T_TITLE.badgePadX}px`,
            borderRadius: 999,
            background: T_COLORS.violet,
            boxShadow: '0 18px 60px rgba(139, 92, 246, 0.45)',
            fontFamily: T_FONTS.body,
            fontWeight: 700,
            fontSize: T_TITLE.badgeSize,
            color: T_COLORS.text,
            whiteSpace: 'nowrap',
            opacity: interpolate(handleIn, [0, 0.5], [0, 1], {
              extrapolateRight: 'clamp',
            }),
            transform: `scale(${0.7 + handleIn * 0.3})`,
          }}
        >
          {badge}
        </div>
      </div>
    </Shell>
  );
};
