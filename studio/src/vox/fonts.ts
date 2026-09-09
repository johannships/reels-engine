import {HN_BOLD, HN_CBLACK, HN_MEDIUM} from './fontData';

// One typeface: Helvetica Neue, pulled off this Mac's system .ttc, subset and
// inlined as woff2 data URIs. Data URIs decode synchronously during style
// resolution, so there is no wrong-font first paint and no delayRender to hang.
export const FONT = 'VoxHelv';
export const FONT_CN = 'VoxHelvCn';

let injected = false;

export const ensureVoxFonts = () => {
  if (injected || typeof document === 'undefined') return;
  injected = true;
  const style = document.createElement('style');
  style.textContent = `
@font-face {
  font-family: '${FONT}';
  src: url('${HN_MEDIUM}') format('woff2');
  font-weight: 500;
  font-display: block;
}
@font-face {
  font-family: '${FONT}';
  src: url('${HN_BOLD}') format('woff2');
  font-weight: 700;
  font-display: block;
}
@font-face {
  font-family: '${FONT_CN}';
  src: url('${HN_CBLACK}') format('woff2');
  font-weight: 900;
  font-display: block;
}`;
  document.head.appendChild(style);
};
