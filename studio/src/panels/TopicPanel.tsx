import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLORS, FONTS} from './../theme';
import type {TopicScene} from './../types';
import {FlameGlyph} from './glyphs';
import {PanelShell} from './PanelShell';

const numberFmt = new Intl.NumberFormat('en-US');

const StatCount: React.FC<{target: number}> = ({target}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const progress = spring({
    frame: frame - 8,
    fps,
    durationInFrames: 50,
    config: {damping: 200},
  });
  return (
    <span
      style={{
        fontFamily: FONTS.display,
        fontWeight: 800,
        fontSize: 88,
        lineHeight: 1,
        color: COLORS.text,
        fontVariantNumeric: 'tabular-nums',
        fontFeatureSettings: '"tnum"',
        letterSpacing: '-0.01em',
      }}
    >
      {numberFmt.format(Math.round(progress * target))}
    </span>
  );
};

const nameFontSize = (name: string) => {
  if (name.length <= 12) return 108;
  if (name.length <= 18) return 84;
  if (name.length <= 26) return 66;
  return 54;
};

/** News-style stat card for the daily "topic of the day" deep-dive. */
export const TopicPanel: React.FC<{
  scene: TopicScene;
  durationInFrames: number;
}> = ({scene, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const cardIn = spring({frame: frame - 2, fps, config: {damping: 18, stiffness: 130}});
  const pillIn = spring({frame: frame - 22, fps, config: {damping: 13, stiffness: 160}});

  return (
    <PanelShell durationInFrames={durationInFrames}>
      <div
        style={{
          width: 936,
          background: COLORS.card,
          border: `1px solid ${COLORS.border}`,
          borderRadius: 24,
          padding: '58px 64px',
          display: 'flex',
          flexDirection: 'column',
          gap: 30,
          boxShadow: '0 40px 90px rgba(0, 0, 0, 0.5)',
          opacity: interpolate(cardIn, [0, 0.5], [0, 1], {extrapolateRight: 'clamp'}),
          transform: `translateY(${(1 - cardIn) * 36}px)`,
        }}
      >
        <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
          <FlameGlyph size={40} color={COLORS.violetLight} />
          <span
            style={{
              fontFamily: FONTS.body,
              fontWeight: 600,
              fontSize: 28,
              letterSpacing: '0.24em',
              color: COLORS.violetLight,
            }}
          >
            TRENDING TODAY
          </span>
        </div>

        <span
          style={{
            fontFamily: FONTS.display,
            fontWeight: 800,
            fontSize: nameFontSize(scene.name),
            lineHeight: 1.04,
            color: COLORS.text,
            letterSpacing: '-0.02em',
            overflowWrap: 'anywhere',
          }}
        >
          {scene.name}
        </span>

        <p
          style={{
            margin: 0,
            fontFamily: FONTS.body,
            fontWeight: 500,
            fontSize: 33,
            lineHeight: 1.42,
            color: COLORS.muted,
          }}
        >
          {scene.desc}
        </p>

        <div style={{height: 1, background: COLORS.border}} />

        <div
          style={{
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'space-between',
            gap: 24,
          }}
        >
          <div style={{display: 'flex', flexDirection: 'column', gap: 10}}>
            <StatCount target={scene.stat} />
            <span
              style={{
                fontFamily: FONTS.body,
                fontWeight: 600,
                fontSize: 28,
                color: COLORS.muted,
                letterSpacing: '0.04em',
              }}
            >
              {scene.statLabel}
            </span>
          </div>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 12,
              padding: '14px 26px',
              borderRadius: 999,
              background: 'rgba(103, 210, 67, 0.12)',
              border: '1px solid rgba(103, 210, 67, 0.4)',
              opacity: interpolate(pillIn, [0, 0.5], [0, 1], {extrapolateRight: 'clamp'}),
              transform: `scale(${0.7 + pillIn * 0.3})`,
            }}
          >
            <FlameGlyph size={30} color={COLORS.green} />
            <span
              style={{
                fontFamily: FONTS.body,
                fontWeight: 700,
                fontSize: 32,
                color: COLORS.green,
              }}
            >
              {scene.pill}
            </span>
          </div>
        </div>
      </div>
    </PanelShell>
  );
};
