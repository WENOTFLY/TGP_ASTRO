from __future__ import annotations

import json
import os
import urllib.request

from alembic.config import Config
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine


def check_health() -> None:
    url = os.environ["DEPLOY_URL"].rstrip("/") + "/health"
    with urllib.request.urlopen(url) as resp:  # nosec: B310
        if resp.status != 200:
            raise RuntimeError("health check failed")


def check_migrations() -> None:
    db_url = os.environ["DATABASE_URL"]
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", db_url)
    engine = create_engine(db_url, future=True)
    with engine.connect() as conn:
        context = MigrationContext.configure(conn)
        current = context.get_current_revision()
    head = ScriptDirectory.from_config(cfg).get_current_head()
    if current != head:
        raise RuntimeError("database is not migrated")


def check_webhook() -> None:
    token = os.environ["TELEGRAM_TOKEN"]
    expected = os.environ["TELEGRAM_WEBHOOK_URL"]
    api = f"https://api.telegram.org/bot{token}/getWebhookInfo"
    with urllib.request.urlopen(api) as resp:  # nosec: B310
        data = json.load(resp)
    actual = data.get("result", {}).get("url")
    if actual != expected:
        raise RuntimeError("webhook not registered")


def main() -> None:
    check_health()
    check_migrations()
    check_webhook()


if __name__ == "__main__":
    main()
