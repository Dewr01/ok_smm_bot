# config.py
import os


def env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None: return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")


ENABLED_MODULES_DEFAULT = {
    "autopost": env_bool("MODULE_AUTOPOST", True),
    "analytics": env_bool("MODULE_ANALYTICS", True),
    "partner": env_bool("MODULE_PARTNER", True),
    "replies": env_bool("MODULE_REPLIES", True),
    "tg_admin": env_bool("MODULE_TG_ADMIN", True),
    "ai_writer": env_bool("MODULE_AI_WRITER", False),
    "ai_images": env_bool("MODULE_AI_IMAGES", False),
    "content_pool": env_bool("MODULE_CONTENT_POOL", True),
    "polls": env_bool("MODULE_POLLS", True),
    "abtest": env_bool("MODULE_ABTEST", True),
    "crm": env_bool("MODULE_CRM", True),
    "newsletter": env_bool("MODULE_NEWSLETTER", True),
    "store": env_bool("MODULE_STORE", True),
    "ads": env_bool("MODULE_ADS", True),
    "auto_calendar": env_bool("MODULE_AUTO_CALENDAR", True),
    "trends": True,
    "ok_api": True,
    "ai_images_prov": True,
    "ab_auto": True,
    "recommendations": True,
    "store_integrations": True,
    "media_pipeline": True,
    "auto_scheduler": True,
}
