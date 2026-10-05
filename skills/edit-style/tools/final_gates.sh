#!/bin/sh
# Final-render gates: audio length == video length, loudness (-14 LUFS, <= -1.5 dBTP),
# black frames, and a 12-frame contact sheet you must then LOOK at.
# usage: final_gates.sh final.mp4 [contact.png]     exit 1 if a measured gate fails
set -eu
F="$1"; SHEET="${2:-$(dirname "$F")/contact.png}"
NICE="nice -n 15"

vdur=$(ffprobe -v error -select_streams v:0 -show_entries stream=duration -of csv=p=0 "$F")
adur=$(ffprobe -v error -select_streams a:0 -show_entries stream=duration -of csv=p=0 "$F")
fps=$(ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate -of csv=p=0 "$F")
fail=0

# 1. A/V length: within one frame
av=$(awk -v v="$vdur" -v a="$adur" -v r="$fps" 'BEGIN{split(r,p,"/"); f=p[2]/p[1]; d=v-a; if(d<0)d=-d; printf "%.3f %s", d, (d<=f+0.001)?"PASS":"FAIL"}')
echo "A/V length   video ${vdur}s audio ${adur}s diff ${av}"
case "$av" in *FAIL) fail=1;; esac

# 2. Loudness: -14 +/- 1 LUFS integrated, true peak <= -1.5 dBTP
ebu=$($NICE ffmpeg -nostats -hide_banner -i "$F" -map a:0 -af ebur128=peak=true -f null - 2>&1 | grep -A20 "Summary:")
I=$(echo "$ebu" | awk '$1=="I:"{print $2; exit}')
TP=$(echo "$ebu" | awk '$1=="Peak:"{print $2; exit}')
lr=$(awk -v i="$I" -v t="$TP" 'BEGIN{print (i!="" && t!="" && i>=-15 && i<=-13 && t<=-1.5)?"PASS":"FAIL"}')
echo "Loudness     ${I} LUFS, true peak ${TP} dBTP ${lr}"
[ "$lr" = PASS ] || fail=1

# 3. Black frames
nb=$($NICE ffmpeg -nostats -hide_banner -i "$F" -vf blackdetect=d=0.05:pix_th=0.08 -an -f null - 2>&1 | grep -c black_start || true)
echo "Black frames $nb segment(s) $( [ "$nb" -eq 0 ] && echo PASS || echo FAIL)"
[ "$nb" -eq 0 ] || fail=1

# 3b. Colour/encode (3 Oct 2026): SDR BT.709, limited range, 8-bit 4:2:0, tagged, >= 8 Mbps.
#     Encoding JPEG/PNG frames straight to libx264 gives yuvj420p (full range, BT.601 data) and, with a bt709 tag,
#     a matrix mismatch. Encode with:
#       -vf "scale=in_range=pc:out_range=tv:in_color_matrix=bt601:out_color_matrix=bt709,format=yuv420p,setparams=range=tv:color_primaries=bt709:color_trc=bt709:colorspace=bt709"
#       -color_range tv -color_primaries bt709 -color_trc bt709 -colorspace bt709 -c:v libx264 -profile:v high -crf 17
cinfo=$(ffprobe -v error -select_streams v:0 -show_entries stream=pix_fmt,color_range,color_space,color_transfer,color_primaries,bit_rate -of default=nw=1 "$F" | tr '\n' ' ')
cok=$(echo "$cinfo" | awk '{ok=1} !/pix_fmt=yuv420p /{ok=0} !/color_range=tv/{ok=0} !/color_space=bt709/{ok=0} !/color_transfer=bt709/{ok=0} !/color_primaries=bt709/{ok=0} {match($0,/bit_rate=[0-9]+/); br=substr($0,RSTART+9,RLENGTH-9)+0; if(br<8000000)ok=0; print ok?"PASS":"FAIL"}')
echo "Colour       ${cinfo}${cok}"
[ "$cok" = PASS ] || fail=1
echo "Colour look  for an HDR source: compare a face frame against Apple's SDR (avconvert -p Preset1920x1080) - median luma within ~10, no clipped skin"
echo "Skin luma    run tools/skin_luma_check.sh <raw> <t> <final> <t> <box> <box> - within ~2 levels (DJI Pocket 3 .mov is full range: decode as pc)"

# 4. Contact sheet: 12 evenly spaced frames, 6x2, numbered by time
step=$(awk -v d="$vdur" 'BEGIN{printf "%.4f", d/12}')
$NICE ffmpeg -v error -y -i "$F" -vf "fps=1/${step},scale=270:-2,tile=6x2:padding=6:color=white" -frames:v 1 "$SHEET"
echo "Contact      $SHEET (open it and look at every frame: pills, captions over face, logos, private data, 4:5 crop)"

exit $fail
