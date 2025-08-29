# ok_api.py
import hashlib
import json
import os
import requests


class OKApi:
    BASE_URL = "https://api.ok.ru/fb.do"

    def __init__(self):
        self.app_key = os.getenv("OK_APP_KEY")
        self.app_secret = os.getenv("OK_APP_SECRET")
        self.access_token = os.getenv("OK_ACCESS_TOKEN")
        self.group_id = os.getenv("OK_GROUP_ID")
        self.session_secret = hashlib.md5(
            (self.access_token + self.app_secret).encode()).hexdigest() if self.access_token and self.app_secret else ""

    def _sign(self, params: dict) -> str:
        base = ''.join([f"{k}={params[k]}" for k in sorted(params.keys())])
        return hashlib.md5((base + self.session_secret).encode()).hexdigest()

    def call(self, method: str, params: dict):
        core = {
            "method": method,
            "application_key": self.app_key,
            "access_token": self.access_token,
            "format": "json",
        }
        payload = {**core, **params}
        if self.session_secret:
            payload["sig"] = self._sign(payload)
        r = requests.post(self.BASE_URL, data=payload, timeout=20)
        r.raise_for_status()
        return r.json()

    def send_message(self, uid: str, message: str):
        try:
            return self.call("messages.send", {"recipient": uid, "message": message})
        except Exception as e:
            return {"error": str(e)}

    def post_text(self, text: str):
        attachment = {"media": [{"type": "text", "text": text}]}
        return self.call("mediatopic.post", {"gid": self.group_id, "type": "GROUP_THEME",
                                             "attachment": json.dumps(attachment, separators=(',', ':'))})
