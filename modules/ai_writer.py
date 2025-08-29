# modules/ai_writer.py
from . import ModuleBase
import os
import uuid
import requests
import urllib3
from dotenv import load_dotenv

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
load_dotenv()


class AIWriterModule(ModuleBase):
    name = "ai_writer"
    title = "AI тексты"

    AUTH_URL = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"
    CHAT_URL = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"

    def _get_access_token(self):
        auth_key = os.getenv("GIGACHAT_AUTH_KEY", "").strip()
        if not auth_key:
            raise RuntimeError("Нет GIGACHAT_AUTH_KEY в .env")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": str(uuid.uuid4()),
            "Authorization": f"Basic {auth_key}",
        }
        data = {"scope": "GIGACHAT_API_PERS"}
        resp = requests.post(self.AUTH_URL, headers=headers, data=data, verify=False, timeout=15)
        resp.raise_for_status()
        return resp.json()["access_token"]

    def _gigachat_text(self, prompt: str) -> str:
        token = self._get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        payload = {
            "model": "GigaChat",
            "messages": [
                {
                    "role": "system",
                    "content": "Ты — автор коротких и интересных постов для соцсетей."
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_tokens": 700,
        }
        resp = requests.post(self.CHAT_URL, headers=headers, json=payload, verify=False, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data["choices"][0]["message"]["content"]

    def generate(self, template: str, topic: str, tone: str = "дружелюбный"):
        base = f"Тема: {topic}\nТон: {tone}\nШаблон: {template}\n"
        try:
            return self._gigachat_text(base)
        except Exception as e:
            # fallback — простые заготовки
            if template == "Совет дня":
                return base + "Совет дня: пейте воду 💧"
            if template == "ТОП-5":
                return base + "ТОП-5: 1) Вода 2) Сон 3) Движение 4) Свет 5) Режим"
            if template == "Вопрос подписчикам":
                return base + "Вопрос: как вы заботитесь о коже утром?"
            return base + f"[AI fallback] Ошибка GigaChat: {e}"
