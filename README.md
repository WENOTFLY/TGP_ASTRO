# TGP_ASTRO

## Launch
1. Copy `.env.sample` to `.env` and fill secrets.
2. Install dependencies: `pip install -r requirements.txt`.
3. Run services: `docker-compose up --build`.
4. The Telegram webhook is exposed at `/tg/webhook`.

## Deploy
- Build the Docker image and push to your registry.
- Configure environment variables and run `docker-compose up -d` on the server.
- Use `make migrate` for database migrations.

## Assets structure
```
assets/
  tarot/<deck_id>/cards/*.png
  runes/<set_id>/runes/*.png
  dreams/lexicon.json
```
All assets are validated on startup and indexed in the database.

## Runbook
- **Webhook errors**: check logs, verify Telegram token, redeploy if needed.
- **Asset validation failure**: run `make ingest` and inspect `/admin/decks` for details.
- **High latency**: check worker queue and Redis status, scale workers if required.

## FAQ and Admin panel
See [docs/FAQ.md](docs/FAQ.md) for adding new decks, runes or lexicons and for admin panel usage.
The admin panel exposes `/admin/metrics`, `/admin/decks` and optional `/admin/broadcast` endpoints.
