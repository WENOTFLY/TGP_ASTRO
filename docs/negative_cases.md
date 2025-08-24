# Negative Cases

## Asset errors
- Missing `deck.json`/`set.json` or malformed manifests.
- Image files absent or with wrong aspect ratio trigger `AssetValidationError`.
- Failing ingestion leaves the deck unavailable until the issues are fixed and assets reloaded.

## LLM failures
- `Verifier` detects mismatched facts in generated text and forces regeneration.
- After repeated failures, the flow falls back without consuming user quota.
- Logs contain details for troubleshooting model outputs.

## Payment failures
- Stars invoice rejection or network issues raise `QuotaError` and halt processing.
- Quota remains unchanged when payment does not succeed.
- Users should retry or purchase a new entitlement to continue.
