import React from 'react';
import {
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import type {RepoScene} from '../types';
import {FlameGlyph, GitHubMark, StarGlyph} from '../panels/glyphs';
import {Shell} from './Shell';
import {
  T_CARD,
  T_CARD_TYPE,
  T_CHIP,
  T_COLORS,
  T_FONTS,
  descSizeFor,
  nameSizeFor,
} from './theme';

const numberFmt = new Intl.NumberFormat('en-US');

/**
 * The star count-up, measured off the reference rather than guessed.
 *
 * Sampled the "page-agent" card in ref.mp4 (scene starts frame ~613):
 *   frame 615 -> "0"        (0%)
 *   frame 630 -> "13,386"   (58.7% of 22,814)
 *   frame 660 -> "22,655"   (99.3%)
 *   frame 690 -> "22,814"   (settled)
 * An ease-out cubic over 60 frames (2.0s) predicts 57.8% at frame 630 and
 * 98.4% at frame 660 — so: from ZERO, 2.0s, ease-out cubic.
 */
const COUNT_START = 2; // frames — the count starts as the card lands
const COUNT_FRAMES = 60; // 2.0s at 30fps

const StarCount: React.FC<{target: number}> = ({target}) => {
  const frame = useCurrentFrame();
  const progress = interpolate(
    frame,
    [COUNT_START, COUNT_START + COUNT_FRAMES],
    [0, 1],
    {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: Easing.out(Easing.cubic),
    },
  );
  return (
    <span
      style={{
        fontFamily: T_FONTS.display,
        fontWeight: 800,
        fontSize: T_CARD_TYPE.countSize,
        lineHeight: 1,
        color: T_COLORS.text,
        // Tabular figures: without them the number jitters horizontally
        // through the whole count-up.
        fontVariantNumeric: 'tabular-nums',
        fontFeatureSettings: '"tnum"',
        letterSpacing: '-0.01em',
      }}
    >
      {numberFmt.format(Math.round(progress * target))}
    </span>
  );
};

export const RepoCard: React.FC<{
  scene: RepoScene;
  rank: number;
  durationInFrames: number;
}> = ({scene, rank, durationInFrames}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const [owner, name] = scene.repo.split('/');
  const repoName = name ?? scene.repo;

  const cardIn = spring({
    frame: frame - 2,
    fps,
    config: {damping: 18, stiffness: 130},
  });
  // The chip slides in from the right and settles after the count-up is
  // already running — in the reference it is absent on the first frames of
  // the scene and present by the time the number is legible.
  const chipIn = spring({
    frame: frame - 22,
    fps,
    config: {damping: 14, stiffness: 160},
  });

  const descSize = descSizeFor(scene.desc);

  return (
    <Shell durationInFrames={durationInFrames} center={false}>
      <div
        style={{
          position: 'absolute',
          top: T_CARD.top,
          left: (1080 - T_CARD.width) / 2,
          width: T_CARD.width,
          boxSizing: 'border-box',
          background: T_COLORS.card,
          border: `1px solid ${T_COLORS.border}`,
          borderRadius: T_CARD.radius,
          padding: `${T_CARD.padY}px ${T_CARD.padX}px`,
          display: 'flex',
          flexDirection: 'column',
          gap: T_CARD.gap,
          boxShadow: '0 40px 90px rgba(0, 0, 0, 0.5)',
          opacity: interpolate(cardIn, [0, 0.5], [0, 1], {
            extrapolateRight: 'clamp',
          }),
          transform: `translateY(${(1 - cardIn) * 36}px)`,
        }}
      >
        {/* Header: GitHub mark + "TRENDING #N" left, "N/3" right */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: T_CARD_TYPE.labelGap,
            }}
          >
            <GitHubMark size={T_CARD_TYPE.markSize} color={T_COLORS.muted} />
            <span
              style={{
                fontFamily: T_FONTS.body,
                fontWeight: 600,
                fontSize: T_CARD_TYPE.labelSize,
                letterSpacing: T_CARD_TYPE.labelTracking,
                color: T_COLORS.violetLight,
              }}
            >
              TRENDING #{rank}
            </span>
          </div>
          <span
            style={{
              fontFamily: T_FONTS.body,
              fontWeight: 600,
              fontSize: T_CARD_TYPE.rankSize,
              letterSpacing: T_CARD_TYPE.rankTracking,
              color: T_COLORS.muted,
            }}
          >
            {rank}/3
          </span>
        </div>

        {/* owner/ above the name in huge white display type */}
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            gap: T_CARD_TYPE.ownerGap,
          }}
        >
          <span
            style={{
              fontFamily: T_FONTS.body,
              fontWeight: 500,
              fontSize: T_CARD_TYPE.ownerSize,
              color: T_COLORS.muted,
              letterSpacing: '0.01em',
            }}
          >
            {owner}/
          </span>
          {/* Fixed-height block: the name steps down in size for long repo
              names, and reserving the reference's 118px keeps the card (and
              therefore the safe-zone budget) exactly the same height for
              every repo. */}
          <div
            style={{
              height: T_CARD_TYPE.nameBlock,
              display: 'flex',
              alignItems: 'center',
            }}
          >
            <span
              style={{
                fontFamily: T_FONTS.display,
                fontWeight: 800,
                fontSize: nameSizeFor(repoName),
                lineHeight: T_CARD_TYPE.nameLineHeight,
                color: T_COLORS.text,
                letterSpacing: T_CARD_TYPE.nameTracking,
                overflowWrap: 'anywhere',
              }}
            >
              {repoName}
            </span>
          </div>
        </div>

        {/* Description — clamped to the reference's 2 lines */}
        <p
          style={{
            margin: 0,
            height: Math.round(
              descSize * T_CARD_TYPE.descLineHeight * T_CARD_TYPE.descLines,
            ),
            fontFamily: T_FONTS.body,
            fontWeight: 500,
            fontSize: descSize,
            lineHeight: T_CARD_TYPE.descLineHeight,
            color: T_COLORS.muted,
            display: '-webkit-box',
            WebkitBoxOrient: 'vertical',
            WebkitLineClamp: T_CARD_TYPE.descLines,
            overflow: 'hidden',
          }}
        >
          {scene.desc}
        </p>

        <div style={{height: 1, background: T_COLORS.border}} />

        {/* Stars row: violet star + count-up left, green chip right */}
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            gap: 24,
          }}
        >
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: T_CARD_TYPE.starGap,
            }}
          >
            <StarGlyph
              size={T_CARD_TYPE.starSize}
              color={T_COLORS.violetLight}
            />
            <StarCount target={scene.stars} />
          </div>
          {scene.today ? (
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: T_CHIP.gap,
                padding: `${T_CHIP.padY}px ${T_CHIP.padX}px`,
                borderRadius: T_CHIP.radius,
                background: T_COLORS.greenFill,
                border: `1px solid ${T_COLORS.greenLine}`,
                whiteSpace: 'nowrap',
                opacity: interpolate(chipIn, [0, 0.5], [0, 1], {
                  extrapolateRight: 'clamp',
                }),
                transform: `translateX(${(1 - chipIn) * 40}px)`,
              }}
            >
              <FlameGlyph size={T_CHIP.flameSize} color={T_COLORS.green} />
              <span
                style={{
                  fontFamily: T_FONTS.body,
                  fontWeight: 700,
                  fontSize: T_CHIP.textSize,
                  color: T_COLORS.green,
                  fontVariantNumeric: 'tabular-nums',
                }}
              >
                +{numberFmt.format(scene.today)} today
              </span>
            </div>
          ) : null}
        </div>
      </div>
    </Shell>
  );
};
