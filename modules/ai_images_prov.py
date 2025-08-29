# modules/ai_images_prov.py
from . import ModuleBase
import os


class AiImagesProvModule(ModuleBase):
    name = "ai_images_prov"
    title = "AI Картинки (OpenAI/SD)"

    def generate(self, prompt: str):
        if os.getenv("OPENAI_API_KEY"):
            # placeholder content; in prod call OpenAI Images API
            return b"[PNG-DATA]"
        if os.getenv("STABLE_DIFFUSION_URL"):
            # placeholder content; in prod call SD server
            return b"[PNG-DATA]"
        return None
