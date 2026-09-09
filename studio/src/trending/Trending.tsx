import React, {useMemo} from 'react';
import {AbsoluteFill, Sequence, useVideoConfig} from 'remotion';
import {AvatarSlot} from '../AvatarSlot';
import {buildPlaceholderCaptions} from '../captions';
import {IsenPanel} from '../panels/IsenPanel';
import {KineticPanel} from '../panels/KineticPanel';
import {ShotPanel} from '../panels/ShotPanel';
import {TopicPanel} from '../panels/TopicPanel';
import type {EpisodeProps} from '../types';
import {makeAccentTest} from './accents';
import {Captions} from './Captions';
import {TrendingCta} from './CtaPanel';
import {HookPanel} from './HookPanel';
import {RepoCard} from './RepoCard';
import {T_COLORS, T_LAYOUT} from './theme';

/**
 * "Trending" — a Remotion reproduction of the best-performing repo-radar
 * format (see trending/theme.ts for the measurements and the reference).
 *
 * Structure per scene:
 *   intro -> full-frame dark title treatment (no card)
 *   repo  -> the dark card: TRENDING #N / owner / NAME / desc / stars + chip
 *   cta   -> card-less closing title + handle pill
 * Captions are drawn once, over everything, from absolute word timings — so
 * they appear on every scene, as in the reference.
 */
export const Trending: React.FC<EpisodeProps> = ({
  date,
  scenes,
  avatarSrc,
  avatarW,
  avatarH,
  avatarFocusY,
  avatarTransparent,
  layout = 'split',
  captions,
  accentWords,
}) => {
  const fullscreen = layout === 'fullscreen';
  const {fps} = useVideoConfig();

  const words = useMemo(
    () => captions ?? buildPlaceholderCaptions(scenes),
    [captions, scenes],
  );

  const accent = useMemo(
    () => makeAccentTest(scenes, accentWords),
    [scenes, accentWords],
  );

  const timeline = useMemo(() => {
    let from = 0;
    let repoRank = 0;
    return scenes.map((scene, i) => {
      const durationInFrames = Math.round(scene.durationSec * fps);
      if (scene.type === 'repo') repoRank += 1;
      const entry = {scene, from, durationInFrames, rank: repoRank, key: i};
      from += durationInFrames;
      return entry;
    });
  }, [scenes, fps]);

  return (
    <AbsoluteFill
      style={{background: avatarTransparent ? undefined : T_COLORS.ground}}
    >
      {/* Graphic region: the full frame in fullscreen, the top 960 in split
          (which is the only part ffmpeg keeps — see prep.py's crop). */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: T_LAYOUT.width,
          height: fullscreen ? T_LAYOUT.height : T_LAYOUT.seam,
          overflow: 'hidden',
          background: fullscreen ? 'transparent' : T_COLORS.ground,
        }}
      >
        {timeline.map(({scene, from, durationInFrames, rank, key}) => (
          <Sequence
            key={key}
            from={from}
            durationInFrames={durationInFrames}
            name={scene.type === 'repo' ? `repo-${rank}` : scene.type}
          >
            {scene.type === 'intro' ? (
              <HookPanel
                date={date}
                durationInFrames={durationInFrames}
                eyebrow={scene.eyebrow}
                line1={scene.line1}
                line2={scene.line2}
                showGithub={scene.showGithub}
              />
            ) : scene.type === 'repo' ? (
              <RepoCard
                scene={scene}
                rank={rank}
                durationInFrames={durationInFrames}
              />
            ) : scene.type === 'cta' ? (
              <TrendingCta
                durationInFrames={durationInFrames}
                line1={scene.line1}
                line2={scene.line2}
                badge={scene.badge}
              />
            ) : scene.type === 'topic' ? (
              <TopicPanel scene={scene} durationInFrames={durationInFrames} />
            ) : scene.type === 'shot' ? (
              <ShotPanel scene={scene} durationInFrames={durationInFrames} />
            ) : scene.type === 'kinetic' ? (
              <KineticPanel scene={scene} durationInFrames={durationInFrames} />
            ) : scene.type === 'isen' ? (
              <IsenPanel scene={scene} />
            ) : null}
          </Sequence>
        ))}
      </div>

      {fullscreen ? null : (
        <AvatarSlot
          avatarSrc={avatarSrc}
          sourceW={avatarW}
          sourceH={avatarH}
          focusY={avatarFocusY}
          transparent={avatarTransparent}
        />
      )}

      <Captions words={words} accent={accent} />
    </AbsoluteFill>
  );
};
