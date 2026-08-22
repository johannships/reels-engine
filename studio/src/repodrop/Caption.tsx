import React from 'react';
import {useCurrentFrame, useVideoConfig} from 'remotion';
import {RD_CAP} from './theme';

export type RDCue = {start: number; end: number; text: string};

/**
 * Serif ALL-CAPS caption band shown on graphic scenes.
 *
 * Long words are shrunk to fit rather than allowed to run off the frame — an
 * un-fitted caption clipped "OVERCOMPLICATING" to "OVERCOMPLICAT." in testing.
 */
export const RDCaption: React.FC<{cues: RDCue[]; color: string; y?: number}> = ({
  cues, color, y = 0.5,
}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const cue = cues.find((c) => t >= c.start && t < c.end);
  if (!cue) return null;
  const age = t - cue.start;
  const pop = 1 + 0.035 * Math.exp(-age * 14);
  const longest = Math.max(...cue.text.split(/\s+/).map((w) => w.length));
  const size = Math.min(RD_CAP.size, Math.floor(RD_CAP.maxWidth / (longest * 0.7)));
  return (
    <div style={{position:'absolute',left:70,right:70,top:`${y*100}%`,textAlign:'center',
      pointerEvents:'none'}}>
      <span style={{display:'inline-block',maxWidth:RD_CAP.maxWidth,
        fontFamily:RD_CAP.family,fontStyle:'italic',fontSize:size,
        letterSpacing:RD_CAP.spacing,color,textTransform:'uppercase',
        transform:`scale(${pop})`,lineHeight:1.04}}>{cue.text}</span>
    </div>
  );
};
