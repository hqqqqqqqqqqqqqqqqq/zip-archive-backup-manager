import json
import os
import subprocess
import sys
import threading
import time
import webbrowser

from flask import Flask, jsonify, request, send_from_directory

from backup_core import run_backup_job

APP_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(APP_DIR, "config.json")
DIALOG_HELPER = os.path.join(APP_DIR, "dialog_helper.py")
PORT = 5151

app = Flask(__name__, static_folder=None)

# ---- shared backup-job state, guarded by a lock since Flask runs threaded ----
_lock = threading.Lock()
_log_lines = []
_status = "idle"  # idle | running | done | error


def _log(msg):
    with _lock:
        _log_lines.append(msg)


def _pick_folder():
    """Launches a brand-new, isolated Python process just for the dialog.
    Nothing here shares memory or threads with the Flask app, so a stuck
    dialog can never freeze the server -- worst case, that one subprocess
    hangs and you just close it, the app keeps running."""
    try:
        result = subprocess.run(
            [sys.executable, DIALOG_HELPER],
            capture_output=True,
            text=True,
            timeout=120,
        )
        path = result.stdout.strip()
        return path or None
    except subprocess.TimeoutExpired:
        return None


@app.route("/")
def index():
    resp = send_from_directory(APP_DIR, "index.html")
    resp.headers["Cache-Control"] = "no-store"
    return resp


@app.route("/api/config", methods=["GET"])
def get_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                return jsonify(json.load(f))
        except (json.JSONDecodeError, OSError):
            pass
    return jsonify({"sources": [], "destination": ""})


@app.route("/api/config", methods=["POST"])
def save_config():
    with open(CONFIG_PATH, "w") as f:
        json.dump(request.json, f, indent=2)
    return jsonify({"ok": True})


@app.route("/api/pick_sources", methods=["POST"])
def pick_sources():
    return jsonify({"path": _pick_folder()})


@app.route("/api/pick_destination", methods=["POST"])
def pick_destination():
    return jsonify({"path": _pick_folder()})


@app.route("/api/run_backup", methods=["POST"])
def run_backup():
    global _status
    data = request.json or {}
    sources = data.get("sources", [])
    destination = data.get("destination", "")

    with _lock:
        if _status == "running":
            return jsonify({"started": False, "reason": "already running"}), 409
        _log_lines.clear()
        _status = "running"

    def worker():
        global _status
        try:
            results = run_backup_job(sources, destination, log=_log)
            with _lock:
                _status = "error" if any(r["status"] == "error" for r in results) else "done"
        except Exception as e:
            _log(f"Unexpected error: {e}")
            with _lock:
                _status = "error"

    threading.Thread(target=worker, daemon=True).start()
    return jsonify({"started": True})


@app.route("/api/log")
def get_log():
    since = int(request.args.get("since", 0))
    with _lock:
        lines = _log_lines[since:]
        status = _status
        total = len(_log_lines)
    return jsonify({"lines": lines, "next": total, "status": status})


def open_browser():
    time.sleep(0.8)
    webbrowser.open(f"http://127.0.0.1:{PORT}")


if __name__ == "__main__":
    threading.Thread(target=open_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=PORT, debug=False, threaded=True)