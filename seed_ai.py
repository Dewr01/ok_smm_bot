import os
import datetime
import random
from dotenv import load_dotenv

from modules.ai_writer import AIWriterModule
from db import add_post, init_db

load_dotenv()


def get_ai_topics():
    """
    Читает список тем из .env.
    Формат: AI_TOPICS="Совет дня:здоровый сон;ТОП-5:биохакинг привычки;Вопрос подписчикам:мотивация"
    """
    raw = os.getenv("AI_TOPICS", "").strip()
    topics = []

    if raw:
        for part in raw.split(";"):
            if ":" in part:
                tpl, topic = part.split(":", 1)
                topics.append((tpl.strip(), topic.strip()))

    # дефолтные темы
    if not topics:
        topics = [
            ("Совет дня", "здоровый образ жизни"),
            ("ТОП-5", "продукты для энергии"),
            ("Совет дня", "психология отношений"),
            ("Совет дня", "биохакинг"),
            ("ТОП-5", "здоровые привычки"),
            ("Рецепт дня", "правильное питание"),
        ]

    return topics


def main():
    print(">> init db")
    init_db()

    services = {}  # можно расширить, если нужно
    ai_writer = AIWriterModule(services)

    per_run = int(os.getenv("AI_POSTS_PER_RUN", "3"))
    topics_pool = get_ai_topics()

    chosen = random.sample(topics_pool, min(per_run, len(topics_pool)))

    posts = []
    for tpl, topic in chosen:
        print(f">> Генерация AI-поста: {tpl} ({topic})")
        try:
            text = ai_writer.generate(tpl, topic)
            if text:
                posts.append((text, None))
        except Exception as e:
            print(f"[ERR] {e}")

    for idx, (text, image) in enumerate(posts, start=1):
        dt = datetime.datetime.now() + datetime.timedelta(minutes=idx * 30)
        add_post(text, image, dt)
        print(f"   {dt} -> {text[:60]}...")

    print(f">> Сгенерировано {len(posts)} AI-постов")


if __name__ == "__main__":
    main()
