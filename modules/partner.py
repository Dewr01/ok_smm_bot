# modules/partner.py
from . import ModuleBase
from urllib.parse import urlencode


class PartnerModule(ModuleBase):
    name = "partner"
    title = "Партнёрки + редиректы"

    def build_link(self, base_url: str, slug: str, source="ok_smart", campaign="default", extra: dict = None):
        q = {"utm_source": source, "utm_medium": "ok", "utm_campaign": campaign, "utm_content": slug}
        if extra: q.update(extra)
        sep = "&" if "?" in base_url else "?"
        # сокращаем через наш редиректор /r/<slug>
        target = f"{base_url}{sep}{urlencode(q)}"
        return f"/r/{slug}?u={urlencode({'t': target})}"
