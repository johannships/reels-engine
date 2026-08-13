#!/usr/bin/env python3
"""Telegram delivery: send finished reels + alerts to the owner's phone.

Env (pipeline/.env / Railway):
  TELEGRAM_BOT_TOKEN
  TELEGRAM_CHAT_ID

send_video is called by prep.py after the QA gate passes, so the approval
surface is: video arrives in Telegram -> watch it -> veto in Metricool if
needed. notify() in watch.py also mirrors alerts here.

CLI: python3 telegram.py "some text"          (test message)
     python3 telegram.py --video path.mp4 "caption"
"""
import json, mimetypes, os, sys, urllib.request, uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from heygen import env  # noqa: E402  (.env loader)

API = "https://api.telegram.org"


def _enabled():
    try:
        from configlib import load_config
        cfg = load_config(os.path.dirname(os.path.abspath(__file__)))
        return cfg.get("notifications", {}).get("telegram", True)
    except Exception:
        return True


def _configured():
    return bool(env("TELEGRAM_BOT_TOKEN") and env("TELEGRAM_CHAT_ID"))


def send_text(text):
    if not _enabled():
        return True
    if not _configured():
        return False
    body = json.dumps({"chat_id": env("TELEGRAM_CHAT_ID"), "text": text}).encode()
    req = urllib.request.Request(
        f"{API}/bot{env('TELEGRAM_BOT_TOKEN')}/sendMessage", data=body,
        headers={"content-type": "application/json"})
    urllib.request.urlopen(req, timeout=30)
    return True


def _send_file(path, caption, method, field):
    if not _enabled():
        return True
    if not _configured():
        return False
    boundary = uuid.uuid4().hex
    fname = os.path.basename(path)
    ctype = mimetypes.guess_type(fname)[0] or "video/mp4"
    parts = b""
    for name, value in (("chat_id", env("TELEGRAM_CHAT_ID")),
                        ("caption", caption[:1000]),
                        ("supports_streaming", "true")):
        parts += (f"--{boundary}\r\nContent-Disposition: form-data; "
                  f'name="{name}"\r\n\r\n{value}\r\n').encode()
    parts += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{field}\"; "
              f'filename="{fname}"\r\nContent-Type: {ctype}\r\n\r\n').encode()
    parts += open(path, "rb").read() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{API}/bot{env('TELEGRAM_BOT_TOKEN')}/{method}", data=parts,
        headers={"content-type": f"multipart/form-data; boundary={boundary}"})
    resp = json.loads(urllib.request.urlopen(req, timeout=300).read())
    return resp.get("ok", False)


def get_updates(offset=0):
    """Fetch new messages from the owner's chat. Returns (texts, new_offset)."""
    if not env("TELEGRAM_BOT_TOKEN"):
        return [], offset
    try:
        req = urllib.request.Request(
            f"{API}/bot{env('TELEGRAM_BOT_TOKEN')}/getUpdates?offset={offset + 1}&timeout=0")
        d = json.loads(urllib.request.urlopen(req, timeout=30).read())
        texts, new_offset = [], offset
        for u in d.get("result", []):
            new_offset = max(new_offset, u["update_id"])
            m = u.get("message") or {}
            if str(m.get("chat", {}).get("id")) == str(env("TELEGRAM_CHAT_ID")) and m.get("text"):
                texts.append(m["text"])
        return texts, new_offset
    except Exception:
        return [], offset


def send_video(path, caption=""):
    """Inline, streamable — Telegram MAY recompress. Bot API limit: 50 MB."""
    return _send_file(path, caption, "sendVideo", "video")


def send_document(path, caption=""):
    """Original bytes, zero recompression — use this for the postable file."""
    return _send_file(path, caption, "sendDocument", "document")


if __name__ == "__main__":
    args = sys.argv[1:]
    if args and args[0] == "--video":
        ok = send_video(args[1], args[2] if len(args) > 2 else "")
    else:
        ok = send_text(args[0] if args else "Reels Engine test ✅")
    print("sent" if ok else "not configured / failed")
