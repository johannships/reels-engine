#!/bin/sh
# Skin-luma gate (5 Oct 2026): the final's face must sit within ~2 luma levels of the source.
# Catches range mistakes (DJI Pocket 3 "glamour" .mov is SDR but tagged FULL range; decoded as
# limited it renders faces ~12 levels too dark with crushed blacks) and any tone-map drift.
# Both clips are decoded with their own range to full-range 8-bit grey, then a face box is averaged.
# usage: skin_luma_check.sh <source> <t_src> <final.mp4> <t_final> <src_box> <final_box> [src_range=auto|pc|tv] [tol=2]
#   box = x:y:w:h in that file's pixels (a patch of cheek/forehead skin, not hair or background)
#   pick the SAME moment in both (t_final = t_src minus whatever was trimmed before it)
# exit 1 if |final - source| > tol
set -eu
S="$1"; TS="$2"; F="$3"; TF="$4"; SB="$5"; FB="$6"; SR="${7:-auto}"; TOL="${8:-2}"

range_of() { r=$(ffprobe -v error -select_streams v:0 -show_entries stream=color_range -of csv=p=0 "$1"); [ "$r" = pc ] && echo pc || echo tv; }
[ "$SR" = auto ] && SR=$(range_of "$S")
FR=$(range_of "$F")

yavg() { # file time range box
  nice -n 15 ffmpeg -v error -ss "$2" -i "$1" -frames:v 1 \
    -vf "scale=in_range=$3:out_range=pc,format=gray,crop=$4,signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-" \
    -f null - | awk -F= '/YAVG/{printf "%.1f", $2; exit}'
}
ys=$(yavg "$S" "$TS" "$SR" "$SB"); yf=$(yavg "$F" "$TF" "$FR" "$FB")
res=$(awk -v a="$ys" -v b="$yf" -v t="$TOL" 'BEGIN{d=b-a; if(d<0)d=-d; printf "diff %.1f %s", d, (a!="" && b!="" && d<=t)?"PASS":"FAIL"}')
echo "Skin luma    source ${ys} (${SR}) final ${yf} (${FR}) ${res}"
case "$res" in *FAIL) exit 1;; esac
