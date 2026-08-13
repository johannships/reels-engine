#!/usr/bin/env python3
"""Explicit-approval posting: every QA-passed video WAITS in a pending queue
until the owner replies in Telegram. Nothing can post itself.

Flow:
  chain (topics/daily/watch/...) -> approvals.request(ep)
    -> video already delivered to Telegram by prep.py
    -> pending entry + instructions message with a short id
  worker.py polls Telegram every ~45s -> handle_commands()

Commands (plain replies in the bot chat):
  post 3            schedule episode #3  (+30 min)
  post 3 20:30      schedule at the next 20:30 (your timezone)
  post 3 6h         schedule in 6 hours
  skip 3            discard (marks skipped; never posts)
  fb 3 <note>       feedback on that episode -> feedback.log (and skips post
                    only if you also send skip)
  fb <note>         general feedback -> feedback.log
  list              show what's pending
"""
import datetime, json, os, re, subprocess, sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import telegram
from heygen import env

from configlib import load_config
CFG = load_config(HERE)
EPISODES = os.environ.get("REELS_EPISODES_DIR") or os.path.normpath(
    os.path.join(HERE, CFG["paths"]["episodes"]))
PENDING = os.path.join(EPISODES, "pending.json")
FEEDBACK = os.path.join(EPISODES, "feedback.log")


def _load():
    try:
        return json.load(open(PENDING))
    except Exception:
        return {"seq": 0, "items": {}, "tg_offset": 0}


def _save(d):
    json.dump(d, open(PENDING, "w"), indent=1)


def request_generation(ep):
    """Stage 1: the script is written — show it and WAIT before spending on
    a render. the owner replies 'go N' (render it), 'skip N', or 'fb N <note>'
    (feedback; scriptgen reruns with it on the next 'redo N')."""
    d = _load()
    d["seq"] += 1
    n = str(d["seq"])
    d["items"][n] = {"ep": ep, "stage": "script",
                     "at": datetime.datetime.utcnow().isoformat()}
    _save(d)
    lines, title = [], ""
    try:
        sc = json.load(open(os.path.join(EPISODES, ep, "script.json")))
        title = sc["social"]["title"]
        lines = [f"[{x['type']}] {x['text']}" for x in sc["scenes"]]
    except Exception:
        pass
    telegram.send_text(
        f"🔥 TRENDING — proposed video #{n}\n{ep}\n\nTITLE: {title}\n\n"
        + "\n".join(lines)
        + f"\n\nReply:  go {n} (render it)  ·  redo {n} <notes> (rewrite script)"
        + f"\n        skip {n}  ·  fb {n} <note>")
    return n


def request(ep):
    """Queue a QA-passed episode for approval and tell the owner how to act."""
    d = _load()
    d["seq"] += 1
    n = str(d["seq"])
    d["items"][n] = {"ep": ep, "at": datetime.datetime.utcnow().isoformat()}
    _save(d)
    title = ""
    try:
        title = json.load(open(os.path.join(EPISODES, ep, "script.json")))[
            "social"]["title"]
    except Exception:
        pass
    telegram.send_text(
        f"⏸ #{n} awaiting your call — {ep}\n{title}\n\n"
        f"Reply:  post {n}   ·  post {n} 20:30  ·  post {n} 6h\n"
        f"        skip {n}   ·  fb {n} <what's wrong>")
    return n


def _schedule(ep, when_arg):
    hours = 0.5
    if when_arg:
        m = re.fullmatch(r"(\d+(?:\.\d+)?)h", when_arg)
        t = re.fullmatch(r"(\d{1,2}):(\d{2})", when_arg)
        if m:
            hours = float(m.group(1))
        elif t:
            from zoneinfo import ZoneInfo
            tz = ZoneInfo(env("TIMEZONE", "Asia/Bangkok"))
            now = datetime.datetime.now(tz)
            target = now.replace(hour=int(t.group(1)), minute=int(t.group(2)),
                                 second=0)
            if target <= now:
                target += datetime.timedelta(days=1)
            hours = (target - now).total_seconds() / 3600
    r = subprocess.run(
        [sys.executable, os.path.join(HERE, "metricool.py"), ep,
         "--in-hours", f"{hours:.2f}"], capture_output=True, text=True)
    ok = r.returncode == 0
    return ok, (r.stdout + r.stderr).strip()[-300:]


def handle_commands():
    """Poll Telegram and act on the owner's replies. Called from worker loop."""
    d = _load()
    updates, d["tg_offset"] = telegram.get_updates(d.get("tg_offset", 0))
    my_chat = str(env("TELEGRAM_CHAT_ID"))
    for text in updates:
        cmd = text.strip()
        low = cmd.lower()
        if low == "list":
            items = d["items"]
            telegram.send_text("Pending:\n" + "\n".join(
                f"  #{k}: {v['ep']}" for k, v in items.items()) if items
                else "Nothing pending. 🫡")
        elif low.startswith("post "):
            parts = cmd.split()
            n = parts[1] if len(parts) > 1 else ""
            when = parts[2] if len(parts) > 2 else ""
            item = d["items"].get(n)
            if not item:
                telegram.send_text(f"#{n}? Not pending. Send 'list'.")
                continue
            ok, msg = _schedule(item["ep"], when)
            if ok:
                del d["items"][n]
                telegram.send_text(f"✅ #{n} scheduled. {msg.splitlines()[-1] if msg else ''}")
            else:
                telegram.send_text(f"❌ scheduling #{n} failed:\n{msg}")
        elif low.startswith("go "):
            n = cmd.split()[1] if len(cmd.split()) > 1 else ""
            item = d["items"].get(n)
            if not item or item.get("stage") != "script":
                telegram.send_text(f"#{n} isn't awaiting a render. Send 'list'.")
                continue
            ep = item["ep"]
            del d["items"][n]
            _save(d)
            telegram.send_text(f"🎬 rendering #{n} — the finished video will "
                               f"arrive here for the final call (~10 min).")
            def _render(ep=ep):
                try:
                    for scpt in ("heygen.py", "prep.py"):
                        subprocess.run([sys.executable, os.path.join(HERE, scpt), ep],
                                       check=True)
                    request(ep)
                except Exception as e:
                    telegram.send_text(f"❌ render failed for {ep}: {str(e)[:200]}")
            import threading
            threading.Thread(target=_render, daemon=True).start()
            d = _load()
        elif low.startswith("redo "):
            parts = cmd.split(maxsplit=2)
            n = parts[1] if len(parts) > 1 else ""
            note = parts[2] if len(parts) > 2 else ""
            item = d["items"].get(n)
            if not item:
                telegram.send_text(f"#{n}? Not pending.")
                continue
            ep = item["ep"]
            if note:
                with open(FEEDBACK, "a") as f:
                    f.write(f"{datetime.date.today().isoformat()} (redo request"
                            f" for {ep}): {note}\n")
            try:
                subprocess.run([sys.executable, os.path.join(HERE, "scriptgen.py"), ep],
                               check=True)
                del d["items"][n]
                _save(d)
                request_generation(ep)
                d = _load()
            except Exception as e:
                telegram.send_text(f"❌ rewrite failed: {str(e)[:200]}")
        elif low.startswith("skip "):
            n = cmd.split()[1] if len(cmd.split()) > 1 else ""
            if n in d["items"]:
                ep = d["items"].pop(n)["ep"]
                open(os.path.join(EPISODES, ep, "skipped"), "w").write("skipped")
                telegram.send_text(f"🗑 #{n} skipped — will never post.")
            else:
                telegram.send_text(f"#{n}? Not pending.")
        elif low.startswith("fb"):
            note = cmd[2:].strip()
            m = re.match(r"(\d+)\s+(.*)", note)
            tag = ""
            if m and m.group(1) in d["items"]:
                tag = f" [re {d['items'][m.group(1)]['ep']}]"
                note = m.group(2)
            if note:
                stamp = datetime.date.today().isoformat()
                with open(FEEDBACK, "a") as f:
                    f.write(f"{stamp} (owner via Telegram){tag}: {note}\n")
                telegram.send_text("📝 noted — every future script obeys it.")
    _save(d)


if __name__ == "__main__":
    # CLI for agents (hermes):
    #   approvals.py                 poll telegram once + print pending
    #   approvals.py pending         print pending as JSON (no telegram poll)
    #   approvals.py resolve <n>     remove item n (agent handled it directly)
    if len(sys.argv) > 1 and sys.argv[1] == "pending":
        print(json.dumps(_load()["items"], indent=1))
    elif len(sys.argv) > 2 and sys.argv[1] == "resolve":
        d = _load()
        item = d["items"].pop(sys.argv[2], None)
        _save(d)
        print("resolved:", item["ep"] if item else "not found")
    else:
        handle_commands()
        print("pending:", json.dumps(_load()["items"], indent=1))
