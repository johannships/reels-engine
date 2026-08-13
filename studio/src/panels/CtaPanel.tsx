import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLORS, FONTS} from './../theme';
import {PanelShell} from './PanelShell';

export const CtaPanel: React.FC<{
  durationInFrames: number;
  /** Two display lines; second line renders violet. Defaults keep the
   * standard "Follow for tomorrow's 3." close. */
  line1?: string;
  line2?: string;
  badge?: string;
}> = ({
  durationInFrames,
  line1 = 'Follow for',
  line2 = 'tomorrow’s drop.',
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
    <PanelShell durationInFrames={durationInFrames}>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 48,
          textAlign: 'center',
        }}
      >
        <div
          style={{
            fontFamily: FONTS.display,
            fontWeight: 800,
            fontSize: 100,
            lineHeight: 1.06,
            letterSpacing: '-0.02em',
            color: COLORS.text,
            opacity: interpolate(headlineIn, [0, 0.6], [0, 1], {
              extrapolateRight: 'clamp',
            }),
            transform: `translateY(${(1 - headlineIn) * 44}px)`,
          }}
        >
          {line1}
          <br />
          <span style={{color: COLORS.violetLight}}>{line2}</span>
        </div>

        <div
          style={{
            padding: '22px 44px',
            borderRadius: 999,
            background: COLORS.violet,
            boxShadow: '0 18px 60px rgba(139, 92, 246, 0.45)',
            fontFamily: FONTS.body,
            fontWeight: 700,
            fontSize: 44,
            color: COLORS.text,
            opacity: interpolate(handleIn, [0, 0.5], [0, 1], {
              extrapolateRight: 'clamp',
            }),
            transform: `scale(${0.7 + handleIn * 0.3})`,
          }}
        >
          {badge}
        </div>
      </div>
    </PanelShell>
  );
};
