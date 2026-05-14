# app/

Main application code for the gateway service.

See the full documentation in [`../../README.md`](../../README.md).

## Subdirectories

- `api/` — Route handlers. All endpoints and proxy forwarding logic.
- `core/` — Configuration, JWT validation, and request middleware.
- `main.py` — FastAPI app bootstrap. Start here.
