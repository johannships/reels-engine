import React, {useMemo} from 'react';
import {AbsoluteFill, Sequence, useVideoConfig} from 'remotion';
import {AvatarSlot} from './AvatarSlot';
import {buildPlaceholderCaptions} from './captions';
import {Karaoke} from './Karaoke';
import {CtaPanel} from './panels/CtaPanel';
import {IntroPanel} from './panels/IntroPanel';
import {RepoPanel} from './panels/RepoPanel';
import {KineticPanel} from './panels/KineticPanel';
import {IsenPanel} from './panels/IsenPanel';
import {OverlayText} from './panels/OverlayText';
import {ShotPanel} from './panels/ShotPanel';
import {TopicPanel} from './panels/TopicPanel';
import {COLORS, LAYOUT} from './theme';
import type {EpisodeProps} from './types';

export const RepoRadar: React.FC<EpisodeProps> = ({
  date,
  scenes,
  avatarSrc,
  avatarW,
  avatarH,
  avatarFocusY,
  avatarTransparent,
  layout = 'split',
  captions,
}) => {
  const fullscreen = layout === 'fullscreen';
  const {fps} = useVideoConfig();

  const words = useMemo(
    () => captions ?? buildPlaceholderCaptions(scenes),
    [captions, scenes],
  );

  const timeline = useMemo(() => {
    let from = 0;
    let repoRank = 0;
    return scenes.map((scene, i) => {
      const durationInFrames = Math.round(scene.durationSec * fps);
      if (scene.type === 'repo') {
        repoRank += 1;
      }
      const entry = {scene, from, durationInFrames, rank: repoRank, key: i};
      from += durationInFrames;
      return entry;
    });
  }, [scenes, fps]);

  return (
    <AbsoluteFill
      style={{background: avatarTransparent ? undefined : COLORS.ground}}
    >
      {/* Visual canvas: full frame in fullscreen mode, top 960 in split */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: LAYOUT.width,
          height: fullscreen ? LAYOUT.height : LAYOUT.canvasHeight,
          overflow: 'hidden',
          background: fullscreen ? 'transparent' : COLORS.ground,
        }}
      >
        {timeline.map(({scene, from, durationInFrames, rank, key}) => (
          <Sequence
            key={key}
            from={from}
            durationInFrames={durationInFrames}
            name={scene.type === 'repo' ? `repo-${rank}` : scene.type}
          >
            {scene.type === 'avatar' ? (
              scene.overlayText ? (
                <OverlayText
                  text={scene.overlayText}
                  durationInFrames={durationInFrames}
                />
              ) : null
            ) : scene.type === 'isen' ? (
              <IsenPanel scene={scene} />
            ) : scene.type === 'kinetic' ? (
              <KineticPanel scene={scene} durationInFrames={durationInFrames} />
            ) : scene.type === 'intro' ? (
              <IntroPanel
                date={date}
                durationInFrames={durationInFrames}
                eyebrow={scene.eyebrow}
                line1={scene.line1}
                line2={scene.line2}
                logo={scene.logo}
                logo2={scene.logo2}
                showGithub={scene.showGithub}
              />
            ) : scene.type === 'repo' ? (
              <RepoPanel
                scene={scene}
                rank={rank}
                durationInFrames={durationInFrames}
              />
            ) : scene.type === 'topic' ? (
              <TopicPanel scene={scene} durationInFrames={durationInFrames} />
            ) : scene.type === 'shot' ? (
              <ShotPanel scene={scene} durationInFrames={durationInFrames} />
            ) : (
              <CtaPanel
                durationInFrames={durationInFrames}
                line1={scene.line1}
                line2={scene.line2}
                badge={scene.badge}
              />
            )}
          </Sequence>
        ))}
      </div>

      {/* Avatar slot (split layout only) */}
      {fullscreen ? null : (
        <AvatarSlot
          avatarSrc={avatarSrc}
          sourceW={avatarW}
          sourceH={avatarH}
          focusY={avatarFocusY}
          transparent={avatarTransparent}
        />
      )}

      {/* Karaoke captions: seam in split, lower-third in fullscreen */}
      <Karaoke words={words} top={fullscreen ? 1430 : undefined} />
    </AbsoluteFill>
  );
};
