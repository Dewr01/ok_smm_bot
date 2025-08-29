# modules/autopost.py
from . import ModuleBase
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import traceback


class AutoPostModule(ModuleBase):
    name = "autopost"
    title = "Автопостинг + очередь + шаблоны"

    def __init__(self, services):
        super().__init__(services)
        self.scheduler = BackgroundScheduler()
        self.job = None

    def init_app(self, app):
        self.scheduler.start()
        if not self.job:
            self.job = self.scheduler.add_job(self._tick, "interval", minutes=2, id="autopost_tick")

        @app.post("/admin/publish_now/<int:post_id>")
        def publish_now(post_id):
            self._publish_post_id(post_id)
            return {"status": "ok"}

    def _tick(self):
        db = self.services["db"]
        ok = self.services["ok"]
        now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        due = db.next_due(now_iso)
        if not due: return
        self._publish(due, ok, db)

    def _publish_post_id(self, post_id: int):
        db = self.services["db"]
        ok = self.services["ok"]
        posts = [p for p in db.list_posts(limit=1000) if p["id"] == post_id]
        if not posts: return
        self._publish(posts[0], ok, db)

    def run(self):
        ok = self.services["ok"]
        db = self.services["db"]
        # достаём все посты, у которых статус "scheduled"
        posts = db.get_scheduled_posts()
        for post in posts:
            self._publish(post, ok, db)

    def _publish(self, post, ok, db):
        text = post.get("text") or ""
        image_path = post.get("image_path")  # 👈 добавлено

        try:
            if image_path:
                # если у поста есть картинка → загружаем фото и публикуем с ним
                tokens = ok.upload_photos(gid=ok.group_id, paths=[image_path])
                if tokens:
                    ok.post_with_image(text, tokens[0])
                else:
                    ok.post_text(text)
            else:
                ok.post_text(text)

            db.mark_published(post["id"])
            db.log_event("system", "group_post", f"id={post['id']}")

        except Exception as e:
            db.mark_error(post["id"])
            db.log_event("system", "group_post_error", str(post['id']) + " " + str(e))
            traceback.print_exc()
