# modules/recommendations.py
from . import ModuleBase
from collections import Counter


class RecommendationsModule(ModuleBase):
    name = "recommendations"
    title = "AI-рекомендации (эвристики)"

    def suggest(self):
        db = self.services["db"]
        hist = db.engagement_histogram_by_hour()  # {hour:score}
        hours_sorted = sorted(hist.items(), key=lambda kv: kv[1], reverse=True)
        tip_time = [h for h, _ in hours_sorted[:3]] if hours_sorted else [12, 18, 20]
        # simple format tip: inspect templates usage & engagement
        posts = db.list_posts(limit=200)
        templates = [p.get("template") for p in posts if p.get("template")]
        t = Counter(templates).most_common(1)[0][0] if templates else "мем"
        return {
            "best_hours": tip_time,
            "format_tip": f"Сейчас лучше зайдёт короткий пост в формате «{t}» с картинкой."
        }
