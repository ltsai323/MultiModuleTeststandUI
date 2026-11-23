#!/usr/bin/env python3
from __future__ import annotations
import os
import re
from flask import Flask, render_template_string, send_from_directory, send_file, url_for, abort, Response, redirect
import logging
import sys

log = logging.getLogger(__name__)

from flask import Blueprint
from flask import current_app

app = Blueprint('daqsummary', __name__, url_prefix="/daqsummary")


#app = Flask(__name__)

# --- Configuration ---
# # Base directory where your run1 PNGs live. You can override via env var DAQPLOTS_DIR.
# BASE_PLOTS_DIR = os.environ.get("DAQPLOTS_DIR", os.path.expanduser("~/stored_data/daqplots/"))
# # Default/fallback image when a required figure is missing or fails to load.
# DEFAULT_IMG = os.path.expanduser("~/stored_data/daqplots.nodata.png")
andrewCONF = f'{os.environ.get("AndrewModuleTestingGUI_BASE")}/configuration.yaml'
try:
    with open(andrewCONF, 'r') as fIN:
        import yaml
        conf = yaml.safe_load(fIN)
        BASE_PLOTS_DIR = f'{conf["DataLoc"]}/daqplots/'
        DEFAULT_IMG = f'{conf["DataLoc"]}/daqplots.nodata.png'
except FileNotFoundError as e:
    raise FileNotFoundError(f'\n\n[NoEnvVar] Need to `source ./init_bash_vars.sh` before execute this file') from e

# Blocks/keys to render when a run directory holds nothing (3 columns x 2 rows)
BLOCKS = [
        "1L", "1C", "1R",
        "2L", "2C", "2R",
        ]

# Strict file names: "1L-adc_mean.png" (tray position) or "A-adc_mean.png" (mux slot).
FNAME_RE = re.compile(r"^(?P<key>[1-9][LCR]|[ABC])-.*\.png$")


def blocks_in(run: str):
    """Keys that have plots in a run directory (1L..2R or A..C), else the default grid."""
    try:
        names = os.listdir(os.path.join(BASE_PLOTS_DIR, run))
    except OSError:
        return BLOCKS
    keys = {m.group("key") for m in (FNAME_RE.match(n) for n in names) if m}
    return sorted(keys) if keys else BLOCKS


def serial_of(run: str, key: str) -> str:
    """Module serial from "<key>.serial" next to a slot's maps, or "" if absent."""
    if not re.fullmatch(r"[ABC]", key):
        return ""
    try:
        with open(os.path.join(BASE_PLOTS_DIR, run, f"{key}.serial")) as f:
            s = f.read().strip()
    except OSError:
        return ""
    return s if re.fullmatch(r"[A-Za-z0-9-]{1,32}", s) else ""


def has_png(path: str) -> bool:
    try:
        return os.path.isfile(path)
    except OSError:
        return False
# ---------------- Template (inline for single-file app) ----------------
### TEMPLATE = r"""<!doctype html>
### <html lang="en">
### <head>
###   <meta charset="utf-8">
###   <meta name="viewport" content="width=device-width, initial-scale=1">
###   <title>DAQ Run1 Plots</title>
###   <style>
###     :root { --bg:#0b1020; --card:#121a33; --ink:#e7ecff; --muted:#9fb0ffb3; }
###     *{box-sizing:border-box}
###     body{margin:0;background:linear-gradient(180deg,#0b1020 0%,#0b1020 60%,#0e1530 100%);color:var(--ink);font-family:ui-sans-serif,system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial}
###     header{max-width:2000px;margin:0 auto;padding:24px 20px 8px}
###     h1{margin:0 0 6px}
###     .sub{color:var(--muted);font-size:.95rem}
###     .grid{max-width:2000px;margin:16px auto 60px;padding:0 20px;display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
###     @media (max-width:1100px){.grid{grid-template-columns:repeat(2,1fr)}}
###     @media (max-width:720px){.grid{grid-template-columns:1fr}}
###     .block{background:radial-gradient(120% 120% at 100% 0%,#1a244a 0%,#0f1836 50%,var(--card) 100%);border-radius:16px;border:1px solid #2a3a7a55;box-shadow:0 10px 30px #000a; padding:14px}
###     .block-title{display:flex;justify-content:space-between;align-items:center;margin:2px 2px 10px;padding:8px 10px;background:#0e1530;border:1px solid #2a3a7a66;border-radius:12px}
###     .figwrap{display:grid;grid-template-columns:1fr 1fr;gap:10px}
###     @media (max-width:560px){.figwrap{grid-template-columns:1fr}}
###     figure{margin:0;padding:10px;border-radius:12px;background:#0b122a;border:1px solid #2a3a7a55}
###     img{width:100%;height:260px;object-fit:contain;display:block;border-radius:8px;background:#050915}
###     figcaption{margin-top:8px;font-size:.85rem;color:var(--muted);word-break:break-all}
###     .badge{font-size:.75rem;color:var(--muted)}
###     .legend{max-width:2000px;margin:0 auto 28px;padding:0 20px;color:var(--muted);font-size:.9rem}
###     code{background:#0e1530;border:1px solid #2a3a7a55;padding:2px 6px;border-radius:6px}
###   </style>
### </head>
### """
TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>DAQ Summary</title>
  <link rel="stylesheet" href="{{ url_for('static', filename='css/theme.css') }}">
</head>
<body>
  <header>
    <h1>DAQ Run1 Figures</h1>
    <div class="sub">3 columns × 2 rows. Each block shows <code>_1.png</code> and <code>_2.png</code>. Filenames are captions. Missing images fall back to <code>~/stored_data/daqplots.default.png</code>.</div>
  </header>
  <main class="grid">
    {% for card in cards %}
      <section class="block">
        <div class="block-title"><span>{{ card.title }}</span><span class="badge">run1</span></div>
        <div class="figwrap">
          {% for img in card.images %}
            <figure>
              <img src="{{ img.src }}" alt="{{ img.file }}" loading="lazy">
              <figcaption>{{ img.file }}</figcaption>
            </figure>
          {% endfor %}
        </div>
      </section>
    {% endfor %}
  </main>
  <div class="legend">Serve directory is handled on the server. You can change it via env <code>DAQPLOTS_DIR</code> or by editing <code>BASE_PLOTS_DIR</code> in the app.</div>
</body>
</html>"""







@app.route("/plots/<path:filepath>")
def serve_plot(filepath: str):
    """Serve a plot from BASE_PLOTS_DIR if present, otherwise serve DEFAULT_IMG.
    This keeps all basePath logic in Python so you can add auth, logging, etc.
    """
    # Security: only allow our strict pattern and no path segments
    log.warning(f'[GotFilename] {filepath}')

    if "/" not in filepath or "\\" in filepath or ";" in filepath:
        log.warning(f'[InvalidFilePath] path "{filepath}" should be run1/1L-adc_mean.png')
        abort(404)

    filename = filepath.split('/')[-1]
    if not FNAME_RE.match(filename): ## check filename in formatted. ex: 1L-adc_mean.png
        log.debug(f'[check] FNAME_RE.match(filename) {not FNAME_RE.match(filename.strip())}')
        log.debug(f'abort serve_plot')
        log.warning(f'[InvalidFileName] filename "{filename}" is invalid.')
        abort(404)

    fs_path = os.path.join(BASE_PLOTS_DIR, filepath)
    log.debug(f'[RequiredFigure] full path "{fs_path}"')
    if has_png(fs_path):
        log.debug(f'sending image {filepath}')
        return send_from_directory(BASE_PLOTS_DIR, filepath)

    # Fallback: default image
    if has_png(DEFAULT_IMG):
        log.debug(f'sending default image {DEFAULT_IMG}')
        return send_file(DEFAULT_IMG)

    # Last-resort vector placeholder if DEFAULT_IMG is missing
    svg = f"""
    <svg xmlns='http://www.w3.org/2000/svg' width='800' height='500'>
      <rect width='100%' height='100%' fill='#0b1020'/>
      <text x='50%' y='45%' text-anchor='middle' fill='#9fb0ff' font-size='22' font-family='monospace'>Missing figure</text>
      <text x='50%' y='55%' text-anchor='middle' fill='#9fb0ff' font-size='16' font-family='monospace'>{{{filepath}}}</text>
    </svg>
    """.replace("{{{filepath}}}", filepath)
    log.warning(f'no any file sent!!!')
    return Response(svg, mimetype="image/svg+xml")


# --------------------------------------------------------------------------
# One module at every bias voltage: <RESULTS_DIR>/<serial>/hexmaps/ (hexmap_robust.py).
# Readable only when the GUI host is the client host.
# --------------------------------------------------------------------------
import json
import subprocess
_RESULTS = {}
SERIAL_RE = re.compile(r"^[A-Z0-9]{6,20}$")
HEXMAP_RE = re.compile(r"^(adc_mean|adc_stdd|robust_adc_stdd)_BV(\d{4}|none)_[A-Za-z0-9_-]+\.png$")
MAP_NAMES = {"adc_stdd": "noise (adc_stdd)", "adc_mean": "pedestal (adc_mean)",
             "robust_adc_stdd": "robust noise"}


def results_dir() -> str:
    """$RESULTS_DIR of the client host, asked once through on_client.sh."""
    if "dir" in _RESULTS:
        return _RESULTS["dir"]
    d = os.environ.get("MMTS_RESULTS_DIR", "")
    if not d:
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        try:
            out = subprocess.run(["bash", os.path.join(root, "scripts/task4_mmts_pedestal/on_client.sh"),
                                  'echo "RESULTS=${RESULTS_DIR:-$MMTS_ROOT/Results}"'],
                                 capture_output=True, text=True, timeout=30).stdout
            m = re.search(r"^RESULTS=(/\S+)$", out, re.M)
            d = m.group(1) if m else ""
        except (OSError, subprocess.SubprocessError):
            d = ""
    if d and os.path.isdir(d):
        _RESULTS["dir"] = d
    return d if d and os.path.isdir(d) else ""


def module_records(serial: str):
    """conditions.jsonl rows whose files still exist, newest session first, BV ascending."""
    base = os.path.join(results_dir(), serial, "hexmaps")
    rows = []
    try:
        with open(os.path.join(base, "conditions.jsonl")) as f:
            for line in f:
                try:
                    r = json.loads(line)
                except ValueError:
                    continue
                if isinstance(r, dict) and r.get("files"):
                    rows.append(r)
    except OSError:
        return []
    return rows


@app.route("/modules.json")
def modules_json():
    d = results_dir()
    out = []
    if d:
        for s in sorted(os.listdir(d)):
            j = os.path.join(d, s, "hexmaps", "conditions.jsonl")
            if SERIAL_RE.match(s) and os.path.isfile(j):
                with open(j) as f:
                    out.append({"serial": s, "n": sum(1 for _ in f)})
    return json.dumps(out), 200, {"Content-Type": "application/json"}


@app.route("/hexmap/<serial>/<fname>")
def hexmap(serial: str, fname: str):
    if not SERIAL_RE.match(serial) or not HEXMAP_RE.match(fname) or not results_dir():
        abort(404)
    return send_from_directory(os.path.join(results_dir(), serial, "hexmaps"), fname)


@app.route("/module/<serial>")
def module_page(serial: str):
    """Columns = bias voltages, rows = sessions; one map type at a time."""
    from flask import request
    serial = serial.upper()
    if not SERIAL_RE.match(serial):
        abort(404)
    kind = request.args.get("map", "adc_stdd")
    if kind not in MAP_NAMES:
        kind = "adc_stdd"
    allruns = request.args.get("all") == "1"
    rows = [r for r in module_records(serial) if kind in r["files"]]
    ### a session is one GUI run (runtag); backfilled runs group by label and day
    sessions = {}
    for r in rows:
        key = r.get("runtag") or f'{r.get("time", "")[:10]} {r.get("label", "")}'
        sessions.setdefault(key, []).append(r)
    blocks = []
    for key, rs in sessions.items():
        rs.sort(key=lambda r: (r["bv"] is not None, r["bv"] or 0, r.get("time", "")))
        if not allruns:   # the last run at each bias point
            last = {}
            for r in rs:
                last[r["bv"]] = r
            rs = list(last.values())
        cells = [{"src": url_for("daqsummary.hexmap", serial=serial, fname=r["files"][kind]),
                  "bv": "no HV" if r["bv"] is None else f'{r["bv"]} V',
                  "leak": "" if r.get("leak_uA") is None else f'{r["leak_uA"]:.4g} uA',
                  "cond": " · ".join(x for x in (
                      "" if r.get("temperature_C") is None else f'{r["temperature_C"]:g} °C',
                      "" if r.get("humidity_pct") is None else f'{r["humidity_pct"]:g} %RH') if x),
                  "run": r["run"], "label": r.get("label", ""), "slot": r.get("slot", ""),
                  "file": r["files"][kind]} for r in rs]
        start = min(r.get("time", "") for r in rs)
        blocks.append({"key": key, "start": start, "cells": cells})
    blocks.sort(key=lambda b: b["start"], reverse=True)

    template = r"""<!doctype html>
    <html lang="en"><head><meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{{serial}} vs HV</title>
    <style>
      body { background:#0b1020; color:#e7ecff; font-family:sans-serif; margin:0; }
      header { padding:16px 20px 6px; display:flex; gap:18px; align-items:baseline; flex-wrap:wrap; }
      h1 { margin:0; font-size:1.5em; }
      header a { color:#9fb0ff; }
      header a.on { color:#fff; font-weight:700; text-decoration:none; border-bottom:2px solid #d29800; }
      .muted { color:#9fb0ff; font-size:.9em; }
      section { margin:10px 20px 22px; padding:10px; background:#121a33; border-radius:12px; }
      section h2 { font-size:1em; margin:2px 4px 10px; color:#cfd8ff; }
      .row { display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:12px; }
      figure { margin:0; padding:8px; background:#0b122a; border-radius:10px; border:1px solid #2a3a7a55; }
      figure b { font-size:1.15em; }
      img { width:100%; display:block; border-radius:6px; background:#050915; margin-top:6px; }
      figcaption { font-size:.8em; color:#9fb0ff; margin-top:4px; word-break:break-all; }
    </style></head><body>
    <header>
      <h1>{{serial}}</h1>
      {% for k, name in maps.items() %}<a class="{{ 'on' if k == kind }}" href="?map={{k}}{{ '&all=1' if allruns }}">{{name}}</a>{% endfor %}
      <a href="?map={{kind}}{{ '' if allruns else '&all=1' }}">{{ 'last run per bias point' if allruns else 'every run' }}</a>
      <span class="muted">files: {{ folder }}</span>
    </header>
    {% if not blocks %}<section>No archived hexmaps for {{serial}}{% if not folder %} (RESULTS_DIR is not readable from the GUI host){% endif %}.</section>{% endif %}
    {% for b in blocks %}
    <section><h2>{{ b.key }} &nbsp; <span class="muted">{{ b.start.replace('T', ' ') }}</span></h2>
      <div class="row">
      {% for c in b.cells %}
        <figure>
          <b>{{ c.bv }}</b> <span class="muted">{{ c.leak }}{% if c.leak and c.cond %} · {% endif %}{{ c.cond }}</span>
          <a href="{{ c.src }}" target="_blank"><img src="{{ c.src }}" loading="lazy" alt="{{ c.file }}"></a>
          <figcaption>slot {{ c.slot }} · {{ c.label }} · {{ c.run }}</figcaption>
        </figure>
      {% endfor %}
      </div>
    </section>
    {% endfor %}
    </body></html>"""
    folder = os.path.join(results_dir(), serial, "hexmaps") if results_dir() else ""
    return render_template_string(template, serial=serial, blocks=blocks, maps=MAP_NAMES,
                                  kind=kind, allruns=allruns, folder=folder)


@app.route("/gallery/<run>")
def gallery(run: str):
    """Main gallery page—embeds each block page via iframe."""
    cards = []
    for key in blocks_in(run):
        url = url_for("daqsummary.block_page", run=run, key=key)
        cards.append({"title": key, "url": url})

    template = r"""<!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>DAQ {{run}} Plots</title>
      <style>
        body { background:#0b1020; color:#e7ecff; font-family:sans-serif; margin:0; }
        h1 { padding:20px; margin:0; }
        .grid { display:grid; grid-template-columns:repeat(3,1fr); gap:16px; padding:20px; max-width:1500px; margin:auto; }
        iframe { width:100%; height:270px; border:none; border-radius:12px; background:#121a33; }
      </style>
    </head>
    <body>
      <h1>DAQ {{run}} Figures</h1>
      <div class="grid">
        {% for card in cards %}
          <iframe src="{{ card.url }}"></iframe>
        {% endfor %}
      </div>
    </body>
    </html>"""
    return render_template_string(template, cards=cards, run=run)


@app.route("/gallery/<run>/<key>")
def block_page(run: str, key: str):
    """Render a page for a single block, showing its two plots."""
    imgs = []
    for i in ("adc_mean", "adc_stdd"):
        fname = f"{run}/{key}-{i}.png"
        fs_path = os.path.join(BASE_PLOTS_DIR, fname)
        exists = has_png(fs_path)
        src = url_for("daqsummary.serve_plot", filepath=fname)
        imgs.append({"file": fname, "src": src, "exists": exists})
    self_url = url_for("daqsummary.block_page", run=run, key=key)
    # A, B, C are mux slots on the multi-module bench; 1L..8R are tray positions.
    title = f"Slot {key}" if key in ("A", "B", "C") else f"Module{key}"
    # Show the serial too: the slot letter alone does not identify the board.
    serial = serial_of(run, key)
    if serial:
        title = f"{title}: {serial}"

    template = r"""<!doctype html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>{{ key }} Plots</title>
      <style>
        html { overflow:hidden; }
        body { background:#121a33; color:#e7ecff; font-family:sans-serif; margin:0; padding:12px; overflow:hidden; }
        .block-title { font-weight:bold; margin-bottom:10px; }
        .block-title{display:flex;justify-content:space-between;align-items:center;margin:2px 2px 10px;padding:8px 10px;background:#0e1530;border:1px solid #2a3a7a66;border-radius:12px}
        .figwrap{display:grid;grid-template-columns:1fr 1fr;gap:10px}
        figure{margin:0;padding:10px;border-radius:12px;background:#0b122a;border:1px solid #2a3a7a55}
        img{width:100%;object-fit:contain;display:block;border-radius:8px;background:#050915}
        figcaption{margin-top:8px;font-size:.85rem;color:var(--muted);word-break:break-all}
      </style>
    </head>
    <body>
      <a href="{{ self_url }}" target="_blank">
        <div class="block-title">{{ title }}</div>
      </a>
      <div class="figwrap">
        {% for img in imgs %}
        <figure>
          <img src="{{ img.src }}" alt="{{ img.file }}" />
          <figcaption>{{ img.file }}</figcaption>
        </figure>
        {% endfor %}
      </div>
    </body>
    </html>"""
    return render_template_string(template, run=run, key=key, imgs=imgs,
                                  title=title, self_url=self_url)


if __name__ == "__main__":
    import os
    loglevel = os.environ.get('LOG_LEVEL', 'INFO') # DEBUG, INFO, WARNING
    DEBUG_MODE = True if loglevel == 'DEBUG' else False
    logLEVEL = getattr(logging, loglevel)
    logging.basicConfig(stream=sys.stdout,level=logLEVEL,
            format='[basicCONFIG] %(levelname)s - %(message)s',
            datefmt='%H:%M:%S')


    # create a simple flask server for testing
    _app = Flask(__name__)

    @_app.route('/')
    @_app.route('/index')
    def index():
        return redirect( url_for('daqsummary.gallery', run='testrun') )

    _app.register_blueprint(app)
    _app.run(host="0.0.0.0", port=5001, debug=True)

