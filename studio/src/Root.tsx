import React from 'react';
import {Composition} from 'remotion';
import episode from './data/episode-01.json';
import {ensureFonts} from './fonts';
import {RepoRadar} from './RepoRadar';
import {RepoDrop} from './repodrop/RepoDrop';
import {LAYOUT} from './theme';
import type {EpisodeProps} from './types';

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
    {/* RepoDrop is the default style. RepoRadar is kept for older episodes. */}
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
    </>
  );
};
