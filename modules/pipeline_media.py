# modules/pipeline_media.py
from . import ModuleBase
import os, json, base64, tempfile, requests
from .ok_client import OkClient, OkApiError


class MediaPipelineModule(ModuleBase):
    name = "media_pipeline"
    title = "Медиапайплайн (AI→OK)"

    def _openai_image(self, prompt: str, size: str = "1024x1024") -> bytes:
        url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1/images/generations")
        key = os.getenv("OPENAI_API_KEY", "")
        if not key:
            return None
        headers = {"Authorization": f"Bearer {key}"}
        payload = {"model": "gpt-image-1", "prompt": prompt, "size": size}
        r = requests.post(url, headers=headers, json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        b64 = data["data"][0]["b64_json"]
        return base64.b64decode(b64)

    def _sd_image(self, prompt: str, size: str = "1024x1024") -> bytes:
        url = os.getenv("STABLE_DIFFUSION_URL", "").strip()
        if not url:
            return None
        r = requests.post(url, json={"prompt": prompt, "size": size}, timeout=120)
        r.raise_for_status()
        # assume it returns base64 field 'image' or raw bytes
        try:
            j = r.json()
            if "image" in j:
                return base64.b64decode(j["image"])
        except Exception:
            pass
        return r.content

    def _gen_one(self, prompt: str) -> bytes:
        img = self._openai_image(prompt) or self._sd_image(prompt)
        if img:
            return img
        # fallback tiny PNG
        return b"\x89PNG\r\n\x1a\n" + b"\x00" * 128

    def generate_and_post(self, text: str, prompt: str, gid: str = None, album_id: str = None, n_images: int = 1):
        gid = gid or os.getenv("OK_GROUP_ID", "")
        okc = OkClient()
        tmp_paths = []
        try:
            for i in range(max(1, n_images)):
                img = self._gen_one(prompt)
                fd, path = tempfile.mkstemp(suffix=".png")
                with os.fdopen(fd, "wb") as f:
                    f.write(img)
                tmp_paths.append(path)
            tokens = okc.upload_photos(gid, tmp_paths, album_id=album_id)
            media_list = [{"type": "picture", "list": [{"id": t}]} for t in tokens]
            attachments = {"media": media_list}
            post = okc.mediatopic_post(gid, text, attachments)
            return {"ok": True, "uploaded": len(tokens), "post": post}
        finally:
            for p in tmp_paths:
                try:
                    os.remove(p)
                except Exception:
                    pass

    def batch_generate(self, items: list, gid: str = None, album_id: str = None):
        """
        items: [{text, prompt, n_images?}] — создаёт серию постов
        """
        results = []
        for it in items:
            res = self.generate_and_post(
                it.get("text", "Пост"),
                it.get("prompt", "минималистичный постер"),
                gid=gid, album_id=album_id, n_images=int(it.get("n_images", 1))
            )
            results.append(res)
        return results
