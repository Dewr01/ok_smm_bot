# modules/analytics.py
import time

from . import ModuleBase
import matplotlib
import matplotlib.pyplot as plt
import os
from flask import render_template_string

matplotlib.use("Agg")


class AnalyticsModule(ModuleBase):
    name = "analytics"
    title = "Аналитика"

    def init_app(self, app):
        def build_engagement():
            """Строит график вовлечённости по часам"""
            hist = self.services["db"].engagement_histogram_by_hour()
            hours = list(hist.keys())
            values = [hist[h] for h in hours]
            plt.figure()
            plt.bar(hours, values)
            plt.title("Engagement by Hour")
            plt.xlabel("Hour")
            plt.ylabel("Events")
            out = os.path.join("static", "charts", "engagement.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            plt.savefig(out, bbox_inches="tight")
            plt.close()
            return out

        def build_ctr():
            """Строит график кликов по slug"""
            data = self.services["db"].clicks_by_slug()
            if not data:
                return None
            labels = [d["slug"] for d in data]
            values = [d["cnt"] for d in data]
            plt.figure()
            plt.bar(labels, values)
            plt.title("Clicks per link (slug)")
            out = os.path.join("static", "charts", "ctr.png")
            os.makedirs(os.path.dirname(out), exist_ok=True)
            plt.savefig(out, bbox_inches="tight")
            plt.close()
            return out

        @app.get("/admin/chart/engagement")
        def chart_engagement():
            out = build_engagement()
            return {"path": "/" + out}

        @app.get("/admin/chart/ctr")
        def chart_ctr():
            out = build_ctr()
            return {"path": "/" + out if out else ""}

        @app.get("/admin/analytics")
        def analytics_page():
            build_engagement()
            build_ctr()
            with open("admin/templates/analytics.html", encoding="utf-8") as f:
                html = f.read()
            return render_template_string(html, timestamp=int(time.time()))
