import {BRICOLAGE_WOFF2, INTER_TIGHT_WOFF2} from './fontData';

// Both files are variable fonts (originally from Google Fonts):
// Bricolage Grotesque: weight axis 200-800 (display type, used at ~800).
// Inter Tight: weight axis 100-900 (body + captions, used at 500-700).
//
// They are injected as plain CSS @font-face rules with base64 data URIs.
// Deliberately NO FontFace API and NO delayRender here: Remotion recycles
// pages mid-render, every fresh page re-runs this module, and an occasional
// hung FontFace.load() promise was timing out delayRender and cancelling
// whole renders. A data-URI @font-face decodes synchronously during style
// resolution, and `font-display: block` guarantees no wrong-font paint.
let injected = false;

export const ensureFonts = () => {
  if (injected || typeof document === 'undefined') {
    return;
  }
  injected = true;
  const style = document.createElement('style');
  style.textContent = `
@font-face {
  font-family: 'Bricolage Grotesque';
  src: url('${BRICOLAGE_WOFF2}') format('woff2');
  font-weight: 200 800;
  font-display: block;
}
@font-face {
  font-family: 'Inter Tight';
  src: url('${INTER_TIGHT_WOFF2}') format('woff2');
  font-weight: 100 900;
  font-display: block;
}`;
  document.head.appendChild(style);
  // Best-effort warm-up so the faces decode before the first frame; never
  // gates the render.
  document.fonts?.load?.("800 40px 'Bricolage Grotesque'").catch(() => {});
  document.fonts?.load?.("600 40px 'Inter Tight'").catch(() => {});
};
