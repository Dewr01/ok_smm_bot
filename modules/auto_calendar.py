# modules/auto_calendar.py
from . import ModuleBase
from datetime import datetime, timedelta, timezone


class AutoCalendarModule(ModuleBase):
    name = "auto_calendar"
    title = "Автокалендарь"

    def spread_week(self, hour_choices=(10, 14, 19)):
        # Расставляет всем 'draft' постам даты на ближайшую неделю по равномерной сетке
        db = self.services["db"]
        posts = [p for p in db.list_posts(limit=1000) if p["status"] == "draft"]
        now = datetime.now(timezone.utc)
        day = 0
        for p in posts:
            dt = (now + timedelta(days=day // len(hour_choices))).replace(hour=hour_choices[day % len(hour_choices)],
                                                                          minute=0, second=0, microsecond=0)
            db.schedule_post(p["id"], dt.strftime("%Y-%m-%d %H:%M:%S"))
            day += 1
        return len(posts)
