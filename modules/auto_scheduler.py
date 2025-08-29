# modules/auto_scheduler.py
from . import ModuleBase
from datetime import datetime, timedelta
from .ab_auto import AbAutoModule


class AutoSchedulerModule(ModuleBase):
    name = "auto_scheduler"
    title = "Авто-расписание (besttime + A/B)"

    def next_slots(self, days=7, hours=(10, 14, 19), best_hours=None):
        now = datetime.now()
        slots = []
        for d in range(days):
            day = now + timedelta(days=d)
            for h in (best_hours or hours):
                slots.append(day.replace(hour=int(h), minute=0, second=0, microsecond=0))
        return [s for s in slots if s > now]

    def schedule_winners_and_drafts(self, limit=20):
        db = self.services["db"]
        hist = db.engagement_histogram_by_hour()
        best_hours = [h for h, _ in sorted(hist.items(), key=lambda kv: kv[1], reverse=True)[:3]] or [10, 14, 19]
        clicks = db.clicks_by_slug()
        stats = db.ab_group_stats()
        winners = AbAutoModule(self.services).pick_winner(stats, clicks)
        posts_queue = [w["post_id"] for w in winners.values()]
        # add drafts (unscheduled)
        for p in db.list_posts(limit=limit):
            if p["status"] == "draft":
                posts_queue.append(p["id"])
        slots = self.next_slots(best_hours=best_hours)
        n = min(len(posts_queue), len(slots))
        for i in range(n):
            dt = slots[i].strftime("%Y-%m-%d %H:%M:%S")
            db.schedule_post(posts_queue[i], dt)
        return {"scheduled": n, "best_hours": best_hours}
