# Reels Engine worker — Railway (or any Docker host)
FROM node:20-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg python3 python3-pip chromium git build-essential cmake curl \
      ca-certificates tzdata \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --no-cache-dir --break-system-packages opencv-python-headless numpy

# whisper.cpp (word-level caption timestamps) — static build so the binary
# has no shared-lib dependencies (exit 127 otherwise)
RUN git clone --depth 1 https://github.com/ggml-org/whisper.cpp /tmp/w \
    && cmake -S /tmp/w -B /tmp/w/build -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=OFF \
    && cmake --build /tmp/w/build -j"$(nproc)" \
    && cp /tmp/w/build/bin/whisper-cli /usr/local/bin/ \
    && /usr/local/bin/whisper-cli --help > /dev/null \
    && rm -rf /tmp/w
RUN mkdir -p /models && curl -fsSL -o /models/ggml-small.en.bin \
    https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-small.en.bin

# Claude Code CLI — scriptgen runs it headless (`claude -p`) authenticated by
# CLAUDE_CODE_OAUTH_TOKEN, so scripts bill against the subscription rather than
# per-token API credits. Native installer (no Node 22+ requirement).
ENV PATH="/root/.local/bin:${PATH}"
RUN curl -fsSL https://claude.ai/install.sh | bash \
    && CLAUDE_BIN="$(command -v claude || find /root -maxdepth 4 -name claude -type f -perm -u+x | head -1)" \
    && test -n "$CLAUDE_BIN" \
    && ln -sf "$CLAUDE_BIN" /usr/local/bin/claude \
    && claude --version

WORKDIR /app
COPY studio/package.json studio/package-lock.json studio/
RUN cd studio && npm ci && npx remotion browser ensure

COPY . .

# Remotion uses its own pre-downloaded headless shell (sandbox-safe in Docker);
# system chromium remains for screenshot.py page captures.
ENV WHISPER_MODEL=/models/ggml-small.en.bin \
    SCREENSHOT_BROWSER=/usr/bin/chromium \
    REELS_EPISODES_DIR=/data/episodes \
    HOME=/root \
    LLM_PROVIDER=claude-cli \
    LLM_MODELS=fable,opus

# /data must be a mounted volume (episodes, dedupe state, worker stamps)
CMD ["python3", "pipeline/worker.py"]
