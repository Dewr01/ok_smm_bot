import hashlib
import json
import os
import random
import time

import requests
from dotenv import load_dotenv

from .ratelimit import RateLimiter

load_dotenv()


class OkApiError(Exception):
    pass


class OkClient:
    def __init__(self, session=None, limiter: RateLimiter = None):
        self.app_key = os.getenv("OK_APP_KEY", "")
        self.access_token = os.getenv("OK_ACCESS_TOKEN", "")
        self.session_secret_key = os.getenv("OK_SESSION_SECRET_KEY", "")
        self.group_id = os.getenv("OK_GROUP_ID", "")
        self.api_server = os.getenv("OK_API_SERVER", "https://api.ok.ru/fb.do")
        self.format = "json"
        self.s = session or requests.Session()
        self.timeout = (6, 45)  # connect, read
        self.retries = 3
        self.limiter = limiter or RateLimiter(5, 1.0)  # 5 rps

    def _sig(self, params: dict) -> str:
        raw = "".join([f"{k}={params[k]}" for k in sorted(params.keys())])
        return hashlib.md5((raw + self.session_secret_key).encode("utf-8")).hexdigest()

    def _call_once(self, payload):
        self.limiter.acquire()
        resp = self.s.post(self.api_server, data=payload, timeout=self.timeout)
        resp.raise_for_status()
        data = resp.json()
        if isinstance(data, dict) and data.get("error_code"):
            raise OkApiError(f"{data.get('error_code')}:{data.get('error_msg')}")
        return data

    def call(self, method: str, **kwargs):
        base = {
            "application_key": self.app_key,
            "method": method,
            "format": self.format,
        }
        base.update(kwargs)

        # строим подпись БЕЗ access_token
        sig_params = {k: v for k, v in base.items() if k != "access_token"}
        raw = "".join([f"{k}={sig_params[k]}" for k in sorted(sig_params.keys())])
        sig = hashlib.md5((raw + self.session_secret_key).encode("utf-8")).hexdigest()

        # добавляем access_token и sig
        base["access_token"] = self.access_token
        base["sig"] = sig

        last_err = None
        for attempt in range(1, self.retries + 1):
            try:
                return self._call_once(base)
            except (OkApiError, requests.RequestException) as e:
                last_err = e
            time.sleep(min(2**attempt + random.random(), 8))
        raise OkApiError(f"Failed after {self.retries} retries: {last_err}")

    # --- публикации ---
    def mediatopic_post(self, gid: str, text: str, attachments: list = None):
        payload = {
            "type": "GROUP_THEME",
            "gid": gid,
            "attachment": json.dumps({
                "media": [{"type": "text", "text": text}] + (attachments or [])
            }, ensure_ascii=False)
        }
        return self.call("mediatopic.post", **payload)

    def post_text(self, text: str):
        """Алиас для публикации простого текстового поста"""
        return self.mediatopic_post(gid=self.group_id, text=text)

    def post_with_image(self, text: str, image_id: str):
        """Алиас для публикации поста с картинкой"""
        attachment = [
            {"type": "photo", "list": [{"id": image_id}]}
        ]
        return self.mediatopic_post(gid=self.group_id, text=text, attachments=attachment)

    # --- фото ---
    def photos_get_upload_url(self, gid: str, album_id: str = None):
        kwargs = {"gid": gid}
        if album_id:
            kwargs["aid"] = album_id
        return self.call("photosV2.getUploadUrl", **kwargs)

    def photos_commit(self, token: str):
        return self.call("photosV2.commit", token=token)

    def upload_photo_file(self, upload_url: str, file_path: str):
        with open(file_path, "rb") as f:
            files = {"file": (os.path.basename(file_path), f, "image/png")}
            r = self.s.post(upload_url, files=files, timeout=self.timeout)
            r.raise_for_status()
            try:
                return r.json()
            except Exception:
                return {"token": r.text}

    def upload_photos(self, gid: str, paths: list, album_id: str = None):
        up = self.photos_get_upload_url(gid, album_id=album_id)
        upload_url = up.get("upload_url") if isinstance(up, dict) else None
        if not upload_url:
            raise OkApiError("upload_url not received")
        tokens = []
        for p in paths:
            resp = self.upload_photo_file(upload_url, p)
            tok = resp.get("token") or (resp.get("photos", [{}])[0].get("token") if isinstance(resp, dict) else str(resp))
            if tok:
                self.photos_commit(tok)
                tokens.append(tok)
        return tokens
