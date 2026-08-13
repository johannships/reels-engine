import React from 'react';
import {Composition} from 'remotion';
import episode from './data/episode-01.json';
import {ensureFonts} from './fonts';
import {RepoRadar} from './RepoRadar';
import {LAYOUT} from './theme';
import type {EpisodeProps} from './types';

ensureFonts();

const FPS = 30;

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="RepoRadar"
      component={RepoRadar}
      width={LAYOUT.width}
      height={LAYOUT.height}
      fps={FPS}
      durationInFrames={45 * FPS}
      defaultProps={episode as EpisodeProps}
      calculateMetadata={({props}) => {
        const totalSec = props.scenes.reduce(
          (sum, scene) => sum + scene.durationSec,
          0,
        );
        return {
          durationInFrames: Math.round(totalSec * FPS),
        };
      }}
    />
  );
};
