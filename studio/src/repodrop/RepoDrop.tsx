import React from 'react';
import {AbsoluteFill, Sequence, useVideoConfig} from 'remotion';
import type {EpisodeProps, Scene, KaraokeWord} from '../types';
import {RD_CARD} from './theme';
import type {RDCue} from './Caption';
import {RDIntro, RDRepo, RDStat, RDCard, RDShot, RDCta} from './Panels';

/** Group a scene's karaoke words into 1-2 word serif cues, relative to the scene. */
const evenCues = (text: string, dur: number): RDCue[] => {
  const w = (text || '').split(/\s+/).filter(Boolean);
  if (!w.length) return [];
  const groups: string[] = [];
  for (let i = 0; i < w.length; i += 2) groups.push(w.slice(i, i + 2).join(' '));
  const each = dur / groups.length;
  return groups.map((text, i) => ({
    start: i * each,
    end: (i + 1) * each,
    text: text.replace(/[,.]+$/, ''),
  }));
};

const cuesFor = (words: KaraokeWord[] | undefined, startSec: number, endSec: number): RDCue[] => {
  if (!words?.length) return [];
  const inWindow = words.filter(
    (w) => w.startMs / 1000 >= startSec - 0.01 && w.endMs / 1000 <= endSec + 0.01,
  );
  const out: RDCue[] = [];
  for (let i = 0; i < inWindow.length; i += 2) {
    const g = inWindow.slice(i, i + 2);
    const text = g.map((x) => x.word).join(' ').replace(/[,.]+$/, '').trim();
    if (text) {
      out.push({
        start: g[0].startMs / 1000 - startSec,
        end: g[g.length - 1].endMs / 1000 - startSec,
        text,
      });
    }
  }
  for (let k = 0; k < out.length - 1; k++) out[k].end = Math.min(out[k].end, out[k + 1].start);
  if (out.length) out[out.length - 1].end = endSec - startSec;
  return out;
};

/**
 * Knock a rounded-top rectangle out of the bottom of the frame so ffmpeg can
 * composite the avatar into it. Rendered as a mask rather than a painted box,
 * because the avatar has to show *through* the graphics layer.
 */
const CARD_MASK =
  `url("data:image/svg+xml;utf8,${encodeURIComponent(
    `<svg xmlns='http://www.w3.org/2000/svg' width='1080' height='1920'>` +
      `<rect width='1080' height='1920' fill='white'/>` +
      `<rect x='0' y='${RD_CARD.top}' width='1080' height='${RD_CARD.height}' ` +
      `rx='${RD_CARD.radius}' ry='${RD_CARD.radius}' fill='black'/></svg>`,
  )}")`;

const SceneView: React.FC<{scene: Scene; cues: RDCue[]}> = ({scene, cues}) => {
  switch (scene.type) {
    case 'intro':
      return <RDIntro cues={cues} line1={scene.line1} line2={scene.line2} />;
    case 'repo':
      return <RDRepo cues={cues} repo={scene.repo} stars={scene.stars}
        today={scene.today} desc={scene.desc} />;
    case 'topic':
      return <RDStat cues={cues} stat={scene.stat} statLabel={scene.statLabel} pill={scene.pill} />;
    case 'kinetic':
      return <RDCard cues={cues} title={scene.keyText} />;
    case 'isen':
      return <RDCard cues={cues} title={scene.title}
        items={(scene.items ?? []).map((i) => i.label)} light={scene.variant === 'faceoff'} />;
    case 'shot':
      return <RDShot cues={cues} image={scene.image} label={scene.label} />;
    case 'cta':
      return <RDCta cues={cues} badge={scene.badge} line1={scene.line1} line2={scene.line2} />;
    case 'avatar':
    default:
      return null; // fullscreen talking head — the footage shows through
  }
};

export const RepoDrop: React.FC<EpisodeProps> = ({scenes, captions, layout = 'pip'}) => {
  const {fps} = useVideoConfig();
  let acc = 0;
  return (
    <AbsoluteFill style={{backgroundColor: 'transparent'}}>
      {scenes.map((scene, i) => {
        const start = acc;
        const end = acc + scene.durationSec;
        acc = end;
        const isAvatar = scene.type === 'avatar';
        // PIP: graphic on top with the avatar showing through the card below.
        const card = layout === 'pip' && !isAvatar && (scene as {half?: boolean}).half !== false;
        return (
          <Sequence key={i} from={Math.round(start * fps)}
            durationInFrames={Math.max(1, Math.round(scene.durationSec * fps))}>
            <AbsoluteFill style={card
              ? {WebkitMaskImage: CARD_MASK, maskImage: CARD_MASK,
                 WebkitMaskSize: '100% 100%', maskSize: '100% 100%'}
              : undefined}>
              <SceneView
                scene={scene}
                cues={
                  cuesFor(captions, start, end).length
                    ? cuesFor(captions, start, end)
                    : evenCues((scene as {text?: string}).text ?? '', scene.durationSec)
                }
              />
            </AbsoluteFill>
          </Sequence>
        );
      })}
    </AbsoluteFill>
  );
};
