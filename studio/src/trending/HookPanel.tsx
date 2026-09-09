import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {GitHubMark} from '../panels/glyphs';
import {Shell} from './Shell';
import {T_COLORS, T_FONTS, T_TITLE} from './theme';

const MONTHS = [
  'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
  'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC',
];

const formatDate = (iso: string) => {
  const [y, m, d] = iso.split('-').map(Number);
  return `${MONTHS[(m ?? 1) - 1]} ${d}, ${y}`;
};

/** Staggered rise — each block lands a few frames after the one above. */
const Rise: React.FC<{delay: number; children: React.ReactNode}> = ({
  delay,
  children,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({
    frame: frame - delay,
    fps,
    config: {damping: 16, stiffness: 140},
  });
  return (
    <div
      style={{
        opacity: interpolate(p, [0, 0.6], [0, 1], {extrapolateRight: 'clamp'}),
        transform: `translateY(${(1 - p) * 44}px)`,
      }}
    >
      {children}
    </div>
  );
};

/**
 * Scene 1: a dark full-frame title treatment in the card's type system —
 * no repo card, same eyebrow/display/accent stack.
 *
 * Reference (f_090, t 3.0s): eyebrow pill ink y 279..312, "3 AI REPOS" ink
 * y 384..476 in white, "BLOWING UP TODAY" ink y 516..573 in violet, and a
 * 110x6 violet rule at y 624..630. All four are centred on x 540.
 */
export const HookPanel: React.FC<{
  date: string;
  durationInFrames: number;
  eyebrow?: string;
  line1?: string;
  line2?: string;
  showGithub?: boolean;
}> = ({
  date,
  durationInFrames,
  eyebrow,
  line1 = '3 AI REPOS',
  line2 = 'BLOWING UP TODAY',
  showGithub = true,
}) => {
  // Step down when an episode overrides the copy with something longer than
  // the measured "3 AI REPOS" / "BLOWING UP TODAY".
  const size1 =
    line1.length <= 12
      ? T_TITLE.hookLine1
      : line1.length <= 18
        ? 104
        : 84;
  const size2 =
    line2.length <= 16
      ? T_TITLE.hookLine2
      : line2.length <= 24
        ? 64
        : 52;

  return (
    <Shell durationInFrames={durationInFrames}>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: T_TITLE.gap,
        }}
      >
        <Rise delay={2}>
          <div
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 16,
              padding: '14px 28px',
              borderRadius: 999,
              border: `1px solid ${T_COLORS.border}`,
              background: T_COLORS.card,
            }}
          >
            {showGithub ? (
              <GitHubMark size={34} color={T_COLORS.muted} />
            ) : null}
            <span
              style={{
                fontFamily: T_FONTS.body,
                fontWeight: 600,
                fontSize: T_TITLE.eyebrowSize,
                letterSpacing: T_TITLE.eyebrowTracking,
                color: T_COLORS.muted,
              }}
            >
              {eyebrow ?? `GITHUB · ${formatDate(date)}`}
            </span>
          </div>
        </Rise>

        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 4,
            textAlign: 'center',
            fontFamily: T_FONTS.display,
            fontWeight: 800,
            lineHeight: 1.02,
            letterSpacing: '-0.02em',
          }}
        >
          <Rise delay={5}>
            <div style={{fontSize: size1, color: T_COLORS.text}}>{line1}</div>
          </Rise>
          <Rise delay={8}>
            <div
              style={{
                fontSize: size2,
                color: T_COLORS.violetLight,
                whiteSpace: 'nowrap',
              }}
            >
              {line2}
            </div>
          </Rise>
        </div>

        <Rise delay={12}>
          <div
            style={{
              width: T_TITLE.ruleW,
              height: T_TITLE.ruleH,
              borderRadius: T_TITLE.ruleH / 2,
              background: T_COLORS.violet,
            }}
          />
        </Rise>
      </div>
    </Shell>
  );
};
