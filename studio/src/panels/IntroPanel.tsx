import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {COLORS, FONTS} from './../theme';
import {AgentMemoryMark, ClaudeMark, CloudflareMark, DeepSeekMark, GitHubMark, GoogleMark, MicrosoftMark, YCMark} from './glyphs';
import {PanelShell} from './PanelShell';

const formatDate = (iso: string) => {
  const [y, m, d] = iso.split('-').map(Number);
  const months = [
    'JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
    'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC',
  ];
  return `${months[(m ?? 1) - 1]} ${d}, ${y}`;
};

const Rise: React.FC<{delay: number; children: React.ReactNode}> = ({
  delay,
  children,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: frame - delay, fps, config: {damping: 16, stiffness: 140}});
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

const LOGOS: Record<string, React.FC<{size?: number; color?: string}>> = {
  agentmemory: AgentMemoryMark,
  claude: ClaudeMark,
  google: GoogleMark,
  cloudflare: CloudflareMark,
  deepseek: DeepSeekMark,
  github: GitHubMark,
  microsoft: MicrosoftMark,
  yc: YCMark,
};

/** Spring scale-in with a slight overshoot, for logo badges. */
const Pop: React.FC<{delay: number; children: React.ReactNode}> = ({
  delay,
  children,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: frame - delay, fps, config: {damping: 11, stiffness: 160}});
  return (
    <div style={{transform: `scale(${0.82 + p * 0.18})`}}>
      {children}
    </div>
  );
};

export const IntroPanel: React.FC<{
  date: string;
  durationInFrames: number;
  eyebrow?: string;
  line1?: string;
  line2?: string;
  logo?: string;
  logo2?: string;
  showGithub?: boolean;
}> = ({
  date,
  durationInFrames,
  eyebrow,
  line1 = '3 AI REPOS',
  line2 = 'BLOWING UP TODAY',
  logo,
  logo2,
  showGithub = true,
}) => {
  const Logo = logo ? LOGOS[logo] : undefined;
  const Logo2 = logo2 ? LOGOS[logo2] : undefined;
  const line1Size = line1.length <= 12 ? 132 : line1.length <= 18 ? 104 : 84;
  const line2Size = line2.length <= 16 ? 84 : line2.length <= 24 ? 64 : 52;
  return (
    <PanelShell durationInFrames={durationInFrames}>
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 36,
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
              border: `1px solid ${COLORS.border}`,
              background: COLORS.card,
            }}
          >
            {showGithub ? <GitHubMark size={34} color={COLORS.muted} /> : null}
            <span
              style={{
                fontFamily: FONTS.body,
                fontWeight: 600,
                fontSize: 30,
                letterSpacing: '0.22em',
                color: COLORS.muted,
              }}
            >
              {eyebrow ?? `GITHUB · ${formatDate(date)}`}
            </span>
          </div>
        </Rise>

        {Logo ? (
          <Rise delay={4}>
            <div style={{display: 'flex', alignItems: 'center', gap: 24}}>
              <Pop delay={4}>
                <div
                  style={{
                    width: 148,
                    height: 148,
                    borderRadius: 40,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    border: `1px solid ${COLORS.border}`,
                    background: COLORS.card,
                  }}
                >
                  <Logo size={92} />
                </div>
              </Pop>
              {Logo2 ? (
                <>
                  <span
                    style={{
                      fontFamily: FONTS.display,
                      fontWeight: 800,
                      fontSize: 56,
                      color: COLORS.muted,
                    }}
                  >
                    ×
                  </span>
                  <Pop delay={7}>
                    <div
                      style={{
                        width: 148,
                        height: 148,
                        borderRadius: 40,
                        display: 'flex',
                        alignItems: 'center',
                        justifyContent: 'center',
                        border: `1px solid ${COLORS.border}`,
                        background: COLORS.card,
                      }}
                    >
                      <Logo2 size={92} />
                    </div>
                  </Pop>
                </>
              ) : null}
            </div>
          </Rise>
        ) : null}

        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 4,
            textAlign: 'center',
            fontFamily: FONTS.display,
            fontWeight: 800,
            lineHeight: 1.02,
            letterSpacing: '-0.02em',
          }}
        >
          <Rise delay={5}>
            <div style={{fontSize: line1Size, color: COLORS.text}}>
              {line1}
            </div>
          </Rise>
          <Rise delay={8}>
            <div
              style={{
                fontSize: line2Size,
                color: COLORS.violetLight,
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
              width: 110,
              height: 6,
              borderRadius: 3,
              background: COLORS.violet,
            }}
          />
        </Rise>
      </div>
    </PanelShell>
  );
};
