#!/usr/bin/env python3
"""Media server + review dashboard.

  /<TOKEN>/<episode>/final.mp4   -> video files (Metricool fetches these)
  /<TOKEN>/dash                  -> human review dashboard: every episode's
                                    stage, QA verdict, title, schedule, and
                                    a link to watch the final

Env: REELS_SERVE_TOKEN (required), REELS_SERVE_PORT (default 8737, or PORT)
"""
import datetime, html, http.server, json, os, sys, urllib.parse, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from heygen import env  # noqa: E402
import ledger  # noqa: E402


def scheduled_posts():
    """Live view of the Metricool planner (next 14 days). Best-effort."""
    if not env("METRICOOL_USER_TOKEN"):
        return []
    try:
        start = datetime.date.today().isoformat()
        end = (datetime.date.today() + datetime.timedelta(days=14)).isoformat()
        url = (f"https://app.metricool.com/api/v2/scheduler/posts"
               f"?start={start}T00:00:00&end={end}T23:59:59"
               f"&userId={env('METRICOOL_USER_ID')}&blogId={env('METRICOOL_BLOG_ID')}")
        req = urllib.request.Request(url, headers={
            "X-Mc-Auth": env("METRICOOL_USER_TOKEN"), "accept": "application/json"})
        d = json.loads(urllib.request.urlopen(req, timeout=20).read())
        posts = d.get("data", d) if isinstance(d, dict) else d
        out = []
        for p in (posts or []):
            if not isinstance(p, dict):
                continue
            when = (p.get("publicationDate") or {}).get("dateTime", "")[:16]
            nets = ",".join(pr.get("network", "?") for pr in p.get("providers", []))
            out.append({"when": when, "nets": nets,
                        "text": (p.get("text") or "")[:80]})
        return sorted(out, key=lambda x: x["when"])
    except Exception as e:
        return [{"when": "", "nets": "error", "text": f"planner fetch failed: {e}"}]

from configlib import load_config
CFG = load_config(HERE)
EPISODES = os.environ.get("REELS_EPISODES_DIR") or os.path.normpath(
    os.path.join(HERE, CFG["paths"]["episodes"]))
TOKEN = env("REELS_SERVE_TOKEN")
PORT = int(env("REELS_SERVE_PORT", env("PORT", "8737") or "8737"))


def read_json(path):
    try:
        return json.load(open(path))
    except Exception:
        return None


def episode_rows():
    rows = []
    if not os.path.isdir(EPISODES):
        return rows
    for ep in sorted(os.listdir(EPISODES), reverse=True):
        epdir = os.path.join(EPISODES, ep)
        if not os.path.isdir(epdir):
            continue
        script = read_json(os.path.join(epdir, "script.json"))
        qa = read_json(os.path.join(epdir, "qa.json"))
        posted = read_json(os.path.join(epdir, "posted.json"))
        has = lambda f: os.path.exists(os.path.join(epdir, f))  # noqa: E731
        if posted:
            stage, cls = f"scheduled {posted.get('scheduledFor', '')[:16]}", "ok"
        elif qa and qa.get("pass"):
            stage, cls = "QA pass — awaiting post", "ok"
        elif qa:
            fails = [k for k, v in qa.items()
                     if isinstance(v, dict) and not v.get("pass")]
            stage, cls = "QA FAIL: " + ", ".join(fails), "bad"
        elif has("final.mp4"):
            stage, cls = "rendered, QA pending", "warn"
        elif has("avatar.mp4"):
            stage, cls = "avatar in, assembling", "warn"
        elif script:
            stage, cls = "script ready — needs avatar", "warn"
        elif has("research.json"):
            stage, cls = "researched", "warn"
        else:
            continue
        title = (script or {}).get("social", {}).get("title", "")
        face = ""
        if qa and isinstance(qa.get("face"), dict):
            hrs = [f["headroom"] for f in qa["face"].get("frames", [])
                   if isinstance(f, dict) and f.get("headroom") is not None]
            if hrs:
                face = f"headroom {min(hrs)}px"
        rows.append({"ep": ep, "stage": stage, "cls": cls, "title": title,
                     "face": face, "final": has("final.mp4")})
    return rows


def dash_html():
    rows = episode_rows()
    tr = ""
    for r in rows[:60]:
        watch = (f'<a href="/{TOKEN}/{html.escape(r["ep"])}/final.mp4">watch</a>'
                 if r["final"] else "—")
        tr += (f'<tr><td>{html.escape(r["ep"])}</td>'
               f'<td class="{r["cls"]}">{html.escape(r["stage"])}</td>'
               f'<td>{html.escape(r["title"][:70])}</td>'
               f'<td>{html.escape(r["face"])}</td><td>{watch}</td></tr>')
    sched_rows = "".join(
        f'<tr><td>{html.escape(p["when"])}</td><td>{html.escape(p["nets"])}</td>'
        f'<td>{html.escape(p["text"])}</td></tr>' for p in scheduled_posts()[:20])
    cov_rows = "".join(
        f'<tr><td>{html.escape(e["date"])}</td><td>{e["kind"]}</td>'
        f'<td>{html.escape(e["key"])}</td>'
        f'<td><form method="POST" action="/{TOKEN}/covered" style="margin:0">'
        f'<input type="hidden" name="key" value="{html.escape(e["key"])}">'
        f'<button name="action" value="remove" style="background:none;border:0;color:#ff6d6d;cursor:pointer">remove</button>'
        f'</form></td></tr>' for e in ledger.entries()[:60])
    n_ok = sum(1 for r in rows if r["cls"] == "ok")
    n_bad = sum(1 for r in rows if r["cls"] == "bad")
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    return f"""<!doctype html><meta charset="utf-8">
<meta http-equiv="refresh" content="120">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Reels Engine — review</title>
<style>
body{{background:#0A0A0D;color:#fff;font:15px -apple-system,system-ui,sans-serif;margin:0;padding:28px}}
h1{{font-size:22px;margin:0 0 4px}} .sub{{color:#A49FB3;margin-bottom:22px}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;color:#A78BFA;font-size:12px;letter-spacing:.12em;text-transform:uppercase;padding:8px 10px;border-bottom:1px solid #232028}}
td{{padding:10px;border-bottom:1px solid #1a181f;vertical-align:top}}
tr:hover td{{background:#141318}}
.ok{{color:#67D243}} .bad{{color:#ff6d6d;font-weight:600}} .warn{{color:#ffcf5f}}
a{{color:#A78BFA}}
.pill{{display:inline-block;padding:2px 10px;border-radius:99px;border:1px solid #232028;background:#141318;color:#A49FB3;font-size:13px;margin-right:8px}}
</style>
<h1>Reels Engine <span style="color:#8B5CF6">review</span></h1>
<div class="sub">
  <span class="pill">{len(rows)} episodes</span>
  <span class="pill ok">{n_ok} scheduled/passed</span>
  <span class="pill bad">{n_bad} failed QA</span>
  <span class="pill">updated {now} · auto-refreshes</span>
</div>
<table>
<tr><th>Episode</th><th>Stage</th><th>Title</th><th>Face QA</th><th></th></tr>
{tr if tr else '<tr><td colspan="5" style="color:#A49FB3">no episodes yet</td></tr>'}
</table>

<h1 style="margin-top:36px">Scheduled <span style="color:#8B5CF6">on Metricool</span></h1>
<div class="sub">live from the planner — delete/move posts in Metricool itself</div>
<table>
<tr><th>When</th><th>Platforms</th><th>Caption</th></tr>
{sched_rows or '<tr><td colspan="3" style="color:#A49FB3">nothing scheduled</td></tr>'}
</table>

<h1 style="margin-top:36px">Covered <span style="color:#8B5CF6">content</span></h1>
<div class="sub">everything the pickers will refuse to repeat — add anything you posted manually</div>
<form method="POST" action="/{TOKEN}/covered" style="margin-bottom:14px;display:flex;gap:10px">
  <input name="key" placeholder="e.g. meetily, owner/repo, gemini 3.5 leak" required
    style="flex:1;max-width:420px;background:#141318;border:1px solid #232028;border-radius:8px;color:#fff;padding:9px 12px">
  <button name="action" value="add" style="background:#8B5CF6;color:#fff;border:0;border-radius:8px;padding:9px 18px;font-weight:600;cursor:pointer">Mark covered</button>
</form>
<table>
<tr><th>Since</th><th>Kind</th><th>Key</th><th></th></tr>
{cov_rows or '<tr><td colspan="4" style="color:#A49FB3">empty</td></tr>'}
</table>"""


import subprocess, threading

RUNNING = {}  # ep -> "rendering" | "failed: ..." (in-memory job status)


def _tool(args, timeout=1800):
    r = subprocess.run(["python3"] + args, cwd=HERE, capture_output=True,
                       text=True, timeout=timeout)
    return r.returncode == 0, (r.stdout + r.stderr)[-2000:]


def api_route(method, path, body):
    """(status, dict) — the whole pipeline as stage-gated HTTP endpoints."""
    parts = [p for p in path.split("/") if p]
    # GET /api/menu?n=5
    if method == "GET" and parts[:2] == ["api", "menu"]:
        ok, out = _tool(["topics.py", "--menu", "5"], timeout=300)
        menu = []
        mpath = os.path.join(EPISODES, "menu.json")
        if ok and os.path.exists(mpath):
            menu = json.load(open(mpath)).get("candidates", [])
        return (200 if ok else 500), {"ok": ok, "ideas": [
            {"n": i + 1, "title": c["title"], "source": c["source"],
             "metric": (f"{c['score']} {c['statLabel']}"
                        if not c.get("prefiltered") else None)}
            for i, c in enumerate(menu)], "log": None if ok else out}
    # POST /api/episodes {"menuIndex": 2}
    if method == "POST" and parts == ["api", "episodes"]:
        idx = int(body.get("menuIndex", 0))
        ok, out = _tool(["topics.py", "--from-menu", str(idx)], timeout=600)
        ep = ""
        for line in out.splitlines():
            if line.startswith("episode ready: "):
                ep = line.split(": ", 1)[1].strip()
        return (200 if ok else 500), {"ok": ok, "episode": ep,
                                      "log": None if ok else out}
    # GET /api/episodes/<ep>
    if method == "GET" and parts[:2] == ["api", "episodes"] and len(parts) == 3:
        ep = parts[2]
        epdir = os.path.join(EPISODES, ep)
        if not os.path.isdir(epdir):
            return 404, {"ok": False, "error": "no such episode"}
        out = {"ok": True, "episode": ep, "job": RUNNING.get(ep)}
        for f, key in (("script.json", "script"), ("qa.json", "qa"),
                       ("posted.json", "posted")):
            p = os.path.join(epdir, f)
            if os.path.exists(p):
                out[key] = json.load(open(p))
        out["rendered"] = os.path.exists(os.path.join(epdir, "final.mp4"))
        if out["rendered"]:
            out["videoUrl"] = f"{env('REELS_PUBLIC_BASE','').rstrip('/')}/{ep}/final.mp4"
        return 200, out
    # POST /api/episodes/<ep>/redo {"note": "..."}
    if method == "POST" and len(parts) == 4 and parts[3] == "redo":
        ep = parts[2]
        note = (body.get("note") or "").strip()
        if note:
            with open(os.path.join(EPISODES, "feedback.log"), "a") as f:
                f.write(f"{datetime.date.today().isoformat()} (redo {ep}): {note}\n")
        ok, out = _tool(["scriptgen.py", ep], timeout=600)
        script = {}
        sp = os.path.join(EPISODES, ep, "script.json")
        if ok and os.path.exists(sp):
            script = json.load(open(sp))
        return (200 if ok else 500), {"ok": ok, "script": script,
                                      "log": None if ok else out}
    # POST /api/episodes/<ep>/render   (async, ~$0.50 + ~10 min)
    if method == "POST" and len(parts) == 4 and parts[3] == "render":
        ep = parts[2]
        if RUNNING.get(ep) == "rendering":
            return 409, {"ok": False, "error": "already rendering"}
        RUNNING[ep] = "rendering"
        def _job():
            for tool_name in ("heygen.py", "prep.py"):
                ok, out = _tool([tool_name, ep])
                if not ok:
                    RUNNING[ep] = f"failed at {tool_name}: {out[-300:]}"
                    return
            RUNNING[ep] = "done"
        threading.Thread(target=_job, daemon=True).start()
        return 202, {"ok": True, "status": "rendering",
                     "note": "poll GET /api/episodes/<ep> — QA-gated; video "
                             "also lands in Telegram when it passes"}
    # POST /api/episodes/<ep>/schedule {"inHours": 6}  (1h floor enforced)
    if method == "POST" and len(parts) == 4 and parts[3] == "schedule":
        ep = parts[2]
        hours = max(1.0, float(body.get("inHours", 24)))
        ok, out = _tool(["metricool.py", ep, "--in-hours", str(hours)],
                        timeout=300)
        return (200 if ok else 500), {"ok": ok, "log": out[-400:]}
    # GET /api/pending
    if method == "GET" and parts == ["api", "pending"]:
        p = os.path.join(EPISODES, "pending.json")
        items = json.load(open(p)).get("items", {}) if os.path.exists(p) else {}
        return 200, {"ok": True, "pending": items}
    return 404, {"ok": False, "error": "unknown endpoint"}


class Handler(http.server.SimpleHTTPRequestHandler):
    def _authed(self):
        """HTTP Basic auth for human-facing pages. Media URLs stay
        token-only so Metricool can fetch them."""
        pw = env("DASH_PASSWORD")
        if not pw:
            return True
        import base64
        h = self.headers.get("authorization", "")
        if h.startswith("Basic "):
            try:
                creds = base64.b64decode(h[6:]).decode()
                if creds.split(":", 1)[-1] == pw:
                    return True
            except Exception:
                pass
        self.send_response(401)
        self.send_header("WWW-Authenticate", 'Basic realm="Reels Engine"')
        self.send_header("content-length", "0")
        self.end_headers()
        return False

    def _api(self, method):
        clean = self.path.split("?")[0].rstrip("/")
        prefix = f"/{TOKEN}/api"
        if not clean.startswith(prefix):
            return False
        body = {}
        if method == "POST":
            ln = int(self.headers.get("content-length", 0) or 0)
            try:
                body = json.loads(self.rfile.read(ln).decode() or "{}")
            except Exception:
                body = {}
        status, payload = api_route(method, clean[len(f"/{TOKEN}"):], body)
        data = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        return True

    def do_POST(self):
        if self._api("POST"):
            return
        clean = self.path.split("?")[0].rstrip("/")
        if clean != f"/{TOKEN}/covered":
            self.send_error(404)
            return
        if not self._authed():
            return
        length = int(self.headers.get("content-length", 0) or 0)
        form = urllib.parse.parse_qs(self.rfile.read(length).decode())
        key = (form.get("key") or [""])[0].strip()
        action = (form.get("action") or ["add"])[0]
        if key:
            if action == "remove":
                ledger.remove(key)
            else:
                ledger.add(key)
        self.send_response(303)
        self.send_header("location", f"/{TOKEN}/dash")
        self.end_headers()

    def do_GET(self):
        if self._api("GET"):
            return
        clean = self.path.split("?")[0].rstrip("/")
        if clean == f"/{TOKEN}/dash":
            if not self._authed():
                return
            body = dash_html().encode()
            self.send_response(200)
            self.send_header("content-type", "text/html; charset=utf-8")
            self.send_header("content-length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        return super().do_GET()

    def translate_path(self, path):
        parts = path.lstrip("/").split("/", 1)
        if len(parts) != 2 or parts[0] != TOKEN or ".." in parts[1]:
            return "/nonexistent"
        # only expose mp4 finals
        if not parts[1].endswith(".mp4"):
            return "/nonexistent"
        return os.path.join(EPISODES, parts[1])

    def log_message(self, fmt, *args):
        print(self.address_string(), fmt % args)


if __name__ == "__main__":
    if not TOKEN:
        raise SystemExit("Set REELS_SERVE_TOKEN in pipeline/.env (any long random string)")
    print(f"serving episodes + /dash on :{PORT} under /{TOKEN[:4]}…/")
    http.server.ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
