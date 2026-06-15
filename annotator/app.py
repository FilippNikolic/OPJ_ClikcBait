#!/usr/bin/env python3
"""Mini web anotator za klikbejt klasifikaciju (Faza 2).

Zero-dependency (samo Python stdlib). Piše direktno u CSV datoteke:
  Filip:  data/calibration/filip_unakrsna.csv  + data/annotated/filip_glavna.csv
  Danilo: data/calibration/danilo_unakrsna.csv + data/annotated/danilo_glavna.csv

Redosled: PRVO unakrsna (110) + prvih 110 glavne = 220 kalibracionih, pa ostatak.
Upisuje labela = 1 (JESTE klikbejt) ili 0 (NIJE). Nastavlja od prvog
neklasifikovanog. Brza tastatura: → / 1 = JESTE,  ← / 0 = NIJE,  U = nazad.

Pokretanje:
  .venv/bin/python annotator/app.py
Pa otvori:  http://localhost:8000

Kad zavrsis sa anotacijom, ceo folder annotator/ se moze obrisati — podaci
ostaju u data/.
"""
import csv
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["id", "naslov", "labela", "podtip", "napomena"]
PORT = 8000

# redosled datoteka po korisniku: kalibracija (unakrsna) PRVO, pa glavna
USER_FILES = {
    "filip": [
        ROOT / "data" / "calibration" / "filip_unakrsna.csv",
        ROOT / "data" / "annotated" / "filip_glavna.csv",
    ],
    "danilo": [
        ROOT / "data" / "calibration" / "danilo_unakrsna.csv",
        ROOT / "data" / "annotated" / "danilo_glavna.csv",
    ],
}

_lock = threading.Lock()


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_rows(path, rows):
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)


def counts(user):
    total = done = 0
    for p in USER_FILES[user]:
        for r in read_rows(p):
            total += 1
            if (r.get("labela") or "").strip() in ("0", "1"):
                done += 1
    return total, done


def class_counts():
    """Progres: broj klikbejt/nije kroz SVE datoteke (glavna + unakrsna),
    tj. sve što je do sada klasifikovano — svaki klik se broji."""
    kb = ne = 0
    for usr in USER_FILES:
        for p in USER_FILES[usr]:
            for r in read_rows(p):
                l = (r.get("labela") or "").strip()
                if l == "1":
                    kb += 1
                elif l == "0":
                    ne += 1
    return kb, ne


def next_item(user):
    kb, ne = class_counts()
    for p in USER_FILES[user]:
        for r in read_rows(p):
            if (r.get("labela") or "").strip() not in ("0", "1"):
                total, done = counts(user)
                return {
                    "done": False,
                    "id": r["id"],
                    "naslov": r["naslov"],
                    "remaining": total - done,
                    "total": total,
                    "position": done + 1,
                    "kb": kb, "ne": ne,
                }
    total, done = counts(user)
    return {"done": True, "remaining": 0, "total": total, "kb": kb, "ne": ne}


def set_label(user, hid, value):
    """value '0'/'1' postavlja labelu; '' je poništava (undo)."""
    for p in USER_FILES[user]:
        rows = read_rows(p)
        changed = False
        for r in rows:
            if r["id"] == hid:
                r["labela"] = value
                changed = True
                break
        if changed:
            write_rows(p, rows)
            return True
    return False


PAGE = """<!DOCTYPE html>
<html lang="sr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Klikbejt anotator</title>
<style>
  * { box-sizing: border-box; }
  body { font-family: -apple-system, system-ui, Arial, sans-serif; margin: 0;
         background: #f4f4f4; color: #111; }
  .wrap { max-width: 820px; margin: 0 auto; padding: 24px; }
  h1 { font-size: 1.2rem; font-weight: 600; }
  .pick button { display: block; width: 100%; font-size: 1.6rem; padding: 28px;
         margin: 16px 0; border: 2px solid #333; background: #fff; cursor: pointer;
         border-radius: 8px; }
  .pick button:hover { background: #eee; }
  .bar { display:flex; justify-content: space-between; align-items:center;
         font-size: 1rem; color:#555; margin-bottom: 24px; }
  .bar a { color:#06c; cursor:pointer; text-decoration:none; }
  .count { font-size: 1.3rem; font-weight: 700; color:#111; }
  .card { background:#fff; border:1px solid #ddd; border-radius:10px;
          padding: 48px 32px; min-height: 200px; display:flex; align-items:center;
          justify-content:center; text-align:center; }
  .naslov { font-size: 2.4rem; line-height: 1.3; font-weight: 600; }
  .btns { display:flex; gap:20px; margin-top: 28px; }
  .btns button { flex:1; font-size: 1.8rem; font-weight:700; padding: 40px 0;
          border:none; border-radius:10px; cursor:pointer; color:#fff; }
  .jeste { background:#2d6a4f; } .jeste:hover { background:#235641; }
  .nije  { background:#c0392b; } .nije:hover  { background:#a93226; }
  .pitanje { text-align:center; font-size:1.5rem; font-weight:600; margin-bottom:18px; }
  .progress { margin-top:32px; padding:24px; background:#fff; border:1px solid #ddd;
              border-radius:10px; text-align:center; font-size:1.3rem; line-height:1.9; }
  .progress b { font-size:1.6rem; }
  .progress .kb { color:#2d6a4f; } .progress .ne { color:#c0392b; }
  .hint { text-align:center; color:#888; margin-top:14px; font-size:.9rem; }
  .done { text-align:center; font-size:1.6rem; padding:60px 0; }
</style></head>
<body><div class="wrap" id="app"></div>
<script>
let user=null, cur=null, stack=[];

function api(path, opts){ return fetch(path, opts).then(r=>r.json()); }

async function showPick(){
  user=null;
  const s = await api('/api/status');
  document.getElementById('app').innerHTML =
    `<h1>Klikbejt anotator — izaberi korisnika</h1><div class="pick">
     <button onclick="pick('filip')">FILIP &nbsp;<small>(${s.filip.remaining} preostalo)</small></button>
     <button onclick="pick('danilo')">DANILO &nbsp;<small>(${s.danilo.remaining} preostalo)</small></button>
     </div>
     <div class="progress">
       <div>Klikbejt: <b class="kb">${s.klasa.kb}</b></div>
       <div>Nije klikbejt: <b class="ne">${s.klasa.ne}</b></div>
       <div>Ukupno: <b>${s.klasa.ukupno}</b> / ${s.klasa.dataset}</div>
     </div>`;
}
function pick(u){ user=u; stack=[]; loadNext(); }

async function loadNext(){
  cur = await api('/api/next?user='+user);
  render();
}
function render(){
  const app=document.getElementById('app');
  if(cur.done){
    app.innerHTML = `<div class="bar"><a onclick="showPick()">&larr; promeni korisnika</a>
      <span class="count">Gotovo: ${cur.total}/${cur.total}</span></div>
      <div class="done">✅ Svi naslovi su klasifikovani.<br><small>Možeš zatvoriti i obrisati annotator/.</small></div>`;
    return;
  }
  app.innerHTML =
    `<div class="bar">
        <a onclick="showPick()">&larr; ${user}</a>
        <span class="count">Preostalo: ${cur.remaining}</span>
        <a onclick="undo()" ${stack.length? '':'style="visibility:hidden"'}>&#8634; nazad (U)</a>
     </div>
     <div class="pitanje">Da li je ovaj naslov clickbait?</div>
     <div class="card"><div class="naslov"></div></div>
     <div class="btns">
        <button class="nije"  onclick="label('0')">NIJE</button>
        <button class="jeste" onclick="label('1')">JESTE</button>
     </div>
     <div class="hint">&larr; / 0 = NIJE &nbsp;·&nbsp; &rarr; / 1 = JESTE &nbsp;·&nbsp; U = nazad</div>`;
  app.querySelector('.naslov').textContent = cur.naslov;  // textContent = bezbedno za navodnike
}
async function label(v){
  if(!cur || cur.done) return;
  const id=cur.id;
  await api('/api/label', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({user, id, labela:v})});
  stack.push(id);
  loadNext();
}
async function undo(){
  if(!stack.length) return;
  const id=stack.pop();
  await api('/api/label', {method:'POST', headers:{'Content-Type':'application/json'},
      body: JSON.stringify({user, id, labela:''})});
  loadNext();
}
document.addEventListener('keydown', e=>{
  if(!user || !cur || cur.done) return;
  if(e.key==='ArrowRight'||e.key==='1') label('1');
  else if(e.key==='ArrowLeft'||e.key==='0') label('0');
  else if(e.key.toLowerCase()==='u') undo();
});
showPick();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json"):
        data = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass  # tiho

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/":
            return self._send(200, PAGE, "text/html")
        if u.path == "/api/status":
            with _lock:
                out = {}
                for usr in USER_FILES:
                    t, d = counts(usr)
                    out[usr] = {"total": t, "done": d, "remaining": t - d}
                kb, ne = class_counts()
                dataset = sum(len(read_rows(p)) for usr in USER_FILES for p in USER_FILES[usr])
                out["klasa"] = {"kb": kb, "ne": ne, "ukupno": kb + ne, "dataset": dataset}
            return self._send(200, json.dumps(out))
        if u.path == "/api/next":
            usr = parse_qs(u.query).get("user", [""])[0]
            if usr not in USER_FILES:
                return self._send(400, json.dumps({"error": "bad user"}))
            with _lock:
                return self._send(200, json.dumps(next_item(usr)))
        return self._send(404, json.dumps({"error": "not found"}))

    def do_POST(self):
        if urlparse(self.path).path != "/api/label":
            return self._send(404, json.dumps({"error": "not found"}))
        n = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(n) or b"{}")
        usr, hid, val = data.get("user"), data.get("id"), data.get("labela", "")
        if usr not in USER_FILES or not hid or val not in ("0", "1", ""):
            return self._send(400, json.dumps({"error": "bad request"}))
        with _lock:
            ok = set_label(usr, hid, val)
            t, d = counts(usr)
        return self._send(200, json.dumps({"ok": ok, "remaining": t - d, "total": t}))


if __name__ == "__main__":
    print(f"Anotator radi na  ->  http://localhost:{PORT}")
    print("Zaustavi sa Ctrl+C. Podaci se pišu u data/ (CSV).")
    ThreadingHTTPServer(("127.0.0.1", PORT), Handler).serve_forever()
