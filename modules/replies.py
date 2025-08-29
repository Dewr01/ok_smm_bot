# modules/replies.py
from . import ModuleBase

FAQ = {
    "привет": "Привет! Я SMM-комбайн для OK. Напиши /start, чтобы увидеть меню.",
    "помощь": "Доступные команды: 1) совет 2) партнёрка 3) опрос 4) магазин",
}


class RepliesModule(ModuleBase):
    name = "replies"
    title = "Автоответы (FAQ + GPT-заглушка)"

    def init_app(self, app):
        @app.post("/hook/reply-demo")
        def reply_demo():
            data = app.request_data_cache or {}
            uid = str((data.get("user") or {}).get("uid") or "0")
            text = (data.get("text") or "").lower().strip()
            self.services["db"].add_user(uid)
            msg = FAQ.get(text, "Напиши /start")
            try:
                self.services["ok"].send_message(uid, msg)
            except Exception:
                pass
            return {"status": "ok"}

        @app.post("/hook/auto-reply")
        def auto_reply():
            data = app.request_data_cache or {}
            uid = str((data.get("user") or {}).get("uid") or "0")
            text = (data.get("text") or "").strip()
            self.services["db"].add_user(uid)
            # GPT-like fallback
            import os
            if os.getenv("OPENAI_API_KEY", ""):
                reply = f"[AI] Ответ на: {text}"
            else:
                reply = FAQ.get(text.lower(), "Напиши /start")
            try:
                self.services["ok"].send_message(uid, reply)
            except Exception:
                pass
            return {"status": "ok"}
