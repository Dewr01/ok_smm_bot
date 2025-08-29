import csv
import html
import os
import random
import re
import time
from datetime import date
from datetime import datetime, timedelta
import feedparser
import requests
import tempfile
from db import add_post, set_setting, upsert_template, clear_posts
from dotenv import load_dotenv

load_dotenv()


def run_seed():
    print(">> init db")

    try:
        clear_posts()
        print(">> old posts cleared")
    except Exception as e:
        print("!! clear skipped:", e)

    # ==========================
    # Включенные модули
    # ==========================
    enabled = {
        "autopost": True,
        "analytics": True,
        "partner": True,
        "replies": True,
        "tg_admin": True,
        "ai_writer": False,  # включи в админке и добавь OPENAI_API_KEY в .env
        "ai_images": False,  # включи в админке и добавь OPENAI_API_KEY в .env
        "content_pool": True,
        "polls": True,
        "abtest": True,
        "crm": True,
        "newsletter": True,
        "store": True,
        "ads": True,
        "auto_calendar": True,
    }
    set_setting("enabled_modules", enabled)
    print(">> enabled modules saved")

    # ==========================
    # Шаблоны
    # ==========================
    templates = {
        "Совет дня": "Совет дня: {{ tip }}\n#советдня #лайфхак",
        "ТОП-5": "ТОП-5 по теме {{ topic }}:\n1) {{i1}}\n2) {{i2}}\n3) {{i3}}\n4) {{i4}}\n5) {{i5}}",
        "Вопрос подписчикам": "Вопрос:\n{{ question }}\nПишите в комментариях!",
    }
    for name, body in templates.items():
        upsert_template(name, body)
    print(">> templates upserted:", ", ".join(templates.keys()))

    # ==========================
    # Старые генераторы (закомментированы)
    # ==========================
    """
    def _gen_advice():
        advices = [
            "Совет дня: Пейте воду 💧 — до {liters} литров в день.",
            "Начните утро с зарядки ⚡ — +100 к энергии.",
            "Не забудьте отдохнуть от экрана 👀 каждый час.",
        ]
        return random.choice(advices).format(liters=random.randint(1, 3))
    """

    # ==========================
    # Хелпер для очистки HTML
    # ==========================
    def _clean_html(html_text: str) -> str:
        if not html_text:
            return ""
        html_text = re.sub(r"<a\b[^>]*>(.*?)</a>", r"\1", html_text, flags=re.I | re.S)
        html_text = re.sub(r"</p\s*>", "\n\n", html_text, flags=re.I)
        html_text = re.sub(r"<br\s*/?>", "\n", html_text, flags=re.I)
        html_text = re.sub(r"<[^>]+>", "", html_text)
        text = html.unescape(html_text)
        text = re.sub(r"\s+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _is_recent(entry, days=1):
        """Пропускаем только статьи, опубликованные не позже чем N дней назад"""
        published = None
        if hasattr(entry, "published_parsed") and entry.published_parsed:
            published = entry.published_parsed
        elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
            published = entry.updated_parsed

        if not published:
            return True  # если даты нет — считаем свежим

        pub_date = date(published.tm_year, published.tm_mon, published.tm_mday)
        today = date.today()
        return (today - pub_date).days <= days

    # ==========================
    # Вытягивание картинки из RSS entry
    # ==========================
    def _extract_image(e):
        img_url = None
        if "media_content" in e:
            for m in e.media_content:
                if m.get("url"):
                    img_url = m["url"]
                    break
        if not img_url and "media_thumbnail" in e:
            img_url = e.media_thumbnail[0].get("url")
        if not img_url:
            for l in e.get("links", []):
                if l.get("rel") == "enclosure" and l.get("type", "").startswith("image/"):
                    img_url = l.get("href")
                    break
        if img_url:
            try:
                resp = requests.get(img_url, timeout=10)
                resp.raise_for_status()
                fd, path = tempfile.mkstemp(suffix=".jpg")
                with os.fdopen(fd, "wb") as f:
                    f.write(resp.content)
                return path
            except Exception as ex:
                print("[IMG-ERR]", img_url, ex)
        return None

    # ==========================
    # Источники контента
    # ==========================

    def fetch_articles_from_rss():
        """Тянем статьи по теме (здоровье/красота/психология/юмор) из RSS с UA и фолбэком."""
        raw_feeds = os.getenv("RSS_FEEDS", "")
        print(">> RAW RSS_FEEDS from .env:", repr(raw_feeds))

        # поддержка многострочного формата в .env
        feeds = []
        for line in raw_feeds.splitlines():
            for f in line.split(","):
                f = f.strip()
                if f:
                    feeds.append(f)

        print(f">> Загружено {len(feeds)} RSS-фидов из .env")
        print(">> Фиды:", feeds)

        headers = {"User-Agent": "Mozilla/5.0 (OK SMM Seeder/1.0)"}
        articles = []

        for url in feeds:
            d = None
            try:
                resp = requests.get(url, headers=headers, timeout=5)
                resp.raise_for_status()
                d = feedparser.parse(resp.content)
            except Exception as e:
                print(f"[WARN] {url}: {e} → fallback на feedparser.parse(url)")
                try:
                    d = feedparser.parse(url)
                except Exception as e2:
                    print(f"[SKIP] {url}: {e2}")
                    continue

            # Берём до 5 материалов на источник
            count = 0
            for e in d.entries[:10]:
                if not _is_recent(e, days=1):
                    continue

                title = (e.get("title") or "").strip()
                link = (e.get("link") or "").strip()

                raw_html = ""
                if e.get("content"):
                    try:
                        raw_html = e["content"][0].get("value") or ""
                    except Exception:
                        raw_html = ""
                if not raw_html:
                    raw_html = e.get("summary") or e.get("description") or ""
                body = _clean_html(raw_html)

                if title and (body or link):
                    text = title
                    if body:
                        text += "\n\n" + body
                    if link:
                        clean_link = link.replace("https://", "").replace("http://", "")
                        text += "\n\nИсточник: " + clean_link
                    image_path = _extract_image(e)
                    articles.append((text, image_path))
                    count += 1

                if count >= 1:
                    break

            time.sleep(0.5)

        return articles

    def fetch_memes_reddit():
        """Мемы с Reddit API (без токена через .json)"""
        url = "https://www.reddit.com/r/memes/hot.json?limit=5"
        headers = {"User-Agent": "ok-smm-bot"}
        r = requests.get(url, headers=headers, timeout=10)
        memes = []
        if r.ok:
            data = r.json()
            for post in data["data"]["children"]:
                title = post["data"]["title"]
                link = "https://reddit.com" + post["data"]["permalink"]
                memes.append(f"😂 {title}\n{link}")
        return memes

    def fetch_tips_csv(path="tips.csv"):
        tips = []
        if not os.path.exists(path):
            return ["💡 Совет: файл tips.csv пока пуст — добавь советы туда!"]
        with open(path, encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row and row[0].strip():
                    tips.append("💡 " + row[0].strip())
        return tips

    # ==========================
    # Сборка постов
    # ==========================
    posts = []
    posts.extend(fetch_articles_from_rss())
    # posts.extend(fetch_memes_reddit())
    # posts.extend(fetch_tips_csv())

    print(f">> собрано {len(posts)} постов")

    # ==========================
    # Автокалендарь (3–4 поста в день)
    # ==========================
    start_date = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
    daily_times = [9, 13, 18, 21]
    day_count = 7

    scheduled = []
    idx = 0

    for day in range(day_count):
        base_date = start_date + timedelta(days=day)
        count_today = random.choice([3, 4])
        times_today = random.sample(daily_times, count_today)
        times_today.sort()
        for h in times_today:
            if idx >= len(posts):
                break
            publish_time = base_date.replace(hour=h)
            body, img = posts[idx]
            add_post(body, image_path=img)
            scheduled.append((publish_time, body))
            idx += 1

    for t, body in scheduled:
        add_post(body)

    print(f">> запланировано {len(scheduled)} постов")
    for t, body in scheduled:
        print("  ", t.strftime("%Y-%m-%d %H:%M"), "->", body[:60], "...")


if __name__ == "__main__":
    run_seed()
