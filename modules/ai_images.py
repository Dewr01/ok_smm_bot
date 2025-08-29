# modules/ai_images.py
from . import ModuleBase
import os, base64


class AIImagesModule(ModuleBase):
    name = "ai_images"
    title = "AI картинки"

    def generate(self, prompt: str):
        # Заглушка — кладём 1x1 PNG как файл
        out_path = os.path.join("static", "images", "ai_demo.png")
        png = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg==")
        with open(out_path, "wb") as f: f.write(png)
        return out_path
