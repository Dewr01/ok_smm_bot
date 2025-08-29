# modules/polls.py
from . import ModuleBase
import json
from datetime import datetime


class PollsModule(ModuleBase):
    name = "polls"
    title = "Опросы/викторины"

    def init_app(self, app):
        @app.post("/admin/polls/create")
        def create_poll():
            q = app.request.values.get("question", "").strip()
            opts = [o.strip() for o in app.request.values.get("options", "").split("\n") if o.strip()]
            db = self.services["db"]
            conn = db.get_conn()
            cur = conn.cursor()
            cur.execute("INSERT INTO polls (question, options, created_at) VALUES (?,?,?)",
                        (q, json.dumps(opts), datetime.now()))
            conn.commit()
            conn.close()
            return {"status": "ok"}
