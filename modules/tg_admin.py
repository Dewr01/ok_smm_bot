import os
import asyncio
import threading
from telegram.ext import Application, CommandHandler

import db
from modules.ok_api import OkApiModule
from seed import run_seed
from seed_ai import main as seed_ai_main
from .autopost import AutoPostModule

from . import ModuleBase
from db import list_queue, publish_post, add_post


class TGAdminModule(ModuleBase):
    name = "tg_admin"

    def __init__(self, services):
        super().__init__(services)
        self.services = services or {}
        self._app = None
        self._thread = None

    def init_app(self, app):
        """Метод, который вызывает app.py для инициализации модуля"""
        self.init()

    def init(self):
        token = os.getenv("TG_BOT_TOKEN")
        if not token:
            print("⚠️ TG_BOT_TOKEN не найден в .env — Telegram-бот не запущен")
            return

        self._app = Application.builder().token(token).build()

        # === Команды ===
        async def start(update, context):
            await update.message.reply_text("Доступные команды:\n"
                                            "/posts - список постов\n"
                                            "/update_posts - обновить список постов\n"
                                            "/queue - очередь публикаций\n"
                                            "/preview <id> - предпросмотр поста\n"
                                            "/publish <id> - опубликовать пост\n"
                                            "/delete <id> - удалить пост\n"
                                            "/addpost <текст> - добавить новый пост")

        async def queue(update, context):
            posts = list_queue()
            if not posts:
                await update.message.reply_text("Очередь пуста.")
            else:
                msg = "\n\n".join([f"{i + 1}. {p['body']}" for i, p in enumerate(posts)])
                await update.message.reply_text("Черновики:\n" + msg)

        async def posts(update, context):
            try:
                limit = 10
                if context.args:
                    try:
                        limit = min(int(context.args[0]), 50)
                    except Exception:
                        pass

                posts = __import__("db").list_posts(limit=limit)
                if not posts:
                    await update.message.reply_text("📭 Постов нет.")
                    return

                lines = []
                for p in posts:
                    pid = p.get("id")
                    body = (p.get("text") or "").strip()
                    body_short = body.replace("\n", " ")[:120]  # первые 120 символов
                    status = "🕒 в очереди"
                    if p.get("published_at"):
                        status = "✅ опубликован"
                    elif p.get("scheduled_at"):
                        status = f"📅 запланирован на {p['scheduled_at']}"
                    lines.append(f"ID {pid}: {body_short} ({status})")

                msg = "\n\n".join(lines)
                await update.message.reply_text(msg[:4000])  # лимит телеги
            except Exception as e:
                await update.message.reply_text(f"Ошибка: {e}")

        async def update_posts(update, context):
            try:
                run_seed()
                seed_ai_main()
                await update.message.reply_text("✅ Посты обновлены!")
            except Exception as e:
                await update.message.reply_text(f"Ошибка: {e}")

        async def publish(update, context):
            if not context.args:
                await update.message.reply_text("⚠️ Используй: /publish <id>")
                return
            try:
                pid = int(context.args[0])
                posts = __import__("db").list_posts(limit=500)
                post = next((p for p in posts if p["id"] == pid), None)
                if not post:
                    await update.message.reply_text(f"❌ Пост с ID {pid} не найден.")
                    return
                if post.get("published_at"):
                    await update.message.reply_text("⚠️ Этот пост уже опубликован.")
                    return

                # Прямой вызов API
                from .ok_client import OkClient  # ← ПРАВИЛЬНЫЙ ИМПОРТ

                ok_api = OkClient()  # ← создаем экземпляр клиента

                text = post.get("text", "")
                image_path = post.get("image_path")

                try:
                    if image_path and os.path.exists(image_path):
                        # Используем правильный метод из OkClient
                        tokens = ok_api.upload_photos(ok_api.group_id, [image_path])
                        if tokens:
                            result = ok_api.post_with_image(text, tokens[0])
                        else:
                            result = ok_api.post_text(text)
                    else:
                        result = ok_api.post_text(text)

                    db.mark_published(pid)
                    await update.message.reply_text(f"✅ Пост #{pid} опубликован в Одноклассниках!")

                except Exception as api_error:
                    await update.message.reply_text(f"❌ Ошибка API: {api_error}")

                await update.message.reply_text(f"✅ Пост {pid} опубликован!")
            except Exception as e:
                await update.message.reply_text(f"Ошибка: {e}")

        async def add(update, context):
            body = " ".join(context.args)
            if not body:
                await update.message.reply_text("⚠️ Используй: /addpost <текст>")
                return
            add_post(body)
            await update.message.reply_text("✅ Пост добавлен в очередь.")

        async def delete(update, context):
            if not context.args:
                await update.message.reply_text("⚠️ Используй: /delete <id>")
                return
            try:
                pid = int(context.args[0])
                db = __import__("db")
                posts = db.list_posts(limit=500)
                post = next((p for p in posts if p["id"] == pid), None)
                if not post:
                    await update.message.reply_text(f"❌ Пост с ID {pid} не найден.")
                    return

                db.delete_post(pid)
                await update.message.reply_text(f"🗑 Пост {pid} удалён.")
            except Exception as e:
                await update.message.reply_text(f"Ошибка: {e}")


        # Регистрируем команды
        self._app.add_handler(CommandHandler("start", start))
        self._app.add_handler(CommandHandler("queue", queue))
        self._app.add_handler(CommandHandler("publish", publish))
        self._app.add_handler(CommandHandler("addpost", add))
        self._app.add_handler(CommandHandler("posts", posts))
        self._app.add_handler(CommandHandler("update_posts", update_posts))
        self._app.add_handler(CommandHandler("delete", delete))

        # Запускаем бота в отдельном потоке с собственным event loop
        def run():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self._app.initialize())
            loop.run_until_complete(self._app.start())
            loop.create_task(self._app.updater.start_polling())
            try:
                loop.run_forever()
            finally:
                loop.run_until_complete(self._app.stop())
                loop.close()

        self._thread = threading.Thread(target=run, daemon=True)
        self._thread.start()


# Позволяет запускать модуль отдельно для отладки
if __name__ == "__main__":
    mod = TGAdminModule({"db": __import__("db")})
    mod.init()
    print("TG Admin Bot запущен. Нажмите Ctrl+C для выхода.")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        print("Остановка.")
