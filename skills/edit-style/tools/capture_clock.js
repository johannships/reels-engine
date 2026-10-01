// Clock-controlled headless capture: smooth, exact screen footage of any web page.
// The page's clock (performance.now, Date.now, requestAnimationFrame) is frozen and stepped
// at a simulated 60 Hz; every 2nd frame is kept for 30 fps. Slow machines can't drop frames.
//
// usage: node capture_clock.js <url> <outdir> [seconds=8] [warmup=3] [cssW=432] [cssH=768] [scale=2.5]
//   then: ffmpeg -framerate 30 -i <outdir>/f%04d.jpg -c:v libx264 -pix_fmt yuv420p clip.mp4
// needs: npm i playwright && npx playwright install chromium   (always headless)
const { chromium } = require('playwright');
const path = require('path'), fs = require('fs');

const INIT = `(() => {
  let now = 0; const start = Date.now(); const cbs = new Map(); let id = 0;
  performance.now = () => now; Date.now = () => start + now;
  window.requestAnimationFrame = cb => { id++; cbs.set(id, cb); return id; };
  window.cancelAnimationFrame = i => cbs.delete(i);
  window.__step = dt => { now += dt; const l = [...cbs.entries()]; cbs.clear();
    for (const [, cb] of l) { try { cb(now); } catch (e) { console.error(e); } } };
})();`;

(async () => {
  const [url, out, secs = '8', warm = '3', w = '432', h = '768', scale = '2.5'] = process.argv.slice(2);
  if (!url || !out) { console.error('usage: node capture_clock.js <url> <outdir> [seconds] [warmup] [cssW] [cssH] [scale]'); process.exit(1); }
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ headless: true });
  const ctx = await browser.newContext({ viewport: { width: +w, height: +h }, deviceScaleFactor: +scale, isMobile: true, hasTouch: true });
  await ctx.addInitScript(INIT);
  const page = await ctx.newPage();
  const errs = []; page.on('pageerror', e => errs.push(e.message));
  await page.goto(url, { waitUntil: 'networkidle' });
  const dt = 1000 / 60;
  for (let i = 0; i < Math.round(+warm * 60); i++) await page.evaluate(d => window.__step(d), dt);
  const N = Math.round(+secs * 30);
  for (let i = 0; i < N; i++) {
    await page.evaluate(d => { window.__step(d); window.__step(d); }, dt);
    await page.screenshot({ path: path.join(out, 'f' + String(i).padStart(4, '0') + '.jpg'), type: 'jpeg', quality: 93 });
  }
  await browser.close();
  console.log(url, N, 'frames', errs.length ? 'PAGE ERRORS: ' + errs.join(' | ') : 'ok');
})();
