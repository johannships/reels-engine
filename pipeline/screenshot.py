#!/usr/bin/env python3
"""Capture a high-quality screenshot of a page for the ShotPanel.

Uses headless Chrome/Chromium (REELS_BROWSER env, or the macOS Chrome path),
crops to a clean 1080-wide JPEG.

Usage: python3 screenshot.py <url> <out.jpg>
"""
import os, subprocess, sys, tempfile

MAC_CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"


def browser():
    for cand in (os.environ.get("SCREENSHOT_BROWSER"), os.environ.get("REELS_BROWSER"),
                 MAC_CHROME, "/usr/bin/chromium", "/usr/bin/chromium-browser"):
        if cand and os.path.exists(cand):
            return cand
    raise SystemExit("no Chrome/Chromium found (set REELS_BROWSER)")


def main():
    url, out = sys.argv[1], sys.argv[2]
    out2 = sys.argv[3] if len(sys.argv) > 3 else None
    with tempfile.TemporaryDirectory() as td:
        png = os.path.join(td, "shot.png")
        # 2x device scale = retina-crisp text in the Ken Burns pan; capture a
        # tall page so a second slice (deeper content) is available for beat 2
        subprocess.run([
            browser(), "--headless", "--disable-gpu", "--hide-scrollbars",
            "--no-sandbox", "--disable-dev-shm-usage",
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
            "--window-size=1280,3000", "--force-device-scale-factor=2",
            f"--screenshot={png}", url,
        ], check=True, timeout=120,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        # top slice (hero of the page)
        subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-i", png,
                        "-vf", r"crop=iw:min(ih\,3400):0:0,scale=2160:-2",
                        "-q:v", "2", out], check=True)
        if out2:
            subprocess.run(["ffmpeg", "-y", "-v", "quiet", "-i", png,
                            "-vf", r"crop=iw:min(ih\,3400):0:min(ih-3400\,2400),scale=2160:-2",
                            "-q:v", "2", out2], check=False)
    if os.path.getsize(out) < 20_000:
        os.remove(out)
        if out2 and os.path.exists(out2):
            os.remove(out2)
        raise SystemExit(f"capture too small (blocked page?): {url}")
    print(f"screenshot -> {out} ({os.path.getsize(out) // 1024} KB)"
          + (f" + {out2}" if out2 and os.path.exists(out2) else ""))


if __name__ == "__main__":
    main()
