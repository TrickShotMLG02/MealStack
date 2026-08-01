from __future__ import annotations

import importlib
import re
import pkgutil
from dataclasses import dataclass
from functools import lru_cache


@dataclass(frozen=True)
class RecipeImporterSpec:
    name: str
    url_path: str
    importer_cls: type
    url_placeholder: str
    url_patterns: tuple[str, ...]
    base_domain: str

    def matches_url(self, url: str) -> bool:
        normalized_url = (url or "").strip()
        return any(re.match(pattern, normalized_url, flags=re.IGNORECASE) for pattern in self.url_patterns)


_RECIPE_IMPORTERS: list[RecipeImporterSpec] = []


def register_recipe_importer(
    *,
    url_path: str,
    url_patterns: tuple[str, ...],
    base_domain: str,
    name: str | None = None,
    url_placeholder: str | None = None,
):
    def decorator(importer_cls: type):
        importer_name = name or getattr(importer_cls, "site_name", importer_cls.__name__.removesuffix("Importer"))
        importer_placeholder = url_placeholder or getattr(importer_cls, "url_placeholder", "")
        importer_cls.base_domain = base_domain
        _RECIPE_IMPORTERS.append(
            RecipeImporterSpec(
                name=importer_name,
                url_path=url_path,
                importer_cls=importer_cls,
                url_placeholder=importer_placeholder,
                url_patterns=url_patterns,
                base_domain=base_domain,
            )
        )
        return importer_cls

    return decorator


@lru_cache(maxsize=1)
def _discover_recipe_importers() -> None:
    package = importlib.import_module("apps.recipes.importers.recipes")
    for module_info in pkgutil.iter_modules(package.__path__):
        if module_info.name in {"base", "registry"}:
            continue
        importlib.import_module(f"{package.__name__}.{module_info.name}")


def get_recipe_importers() -> list[RecipeImporterSpec]:
    _discover_recipe_importers()
    return sorted(_RECIPE_IMPORTERS, key=lambda spec: spec.name.casefold())
