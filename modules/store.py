# modules/store.py
from . import ModuleBase

SAMPLE = [
    {"sku": "OZ-1001", "title": "Щётка для лица", "price": 999.0, "url": "https://www.ozon.ru",
     "image": "/static/store/brush.png", "tags": "beauty"},
    {"sku": "WB-2002", "title": "Увлажняющий крем", "price": 1299.0, "url": "https://www.wildberries.ru",
     "image": "/static/store/cream.png", "tags": "beauty,skin"}
]


class StoreModule(ModuleBase):
    name = "store"
    title = "Витрина (Ozon/WB — заглушки)"

    def list_products(self):
        return SAMPLE
