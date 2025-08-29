# modules/ab_auto.py
from . import ModuleBase


class AbAutoModule(ModuleBase):
    name = "ab_auto"
    title = "A/B Авто-выбор победителя"

    def pick_winner(self, group_stats, clicks_by_slug: dict):
        # naive rule: variant with higher clicks wins
        # group_stats: list of {group_id, name, post_id, variant_label}
        scores = {}
        for row in group_stats:
            slug = f"ab-{row['group_id']}-{row['variant_label']}"
            clicks = clicks_by_slug.get(slug, 0)
            scores.setdefault(row['group_id'], []).append((row['variant_label'], clicks, row['post_id']))
        winners = {}
        for gid, items in scores.items():
            if not items: continue
            items.sort(key=lambda t: t[1], reverse=True)
            winners[gid] = {"label": items[0][0], "post_id": items[0][2], "clicks": items[0][1]}
        return winners

    def continue_posting(self, winner):
        # create follow-up post (duplicate) or mark as preferred
        db = self.services["db"]
        try:
            p = db.get_post(winner["post_id"])
            db.add_post(f"[WINNER] {p['text']}")
            return True
        except Exception:
            return False
