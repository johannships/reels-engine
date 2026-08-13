import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLORS, FONTS} from './../theme';
import type {KineticScene} from './../types';
import {PanelShell} from './PanelShell';

/**
 * Full-frame kinetic typography — the guaranteed visual floor when no
 * screenshot or real stat exists. The beat's key phrase punches in word by
 * word, huge, on the brand ground. Never lets a scene be visually empty.
 */
export const KineticPanel: React.FC<{
  scene: KineticScene;
  durationInFrames: number;
}> = ({scene, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const words = scene.keyText.trim().toUpperCase().split(/\s+/).slice(0, 8);
  const total = words.join(' ').length;
  const size = total <= 14 ? 150 : total <= 24 ? 118 : 92;
  return (
    <PanelShell durationInFrames={durationInFrames}>
      <div
        style={{
          display: 'flex',
          flexWrap: 'wrap',
          justifyContent: 'center',
          alignContent: 'center',
          columnGap: 30,
          rowGap: 10,
          padding: '0 40px',
          textAlign: 'center',
        }}
      >
        {words.map((w, i) => {
          const p = spring({frame: frame - 3 - i * 4, fps, config: {damping: 13, stiffness: 170}});
          const violet = i % 3 === 2;
          return (
            <span
              key={i}
              style={{
                fontFamily: FONTS.display,
                fontWeight: 800,
                fontSize: size,
                lineHeight: 1.02,
                letterSpacing: '-0.02em',
                color: violet ? COLORS.violetLight : COLORS.text,
                opacity: interpolate(p, [0, 0.4], [0, 1], {extrapolateRight: 'clamp'}),
                transform: `translateY(${(1 - p) * 46}px) scale(${0.7 + p * 0.3})`,
              }}
            >
              {w}
            </span>
          );
        })}
      </div>
    </PanelShell>
  );
};
