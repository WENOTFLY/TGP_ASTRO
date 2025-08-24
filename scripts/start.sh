#!/usr/bin/env bash
set -e
python scripts/prestart.py
exec uvicorn app.api.main:app --host 0.0.0.0 --port 8000
