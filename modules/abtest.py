# modules/abtest.py
from . import ModuleBase


class ABTestModule(ModuleBase):
    name = "abtest"
    title = "A/B тесты постов (заглушка логики)"
    # В реальном мире: публиковать 2 варианта и сравнивать события engagement/clicks
    pass
