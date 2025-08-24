from __future__ import annotations

from . import available, discover


def main() -> None:
    """Print identifiers of all discovered plugins."""

    discover()
    for plugin_id in available():
        print(plugin_id)


if __name__ == "__main__":  # pragma: no cover - CLI utility
    main()
