import importlib
import pkgutil
import os


def load_modules():
    """
    Загружает все модули из пакета `modules` и возвращает их как словарь.
    Ключи — это имя файла без расширения.
    """
    loaded = {}

    base_path = os.path.join(os.path.dirname(__file__))
    package = "modules"

    for _, name, is_pkg in pkgutil.iter_modules([base_path]):
        try:
            module = importlib.import_module(f"{package}.{name}")
            loaded[name] = module
            print(f"✅ Модуль загружен: {name}")
        except Exception as e:
            print(f"⚠️ Ошибка при загрузке модуля {name}: {e}")

    return loaded
