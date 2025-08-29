# modules/ok_api.py
import hashlib
import os
from datetime import datetime

from flask import request, jsonify

from . import ModuleBase


def verify_ok_signature(params: dict, session_secret_key: str) -> bool:
    # Minimalistic OK signature verification (simplified, adjust for prod)
    check_sig = params.get("sig", "")
    if not check_sig: return False
    filtered = {k: v for k, v in params.items() if k not in ("sig")}
    raw = "".join([f"{k}={filtered[k]}" for k in sorted(filtered.keys())])
    calc = hashlib.md5((raw + session_secret_key).encode("utf-8")).hexdigest()
    return calc == check_sig


class OkApiModule(ModuleBase):
    name = "ok_api"
    title = "OK API & Webhooks"

    def init_app(self, app):
        @app.post("/ok/webhook")
        def ok_webhook():
            params = request.form.to_dict() or {}
            sk = os.getenv("OK_SESSION_SECRET_KEY", "")
            # if not verify_ok_signature(params, sk):
            #     return jsonify({"error":"bad signature"}), 403

            kind = params.get("type", "")
            uid = params.get("uid", "")
            text = params.get("text", "")
            # Persist basic events for analytics/CRM
            try:
                self.services["db"].log_event(uid or "0", kind or "ok_event", {"text": text})
            except Exception:
                pass
            return jsonify({"ok": True})

        @app.get("/ok/metrics/pull")
        def ok_metrics_pull():
            # Placeholder: in production, call OK REST methods to fetch stats for group/posts
            # Here we synthesize metrics into analytics tables
            now = datetime.now().isoformat()
            db = self.services["db"]
            # Bump some counters to emulate metrics
            db.log_event("0", "ok_metrics_pull", {"ts": now})
            return jsonify({"ok": True, "ts": now})
