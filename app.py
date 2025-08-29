# app.py
import json
import os
import urllib.parse

from dotenv import load_dotenv
from flask import Flask, request, redirect, jsonify, render_template

from admin import admin_bp
from config import ENABLED_MODULES_DEFAULT
from db import init_db, add_user, update_user, log_event, get_setting
from ok_api import OKApi

load_dotenv()
app = Flask(__name__, static_folder="static", template_folder="admin/templates")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "dev")

init_db()

ok_api = OKApi()
services = {"ok": ok_api, "db": __import__("db")}
app.request_data_cache = None


def load_modules():
    enabled = get_setting("enabled_modules", ENABLED_MODULES_DEFAULT)
    loaded = {}
    if enabled.get("autopost"):
        from modules.autopost import AutoPostModule
        loaded["autopost"] = AutoPostModule(services)
        loaded["autopost"].init_app(app)
    if enabled.get("analytics"):
        from modules.analytics import AnalyticsModule
        loaded["analytics"] = AnalyticsModule(services)
        loaded["analytics"].init_app(app)
    if enabled.get("partner"):
        from modules.partner import PartnerModule
        loaded["partner"] = PartnerModule(services)
    if enabled.get("replies"):
        from modules.replies import RepliesModule
        loaded["replies"] = RepliesModule(services)
        loaded["replies"].init_app(app)
    if enabled.get("tg_admin"):
        from modules.tg_admin import TGAdminModule
        if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            loaded["tg_admin"] = TGAdminModule(services)
            loaded["tg_admin"].init_app(app)
    if enabled.get("ai_writer"):
        from modules.ai_writer import AIWriterModule
        loaded["ai_writer"] = AIWriterModule(services)
    if enabled.get("ai_images"):
        from modules.ai_images import AIImagesModule
        loaded["ai_images"] = AIImagesModule(services)
    if enabled.get("content_pool"):
        from modules.content_pool import ContentPoolModule
        loaded["content_pool"] = ContentPoolModule(services)
    if enabled.get("polls"):
        from modules.polls import PollsModule
        loaded["polls"] = PollsModule(services)
        loaded["polls"].init_app(app)
    if enabled.get("abtest"):
        from modules.abtest import ABTestModule
        loaded["abtest"] = ABTestModule(services)
    if enabled.get("crm"):
        from modules.crm import CRMModule
        loaded["crm"] = CRMModule(services)
    if enabled.get("newsletter"):
        from modules.newsletter import NewsletterModule
        loaded["newsletter"] = NewsletterModule(services)
    if enabled.get("store"):
        from modules.store import StoreModule
        loaded["store"] = StoreModule(services)
    if enabled.get("ads"):
        from modules.ads import AdsModule
        loaded["ads"] = AdsModule(services)
    if enabled.get("trends"):
        from modules.trends import TrendsModule
        loaded["trends"] = TrendsModule(services)
    if enabled.get("ok_api"):
        from modules.ok_api import OkApiModule
        loaded["ok_api"] = OkApiModule(services)
    if enabled.get("ai_images_prov"):
        from modules.ai_images_prov import AiImagesProvModule
        loaded["ai_images_prov"] = AiImagesProvModule(services)
    if enabled.get("ab_auto"):
        from modules.ab_auto import AbAutoModule
        loaded["ab_auto"] = AbAutoModule(services)
    if enabled.get("media_pipeline"):
        from modules.pipeline_media import MediaPipelineModule
        loaded["media_pipeline"] = MediaPipelineModule(services)
    if enabled.get("auto_scheduler"):
        from modules.auto_scheduler import AutoSchedulerModule
        loaded["auto_scheduler"] = AutoSchedulerModule(services)
    if enabled.get("recommendations"):
        from modules.recommendations import RecommendationsModule
        loaded["recommendations"] = RecommendationsModule(services)
    if enabled.get("store_integrations"):
        from modules.store_integrations import StoreIntegrationsModule
        loaded["store_integrations"] = StoreIntegrationsModule(services)
    if enabled.get("auto_calendar"):
        from modules.auto_calendar import AutoCalendarModule
        loaded["auto_calendar"] = AutoCalendarModule(services)
    services["modules"] = loaded
    return loaded


modules = load_modules()
app.register_blueprint(admin_bp)


@app.get("/health")
def health():
    return {"status": "ok", "modules": list(modules.keys())}


# Partner redirector with UTM click logging
@app.get("/r/<slug>")
def redirector(slug):
    target_enc = request.args.get("u", "")
    try:
        target = urllib.parse.parse_qs(target_enc).get("t", [""])[0] if "%3A" in target_enc else target_enc
    except Exception:
        target = target_enc
    ua = request.headers.get("User-Agent", "")
    ip = request.headers.get("X-Forwarded-For") or request.remote_addr
    services["db"].log_click(slug, target, "", ua, ip)
    return redirect(target or "/admin")


@app.post("/webhook")
def webhook():
    data = request.get_json(force=True, silent=True) or {}
    app.request_data_cache = data
    uid = str((data.get("user") or {}).get("uid") or data.get("uid") or "")
    text = (data.get("text") or "").strip().lower()
    if not uid: return jsonify({"status": "no-user"}), 200
    add_user(uid)
    if text in ("/start", "start", "меню"):
        ok_api.send_message(uid, "Меню: 1) совет 2) партнёрка 3) опрос 4) магазин")
        update_user(uid, "start")
        log_event(uid, "start")
        return {"status": "ok"}
    elif text == "1":
        ok_api.send_message(uid, "Совет дня: пейте воду 💧")
        update_user(uid, "tip")
        log_event(uid, "tip")
    elif text == "2":
        partner = modules.get("partner")
        url = partner.build_link(os.getenv("PARTNER_LINK", "https://partner.example/consult"),
                                 slug="consult") if partner else os.getenv("PARTNER_LINK",
                                                                           "https://partner.example/consult")
        ok_api.send_message(uid, f"Консультация: {url}")
        update_user(uid, "partner")
        log_event(uid, "partner")
    elif text == "3":
        ok_api.send_message(uid, "Опрос скоро будет доступен 🗳️")
        update_user(uid, "poll")
        log_event(uid, "poll")
    elif text == "4":
        store = modules.get("store")
        goods = store.list_products() if store else []
        if goods:
            lines = [f"{g['title']} — {g['price']} ₽: {g['url']}" for g in goods]
            ok_api.send_message(uid, "Витрина:\n" + "\n".join(lines))
        else:
            ok_api.send_message(uid, "Витрина пуста.")
        update_user(uid, "store")
        log_event(uid, "store")
    else:
        ok_api.send_message(uid, "Не понял команду. Напиши /start")
        update_user(uid, "unknown")
        log_event(uid, "unknown", text)
    return {"status": "ok"}


@app.post("/admin/drag_reschedule")
def drag_reschedule():
    pid = int(request.form.get("post_id"))
    date = request.form.get("date")  # YYYY-MM-DD
    time = request.form.get("time", "10:00")
    __import__("db").schedule_post(pid, f"{date} {time}:00")
    return jsonify({"ok": True})


@app.post("/admin/import_csv")
def import_csv():
    f = request.files.get("file")
    if not f: return jsonify({"error": "no file"}), 400
    import csv, io
    reader = csv.DictReader(io.StringIO(f.stream.read().decode("utf-8")))
    count = 0
    for r in reader:
        text = r.get("text", "").strip()
        template = r.get("template") or None
        if not text: continue
        __import__("db").add_post(text, None, template)
        if r.get("date") and r.get("time"):
            try:
                __import__("db").schedule_post(__import__("db").list_posts(limit=1)[0]["id"],
                                               f"{r['date']} {r['time']}:00")
            except Exception:
                pass
        count += 1
    return jsonify({"imported": count})


@app.get("/admin/settings/export")
def settings_export():
    s = __import__("db").get_setting("enabled_modules", {})
    from flask import Response
    return Response(json.dumps({"enabled_modules": s}, ensure_ascii=False, indent=2), mimetype="application/json")


@app.post("/admin/settings/import")
def settings_import():
    data = request.get_json(force=True, silent=True) or {}
    if "enabled_modules" in data:
        __import__("db").set_setting("enabled_modules", data["enabled_modules"])
    return jsonify({"ok": True})


@app.post("/admin/ab/create")
def ab_create():
    name = request.form.get("name", "AB Test")
    a_text = request.form.get("a_text", "")
    b_text = request.form.get("b_text", "")
    db = services["db"]
    gid = db.create_ab_group(name)
    if a_text:
        db.add_post(a_text);
        pid = db.list_posts(limit=1)[0]["id"]
        db.add_ab_variant(gid, pid, "A")
    if b_text:
        db.add_post(b_text);
        pid = db.list_posts(limit=1)[0]["id"]
        db.add_ab_variant(gid, pid, "B")
    return jsonify({"group_id": gid})


@app.get("/admin/besttime")
def besttime():
    hist = services["db"].engagement_histogram_by_hour()
    top = sorted(hist.items(), key=lambda kv: kv[1], reverse=True)[:3]
    return jsonify({"best_hours": [h for h, _ in top], "hist": hist})


@app.get("/admin/recommendations")
def admin_recommendations():
    rec = modules.get("recommendations").suggest() if modules.get("recommendations") else {"best_hours": [12, 18, 20],
                                                                                           "format_tip": "Публикуйте короче и с картинкой"}
    return jsonify(rec)


@app.post("/admin/ab/autopick")
def ab_autopick():
    db = services["db"]
    clicks = db.clicks_by_slug()
    stats = db.ab_group_stats()
    mod = modules.get("ab_auto")
    winners = mod.pick_winner(stats, clicks) if mod else {}
    return jsonify({"winners": winners})


@app.post("/admin/ab/post_winner")
def ab_post_winner():
    gid = int(request.form.get("group_id"))
    winners = (services.get("cache_last_winners") or {})
    win = winners.get(gid)
    if not win:
        return jsonify({"error": "no winner cached"}), 400
    ok = modules.get("ab_auto").continue_posting(win)
    return jsonify({"ok": ok})


@app.get("/admin/segments/top")
def segments_top():
    seg = services["db"].segment_top_loyal()
    return jsonify({"top": seg})


@app.post("/admin/auto/schedule_all")
def auto_schedule_all():
    mod = modules.get("auto_scheduler")
    if not mod: return jsonify({"error": "auto_scheduler disabled"}), 400
    res = mod.schedule_winners_and_drafts()
    return jsonify(res)


@app.post("/admin/media/genpost")
def media_genpost():
    mod = modules.get("pipeline_media")
    text = request.form.get("text", "Пост с AI-картинкой")
    prompt = request.form.get("prompt", "милый котик с ноутбуком, пиксель-арт")
    if not mod: return jsonify({"error": "pipeline_media disabled"}), 400
    return jsonify(mod.generate_and_post(text, prompt))


@app.route("/admin/media/batch", methods=["POST"])
def media_batch():
    mod = modules.get("pipeline_media")
    if not mod:
        return jsonify({"error": "pipeline_media module not loaded"}), 500

    items = []

    # 1) JSON-запрос
    if request.is_json:
        data = request.get_json(force=True, silent=True) or {}
        items = data.get("items", [])

    # 2) Форма (textarea -> name="items")
    elif "items" in request.form:
        raw = request.form.get("items")
        for line in raw.strip().split("\n"):
            parts = line.split("|")
            if len(parts) >= 2:
                text = parts[0].strip()
                prompt = parts[1].strip()
                count = int(parts[2]) if len(parts) > 2 else 1
                items.append({"text": text, "prompt": prompt, "n_images": count})

    if not items:
        return jsonify({"error": "No items provided"}), 400

    results = mod.batch_generate(items)
    return jsonify({"status": "ok", "results": results})


@app.get("/admin/media/batch")
def media_batch_page():
    return render_template("media_batch.html")


if __name__ == "__main__":
    debug_mode = os.getenv("FLASK_DEBUG", "true").lower() == "true"

    # Запускаем Flask
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("FLASK_PORT", "5010")),
        debug=debug_mode
    )
