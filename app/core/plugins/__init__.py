from __future__ import annotations

import logging
import pkgutil
from dataclasses import dataclass
from importlib import import_module
from typing import Any, Callable, Dict, Sequence

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class Plugin:
    """Contract for expert plugins."""

    plugin_id: str
    form_steps: Callable[[str], list[dict[str, Any]]]
    prepare: Callable[[dict[str, Any]], dict[str, Any]]
    compose: Callable[[dict[str, Any]], dict[str, Any]]
    write: Callable[[dict[str, Any]], dict[str, Any]]
    verify: Callable[[dict[str, Any]], bool]
    cost: int
    cta: Callable[[str], list[str]]
    products_supported: Sequence[str]


Registry = Dict[str, Plugin]
_registry: Registry = {}


def register(plugin: Plugin) -> None:
    """Register a plugin instance."""

    if plugin.plugin_id in _registry:
        raise ValueError(f"Plugin '{plugin.plugin_id}' already registered")
    _registry[plugin.plugin_id] = plugin


def discover() -> Registry:
    """Discover and load plugins from :mod:`app.experts`."""

    if _registry:
        return _registry

    package = import_module("app.experts")
    for _, name, _ in pkgutil.iter_modules(package.__path__):
        module_name = f"{package.__name__}.{name}"
        try:
            module = import_module(module_name)
        except Exception as exc:  # pragma: no cover - defensive
            log.warning("Failed to load plugin '%s': %s", module_name, exc)
            continue
        plugin = getattr(module, "plugin", None)
        if isinstance(plugin, Plugin):
            try:
                register(plugin)
            except ValueError:
                log.warning("Duplicate plugin_id '%s'", plugin.plugin_id)
        else:
            log.debug("Module '%s' does not expose a plugin", module_name)
    return _registry


def available() -> list[str]:
    """Return identifiers of all registered plugins."""

    return sorted(discover().keys())


__all__ = ["Plugin", "register", "discover", "available"]
