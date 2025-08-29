# admin/routes.py
import calendar
import datetime
import os
from functools import wraps

from flask import Blueprint, render_template, request, redirect, url_for, Response

from config import ENABLED_MODULES_DEFAULT
from db import get_setting, set_setting, list_posts, add_post, schedule_post, list_queue, list_templates, \
    upsert_template, clicks_by_slug

admin_bp = Blueprint("admin", __name__, template_folder="templates")


def requires_auth(f):
    @wraps(f)
    def inner(*args, **kwargs):
        auth = request.authorization
        if not auth or auth.username != os.getenv("ADMIN_USERNAME", "admin") or auth.password != os.getenv(
                "ADMIN_PASSWORD", "changeme"):
            return Response("Auth required", 401, {"WWW-Authenticate": 'Basic realm="Admin"'})
        return f(*args, **kwargs)

    return inner


@admin_bp.get("/admin")
@requires_auth
def dashboard():
    enabled = get_setting("enabled_modules", ENABLED_MODULES_DEFAULT)
    posts = list_posts(limit=30)
    ctr = clicks_by_slug()
    return render_template("dashboard.html", enabled=enabled, posts=posts, ctr=ctr)


@admin_bp.get("/admin/modules")
@requires_auth
def modules_page():
    enabled = get_setting("enabled_modules", ENABLED_MODULES_DEFAULT)
    return render_template("modules.html", enabled=enabled)


@admin_bp.post("/admin/modules")
@requires_auth
def modules_save():
    enabled = {}
    for key in ENABLED_MODULES_DEFAULT.keys():
        enabled[key] = request.form.get(key) == "on"
    set_setting("enabled_modules", enabled)
    return redirect(url_for("admin.modules_page"))


# ---- Content: posts ----
@admin_bp.get("/admin/posts")
@requires_auth
def posts_page():
    posts = list_posts(limit=500)
    templates = list_templates()
    return render_template("posts.html", posts=posts, templates=templates)


@admin_bp.post("/admin/posts")
@requires_auth
def posts_add():
    text = request.form.get("text", "").strip()
    image = request.form.get("image", "").strip() or None
    template = request.form.get("template", "") or None
    if text:
        add_post(text, image, template)
    return redirect(url_for("admin.posts_page"))


# ---- Content: templates ----
@admin_bp.get("/admin/templates")
@requires_auth
def templates_page():
    templates = list_templates()
    return render_template("templates.html", templates=templates)


@admin_bp.post("/admin/templates")
@requires_auth
def templates_save():
    name = request.form.get("name", "").strip()
    body = request.form.get("body", "").strip()
    if name:
        upsert_template(name, body)
    return redirect(url_for("admin.templates_page"))


# ---- Calendar ----
@admin_bp.get("/admin/calendar")
@requires_auth
def calendar_page():
    year = int(request.args.get("year", datetime.date.today().year))
    month = int(request.args.get("month", datetime.date.today().month))
    posts = list_posts(limit=1000)
    by_date = {}
    for p in posts:
        d = None
        if p.get("scheduled_at"):
            d = str(p["scheduled_at"]).split(" ")[0]
        elif p.get("published_at"):
            d = str(p["published_at"]).split(" ")[0]
        if d:
            by_date.setdefault(d, []).append(p)
    cal = calendar.Calendar(firstweekday=0).monthdayscalendar(year, month)
    return render_template("calendar.html", cal=cal, year=year, month=month, by_date=by_date)


@admin_bp.post("/admin/schedule")
@requires_auth
def schedule():
    post_id = int(request.form.get("post_id"))
    date = request.form.get("date")
    time = request.form.get("time")
    dt = f"{date} {time}:00"
    schedule_post(post_id, dt)
    return redirect(url_for("admin.calendar_page", year=date.split("-")[0], month=int(date.split("-")[1])))


@admin_bp.get("/admin/queue")
@requires_auth
def queue_page():
    q = list_queue(limit=200)
    return render_template("queue.html", queue=q)


# ---- Analytics ----
@admin_bp.get("/admin/analytics")
@requires_auth
def analytics_page():
    return render_template("analytics.html")
