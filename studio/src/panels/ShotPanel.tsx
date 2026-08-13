import React from 'react';
import {Img, interpolate, useCurrentFrame} from 'remotion';
import {COLORS, FONTS} from './../theme';
import type {ShotScene} from './../types';
import {PanelShell} from './PanelShell';

/**
 * Full-bleed screenshot with a slow Ken Burns push — the "high-quality
 * real screenshot" ingredient (Nate Herk format). Image arrives as a data
 * URI in props (prep.py injects it from <episode>/shot.jpg).
 */
export const ShotPanel: React.FC<{
  scene: ShotScene;
  durationInFrames: number;
}> = ({scene, durationInFrames}) => {
  const frame = useCurrentFrame();
  const zoom = interpolate(frame, [0, durationInFrames], [1.0, 1.09]);
  const drift = interpolate(frame, [0, durationInFrames], [0, -26]);

  return (
    <PanelShell durationInFrames={durationInFrames}>
      <div
        style={{
          position: 'absolute',
          inset: 0,
          overflow: 'hidden',
          background: COLORS.ground,
        }}
      >
        <Img
          src={scene.image}
          style={{
            position: 'absolute',
            top: 0,
            left: '50%',
            width: 1080,
            transform: `translateX(-50%) translateY(${drift}px) scale(${zoom})`,
            transformOrigin: 'top center',
          }}
        />
        {/* legibility gradient + source pill */}
        <div
          style={{
            position: 'absolute',
            left: 0,
            right: 0,
            bottom: 0,
            height: 300,
            background:
              'linear-gradient(to bottom, rgba(10,10,13,0), rgba(10,10,13,0.92))',
          }}
        />
        <div
          style={{
            position: 'absolute',
            left: 48,
            top: 40,
            display: 'flex',
            alignItems: 'center',
            gap: 14,
            padding: '12px 24px',
            borderRadius: 999,
            background: 'rgba(20, 19, 24, 0.85)',
            border: `1px solid ${COLORS.border}`,
          }}
        >
          <span
            style={{
              width: 12,
              height: 12,
              borderRadius: 99,
              background: COLORS.green,
            }}
          />
          <span
            style={{
              fontFamily: FONTS.body,
              fontWeight: 600,
              fontSize: 26,
              color: COLORS.text,
              letterSpacing: '0.02em',
            }}
          >
            {scene.label}
          </span>
        </div>
      </div>
    </PanelShell>
  );
};
