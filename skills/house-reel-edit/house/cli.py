"""house-edit: raw clips -> finished reel in the house style, driven by a per-reel JSON beat sheet.

    house-edit CLIP [CLIP ...] --format split|premium --job DIR [--beats beats.json]
               [--stills 0.5,4.2,9] [--limit 10] [--start 0] [--stage prep|audio|stills|render|qa|all]

First run without --beats: prep + transcript, then writes DIR/beats.skeleton.json and stops (exit 2).
The agent writes DIR/beats.json from the transcript (see SKILL.md), then re-runs with --beats.
Every stage is cached in DIR; delete a stage's output to redo it.
"""
import argparse
import os
import re
import sys

from . import audio, beats as B, prep, qa, render, transcribe
from .common import SR, log, read_json, read_wav, write_json


def _words_of(job, wav, name, first=None):
    """first=None: one whisper pass (the first transcript). first=list: per-line re-timing of the FINAL audio."""
    p = os.path.join(job, name)
    if not os.path.exists(p) or os.path.getmtime(p) < os.path.getmtime(wav):
        w16 = transcribe.to16k(wav, os.path.join(job, name.replace(".json", "_16k.wav")))
        if first is None:
            ws = transcribe.words(w16)
            x, sr = read_wav(wav)
            ws = transcribe.snap_onsets(ws, x, sr)
        else:
            from .captions import retime_per_line
            ws = retime_per_line(w16, first, log=lambda m: log(job, m))
        write_json(p, ws)
    return read_json(p)


def skeleton(job, fmt, words, tl):
    """A starting beat sheet: sentence-level scene stubs + keyword guess. The agent fills in the graphics."""
    sents, cur = [], []
    for w in words:
        cur.append(w)
        if w["w"].endswith((".", "?", "!")):
            sents.append(cur); cur = []
    if cur:
        sents.append(cur)
    kw = None
    for i, w in enumerate(words[:-1]):
        if re.sub(r"[^a-z]", "", w["w"].lower()) == "comment":
            kw = re.sub(r"[^A-Za-z0-9]", "", words[i + 1]["w"]).upper()
    sk = {
        "format": fmt,
        "keyword": kw,
        "keyword_flagged_to_owner": False,
        "caption_fixes": {},
        "accents": {} if fmt == "premium" else None,
        "measured": [],
        "sfx": [{"at": 0.1, "sfx": "tick_hi", "why": "first frame"}],
        "scenes": [{"from": " ".join(x["w"] for x in s[:3]) if i else 0, "say": " ".join(x["w"] for x in s), "layout": "split" if fmt == "split" else "face",
                    "elements": []} for i, s in enumerate(sents)],
        "post": {"title": "", "caption": "", "dm": "", "hashtags": [], "notes": []},
        "_transcript": " ".join(f"{w['w']}@{w['t0']:.2f}" for w in words),
        "_duration": tl["dur"],
    }
    if fmt == "split":
        del sk["accents"]
    write_json(os.path.join(job, "beats.skeleton.json"), sk)


def post_md(job, bs, rep, final, tg):
    p = os.path.join(job, "POST.md")
    post = bs.get("post", {})
    plan = read_json(os.path.join(job, "plan.json"))
    kw = bs.get("keyword")
    lines = [f"# POST: {post.get('title') or os.path.basename(job)}", "",
             "Status: DRAFT. Not posted, not scheduled. Posting needs the owner's approval.", "",
             f"**File:** {os.path.basename(final)} · **Telegram copy:** {os.path.basename(tg) if tg else 'not made (QA failed)'}",
             f"**Format:** {bs.get('format')} · **QA:** {'ALL PASS' if rep.get('all_pass') else 'FAIL, see qa/qa.json'}", ""]
    if kw:
        lines += [f"## Keyword (ManyChat)", kw, "",
                  "Spoken on camera." if not bs.get("keyword_flagged_to_owner") else
                  "NOT spoken on camera: flagged to the owner, end card only. Check the ManyChat trigger exists.", ""]
    lines += ["## Title", post.get("title", ""), "", "## Caption (plain lines, ready to paste)", post.get("caption", ""), ""]
    if post.get("dm"):
        lines += ["## ManyChat DM", post["dm"], ""]
    if post.get("hashtags"):
        lines += ["## Hashtags", " ".join(post["hashtags"]), ""]
    lines += ["## Checks",
              f"- Numbers on screen: spoken or listed in beats.json 'measured' (validator passed).",
              f"- Illustrative UI is labelled ILLUSTRATIVE on screen.",
              f"- Missing anchors (element skipped): {plan.get('missing_anchors') or 'none'}",
              f"- OCR private-data gate: {rep['gates']['ocr_private']['pass']}; no-pill gate: {rep['gates']['no_pills']['pass']}",
              f"- Loudness: {rep['gates']['loudness']['lufs']} LUFS / {rep['gates']['loudness']['true_peak']} dBTP",
              f"- Caption sync ({rep['gates']['caption_sync'].get('reference')}): "
              f"{rep['gates']['caption_sync'].get('xcheck_model') or rep['gates']['caption_sync'].get('per_line_whisper')}, "
              f"flicker {len(rep['gates']['caption_sync'].get('flicker_chunks', []))}, coverage {rep['gates']['caption_sync']['coverage']}"]
    for n in post.get("notes", []):
        lines.append(f"- {n}")
    if "[" in post.get("caption", "") + post.get("dm", ""):
        lines.append("- WARNING: a [placeholder] is still in the caption or DM. It must not ship.")
    with open(p, "w") as f:
        f.write("\n".join(lines) + "\n")
    return p


def main(argv=None):
    ap = argparse.ArgumentParser(prog="house-edit", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("clips", nargs="*", help="raw clips in script order (omit to reuse the job's clips)")
    ap.add_argument("--format", choices=["split", "premium"], required=True)
    ap.add_argument("--job", required=True, help="working folder for this reel")
    ap.add_argument("--beats", help="beat sheet JSON (default: JOB/beats.json if present)")
    ap.add_argument("--stage", default="all", choices=["prep", "audio", "stills", "render", "qa", "all"])
    ap.add_argument("--stills", help="comma-separated times: compose look-dev stills and stop")
    ap.add_argument("--limit", type=float, help="render only this many seconds (a quick check, never a final)")
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--out", help="output mp4 (default JOB/final.mp4)")
    a = ap.parse_args(argv)
    job = os.path.abspath(os.path.expanduser(a.job)); os.makedirs(job, exist_ok=True)
    fmt = a.format

    tlp = os.path.join(job, "timeline.json")
    clips = a.clips or (read_json(tlp)["clips"] if os.path.exists(tlp) else [])
    if not clips:
        sys.exit("no clips given and no existing job timeline")
    tl = prep.run(job, [os.path.expanduser(c) for c in clips], fmt)
    if a.stage == "prep":
        return 0
    if not os.path.exists(os.path.join(job, "voice.wav")) or os.path.getmtime(os.path.join(job, "voice.wav")) < os.path.getmtime(os.path.join(job, "voice_raw.wav")):
        audio.voice(job)
    vwords = _words_of(job, os.path.join(job, "voice.wav"), "words_voice.json")
    vwords_raw = [dict(w) for w in vwords]

    bp = a.beats or os.path.join(job, "beats.json")
    if not os.path.exists(bp):
        skeleton(job, fmt, vwords, tl)
        print(f"\nNo beat sheet yet. Transcript + stubs: {job}/beats.skeleton.json\n"
              f"Write {job}/beats.json (see SKILL.md), then re-run with --beats.")
        return 2
    bs = B.load(bp)
    from .captions import apply_fixes
    vwords = apply_fixes(vwords, bs.get("caption_fixes"))   # "Claud" -> "Claude" before the keyword check
    errs, warns = B.validate(bs, vwords, fmt)
    for w_ in warns:
        log(job, "WARN " + w_)
    if errs:
        for e in errs:
            log(job, "BEAT SHEET ERROR " + e)
        return 3

    # SFX cues resolve against the voice words; the master is then re-whispered for captions + graphics
    A = B.Anchors(vwords, tl["dur"])
    cues = [dict(c, t=A.t(c["at"])) for c in bs.get("sfx", [])]
    missing = [c["at"] for c in cues if c["t"] is None]
    cues = [c for c in cues if c["t"] is not None]
    if missing:
        log(job, f"WARN sfx anchors not found: {missing}")
    mp = os.path.join(job, "master.wav")
    if a.stage in ("audio", "all", "stills", "render") and (not os.path.exists(mp) or os.path.getmtime(mp) < os.path.getmtime(bp)):
        audio.mix(job, cues, fmt)
    _words_of(job, mp, "words_final.json", first=vwords_raw)
    if a.stage == "audio":
        return 0
    if a.stills or a.stage == "stills":
        ts = [float(x) for x in (a.stills or "0.5").split(",")]
        for p in render.stills(job, bs, fmt, ts):
            print("still", p)
        return 0
    out = os.path.abspath(os.path.expanduser(a.out or os.path.join(job, "final.mp4" if not a.limit else f"first{int(a.limit)}s.mp4")))
    if a.stage in ("render", "all"):
        render.render(job, bs, fmt, out, a.start, a.limit)
    if a.stage in ("qa", "all"):
        rep = qa.run(job, out, fmt)
        tg = None
        if rep["all_pass"] and not a.limit:
            tg = render.telegram_copy(out, out.replace(".mp4", "_tg.mp4"))
        post_md(job, bs, rep, out, tg)
        print(f"\nQA {'ALL PASS' if rep['all_pass'] else 'FAIL'} -> {job}/qa/qa.json\nLOOK AT: {rep['contact_sheet']}")
        return 0 if rep["all_pass"] else 4
    return 0


if __name__ == "__main__":
    sys.exit(main())
