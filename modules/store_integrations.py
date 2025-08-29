# modules/store_integrations.py
from . import ModuleBase
import os


class StoreIntegrationsModule(ModuleBase):
    name = "store_integrations"
    title = "Витрина Ozon/WB (API)"

    def fetch_ozon(self, query: str = ""):
        if not (os.getenv("OZON_API_KEY") and os.getenv("OZON_CLIENT_ID")):
            return []
        # In prod: call Ozon API search
        return [{"title": "Пример товар Ozon", "price": 999, "link": "https://ozon.ru/t/partner"}]

    def fetch_wb(self, query: str = ""):
        if not os.getenv("WB_API_KEY"):
            return []
        # In prod: call WB API search
        return [{"title": "Пример товар WB", "price": 799, "link": "https://wb.ru/t/partner"}]
