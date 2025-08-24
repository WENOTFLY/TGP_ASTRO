# FAQ

## Loading new decks
1. Create a directory under `assets/tarot/<deck_id>` containing card images and `deck.json`.
2. Run `make ingest` or restart the app to validate and index the deck.
3. Use the admin panel `/admin/decks` to verify the deck appears and passes validation.

## Loading rune sets
1. Add a folder `assets/runes/<set_id>` with rune images and `set.json`.
2. Trigger asset ingestion so the new set is validated and stored in the index.
3. Confirm availability through `/admin/decks`.

## Loading lexicons
1. For dreams or other NLP modules place the JSON lexicon under `assets/<module>/lexicon.json`.
2. Restart the service so the parser reloads the lexicon.

## Admin panel
- Metrics: visit `/admin/metrics` to inspect usage statistics.
- Decks: `/admin/decks` lists all indexed assets and validation status.
- Broadcast: `/admin/broadcast` (optional) sends messages to user segments.
