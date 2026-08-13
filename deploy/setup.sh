#!/usr/bin/env bash
# One-time server setup for the Reels Engine on Ubuntu/Debian (Hetzner).
# Run as a normal user with sudo. Idempotent-ish; safe to re-run.
set -euo pipefail

REPO_DIR="${REPO_DIR:-$HOME/reels-engine}"

echo "== apt deps (ffmpeg, build tools, chromium deps) =="
sudo apt-get update
sudo apt-get install -y ffmpeg git build-essential cmake python3 curl \
  chromium-browser || sudo apt-get install -y chromium
# Remotion/Chrome runtime libs (harmless if already present)
sudo apt-get install -y libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
  libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 libxfixes3 libxrandr2 \
  libgbm1 libasound2 libpango-1.0-0 libcairo2 fonts-liberation || true

echo "== node 20 =="
if ! command -v node >/dev/null || [ "$(node -v | cut -c2-3)" -lt 20 ]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
fi

echo "== whisper.cpp =="
if ! command -v whisper-cli >/dev/null; then
  git clone --depth 1 https://github.com/ggml-org/whisper.cpp /tmp/whisper.cpp
  cmake -S /tmp/whisper.cpp -B /tmp/whisper.cpp/build -DCMAKE_BUILD_TYPE=Release
  cmake --build /tmp/whisper.cpp/build -j"$(nproc)"
  sudo cp /tmp/whisper.cpp/build/bin/whisper-cli /usr/local/bin/
fi
mkdir -p "$HOME/models"
if [ ! -f "$HOME/models/ggml-small.en.bin" ]; then
  curl -L -o "$HOME/models/ggml-small.en.bin" \
    "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin"
fi

echo "== studio node modules =="
cd "$REPO_DIR/studio" && npm ci || npm install

echo "== env =="
cd "$REPO_DIR/pipeline"
[ -f .env ] || cp .env.example .env
grep -q WHISPER_MODEL .env || cat >> .env <<EOF
WHISPER_MODEL=$HOME/models/ggml-small.en.bin
REELS_BROWSER=$(command -v chromium-browser || command -v chromium)
EOF

echo "== cron =="
echo "Install with:  crontab deploy/crontab.example   (edit paths first)"
echo
echo "Setup complete. Fill pipeline/.env (LLM_*, HEYGEN_*, REELS_WEBHOOK_URL),"
echo "then test:  cd $REPO_DIR/pipeline && python3 daily.py"
