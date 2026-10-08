from .can.api import bp
from .models import LogFile, Message, db

from flask import Flask, jsonify, redirect, render_template, request, url_for
import json as _json
import os
from . import paths

# Templates and static assets live at <project root>/templates and
# <project root>/static, next to web/, so resolve them from this file instead
# of the process working directory.

def build_app():
    """Build the application: configuration, database, then routes."""
    app = Flask(__name__, template_folder=str(paths.TEMPLATES_DIR), static_folder=str(paths.STATIC_DIR))
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + str(paths.INSTANCE_DIR / "cananalyzer.db")
    app.secret_key = os.environ.get("CANANALYZER_SECRET", "can-analyzer-dev-secret")
    db.init_app(app)
    with app.app_context():
        db.create_all()
    app.register_blueprint(bp)

    # Toolbar selection kept per process, and the decoded log of what happened.
    # Templates read this (or Message/LogFile rows), never hard-coded sample data.
    PAGE_STATE = {"log_name": "drive1.asc", "dbc_name": "vehicle.dbc",
                  "active_signal": "RPM", "stop_enabled": True,
                  "log": "buffer empty: upload a log and a DBC to decode"}
    DATA_DIR = os.environ.get("CANANALYZER_DATA_DIR", str(paths.DATA_DIR))

    def _focus():
        """The log this request focuses on (``?log_id=``) and its can_id filter."""
        logs = LogFile.query.order_by(LogFile.id.desc()).all()
        wanted = request.args.get("log_id", type=int)
        active_log = next((l.id for l in logs if l.id == wanted), None)
        if active_log is None:
            active_log = logs[0].id if logs else None
        return logs, active_log, (request.args.get("filter") or "").strip().upper()

    @app.context_processor
    def inject_state():
        """Messages, signals and log rows all come from SQLite + the parse buffers."""
        logs, active_log, flt = _focus()
        rows = Message.query.filter_by(log_id=active_log).order_by(Message.id).limit(200).all() \
            if active_log else []
        if flt:
            rows = [m for m in rows if flt in (m.can_id or "").upper()]
        messages = [{"id": m.id, "t": "%.3f" % (m.ts or 0.0), "can_id": m.can_id,
                     "data_hex": m.data_hex, "decoded": m.decoded_json or "{}"} for m in rows]
        messages_note = "" if messages else (
            "no messages decoded yet: POST a log to /api/logs, then POST a DBC to "
            "/api/logs/<id>/dbc and decode it")
        signals = sorted({s for s in
                          (PAGE_STATE["active_signal"],) if s})
        for m in rows[:20]:
            try:
                keys = _json.loads(m.decoded_json or "{}")
            except ValueError:
                keys = {}
            signals = sorted(set(signals) | set(keys.keys()))
        return {
            "app_name": "can-analyzer",
            "data_dir": DATA_DIR,
            "log_files": [{"id": l.id, "name": l.name, "format": l.format,
                           "frame_count": l.frame_count or 0, "uploaded_at": l.uploaded_at}
                          for l in logs],
            "log_count": len(logs),
            "messages": messages,
            "messages_note": messages_note,
            "signals": signals,
            "active_signal": request.args.get("signal") or PAGE_STATE["active_signal"],
            "stop_enabled": PAGE_STATE["stop_enabled"],
            "log_name": request.args.get("log") or PAGE_STATE["log_name"],
            "dbc_name": request.args.get("dbc") or PAGE_STATE["dbc_name"],
            "active_log": active_log or "",
            "filter_value": flt,
            "log": PAGE_STATE["log"],
        }

    @app.get("/")
    def index():
        """Renders the log named by ?log_id= and the rows kept by ?filter= (see _focus)."""
        logs, active_log, flt = _focus()
        return render_template("index.html", focus={"log_id": active_log or "",
                                                    "filter": flt,
                                                    "logs": len(logs)})

    @app.post("/logs")
    def start_log():
        """Control-panel form target: registers the log the API then parses."""
        name = (request.form.get("name") or "drive1.asc").strip()
        fmt = "csv" if name.lower().endswith(".csv") else "asc"
        log = LogFile(name=name, format=fmt, frame_count=0)
        db.session.add(log)
        db.session.commit()
        PAGE_STATE["log_name"] = name
        PAGE_STATE["log"] = "registered log #%d (%s); POST the file to /api/logs" % (log.id, name)
        return redirect(url_for("index", log_id=log.id))

    @app.post("/logs/<int:lid>/replay")
    def replay_log(lid):
        log = LogFile.query.get_or_404(lid)
        PAGE_STATE["log"] = "replay queued for log #%d (%d frames)" % (lid, log.frame_count or 0)
        PAGE_STATE["stop_enabled"] = True
        return redirect(url_for("index", log_id=lid))

    @app.post("/logs/<int:lid>/stop")
    def stop_log(lid):
        """The toolbar stop button: freezes the focused log and disarms replay."""
        log = LogFile.query.get_or_404(lid)
        PAGE_STATE["stop_enabled"] = False
        PAGE_STATE["log"] = "replay stopped on log #%d (%d frames)" % (lid, log.frame_count or 0)
        return redirect(url_for("index", log_id=lid))

    @app.get("/api/health")
    def api_health():
        return jsonify({"status": "ok", "app": "can-analyzer", "version": "0.1.0"})

    @app.get("/api/config")
    def api_config():
        """Data directory and accepted log formats, shared by UI and CLI."""
        return jsonify({"data_dir": DATA_DIR,
                        "formats": ["asc", "csv"],
                        "logs": LogFile.query.count(),
                        "database": app.config["SQLALCHEMY_DATABASE_URI"]})

    if __name__ == "__main__":  # python -m web.app  (see Dockerfile CMD)
        app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))

    return app

app = build_app()
