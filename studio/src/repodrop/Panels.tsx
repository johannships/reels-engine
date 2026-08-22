import React from 'react';
import {useCurrentFrame, useVideoConfig, interpolate, Easing, spring, Img} from 'remotion';
import {RD, RD_MONO, RD_SANS} from './theme';
import {RDCaption, type RDCue} from './Caption';

const W = 1080, H = 1920;

export const Ground: React.FC<{bg: string; children?: React.ReactNode}> = ({bg, children}) => (
  <div style={{width:W,height:H,background:bg,position:'relative',overflow:'hidden'}}>{children}</div>
);

/** Neutral terminal mark. Deliberately not any vendor's logo. */
export const Glyph: React.FC<{size?: number; bg?: string; fg?: string}> = ({
  size=200, bg=RD.ink, fg='#fff',
}) => (
  <div style={{width:size,height:size,borderRadius:size*0.235,background:bg,display:'flex',
    alignItems:'center',justifyContent:'center',boxShadow:'0 18px 60px rgba(0,0,0,.28)'}}>
    <span style={{fontFamily:RD_MONO,fontSize:size*0.4,color:fg,fontWeight:600,
      letterSpacing:-2}}>{'>_'}</span>
  </div>
);

/** intro — glyph with expanding rings. Content sits above the PIP card line. */
export const RDIntro: React.FC<{cues: RDCue[]; line1?: string; line2?: string}> = ({
  cues, line1, line2,
}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const rings = [0,1,2].map((i) => {
    const p = ((f/fps)*0.55 + i/3) % 1;
    return {s: 1 + p*1.9, o: (1-p)*0.5};
  });
  return (
    <Ground bg={RD.dark}>
      <div style={{position:'absolute',left:0,right:0,top:230,height:330,display:'flex',
        alignItems:'center',justifyContent:'center'}}>
        {rings.map((r,i)=>(<div key={i} style={{position:'absolute',width:250,height:250,
          borderRadius:'50%',border:`2px solid ${RD.teal}`,opacity:r.o,transform:`scale(${r.s})`}}/>))}
        <Glyph bg="#fff" fg={RD.ink}/>
      </div>
      {(line1||line2) && (
        <div style={{position:'absolute',left:70,right:70,top:600,textAlign:'center',
          fontFamily:RD_SANS,fontWeight:800,fontSize:52,letterSpacing:2,color:'#fff',lineHeight:1.15}}>
          {line1}{line2 && <><br/>{line2}</>}
        </div>
      )}
      <RDCaption cues={cues} color="#fff" y={(line1||line2) ? 0.46 : 0.36}/>
    </Ground>
  );
};

/** repo — one repository, bar growing, star count counting up. */
export const RDRepo: React.FC<{cues: RDCue[]; repo: string; stars: number; today?: number; desc?: string}> =
({cues, repo, stars, today, desc}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const s = spring({frame:f,fps,config:{damping:200}});
  const n = Math.round(interpolate(s,[0,1],[0,stars]));
  return (
    <Ground bg={RD.white}>
      {today ? (
        <div style={{position:'absolute',left:0,right:0,top:150,textAlign:'center'}}>
          <span style={{fontFamily:RD_SANS,fontSize:26,fontWeight:700,letterSpacing:3,
            color:RD.danger,border:`2px solid ${RD.danger}`,borderRadius:999,padding:'10px 22px'}}>
            +{today.toLocaleString()} STARS TODAY
          </span>
        </div>
      ) : null}
      <div style={{position:'absolute',left:70,right:70,top:270}}>
        <div style={{display:'flex',justifyContent:'space-between',alignItems:'baseline',marginBottom:12}}>
          <span style={{fontFamily:RD_MONO,fontSize:34,color:RD.ink,fontWeight:600}}>{repo}</span>
          <span style={{fontFamily:RD_MONO,fontSize:34,color:RD.ink,fontWeight:700}}>★ {n.toLocaleString()}</span>
        </div>
        <div style={{height:18,background:'#ECECEC',borderRadius:9,overflow:'hidden'}}>
          <div style={{width:`${interpolate(s,[0,1],[0,100])}%`,height:'100%',background:RD.ink,borderRadius:9}}/>
        </div>
        {desc && <div style={{marginTop:18,fontFamily:RD_SANS,fontSize:28,color:'#555'}}>{desc}</div>}
      </div>
      <RDCaption cues={cues} color={RD.ink} y={0.5}/>
    </Ground>
  );
};

/** topic — a single big number counting up. */
export const RDStat: React.FC<{cues: RDCue[]; stat: number; statLabel?: string; pill?: string}> =
({cues, stat, statLabel, pill}) => {
  const f = useCurrentFrame(); const {durationInFrames} = useVideoConfig();
  const p = f/Math.max(durationInFrames-1,1);
  const n = Math.round(interpolate(p,[0,0.8],[0,stat],{extrapolateRight:'clamp',
    easing:Easing.out(Easing.cubic)}));
  return (
    <Ground bg={RD.dark}>
      <div style={{position:'absolute',left:0,right:0,top:270,textAlign:'center'}}>
        {statLabel && <div style={{fontFamily:RD_SANS,fontSize:28,letterSpacing:6,
          color:RD.muted,marginBottom:26,textTransform:'uppercase'}}>{statLabel}</div>}
        <div style={{fontFamily:RD_MONO,fontSize:150,fontWeight:700,color:'#fff',
          letterSpacing:-4}}>{n.toLocaleString()}</div>
        {pill && <div style={{marginTop:28}}>
          <span style={{fontFamily:RD_SANS,fontSize:24,fontWeight:700,letterSpacing:2,color:RD.teal,
            border:`2px solid ${RD.teal}`,borderRadius:999,padding:'9px 18px'}}>{pill}</span>
        </div>}
      </div>
      <RDCaption cues={cues} color="#fff" y={0.5}/>
    </Ground>
  );
};

/** kinetic — a titled card whose bullet points tick in one at a time. */
export const RDCard: React.FC<{cues: RDCue[]; title: string; items?: string[];
  accent?: string; light?: boolean}> = ({cues,title,items=[],accent=RD.teal,light=false}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const bg = light ? RD.white : RD.dark;
  const fg = light ? RD.ink : '#fff';
  return (
    <Ground bg={bg}>
      <div style={{position:'absolute',left:70,right:70,top:190}}>
        <div style={{border:`2px solid ${accent}`,borderRadius:24,padding:'34px 34px 30px',
          background: light?'#fff':RD.darkPanel}}>
          <div style={{fontFamily:RD_MONO,fontSize:34,color:fg,fontWeight:700,
            marginBottom: items.length?26:0}}>{title}</div>
          {items.map((it,i)=>{
            const s = spring({frame:f-10-i*9,fps,config:{damping:200}});
            return (
              <div key={it} style={{display:'flex',alignItems:'center',gap:16,marginBottom:16,
                opacity:s,transform:`translateX(${interpolate(s,[0,1],[26,0])}px)`}}>
                <div style={{width:30,height:30,borderRadius:15,background:accent,flexShrink:0,
                  display:'flex',alignItems:'center',justifyContent:'center',
                  color:light?'#fff':RD.ink,fontSize:19,fontWeight:900}}>✓</div>
                <span style={{fontFamily:RD_SANS,fontSize:31,color:fg,fontWeight:500}}>{it}</span>
              </div>
            );
          })}
        </div>
      </div>
      <RDCaption cues={cues} color={fg} y={0.5}/>
    </Ground>
  );
};

/** shot — a real screenshot in a browser chrome. */
export const RDShot: React.FC<{cues: RDCue[]; image: string; label?: string}> = ({cues,image,label}) => (
  <Ground bg={RD.dark}>
    <div style={{position:'absolute',left:60,right:60,top:200,borderRadius:20,overflow:'hidden',
      border:`1px solid ${RD.line}`,background:'#0B0B0D'}}>
      <div style={{height:52,borderBottom:`1px solid ${RD.line}`,display:'flex',alignItems:'center',
        padding:'0 20px',gap:8}}>
        {['#FF5F57','#FEBC2E','#28C840'].map(c=>(<div key={c} style={{width:12,height:12,
          borderRadius:6,background:c}}/>))}
        {label && <span style={{marginLeft:14,fontFamily:RD_MONO,fontSize:20,
          color:RD.muted}}>{label}</span>}
      </div>
      <Img src={image} style={{width:'100%',display:'block'}}/>
    </div>
    <RDCaption cues={cues} color="#fff" y={0.62}/>
  </Ground>
);

/** cta */
export const RDCta: React.FC<{cues: RDCue[]; badge?: string; line1?: string; line2?: string}> =
({cues,badge,line1,line2}) => {
  const f = useCurrentFrame(); const {fps} = useVideoConfig();
  const s = spring({frame:f,fps,config:{damping:200}});
  return (
    <Ground bg={RD.white}>
      <div style={{position:'absolute',left:0,right:0,top:250,display:'flex',
        flexDirection:'column',alignItems:'center',gap:26}}>
        <div style={{transform:`scale(${interpolate(s,[0,1],[0.8,1])})`}}><Glyph size={190}/></div>
        <div style={{display:'flex',gap:14}}>
          {[line1||'FREE', line2||'OPEN SOURCE', 'ONE COMMAND'].map((b,i)=>(
            <span key={b} style={{fontFamily:RD_SANS,fontSize:22,fontWeight:700,letterSpacing:2,
              color:RD.ink,border:`2px solid ${RD.ink}`,borderRadius:999,padding:'9px 16px',
              opacity:spring({frame:f-8-i*6,fps,config:{damping:200}})}}>{b}</span>
          ))}
        </div>
        {badge && <div style={{fontFamily:RD_SANS,fontSize:26,color:'#666',marginTop:8}}>{badge}</div>}
      </div>
      <RDCaption cues={cues} color={RD.ink} y={0.47}/>
    </Ground>
  );
};
