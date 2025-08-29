import requests


def fetch_health_jokes():
    """Анекдоты о красоте и здоровье с anekdot.ru"""
    url = "https://anekdot.ru/rss/export_j.xml"
    headers = {"User-Agent": "ok-smm-bot/1.0"}
    jokes = []

    try:
        r = requests.get(url, headers=headers, timeout=10)
        if r.ok:
            # Парсим RSS
            import xml.etree.ElementTree as ET
            root = ET.fromstring(r.content)

            # Ищем анекдоты по ключевым словам
            keywords = ["красот", "здоров", "врач", "доктор", "медицин", "диет", "спорт", "зарядк", "космет",
                        "парикмахер", "массаж", "йог", "фитнес", "витамин", "таблетк", "больнич", "клиник"]

            for item in root.findall(".//item"):
                title = item.find("title").text if item.find("title") is not None else ""
                description = item.find("description").text if item.find("description") is not None else ""

                # Объединяем title и description для поиска
                full_text = (title + " " + description).lower()

                # Проверяем наличие ключевых слов
                if any(keyword in full_text for keyword in keywords):
                    joke_text = description if description else title
                    if joke_text:
                        jokes.append(f"😂 {joke_text}")

                    # Ограничим количество
                    if len(jokes) >= 10:
                        break

        # Если не нашли тематических анекдотов, добавим запасные
        if not jokes:
            jokes = [
                "😂 Доктор, я буду жить? - А смысл?",
                "😂 Пришла женщина к врачу: 'Доктор, у меня от витаминов побочный эффект - муж стал внимательнее!'",
                "😂 - Дорогой, я на диете. - Отлично! А что мы будем есть?",
                "😂 Муж спрашивает жену: 'Что это у тебя за крем за 5000 рублей?' - 'Это крем от морщин.' - 'А почему ты его на мою рубашку нанесла?'",
                "😂 Забота о здоровье - это когда ты покупаешь органическую еду, а потом запиваешь её энергетиком."
            ]

    except Exception as e:
        print(f"[WARN] Ошибка загрузки анекдотов: {e}")
        # Запасные анекдоты
        jokes = [
            "😂 Девушка, вы не знаете, где можно купить витамины? - В аптеке. - Странно, там сказали, что у них только лекарства...",
            "😂 - Я начал заниматься йогой. - И как успехи? - Уже могу дотянуться до пульта не вставая с дивана!",
            "😂 Правильное питание - это когда смотришь на пирожное и говоришь: 'Нет, я сильный!' А потом съедаешь его, чтобы не пропало."
        ]

    return jokes


print(fetch_health_jokes())
