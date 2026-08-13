import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLORS, FONTS} from './../theme';
import type {RepoScene} from './../types';
import {FlameGlyph, GitHubMark, StarGlyph} from './glyphs';
import {PanelShell} from './PanelShell';

const numberFmt = new Intl.NumberFormat('en-US');

/** Star count that springs up to the total. Tabular numerals keep it steady. */
const StarCount: React.FC<{target: number}> = ({target}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const progress = spring({
    frame: frame - 8,
    fps,
    durationInFrames: 50,
    config: {damping: 200},
  });
  const value = Math.round(progress * target);
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
      {numberFmt.format(value)}
    </span>
  );
};

/** Pick a display size for the repo name so long names never overflow. */
const nameFontSize = (name: string) => {
  if (name.length <= 10) return 116;
  if (name.length <= 14) return 92;
  if (name.length <= 20) return 72;
  return 58;
};

export const RepoPanel: React.FC<{
  scene: RepoScene;
  rank: number;
  durationInFrames: number;
}> = ({scene, rank, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const [owner, name] = scene.repo.split('/');

  const cardIn = spring({
    frame: frame - 2,
    fps,
    config: {damping: 18, stiffness: 130},
  });
  const pillIn = spring({
    frame: frame - 22,
    fps,
    config: {damping: 13, stiffness: 160},
  });

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
          opacity: interpolate(cardIn, [0, 0.5], [0, 1], {
            extrapolateRight: 'clamp',
          }),
          transform: `translateY(${(1 - cardIn) * 36}px)`,
        }}
      >
        {/* Header row: GitHub mark + trending rank */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 18}}>
            <GitHubMark size={44} color={COLORS.muted} />
            <span
              style={{
                fontFamily: FONTS.body,
                fontWeight: 600,
                fontSize: 28,
                letterSpacing: '0.24em',
                color: COLORS.violetLight,
              }}
            >
              TRENDING #{rank}
            </span>
          </div>
          <span
            style={{
              fontFamily: FONTS.body,
              fontWeight: 600,
              fontSize: 26,
              color: COLORS.muted,
              letterSpacing: '0.12em',
            }}
          >
            {rank}/3
          </span>
        </div>

        {/* Repo full name */}
        <div style={{display: 'flex', flexDirection: 'column', gap: 6}}>
          <span
            style={{
              fontFamily: FONTS.body,
              fontWeight: 500,
              fontSize: 36,
              color: COLORS.muted,
              letterSpacing: '0.01em',
            }}
          >
            {owner}/
          </span>
          <span
            style={{
              fontFamily: FONTS.display,
              fontWeight: 800,
              fontSize: nameFontSize(name ?? scene.repo),
              lineHeight: 1.02,
              color: COLORS.text,
              letterSpacing: '-0.02em',
              overflowWrap: 'anywhere',
            }}
          >
            {name}
          </span>
        </div>

        {/* Description */}
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

        {/* Divider */}
        <div style={{height: 1, background: COLORS.border}} />

        {/* Stars row */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 24,
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 20}}>
            <StarGlyph size={52} color={COLORS.violetLight} />
            <StarCount target={scene.stars} />
          </div>
          {scene.today ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12,
                padding: '14px 26px',
                borderRadius: 999,
                background: 'rgba(103, 210, 67, 0.12)',
                border: '1px solid rgba(103, 210, 67, 0.4)',
                opacity: interpolate(pillIn, [0, 0.5], [0, 1], {
                  extrapolateRight: 'clamp',
                }),
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
                  fontVariantNumeric: 'tabular-nums',
                }}
              >
                +{numberFmt.format(scene.today)} today
              </span>
            </div>
          ) : null}
        </div>
      </div>
    </PanelShell>
  );
};
