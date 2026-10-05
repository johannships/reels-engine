#!/bin/sh
# HDR (iPhone HLG / Dolby Vision) -> SDR BT.709 source frames, using Apple's own tone map (AVAssetReader).
# Added 3 Oct 2026 after reel1 (2 Oct) shipped with a hand-rolled numpy HLG tonemap that blew out the face
# (median luma 148-167 vs Apple's 116, 10% of pixels clipped, skin pushed orange).
# usage: hdr_to_sdr_frames.sh <raw.mov> <need.txt: space-separated frame indices> <outdir> <W> <H> [fps=60]
#   writes <outdir>/s%05d.jpg (q94, BT.709 gamma, 8-bit full-range RGB as every other src frame).
#   VFR-safe: mirrors ffmpeg fps=<fps> indexing, so it is a drop-in for an ffmpeg "fps=60,scale=..." extract.
# Never hand-roll HLG/PQ maths. ffmpeg here has no zscale/libplacebo, so this is the path.
set -eu
D=$(cd "$(dirname "$0")" && pwd); BIN="${TMPDIR:-/tmp}/hdr_to_sdr_frames.bin"
[ -x "$BIN" ] && [ "$BIN" -nt "$D/hdr_to_sdr_frames.swift" ] || swiftc -O "$D/hdr_to_sdr_frames.swift" -o "$BIN" 2>/dev/null
mkdir -p "$3"
nice -n 15 "$BIN" "$1" "$2" "$3" "$4" "$5" "${6:-60}"
