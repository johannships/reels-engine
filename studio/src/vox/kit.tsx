import React from 'react';
import {interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {FONT, FONT_CN} from './fonts';
import {INK, YELLOW} from './data';

// ------------------------------------------------------------------ timing
/** eased 0..1 over `len` frames starting at `start` */
export const ease = (frame: number, start: number, len: number) =>
  interpolate(frame, [start, start + len], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
    easing: (t) => 1 - Math.pow(1 - t, 3),
  });

export const useSpring = (start: number, damping = 13, mass = 0.6) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  return spring({frame: frame - start, fps, config: {damping, mass, stiffness: 120}});
};

// ------------------------------------------------------------------ glyphs
export const Star: React.FC<{size: number; fill: string}> = ({size, fill}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={{display: 'block'}}>
    <path
      fill={fill}
      d="M12 2.2l2.95 6.02 6.65.94-4.8 4.63 1.13 6.58L12 17.28 6.07 20.37l1.13-6.58L2.4 9.16l6.65-.94z"
    />
  </svg>
);

export const Check: React.FC<{size: number; stroke: string; progress: number}> = ({
  size,
  stroke,
  progress,
}) => (
  <svg width={size} height={size} viewBox="0 0 24 24" style={{display: 'block'}}>
    <path
      d="M4.5 12.6l4.6 4.6L19.5 6.8"
      fill="none"
      stroke={stroke}
      strokeWidth={3.4}
      strokeLinecap="round"
      strokeLinejoin="round"
      strokeDasharray={26}
      strokeDashoffset={26 * (1 - progress)}
    />
  </svg>
);

// ------------------------------------------------------------------ texture
/** Dark grain field. Real texture, generated - never a flat colour panel. */
export const Grain: React.FC<{opacity?: number; tint?: string}> = ({
  opacity = 1,
  tint = '#0B0C0A',
}) => {
  const frame = useCurrentFrame();
  const shift = (frame % 4) * 37;
  return (
    <div style={{position: 'absolute', inset: 0, opacity}}>
      <div style={{position: 'absolute', inset: 0, background: tint}} />
      <div
        style={{
          position: 'absolute',
          inset: -80,
          backgroundImage:
            'radial-gradient(rgba(255,255,255,0.055) 1px, transparent 1.2px)',
          backgroundSize: '3px 3px',
          backgroundPosition: `${shift}px ${shift * 0.6}px`,
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(120% 80% at 50% 38%, rgba(120,130,100,0.14), rgba(0,0,0,0) 62%)',
        }}
      />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          background:
            'radial-gradient(100% 70% at 50% 50%, rgba(0,0,0,0) 40%, rgba(0,0,0,0.72) 100%)',
        }}
      />
    </div>
  );
};

// ------------------------------------------------------------------ accents
/** Thin yellow corner brackets - the montage frame accent. */
export const CornerBrackets: React.FC<{
  inset?: number;
  arm?: number;
  t: number;
  weight?: number;
}> = ({inset = 44, arm = 96, t, weight = 6}) => {
  const a = arm * t;
  const c = YELLOW;
  const corner = (
    vStyle: React.CSSProperties,
    hStyle: React.CSSProperties,
  ) => (
    <>
      <div style={{position: 'absolute', background: c, ...vStyle}} />
      <div style={{position: 'absolute', background: c, ...hStyle}} />
    </>
  );
  return (
    <div style={{position: 'absolute', inset, opacity: t}}>
      {corner(
        {left: 0, top: 0, width: weight, height: a},
        {left: 0, top: 0, width: a, height: weight},
      )}
      {corner(
        {right: 0, top: 0, width: weight, height: a},
        {right: 0, top: 0, width: a, height: weight},
      )}
      {corner(
        {left: 0, bottom: 0, width: weight, height: a},
        {left: 0, bottom: 0, width: a, height: weight},
      )}
      {corner(
        {right: 0, bottom: 0, width: weight, height: a},
        {right: 0, bottom: 0, width: a, height: weight},
      )}
    </div>
  );
};

// ------------------------------------------------------------------ receipts
/**
 * The Vox receipt cutaway: a solid masthead bar in the source's own type with
 * the claim underneath, dropped in from the direction of the source.
 */
export const Receipt: React.FC<{
  masthead: React.ReactNode;
  mastheadBg?: string;
  children: React.ReactNode;
  width: number;
  t: number;
  from?: 'top' | 'left' | 'right';
  /** false = transform-only entry, so a hard cut never lands on an empty frame */
  fade?: boolean;
  style?: React.CSSProperties;
}> = ({masthead, mastheadBg = '#000', children, width, t, from = 'top', fade = true, style}) => {
  const d = 40 * (1 - t);
  const tx = from === 'left' ? -d : from === 'right' ? d : 0;
  const ty = from === 'top' ? -d : 0;
  return (
    <div
      style={{
        position: 'absolute',
        width,
        transform: `translate(${tx}px, ${ty}px)`,
        opacity: fade ? t : 1,
        filter: 'drop-shadow(0 16px 34px rgba(0,0,0,0.62))',
        ...style,
      }}
    >
      <div
        style={{
          background: mastheadBg,
          color: '#fff',
          fontFamily: FONT,
          fontWeight: 700,
          padding: '13px 20px',
          display: 'flex',
          alignItems: 'center',
          gap: 12,
        }}
      >
        {masthead}
      </div>
      <div
        style={{
          background: '#fff',
          color: INK,
          fontFamily: FONT,
          fontWeight: 700,
          padding: '16px 20px 18px',
          lineHeight: 1.16,
        }}
      >
        {children}
      </div>
    </div>
  );
};

export const GithubMark: React.FC<{size: number; fill?: string}> = ({size, fill = '#fff'}) => (
  <svg width={size} height={size} viewBox="0 0 16 16" style={{display: 'block'}}>
    <path
      fill={fill}
      d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.94.51-1.16-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82a7.4 7.4 0 0 1 2-.27c.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A7.99 7.99 0 0 0 16 8c0-4.42-3.58-8-8-8z"
    />
  </svg>
);

// ------------------------------------------------------------------ numbers
export const useCountUp = (target: number, start: number, len = 14) => {
  const frame = useCurrentFrame();
  const t = ease(frame, start, len);
  return Math.round(target * t);
};

export const fmt = (n: number) => n.toLocaleString('en-US');

// ------------------------------------------------------------------ type
export const bigStatStyle: React.CSSProperties = {
  fontFamily: FONT,
  fontWeight: 700,
  color: '#fff',
  letterSpacing: '-0.03em',
  lineHeight: 0.94,
  textShadow: '0 6px 30px rgba(0,0,0,0.7)',
};

export const cnStyle: React.CSSProperties = {
  fontFamily: FONT_CN,
  fontWeight: 900,
  letterSpacing: '0.01em',
};
