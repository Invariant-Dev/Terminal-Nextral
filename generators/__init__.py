# generators package - modular payload generation engine
# each language gets its own file, this loader finds them all

import importlib
import pkgutil
from generators.base import BaseGenerator

# registry of all available generators keyed by language id
_GENERATORS: dict[str, type[BaseGenerator]] = {}


def _discover():
    """walk this package and register every generator subclass"""
    for info in pkgutil.iter_modules(__path__):
        mod = importlib.import_module(f"generators.{info.name}")
        for attr in dir(mod):
            cls = getattr(mod, attr)
            if (
                isinstance(cls, type)
                and issubclass(cls, BaseGenerator)
                and cls is not BaseGenerator
                and hasattr(cls, "LANG_ID")
            ):
                _GENERATORS[cls.LANG_ID] = cls


_discover()


def get_generator(lang_id: str) -> BaseGenerator | None:
    """return an instance of the generator for the given language id"""
    cls = _GENERATORS.get(lang_id)
    return cls() if cls else None


def available_languages() -> list[tuple[str, str]]:
    """return list of (display_name, lang_id) for the ui select widget"""
    return [(cls.LANG_NAME, lid) for lid, cls in _GENERATORS.items()]
