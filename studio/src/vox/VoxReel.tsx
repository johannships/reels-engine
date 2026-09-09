import React from 'react';
import {
  AbsoluteFill,
  Img,
  OffthreadVideo,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';
import {
  BEATS,
  BURST_COL,
  STARS,
  FPS,
  HAND,
  H,
  INK,
  SHOTS,
  Shot,
  ShotKind,
  W,
  YELLOW,
  s,
} from './data';
import {Caption} from './Caption';
import {FONT, FONT_CN, ensureVoxFonts} from './fonts';
import {
  Check,
  CornerBrackets,
  GithubMark,
  Grain,
  Receipt,
  Star,
  bigStatStyle,
  cnStyle,
  ease,
  fmt,
} from './kit';

ensureVoxFonts();

const asset = (p: string) => staticFile(`vox/${p}`);

// --------------------------------------------------------------- base layer
/**
 * The take, on the ABSOLUTE timeline.
 *
 * These live at the top level of the composition, NOT inside the per-shot
 * <Sequence>s. That is deliberate and load-bearing: inside a Sequence both
 * useCurrentFrame() and the media clock are shot-relative, so an
 * <OffthreadVideo> there restarts at 0.00s on every cut and the picture
 * desyncs from the audio (his lips land on the wrong words). Passing
 * startFrom fixes the clock but turns every frame into a proxy seek, which
 * times out the render. Hoisting the video to the top level gives it the
 * absolute clock for free, with no seeking. align_gate.py (gate 8) locks
 * this in permanently.
 *
 * Punch-ins stay real scale transforms about a measured face-centre origin;
 * the active shot is looked up from the absolute frame.
 */
const activeShot = (frame: number): Shot =>
  SHOTS.find((sh) => frame >= s(sh.from) && frame < s(sh.to)) ?? SHOTS[SHOTS.length - 1];

const BASE_KINDS: ShotKind[] = ['full', 'guide', 'burst'];

const BaseFull: React.FC = () => {
  const frame = useCurrentFrame(); // absolute
  const shot = activeShot(frame);
  if (!BASE_KINDS.includes(shot.kind)) return null;
  const f0 = s(shot.from);
  const f1 = s(shot.to);
  const drift = interpolate(frame, [f0, f1], [0, 0.008], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const k = (shot.scale ?? 1) + drift;
  return (
    <AbsoluteFill style={{overflow: 'hidden', background: '#000'}}>
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 0,
          width: W,
          height: H,
          transform: `scale(${k})`,
          transformOrigin: `${shot.ox ?? 540}px ${shot.oy ?? 880}px`,
        }}
      >
        <OffthreadVideo
          src={asset('base30.mp4')}
          muted
          style={{width: W, height: H, objectFit: 'cover'}}
        />
      </div>
    </AbsoluteFill>
  );
};

/**
 * The s6b PIP card. Also top-level, for the same absolute clock. The transform
 * is solved from the measured face box: scale 460/1080 with a -60px lift puts
 * the top of his head at 897px and his chin at 1328px on the finished frame.
 */
export const PIP = {x: 552, y: 760, w: 460, h: 560, k: 460 / 1080, lift: -60};

const BasePip: React.FC = () => {
  const frame = useCurrentFrame(); // absolute
  const shot = SHOTS.find((x) => x.id === 's6b');
  if (!shot) return null;
  const f0 = s(shot.from);
  if (frame < f0 || frame >= s(shot.to)) return null;
  const cardT = ease(frame, f0 + 3, 12);
  return (
    <div
      style={{
        position: 'absolute',
        left: PIP.x,
        top: PIP.y,
        width: PIP.w,
        height: PIP.h,
        borderRadius: 30,
        overflow: 'hidden',
        border: '2px solid #26272A',
        boxShadow: '0 26px 60px rgba(0,0,0,0.72)',
        transform: `translateY(${40 * (1 - cardT)}px)`,
      }}
    >
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: PIP.lift,
          width: W,
          height: H,
          transform: `scale(${PIP.k})`,
          transformOrigin: '0 0',
        }}
      >
        <OffthreadVideo
          src={asset('base30.mp4')}
          muted
          style={{width: W, height: H, objectFit: 'cover'}}
        />
      </div>
    </div>
  );
};

// --------------------------------------------------------------- name l3
const NameLower: React.FC = () => {
  const frame = useCurrentFrame(); // top-level: absolute
  const inT = ease(frame, s(BEATS.nameIn), 9);
  const outT = 1 - ease(frame, s(BEATS.nameOut) - 5, 6);
  const t = Math.min(inT, outT);
  if (t <= 0.001) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: 70,
        top: 1250,
        background: YELLOW,
        padding: '18px 30px 20px',
        transform: `translateX(${-46 * (1 - inT)}px)`,
        clipPath: `inset(0 ${(1 - t) * 100}% 0 0)`,
        filter: 'drop-shadow(0 14px 30px rgba(0,0,0,0.5))',
      }}
    >
      <div
        style={{
          fontFamily: FONT,
          fontWeight: 700,
          fontSize: 50,
          color: INK,
          letterSpacing: '-0.015em',
          whiteSpace: 'nowrap',
        }}
      >
        Johann Sathianathen
      </div>
      <div
        style={{
          fontFamily: FONT,
          fontWeight: 500,
          fontSize: 32,
          color: 'rgba(17,17,17,0.72)',
          marginTop: 4,
          whiteSpace: 'nowrap',
        }}
      >
        Cyndra AI
      </div>
    </div>
  );
};

// --------------------------------------------------------------- scrims
const BottomScrim: React.FC<{top?: number}> = ({top = 1320}) => (
  <div
    style={{
      position: 'absolute',
      left: 0,
      right: 0,
      top,
      bottom: 0,
      background:
        'linear-gradient(to bottom, rgba(0,0,0,0) 0%, rgba(0,0,0,0.86) 42%, rgba(0,0,0,0.99) 62%, #000 100%)',
    }}
  />
);

const TopScrim: React.FC = () => (
  <div
    style={{
      position: 'absolute',
      left: 0,
      right: 0,
      top: 0,
      height: 300,
      background: 'linear-gradient(to bottom, rgba(0,0,0,0.55), rgba(0,0,0,0))',
    }}
  />
);

// --------------------------------------------------------------- montage A
/**
 * Two frozen card rows lifted straight out of Johann's own previous reel
 * (CLAUDE CODE / CURSOR / TERMINAL and LOVABLE / SHOPIFY / WORDPRESS).
 * Deliberately FREEZE-FRAMES cropped above his face: any moving footage of him
 * from another reel puts his lips on the wrong words, which reads as broken.
 * Parallax push-in supplies the motion instead.
 */
const MontageA: React.FC<{shot: Shot}> = ({shot}) => {
  const frame = useCurrentFrame();
  const len = s(shot.to) - s(shot.from);
  const kick = ease(frame, 4, 10);
  const in1 = ease(frame, 0, 12);
  const in2 = ease(frame, 5, 12);
  const br = ease(frame, 10, 10);
  const k1 = interpolate(frame, [0, len], [1.0, 1.045], {extrapolateRight: 'clamp'});
  const k2 = interpolate(frame, [0, len], [1.03, 1.075], {extrapolateRight: 'clamp'});
  const strip = (
    src: string,
    top: number,
    k: number,
    origin: string,
    tIn: number,
    dx: number,
  ) => (
    <div
      style={{
        position: 'absolute',
        left: 30,
        top,
        width: 1020,
        height: 470,
        overflow: 'hidden',
        borderRadius: 10,
        border: '2px solid #2A2C2E',
        boxShadow: '0 26px 60px rgba(0,0,0,0.72)',
        transform: `translate(${dx * (1 - tIn)}px, ${34 * (1 - tIn)}px)`,
      }}
    >
      <Img
        src={asset(`img/${src}`)}
        style={{
          width: 1020,
          height: 470,
          display: 'block',
          transform: `scale(${k})`,
          transformOrigin: origin,
        }}
      />
    </div>
  );
  return (
    <AbsoluteFill style={{background: '#0B0C0A', overflow: 'hidden'}}>
      <Grain />
      <div
        style={{
          position: 'absolute',
          left: 62,
          top: 300,
          display: 'flex',
          alignItems: 'center',
          gap: 14,
          opacity: kick,
        }}
      >
        <div style={{width: 52, height: 6, background: YELLOW}} />
        <span
          style={{
            fontFamily: FONT,
            fontWeight: 700,
            fontSize: 30,
            letterSpacing: '0.17em',
            color: YELLOW,
          }}
        >
          MY LAST REELS
        </span>
      </div>
      {strip('row_claude.png', 380, k1, '30% 40%', in1, -30)}
      {strip('row_lovable.png', 890, k2, '72% 60%', in2, 30)}
      <CornerBrackets inset={40} arm={100} t={br} />
    </AbsoluteFill>
  );
};

// --------------------------------------------------------------- montage B
// The receipt cutaway: a frozen screen of a previous edit with its own
// generated graphic cards, under a masthead card. Proof, not a claim. A still,
// for the same reason montage A is: no lips on the wrong words.
const MontageB: React.FC = () => {
  const frame = useCurrentFrame();
  const cardT = ease(frame, 0, 10);
  const headT = ease(frame, 6, 9);
  const brT = ease(frame, 12, 10);
  const CW = 960;
  const CH = 572;
  const CX = 60;
  const CY = 640;
  return (
    <AbsoluteFill style={{background: '#0B0C0A', overflow: 'hidden'}}>
      <Grain />
      <div
        style={{
          position: 'absolute',
          left: CX,
          top: CY,
          width: CW,
          height: CH,
          borderRadius: 16,
          overflow: 'hidden',
          border: '2px solid #2A2C2E',
          transform: `translateY(${60 * (1 - cardT)}px) scale(${0.96 + 0.04 * cardT})`,
          boxShadow: '0 30px 70px rgba(0,0,0,0.7)',
        }}
      >
        <Img src={asset('img/panel_edit.png')} style={{width: CW, height: CH, display: 'block'}} />
        <CornerBrackets inset={18} arm={74} t={brT} weight={5} />
      </div>

      <div
        style={{
          position: 'absolute',
          left: 62,
          top: 262,
          display: 'flex',
          alignItems: 'center',
          gap: 14,
          opacity: headT,
        }}
      >
        <div style={{width: 52, height: 6, background: YELLOW}} />
        <span
          style={{
            fontFamily: FONT,
            fontWeight: 700,
            fontSize: 30,
            letterSpacing: '0.17em',
            color: YELLOW,
          }}
        >
          ONE OF MY LAST REELS
        </span>
      </div>

      <Receipt
        width={780}
        t={headT}
        from="left"
        style={{left: 60, top: 352}}
        masthead={
          <>
            <div style={{width: 16, height: 16, borderRadius: 8, background: YELLOW}} />
            <span style={{...cnStyle, fontSize: 54, color: '#fff'}}>MADE BY: CODE</span>
          </>
        }
      >
        <span style={{fontSize: 40}}>No editor touched this video</span>
      </Receipt>
    </AbsoluteFill>
  );
};

// --------------------------------------------------------------- montage C
/**
 * Big stat type over one frozen card row on dark grain - the Vox
 * "1 gigawatt data center = <$50 billion" frame.
 * Both figures HARD IN at their final value and animate scale/opacity only.
 * A counter that ramps puts a false claim on screen for a few frames
 * ("54% automated", "1 editor"), which is worse than having no motion.
 */
const MontageC: React.FC<{shot: Shot}> = ({shot}) => {
  const frame = useCurrentFrame();
  const abs = frame + s(shot.from);
  const len = s(shot.to) - s(shot.from);
  const s100 = ease(abs, s(BEATS.stat100), 8);
  const s0 = ease(abs, s(BEATS.stat0), 8);
  const stripT = ease(frame, 0, 9);
  const k = interpolate(frame, [0, len], [1.0, 1.05], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: '#0B0C0A', overflow: 'hidden'}}>
      <Grain />
      <div
        style={{
          position: 'absolute',
          left: 0,
          top: 716,
          width: 1080,
          height: 498,
          overflow: 'hidden',
          borderTop: '2px solid rgba(255,255,255,0.14)',
          borderBottom: '2px solid rgba(255,255,255,0.14)',
          boxShadow: '0 28px 64px rgba(0,0,0,0.72)',
        }}
      >
        <Img
          src={asset('img/row_perplexity.png')}
          style={{
            width: 1080,
            height: 498,
            display: 'block',
            transform: `scale(${(0.985 + 0.015 * stripT) * k})`,
            transformOrigin: '540px 249px',
          }}
        />
      </div>

      <div
        style={{
          position: 'absolute',
          left: 70,
          top: 300,
          opacity: s100,
          transform: `scale(${0.9 + 0.1 * s100})`,
          transformOrigin: '0 50%',
        }}
      >
        <div style={{...bigStatStyle, fontSize: 200}}>100%</div>
        <div style={{...bigStatStyle, fontSize: 96, marginTop: 6}}>automated</div>
      </div>

      <div
        style={{
          position: 'absolute',
          left: 70,
          top: 1268,
          display: 'flex',
          alignItems: 'baseline',
          gap: 22,
          opacity: s0,
          transform: `scale(${0.9 + 0.1 * s0})`,
          transformOrigin: '0 50%',
        }}
      >
        <div style={{...bigStatStyle, fontSize: 140}}>0</div>
        <div style={{...bigStatStyle, fontSize: 80}}>editors</div>
      </div>

      <CornerBrackets inset={40} arm={100} t={stripT} />
    </AbsoluteFill>
  );
};

// --------------------------------------------------------------- sites
/**
 * A star count is a factual claim, so the VALUE never animates - only scale and
 * opacity. A ramping counter showed 39,870 for a repo with 48,191 stars.
 */
const StarCount: React.FC<{target: number; start: number}> = ({target, start}) => {
  const frame = useCurrentFrame();
  const t = ease(frame, start, 9);
  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 8,
        opacity: t,
        transform: `scale(${0.86 + 0.14 * t})`,
      }}
    >
      <Star size={30} fill={YELLOW} />
      <span style={{fontFamily: FONT, fontWeight: 700, fontSize: 34, color: YELLOW}}>
        {fmt(target)}
      </span>
    </span>
  );
};

const RepoBar: React.FC<{repo: string; stars: number; start: number; width: number}> = ({
  repo,
  stars,
  start,
  width,
}) => (
  <div
    style={{
      width,
      height: 88,
      background: '#000',
      display: 'flex',
      alignItems: 'center',
      padding: '0 22px',
      boxSizing: 'border-box',
      gap: 14,
      borderTop: `4px solid ${YELLOW}`,
    }}
  >
    <GithubMark size={34} />
    <span style={{fontFamily: FONT, fontWeight: 700, fontSize: 34, color: '#fff'}}>{repo}</span>
    <div style={{flex: 1}} />
    <StarCount target={stars} start={start} />
  </div>
);

// Real remotion.dev / hyperframes.dev hero screenshots, stacked as overlapping
// cards with a hard shadow, each carrying its own GitHub receipt bar.
const Sites: React.FC = () => {
  const frame = useCurrentFrame();
  const t1 = ease(frame, 0, 11);
  const t2 = ease(frame, s(BEATS.hyperframesCard - BEATS.remotionCard), 11);
  return (
    <AbsoluteFill style={{background: '#0A0B0A', overflow: 'hidden'}}>
      <Grain />
      <div
        style={{
          position: 'absolute',
          left: 70,
          top: 264,
          width: 940,
          transform: `translateY(${230 * (1 - t1)}px) rotate(-1.1deg)`,
          filter: 'drop-shadow(0 26px 56px rgba(0,0,0,0.75))',
        }}
      >
        <Img
          src={asset('img/remotion_hero.png')}
          style={{width: 940, display: 'block', border: '2px solid #24262A', borderBottom: 'none'}}
        />
        <RepoBar repo="remotion-dev/remotion" stars={STARS.remotion} start={3} width={940} />
      </div>

      <div
        style={{
          position: 'absolute',
          left: 70,
          top: 790,
          width: 940,
          transform: `translateX(${430 * (1 - t2)}px) rotate(1.1deg)`,
          opacity: t2,
          filter: 'drop-shadow(0 26px 56px rgba(0,0,0,0.75))',
        }}
      >
        <Img
          src={asset('img/hyperframes_hero.png')}
          style={{width: 940, display: 'block', border: '2px solid #24262A', borderBottom: 'none'}}
        />
        <RepoBar
          repo="heygen-com/hyperframes"
          stars={STARS.hyperframes}
          start={s(BEATS.hyperframesCard - BEATS.remotionCard) + 3}
          width={940}
        />
      </div>
    </AbsoluteFill>
  );
};

// --------------------------------------------------------------- pip / chips
const MarkTile: React.FC<{src: string}> = ({src}) => (
  <div
    style={{
      width: 54,
      height: 54,
      borderRadius: 13,
      overflow: 'hidden',
      flex: '0 0 auto',
      border: '1.5px solid rgba(255,255,255,0.16)',
    }}
  >
    <Img src={asset(`img/${src}`)} style={{width: 54, height: 54, display: 'block'}} />
  </div>
);

const AGENTS: {label: string; mark: string}[] = [
  {label: 'Claude Code', mark: 'claude.png'},
  {label: 'Codex', mark: 'openai.png'},
  {label: 'ChatGPT', mark: 'openai.png'},
  {label: 'Claude', mark: 'claude.png'},
];

const CHIP_TOP = 760;
const CHIP_H = 119;
const CHIP_GAP = 27;

const Chip: React.FC<{i: number; abs: number}> = ({i, abs}) => {
  const slotT = ease(abs, s(BEATS.slotsIn) + i * 2, 7);
  const start = s(BEATS.chips[i]);
  const inT = ease(abs, start, 8);
  const chk = ease(abs, start + 5, 8);
  const top = CHIP_TOP + i * (CHIP_H + CHIP_GAP);
  const a = AGENTS[i];
  return (
    <>
      <div
        style={{
          position: 'absolute',
          left: 70,
          top,
          width: 450,
          height: CHIP_H,
          boxSizing: 'border-box',
          background: 'rgba(255,255,255,0.035)',
          borderRadius: 16,
          opacity: slotT * (1 - inT) * 0.8,
        }}
      />
      <div
        style={{
          position: 'absolute',
          left: 70,
          top,
          width: 450,
          height: CHIP_H,
          boxSizing: 'border-box',
          background: '#17181A',
          borderRadius: 16,
          display: 'flex',
          alignItems: 'center',
          gap: 18,
          paddingLeft: 28,
          paddingRight: 22,
          overflow: 'hidden',
          opacity: inT,
          transform: `translateX(${-40 * (1 - inT)}px)`,
          boxShadow: '0 14px 30px rgba(0,0,0,0.55)',
        }}
      >
        <div
          style={{
            position: 'absolute',
            left: 0,
            top: 0,
            bottom: 0,
            width: 9,
            background: YELLOW,
          }}
        />
        <MarkTile src={a.mark} />
        <span
          style={{
            fontFamily: FONT,
            fontWeight: 700,
            fontSize: 37,
            color: '#fff',
            letterSpacing: '-0.015em',
          }}
        >
          {a.label}
        </span>
        <div style={{flex: 1}} />
        <Check size={34} stroke={YELLOW} progress={chk} />
      </div>
    </>
  );
};

/** Blurred real imagery + grain. Never a flat colour panel, never cream. */
const PanelBg: React.FC = () => (
  <>
    <div style={{position: 'absolute', inset: 0, overflow: 'hidden'}}>
      <Img
        src={asset('img/gh_files.png')}
        style={{
          position: 'absolute',
          left: -360,
          top: -180,
          width: 2000,
          filter: 'blur(30px) brightness(0.5) saturate(0.55)',
          opacity: 0.6,
        }}
      />
    </div>
    <Grain opacity={0.6} tint="rgba(9,10,9,0.84)" />
  </>
);

/**
 * The agent panel. Real GitHub file rows (.claude / .codex / .agents) as the
 * receipt on top, four marked chips filling the left column on each spoken
 * name, the take in a card on the right. The card transform is solved from the
 * measured face box: top of head lands 897px, chin 1168px on the final frame.
 */
const Pip: React.FC<{shot: Shot}> = ({shot}) => {
  const frame = useCurrentFrame();
  const abs = frame + s(shot.from);
  const headT = ease(frame, 0, 10);
  const cardT = ease(frame, 3, 12);

  const K = 460 / 1080; // 0.4259
  const CX = 552;
  const CW = 460;
  const CH = 560;

  return (
    <AbsoluteFill style={{background: '#0A0B0A', overflow: 'hidden'}}>
      <PanelBg />

      <Receipt
        width={940}
        t={headT}
        fade={false}
        from="top"
        style={{left: 70, top: 262}}
        mastheadBg="#0D1117"
        masthead={
          <>
            <GithubMark size={32} />
            <span style={{fontFamily: FONT, fontWeight: 700, fontSize: 33, color: '#fff'}}>
              remotion-dev/remotion
            </span>
          </>
        }
      >
        <Img
          src={asset('img/gh_files.png')}
          style={{width: 900, display: 'block', marginTop: -2}}
        />
      </Receipt>

      <div
        style={{
          position: 'absolute',
          left: 74,
          top: 668,
          display: 'flex',
          alignItems: 'center',
          gap: 14,
          opacity: headT,
        }}
      >
        <div style={{width: 52, height: 6, background: YELLOW}} />
        <span
          style={{
            fontFamily: FONT,
            fontWeight: 700,
            fontSize: 30,
            letterSpacing: '0.17em',
            color: YELLOW,
          }}
        >
          WORKS WITH ANY AI AGENT
        </span>
      </div>

      {[0, 1, 2, 3].map((i) => (
        <Chip key={i} i={i} abs={abs} />
      ))}

    </AbsoluteFill>
  );
};

/**
 * "If you want the full guide, I made it a breakdown" - talking head with the
 * guide receipt card at chest level. Card top (1275px) clears the chin, which
 * maxes at 1247px on the finished frame (0.1s YuNet scan).
 */
const Guide: React.FC<{shot: Shot}> = ({shot}) => {
  const frame = useCurrentFrame();
  const abs = frame + s(shot.from);
  const t = ease(abs, s(BEATS.guideCard), 11);
  const out = 1 - ease(abs, s(19.55) - 6, 6);
  return (
    <AbsoluteFill>
      <Receipt
        width={660}
        t={Math.min(t, out)}
        from="left"
        style={{left: 70, top: 1275}}
        masthead={
          <>
            <div style={{width: 14, height: 14, borderRadius: 7, background: YELLOW}} />
            <span style={{...cnStyle, fontSize: 46, color: '#fff'}}>THE FULL GUIDE</span>
          </>
        }
      >
        <span style={{fontSize: 34}}>Step by step breakdown. Free.</span>
      </Receipt>
    </AbsoluteFill>
  );
};

// --------------------------------------------------------------- cta pill
// "comment EDIT" wipes in at chest level on the left, clear of both the chin
// (max 1197px after the punch-in) and the gesturing hand (min x 465px).
const EditPill: React.FC = () => {
  const frame = useCurrentFrame(); // top-level: absolute
  const t = ease(frame, s(BEATS.pillIn), 9);
  if (t <= 0.001 || frame >= s(28.24)) return null;
  return (
    <div style={{position: 'absolute', left: 80, top: 1232, opacity: Math.min(1, t * 1.6)}}>
      <div
        style={{
          fontFamily: FONT,
          fontWeight: 700,
          fontSize: 32,
          letterSpacing: '0.20em',
          color: '#fff',
          textShadow: '0 2px 10px rgba(0,0,0,0.8)',
          marginBottom: 12,
          clipPath: `inset(0 ${(1 - t) * 100}% 0 0)`,
        }}
      >
        COMMENT
      </div>
      <div
        style={{
          background: YELLOW,
          padding: '10px 26px 16px',
          display: 'inline-block',
          clipPath: `inset(0 ${(1 - t) * 100}% 0 0)`,
          filter: 'drop-shadow(0 16px 32px rgba(0,0,0,0.55))',
        }}
      >
        <span style={{...cnStyle, fontSize: 104, color: INK, lineHeight: 1}}>EDIT</span>
      </div>
    </div>
  );
};

// --------------------------------------------------------------- burst
const BarChart: React.FC<{t: number; w: number}> = ({t, w}) => {
  const bars = [0.34, 0.52, 0.68, 0.86, 1.0];
  return (
    <div
      style={{
        width: w,
        height: 190,
        background: '#101112',
        borderRadius: 14,
        border: '1.5px solid rgba(255,255,255,0.14)',
        padding: '16px 18px',
        boxSizing: 'border-box',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div
        style={{
          fontFamily: FONT,
          fontWeight: 700,
          fontSize: 20,
          letterSpacing: '0.14em',
          color: 'rgba(255,255,255,0.6)',
        }}
      >
        RENDERS / DAY
      </div>
      <div
        style={{
          flex: 1,
          display: 'flex',
          alignItems: 'flex-end',
          gap: 12,
          marginTop: 12,
        }}
      >
        {bars.map((b, i) => {
          const p = interpolate(t, [i * 0.1, i * 0.1 + 0.55], [0, 1], {
            extrapolateLeft: 'clamp',
            extrapolateRight: 'clamp',
          });
          return (
            <div
              key={i}
              style={{
                flex: 1,
                height: `${Math.max(4, b * 100 * p)}%`,
                background: i === bars.length - 1 ? YELLOW : 'rgba(245,225,27,0.42)',
                borderRadius: 3,
              }}
            />
          );
        })}
      </div>
    </div>
  );
};

/**
 * The money beat. He points with his right hand at screen-right, mid-frame
 * (facedet reads the hand as a box at x 621-1057, y 1128-1644 at t=29.20), so
 * three elements spring out of that exact point into the clear right column.
 */
const Burst: React.FC<{shot: Shot}> = ({shot}) => {
  const frame = useCurrentFrame();
  const abs = frame + s(shot.from);
  const inF = s(BEATS.burstIn);
  const outF = s(BEATS.burstOut);
  const L = BURST_COL.left;
  const CW = BURST_COL.right - BURST_COL.left; // 310

  const slots = [
    {top: 385, delay: 0},
    {top: 610, delay: 3},
    {top: 835, delay: 6},
  ];

  const el = (i: number) => {
    const st = interpolate(abs, [inF + slots[i].delay, inF + slots[i].delay + 12], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
      easing: (x) => 1 - Math.pow(1 - x, 4),
    });
    const out = ease(abs, outF + i * 2, 8);
    const cx = L + CW / 2;
    const cy = slots[i].top + 90;
    // travel from the measured hand point to the slot
    const x = interpolate(st, [0, 1], [HAND.x - cx, 0]);
    const y = interpolate(st, [0, 1], [HAND.y - cy, 0]);
    const sc = interpolate(st, [0, 1], [0.16, 1]) * (1 - 0.3 * out);
    const rot = interpolate(st, [0, 1], [-16 + i * 9, 0]) + out * 8;
    return {
      opacity: st * (1 - out),
      transform: `translate(${x + out * 520}px, ${y}px) scale(${sc}) rotate(${rot}deg)`,
      pointerEvents: 'none' as const,
    };
  };

  /** Thin yellow trail from the hand to each element, so the burst reads. */
  const trails = slots.map((sl, i) => {
    const st = interpolate(abs, [inF + sl.delay, inF + sl.delay + 12], [0, 1], {
      extrapolateLeft: 'clamp',
      extrapolateRight: 'clamp',
    });
    const fade = 1 - ease(abs, inF + sl.delay + 10, 12);
    const out = ease(abs, outF + i * 2, 6);
    const cx = L + CW / 2;
    const cy = sl.top + 90;
    const dx = cx - HAND.x;
    const dy = cy - HAND.y;
    const len = Math.hypot(dx, dy) * st;
    const ang = (Math.atan2(dy, dx) * 180) / Math.PI;
    return (
      <div
        key={`tr${i}`}
        style={{
          position: 'absolute',
          left: HAND.x,
          top: HAND.y,
          width: len,
          height: 5,
          background: `linear-gradient(to right, rgba(245,225,27,0), ${YELLOW})`,
          transform: `rotate(${ang}deg)`,
          transformOrigin: '0 50%',
          opacity: fade * 0.85 * (1 - out),
          borderRadius: 3,
        }}
      />
    );
  });

  const sparks = Array.from({length: 8}, (_, i) => {
    const ang = (-115 + i * 17) * (Math.PI / 180);
    const p = ease(abs, inF - 1 + Math.floor(i / 3), 12);
    const d = 240 * p;
    return (
      <div
        key={i}
        style={{
          position: 'absolute',
          left: HAND.x + Math.cos(ang) * d,
          top: HAND.y + Math.sin(ang) * d,
          width: 12 + (i % 3) * 5,
          height: 12 + (i % 3) * 5,
          background: YELLOW,
          borderRadius: 3,
          opacity: Math.max(0, (1 - p) * 0.95),
          transform: `rotate(${p * 220 + i * 30}deg)`,
        }}
      />
    );
  });

  const barT = ease(abs, inF + 6, 20);
  const badgeT = ease(abs, inF + 3, 9);

  return (
    <AbsoluteFill>
      {trails}
      {sparks}

      {/* the three elements condense into one chip as they fly off, so a
          graphic is still on screen through "like this". The band y 226-306
          sits above the top of his head, which never rises above 332px in
          29.50-30.05 (measured every 0.1s). */}
      <div
        style={{
          position: 'absolute',
          left: 600,
          top: 222,
          width: 420,
          height: 74,
          background: YELLOW,
          borderRadius: 12,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 14,
          clipPath: `inset(0 ${(1 - ease(abs, outF, 8)) * 100}% 0 0)`,
          filter: 'drop-shadow(0 14px 30px rgba(0,0,0,0.5))',
        }}
      >
        <Star size={30} fill={INK} />
        <span style={{fontFamily: FONT, fontWeight: 700, fontSize: 34, color: INK}}>{fmt(STARS.remotion)}</span>
        <span style={{color: 'rgba(17,17,17,0.4)', fontSize: 30}}>|</span>
        <Star size={30} fill={INK} />
        <span style={{fontFamily: FONT, fontWeight: 700, fontSize: 34, color: INK}}>{fmt(STARS.hyperframes)}</span>
      </div>

      {/* 1 - floating GitHub receipt */}
      <div style={{position: 'absolute', left: L, top: slots[0].top, width: CW, ...el(0)}}>
        <div
          style={{
            width: CW,
            filter: 'drop-shadow(0 18px 36px rgba(0,0,0,0.66))',
          }}
        >
          <div
            style={{
              background: '#0D1117',
              padding: '11px 16px',
              display: 'flex',
              alignItems: 'center',
              gap: 10,
            }}
          >
            <GithubMark size={28} />
            <span style={{fontFamily: FONT, fontWeight: 700, fontSize: 28, color: '#fff'}}>
              GitHub
            </span>
          </div>
          <div style={{background: '#fff', padding: '14px 16px 16px'}}>
            <div
              style={{
                fontFamily: FONT,
                fontWeight: 700,
                fontSize: 29,
                color: INK,
                lineHeight: 1.14,
                letterSpacing: '-0.015em',
              }}
            >
              remotion-dev/
              <br />
              remotion
            </div>
            <div
              style={{
                marginTop: 10,
                display: 'inline-flex',
                alignItems: 'center',
                gap: 7,
                background: YELLOW,
                padding: '4px 10px',
              }}
            >
              <Star size={22} fill={INK} />
              <span style={{fontFamily: FONT, fontWeight: 700, fontSize: 26, color: INK}}>
                {fmt(STARS.remotion)}
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* 2 - bar chart ticking up */}
      <div style={{position: 'absolute', left: L, top: slots[1].top, width: CW, ...el(1)}}>
        <div style={{filter: 'drop-shadow(0 18px 36px rgba(0,0,0,0.6))'}}>
          <BarChart t={barT} w={CW} />
        </div>
      </div>

      {/* 3 - star badge */}
      <div style={{position: 'absolute', left: L + 40, top: slots[2].top, ...el(2)}}>
        <div
          style={{
            background: YELLOW,
            borderRadius: 18,
            padding: '14px 22px 16px',
            width: CW - 40,
            boxSizing: 'border-box',
            filter: 'drop-shadow(0 18px 36px rgba(0,0,0,0.6))',
          }}
        >
          <div style={{display: 'flex', alignItems: 'center', gap: 10}}>
            <Star size={34} fill={INK} />
            <span
              style={{
                fontFamily: FONT,
                fontWeight: 700,
                fontSize: 44,
                color: INK,
                opacity: badgeT,
              }}
            >
              {fmt(STARS.hyperframes)}
            </span>
          </div>
          <div
            style={{
              fontFamily: FONT,
              fontWeight: 700,
              fontSize: 20,
              letterSpacing: '0.16em',
              color: 'rgba(17,17,17,0.66)',
              marginTop: 4,
            }}
          >
            HYPERFRAMES
          </div>
        </div>
      </div>
    </AbsoluteFill>
  );
};

// --------------------------------------------------------------- end card
const EndCard: React.FC = () => {
  const frame = useCurrentFrame();
  const t = ease(frame, s(BEATS.endCard), 12);
  if (t <= 0.001) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: 60,
        top: 1205,
        width: 960,
        background: YELLOW,
        padding: '26px 34px 24px',
        boxSizing: 'border-box',
        transform: `translateY(${170 * (1 - t)}px)`,
        opacity: Math.min(1, t * 2),
        filter: 'drop-shadow(0 -8px 40px rgba(0,0,0,0.55))',
      }}
    >
      <div
        style={{
          fontFamily: FONT,
          fontWeight: 700,
          fontSize: 84,
          color: INK,
          letterSpacing: '-0.03em',
          lineHeight: 1,
        }}
      >
        no editor. just code.
      </div>
      <div style={{height: 3, background: 'rgba(17,17,17,0.25)', margin: '18px 0 14px'}} />
      <div
        style={{
          fontFamily: FONT,
          fontWeight: 700,
          fontSize: 29,
          letterSpacing: '0.13em',
          color: 'rgba(17,17,17,0.78)',
        }}
      >
        COMMENT &ldquo;EDIT&rdquo; FOR THE FULL GUIDE
      </div>
    </div>
  );
};

// --------------------------------------------------------------- shot switch
const ShotBody: React.FC<{shot: Shot}> = ({shot}) => {
  switch (shot.kind) {
    case 'montageA':
      return <MontageA shot={shot} />;
    case 'montageB':
      return <MontageB />;
    case 'montageC':
      return <MontageC shot={shot} />;
    case 'sites':
      return <Sites />;
    case 'guide':
      return <Guide shot={shot} />;
    case 'pip':
      return <Pip shot={shot} />;
    case 'burst':
      return <Burst shot={shot} />;
    case 'full':
      // the base layer is hoisted to the top level for the absolute clock
      return null;
    default:
      return null;
  }
};

export const VoxReel: React.FC = () => {
  const {durationInFrames} = useVideoConfig();
  ensureVoxFonts();
  return (
    <AbsoluteFill style={{background: '#000'}}>
      {/* BaseFull first: the graphic shots below are opaque and cut it away. */}
      <BaseFull />
      {SHOTS.map((shot) => {
        const from = s(shot.from);
        const to = Math.min(s(shot.to), durationInFrames);
        return (
          <Sequence key={shot.id} from={from} durationInFrames={to - from} layout="none">
            <ShotBody shot={shot} />
          </Sequence>
        );
      })}
      {/* BasePip AFTER the shot layer: the s6b panel is an opaque AbsoluteFill,
          so the card has to be drawn on top of it, not under it. */}
      <BasePip />
      {/* overlays live on the global (absolute) timeline, not in a Sequence */}
      <NameLower />
      <EditPill />
      <EndCard />
      <Caption />
    </AbsoluteFill>
  );
};
