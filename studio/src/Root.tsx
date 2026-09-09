import React from 'react';
import {Composition} from 'remotion';
import episode from './data/episode-01.json';
import {ensureFonts} from './fonts';
import {RepoRadar} from './RepoRadar';
import {RepoDrop} from './repodrop/RepoDrop';
import {LAYOUT} from './theme';
import {Trending} from './trending/Trending';
import type {EpisodeProps} from './types';
import {VoxReel} from './vox/VoxReel';
import {H as VOX_H, W as VOX_W} from './vox/data';

ensureFonts();

const FPS = 30;

const calcDuration = ({props}: {props: EpisodeProps}) => ({
  durationInFrames: Math.round(
    props.scenes.reduce((sum, scene) => sum + scene.durationSec, 0) * FPS,
  ),
});

export const RemotionRoot: React.FC = () => {
  return (
    <>
    {/* Trending is the default style for the repo-radar series: a Remotion
        reproduction of the best-performing "3 AI repos blowing up today"
        reel, measured off the reference (see trending/theme.ts). RepoDrop
        and RepoRadar stay selectable via "style" in script.json. */}
    <Composition
      id="Trending"
      component={Trending}
      width={LAYOUT.width}
      height={LAYOUT.height}
      fps={FPS}
      durationInFrames={45 * FPS}
      defaultProps={episode as EpisodeProps}
      calculateMetadata={calcDuration}
    />
    <Composition
      id="RepoDrop"
      component={RepoDrop}
      width={LAYOUT.width}
      height={LAYOUT.height}
      fps={FPS}
      durationInFrames={45 * FPS}
      defaultProps={episode as EpisodeProps}
      calculateMetadata={calcDuration}
    />
    <Composition
      id="RepoRadar"
      component={RepoRadar}
      width={LAYOUT.width}
      height={LAYOUT.height}
      fps={FPS}
      durationInFrames={45 * FPS}
      defaultProps={episode as EpisodeProps}
      calculateMetadata={calcDuration}
    />
    {/* Vox / Johnny Harris style rebuild of the DJI take (Sep 2026). */}
    <Composition
      id="VoxReel"
      component={VoxReel}
      width={VOX_W}
      height={VOX_H}
      fps={FPS}
      durationInFrames={976}
    />
    </>
  );
};
