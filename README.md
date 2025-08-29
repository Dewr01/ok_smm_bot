# OK SMM Combiner

SMM-комбайн для автоматизации публикаций в Одноклассниках. Система включает AI-генерацию контента, планирование публикаций, аналитику и управление через веб-интерфейс и Telegram-бота.

## 🚀 Возможности
- Веб‑админка (Flask + SQLite) для управления шаблонами и постами.
- Динамическая загрузка модулей (AI‑генерация, пул контента, тренды, автопостинг).
- Telegram‑бот‑админ: просмотр очереди, публикация и добавление постов из чата.
- Планировщик постов (auto_scheduler).
- REST‑API для интеграций.
- Простая система конфигурации через `.env`.

## 📦 Установка

### 1. Клонирование
```bash
git clone https://github.com/Dewr01/ok_smm_bot.git
cd ok_smm_bot
```

### 2. Виртуальное окружение
```bash
python -m venv .venv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate    # Windows
```

### 3. Зависимости
```bash
pip install -r requirements.txt
```

### 4. Переменные окружения
Создайте файл `.env` на основе `.env.example` и укажите значения:
```
# OK API настройки
OK_APP_KEY=your_ok_app_key
OK_ACCESS_TOKEN=your_ok_access_token
OK_SESSION_SECRET_KEY=your_ok_session_secret
OK_GROUP_ID=your_group_id

# Telegram бот
TG_BOT_TOKEN=your_telegram_bot_token

# AI сервисы (опционально)
OPENAI_API_KEY=sk-...  # для AI изображений
GIGACHAT_AUTH_KEY=your_gigachat_key  # для AI текстов

# RSS фиды для контента
RSS_FEEDS=https://habr.com/ru/rss/flows/develop/all/,
https://anekdot.ru/rss/export_j.xml,
...

# Партнерские ссылки
PARTNER_LINK=https://partner.example/consult

# SMTP для рассылок
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASS=your_app_password
SMTP_FROM=your_email@gmail.com

# Настройки приложения
FLASK_PORT=5010
FLASK_SECRET_KEY=your_secret_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme
```

## ▶️ Запуск

### Flask‑админка
```bash
python app.py
```
Приложение будет доступно на `http://127.0.0.1:5010`  
Админка: `http://127.0.0.1:5010/admin` (Basic‑Auth из `.env`).

### Инициализация базы данных (в другом окне)

```bash
# Создание БД и наполнение начальными данными из RSS_FEEDS
python seed.py
```
```bash
# AI наполнение БД начальными данными
python seed_ai.py
```


### Telegram‑бот
Если включён модуль `tg_admin` и задан `TG_BOT_TOKEN`, бот стартует автоматически вместе с Flask.  
Команды:
- `/start` — список команд.
- `/update_posts` - обновить список постов. (выполняется сразу seed.py и seed_ai.py)
- `/queue` — очередь публикаций.
- `/publish <номер>` — публикация поста.
- `/addpost <текст>` — добавить новый пост в очередь.
- `/preview <id>` - предпросмотр поста.
- `/delete <id>` - удалить пост.
- `/addpost <текст>` - добавить новый пост.

> ⚠️ В режиме `debug=True` Flask перезапускает процесс. Чтобы бот не стартовал дважды, в `app.py` уже добавлена защита с переменной `WERKZEUG_RUN_MAIN`.

## 📁 Структура проекта

```text
ok_bot/
├── admin/                 # Веб-админка
│   ├── templates/        # HTML шаблоны
│   ├── __init__.py
│   └── routes.py         # Роуты админки
├── modules/              # Модули системы
│   ├── autopost.py       # Автопостинг
│   ├── ai_writer.py      # AI генерация текстов
│   ├── ai_images.py      # AI генерация изображений
│   ├── tg_admin.py       # Telegram бот
│   └── ...              # Другие модули
├── static/              # Статические файлы
├── assistant.db         # База данных (создаётся автоматически)
├── app.py              # Основное приложение
├── db.py               # Работа с базой данных
├── config.py           # Конфигурация
├── seed.py            # Наполнение начальными данными
├── seed_ai.py            # Наполнение начальными данными
└── requirements.txt    # Зависимости
```
## 🛠 Модули системы

### Включение/выключение модулей

#### ✅ **Включено по умолчанию:**
* autopost - автопостинг
* analytics - аналитика
* partner - партнерские ссылки
* content_pool - сбор контента из RSS
* tg_admin - Telegram бot

#### ⚙️ **Требуют настройки:**
* ai_writer - нужен GIGACHAT_AUTH_KEY
* ai_images - нужен OPENAI_API_KEY
* newsletter - нужны SMTP настройки

## 📊 Работа с контентом

### 1. Добавление постов

#### Через веб-интерфейс:
* Перейдите в /admin/posts
* Добавьте текст, картинку (опционально), выберите шаблон

#### Через Telegram:
```text
/addpost Ваш текст поста
```

#### Через импорт CSV:
* Поддерживается импорт из CSV файла
* Формат: text,template,date(YYYY-MM-DD),time(HH:MM)

### 2. Шаблоны постов

Система включает готовые шаблоны:

* Совет дня - советы по здоровому образу жизни
* ТОП-5 - списки и рекомендации
* Вопрос подписчикам - вовлекающие вопросы

### 3. Планирование публикаций

* Автокалендарь - автоматическое распределение постов на неделю
* Ручное планирование - drag&drop в календаре
* Best time - публикация в лучшее время based on analytics

## 🔧 API endpoints

* POST /webhook - вебхуки от Одноклассников
* GET /r/<slug> - партнерские редиректы
* POST /admin/publish_now/<id> - мгновенная публикация
* GET /admin/analytics - аналитика

## 🐳 Docker запуск

Можно запускать веб‑админку и Telegram‑бота как два отдельных сервиса.

**docker-compose.yml** (пример):

```yaml
version: "3.9"
services:
  web:
    build: .
    command: python app.py
    volumes:
      - .:/app
    env_file:
      - .env
    ports:
      - "5010:5010"

  tg_bot:
    build: .
    command: python -m modules.tg_admin
    volumes:
      - .:/app
    env_file:
      - .env
```

Запуск:
```bash
docker-compose up --build
```

Теперь:
- Админка доступна на `http://127.0.0.1:5010`  
- Telegram‑бот работает отдельно и не мешает Flask.


## 🛠️ Разработка

- Код разбит на модули в папке `modules/`.
- Для добавления нового модуля создайте файл `modules/<имя>.py` и реализуйте класс, наследующий `ModuleBase`.
- Включение модуля производится через переменные окружения (`MODULE_<NAME>=true`).

## 📌 Дальнейшие улучшения
- Alembic миграции для базы данных.
- Переход с Basic‑Auth на Flask‑Login с сессиями и CSRF‑защитой.
- CI (GitHub Actions) для линтинга и тестов.

## 📄 Лицензия
MIT
