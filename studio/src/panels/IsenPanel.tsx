import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {GEORGIA_BOLD, GEORGIA_BOLD_ITALIC} from '../isenFonts';
import type {IsenScene} from '../types';

// Isenberg-style motion design: greige paper + grid, extruded forest pills,
// editorial serif with coral italic accents, one organic coral accent/scene.
// Approved by Johann 2026-07-12 as the premium house style.

const PAPER = '#e9e6df';
const FOREST = '#1e3a2f';
const FOREST_HI = '#254a3b';
const FOREST_DK = '#12241c';
const CORAL = '#e8724c';
const CORAL_DK = '#b6522f';
const MUTE = '#6b675e';

const fontCss = `
@font-face { font-family: 'GeorgiaB'; src: url('${GEORGIA_BOLD}'); }
@font-face { font-family: 'GeorgiaBI'; src: url('${GEORGIA_BOLD_ITALIC}'); }
`;

const Stage: React.FC<{children: React.ReactNode; half?: boolean}> = ({children, half}) => (
  <AbsoluteFill
    style={{
      background: half ? 'transparent' : PAPER,
    }}
  >
    <style>{fontCss}</style>
    {half ? (
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 960,
          background: PAPER,
          overflow: 'hidden',
          boxShadow: '0 24px 60px #00000045',
        }}
      >
        <div
          style={{
            position: 'absolute',
            inset: 0,
            backgroundImage:
              'linear-gradient(#00000009 1.5px, transparent 1.5px), linear-gradient(90deg, #00000009 1.5px, transparent 1.5px)',
            backgroundSize: '54px 54px',
          }}
        />
        <div style={{position: 'absolute', inset: 0, transform: 'scale(0.62)', transformOrigin: '50% 8%'}}>{children}</div>
      </div>
    ) : (
      <InnerFull>{children}</InnerFull>
    )}
  </AbsoluteFill>
);

const InnerFull: React.FC<{children: React.ReactNode}> = ({children}) => (
  <AbsoluteFill style={{background: PAPER}}>
    <style>{fontCss}</style>
    <AbsoluteFill
      style={{
        backgroundImage:
          'linear-gradient(#00000009 1.5px, transparent 1.5px), linear-gradient(90deg, #00000009 1.5px, transparent 1.5px)',
        backgroundSize: '54px 54px',
      }}
    />
    <AbsoluteFill style={{boxShadow: 'inset 0 0 280px #00000016'}} />
    {children}
  </AbsoluteFill>
);

const Serif: React.FC<{
  size: number;
  children: React.ReactNode;
  style?: React.CSSProperties;
}> = ({size, children, style}) => (
  <div
    style={{
      fontFamily: 'GeorgiaB, Georgia, serif',
      fontSize: size,
      color: FOREST,
      letterSpacing: -size * 0.03,
      lineHeight: 1.06,
      textAlign: 'center',
      ...style,
    }}
  >
    {children}
  </div>
);

const Accent: React.FC<{children: React.ReactNode}> = ({children}) => (
  <span style={{fontFamily: 'GeorgiaBI, Georgia, serif', fontStyle: 'italic', color: CORAL}}>
    {children}
  </span>
);

// Title with optional *accent* marker: "The 5 levels of *AI automation*"
const Title: React.FC<{text: string; size?: number; at: number}> = ({text, size = 84, at}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: frame - at, fps, config: {damping: 14, stiffness: 120}});
  const parts = text.split('*');
  return (
    <div style={{opacity: p, transform: `translateY(${(1 - p) * 26}px)`}}>
      <Serif size={size}>
        {parts.map((t, i) => (i % 2 === 1 ? <Accent key={i}>{t}</Accent> : <span key={i}>{t}</span>))}
      </Serif>
    </div>
  );
};

const Pill: React.FC<{
  at: number;
  width?: number | string;
  emphasis?: boolean;
  struck?: boolean;
  strikeAt?: number;
  light?: boolean;
  children: React.ReactNode;
}> = ({at, width = '100%', emphasis, struck, strikeAt = 0, light, children}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: frame - at, fps, config: {damping: 12, stiffness: 150}});
  const strike = struck
    ? interpolate(frame - strikeAt, [0, 12], [0, 100], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'})
    : 0;
  return (
    <div
      style={{
        position: 'relative',
        width,
        background: light
          ? 'linear-gradient(180deg, #ffffff, #efece5)'
          : `linear-gradient(180deg, ${emphasis ? '#37604d' : FOREST_HI}, ${emphasis ? FOREST_HI : '#1a3529'})`,
        color: light ? FOREST : '#fff',
        borderRadius: 200,
        boxShadow: light
          ? '0 10px 0 #cfccc4, 0 24px 46px #00000022'
          : `0 12px 0 ${FOREST_DK}, 0 28px 56px #00000038`,
        padding: '26px 40px',
        fontFamily: 'Inter Tight, sans-serif',
        fontWeight: 700,
        display: 'flex',
        alignItems: 'center',
        gap: 20,
        opacity: p,
        transform: `translateY(${(1 - p) * -46}px) scale(${emphasis ? 0.96 + p * 0.08 : 1})`,
      }}
    >
      {children}
      {struck ? (
        <div
          style={{
            position: 'absolute',
            left: '4%',
            top: '50%',
            width: `${strike * 0.92}%`,
            height: 9,
            borderRadius: 6,
            background: CORAL,
            boxShadow: `0 3px 0 ${CORAL_DK}`,
            transform: 'rotate(-2deg)',
          }}
        />
      ) : null}
    </div>
  );
};

const CoralArrow: React.FC<{at: number; style?: React.CSSProperties}> = ({at, style}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const p = spring({frame: frame - at, fps, config: {damping: 16}});
  return (
    <svg width={140} height={190} viewBox="0 0 150 200" style={{position: 'absolute', opacity: p, ...style}}>
      <path
        d="M20 10 C60 40 90 90 75 150 M75 150 L45 120 M75 150 L108 128"
        stroke={CORAL}
        strokeWidth={14}
        fill="none"
        strokeLinecap="round"
        strokeDasharray={300}
        strokeDashoffset={300 * (1 - p)}
      />
    </svg>
  );
};

/* ---------- variant: levels ---------- */
const Levels: React.FC<{scene: IsenScene}> = ({scene}) => {
  const {fps} = useVideoConfig();
  const items = scene.items ?? [];
  const step = ((scene.durationSec ?? 12) * fps - 40) / Math.max(items.length, 1);
  return (
    <div style={{position: 'absolute', inset: 0, padding: '130px 84px', display: 'flex', flexDirection: 'column'}}>
      <Title text={scene.title} at={0} />
      {scene.subtitle ? (
        <div style={{fontFamily: 'Inter Tight, sans-serif', fontSize: 33, color: MUTE, textAlign: 'center', margin: '18px 0 64px'}}>
          {scene.subtitle}
        </div>
      ) : (
        <div style={{height: 64}} />
      )}
      <div style={{display: 'flex', flexDirection: 'column', gap: 30}}>
        {items.map((it, i) => (
          <Pill key={i} at={26 + i * step} emphasis={i === items.length - 1}>
            <div
              style={{
                background: CORAL,
                width: 62,
                height: 62,
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                fontSize: 33,
                flex: 'none',
                boxShadow: `0 7px 0 ${CORAL_DK}`,
              }}
            >
              {i + 1}
            </div>
            <span style={{fontSize: 37}}>{it.label}</span>
            <span style={{marginLeft: 'auto', fontSize: 27, fontWeight: 500, opacity: 0.75}}>{it.note}</span>
          </Pill>
        ))}
      </div>
      <CoralArrow at={20} style={{right: 40, top: 350}} />
    </div>
  );
};

/* ---------- variant: faceoff ---------- */
const AppleMark: React.FC = () => (
  <svg width={170} height={200} viewBox="0 0 170 200">
    <path
      d="M130 106c0-26 21-38 22-39-12-17-30-19-37-20-16-2-31 9-39 9-8 0-20-9-34-9-17 0-33 10-42 26-18 31-5 77 13 102 9 12 19 26 33 25 13-1 18-8 34-8s20 8 34 8c14 0 23-13 32-25 10-14 14-28 14-29-1 0-30-11-30-40z"
      fill="#fff"
    />
    <path d="M107 26c7-9 12-21 11-33-10 1-23 7-30 16-7 8-13 20-11 32 12 1 23-6 30-15z" fill="#fff" transform="translate(0,12)" />
  </svg>
);

const Faceoff: React.FC<{scene: IsenScene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const pL = spring({frame, fps, config: {damping: 13, stiffness: 130}});
  const pR = spring({frame: frame - 8, fps, config: {damping: 13, stiffness: 130}});
  const docAt = (scene.durationSec ?? 13) * fps * 0.48;
  const pDoc = spring({frame: frame - docAt, fps, config: {damping: 15}});
  const tile: React.CSSProperties = {
    width: 290,
    height: 290,
    borderRadius: 46,
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  };
  return (
    <div style={{position: 'absolute', inset: 0, padding: '150px 80px', display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
      <div style={{display: 'flex', alignItems: 'center', gap: 62, marginBottom: 84}}>
        <div
          style={{
            ...tile,
            background: 'linear-gradient(180deg, #2a2a2e, #161619)',
            boxShadow: '0 15px 0 #0c0c0e, 0 34px 66px #00000045',
            opacity: pL,
            transform: `translateX(${(1 - pL) * -160}px)`,
          }}
        >
          <AppleMark />
        </div>
        <div style={{fontFamily: 'GeorgiaBI, Georgia, serif', fontStyle: 'italic', fontSize: 58, color: MUTE, opacity: Math.min(pL, pR)}}>
          v.
        </div>
        <div
          style={{
            ...tile,
            background: 'linear-gradient(180deg, #ffffff, #e6e6e6)',
            boxShadow: '0 15px 0 #c4c4c4, 0 34px 66px #00000030',
            opacity: pR,
            transform: `translateX(${(1 - pR) * 160}px)`,
            fontFamily: 'Inter Tight, sans-serif',
            fontWeight: 800,
            fontSize: 52,
            color: '#111',
          }}
        >
          OpenAI
        </div>
      </div>
      <Title text={scene.title} size={96} at={16} />
      {scene.doc ? (
        <div
          style={{
            marginTop: 70,
            background: '#fff',
            borderRadius: 24,
            boxShadow: '0 12px 0 #cfccc4, 0 30px 58px #00000025',
            padding: '42px 52px',
            fontFamily: 'GeorgiaB, Georgia, serif',
            color: '#333',
            fontSize: 31,
            lineHeight: 1.6,
            maxWidth: 840,
            opacity: pDoc,
            transform: `rotate(${-1.4 * pDoc}deg) translateY(${(1 - pDoc) * 60}px)`,
          }}
        >
          {scene.doc.split('*').map((t, i) =>
            i % 2 === 1 ? (
              <b key={i} style={{background: '#ffe9a8', padding: '0 6px'}}>
                {t}
              </b>
            ) : (
              <span key={i}>{t}</span>
            )
          )}
        </div>
      ) : null}
    </div>
  );
};

/* ---------- variant: orgchart ---------- */
const OrgChart: React.FC<{scene: IsenScene}> = ({scene}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const items = scene.items ?? [];
  const total = (scene.durationSec ?? 15) * fps;
  const struckItems = items.filter((it) => it.struck);
  const strikeWindow = total * 0.72;
  const strikeStep = strikeWindow / Math.max(struckItems.length, 1);
  let struckSeen = 0;
  const counterTarget = scene.counter ?? 800000;
  const counterNow = Math.round(
    interpolate(frame, [total * 0.12, total * 0.84], [0, counterTarget], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    }) / 1000
  );
  return (
    <div style={{position: 'absolute', inset: 0, padding: '116px 64px', display: 'flex', flexDirection: 'column'}}>
      <Title text={scene.title} size={66} at={0} />
      <div style={{height: 52}} />
      <div style={{display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 26}}>
        {items.map((it, i) => {
          const sAt = it.struck ? total * 0.14 + strikeStep * struckSeen++ : 0;
          return (
            <Pill key={i} at={12 + i * 5} light={!it.struck} struck={it.struck} strikeAt={sAt}>
              <span style={{fontSize: 29, fontWeight: it.struck ? 700 : 600}}>{it.label}</span>
              {it.note ? (
                <span style={{marginLeft: 'auto', fontSize: 23, fontWeight: 500, opacity: 0.65}}>{it.note}</span>
              ) : null}
            </Pill>
          );
        })}
      </div>
      <div
        style={{
          marginTop: 'auto',
          marginBottom: 330,
          alignSelf: 'center',
          fontFamily: 'GeorgiaB, Georgia, serif',
          fontSize: 92,
          color: CORAL,
          textShadow: '0 4px 0 #b6522f33',
        }}
      >
        ${counterNow}K
        <span style={{fontFamily: 'Inter Tight, sans-serif', fontSize: 30, color: MUTE, marginLeft: 18}}>
          / year in automatable payroll
        </span>
      </div>
    </div>
  );
};

export const IsenPanel: React.FC<{scene: IsenScene}> = ({scene}) => {
  return (
    <Stage half={scene.half}>
      {scene.variant === 'levels' ? (
        <Levels scene={scene} />
      ) : scene.variant === 'faceoff' ? (
        <Faceoff scene={scene} />
      ) : (
        <OrgChart scene={scene} />
      )}
    </Stage>
  );
};
