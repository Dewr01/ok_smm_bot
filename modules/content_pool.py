# modules/content_pool.py
import feedparser
import os

from . import ModuleBase


class ContentPoolModule(ModuleBase):
    name = "content_pool"
    title = "Контент-пул (RSS импорт)"

    def fetch(self):
        feeds = os.getenv("RSS_FEEDS", "").split(",")
        db = self.services["db"]
        count = 0
        for url in [f.strip() for f in feeds if f.strip()]:
            try:
                fp = feedparser.parse(url)
                for e in fp.entries[:10]:
                    text = e.get("title", "") + "\n" + (e.get("summary", "") or "")[:280]
                    db.add_post(text)
                    count += 1
            except Exception:
                continue
        return count
