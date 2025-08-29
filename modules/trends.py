# modules/trends.py
from . import ModuleBase
import os, feedparser, re
from collections import Counter

STOP = {"и", "в", "на", "о", "а", "что", "как", "это", "к", "до", "от", "из", "по", "за", "с", "для"}


class TrendsModule(ModuleBase):
    name = "trends"
    title = "Трендовые темы (RSS)"

    def fetch_keywords(self, limit_per_feed=20, top_n=20):
        feeds = os.getenv("RSS_FEEDS", "").split(",")
        cnt = Counter()
        for url in [f.strip() for f in feeds if f.strip()]:
            try:
                fp = feedparser.parse(url)
                for e in fp.entries[:limit_per_feed]:
                    text = (e.get("title", "") + " " + e.get("summary", "")).lower()
                    words = re.findall(r"[a-zа-я0-9]{3,}", text)
                    for w in words:
                        if w in STOP: continue
                        cnt[w] += 1
            except Exception:
                continue
        return cnt.most_common(top_n)

    def make_drafts_from_trends(self, top_n=10):
        db = self.services["db"]
        kws = [w for w, _ in self.fetch_keywords(top_n=top_n)]
        for kw in kws:
            db.add_post(f"Тренд: {kw}\nЧто вы думаете об этом?")
        return len(kws)
