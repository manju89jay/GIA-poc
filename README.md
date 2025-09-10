# GIA Adapter API

## What this service does
Generates versioned adapters for C structs by calling an LLM. Given two preprocessed headers and a root struct name, it returns four files implementing conversion logic between versions.

## How to run
### Local
```bash
pip install -r requirements.txt
uvicorn app:app --reload
```
Service listens on `http://localhost:8000`.

### Docker
```bash
docker build -t gia-adapter .
docker run -p 8000:8000 gia-adapter
```

## API
POST `/generate`
```json
{
  "root": "ExamplePort",
  "old_header": "<OLD HEADER>",
  "new_header": "<NEW HEADER>",
  "backend": "openai",
  "model": "gpt-5",
  "temperature": 0.0,
  "return_zip": true
}
```
Response contains the generated files and optional base64 ZIP.

Example:
```bash
curl -X POST http://localhost:8000/generate \
  -H 'Content-Type: application/json' \
  -d '{"root":"R","old_header":"H1","new_header":"H2"}'
```

## Backend config
* **OpenAI** (default) — requires `OPENAI_API_KEY` env var.
* **Offline** — set `backend` to `offline` and provide `OFFLINE_LLM_ENDPOINT` env var.

## Prompt contract
System and user prompts are defined in `prompt_text.py`. The LLM must return exactly four files or a single C comment block on error.

## Validation & error codes
* `400` – missing or oversized inputs.
* `409` – no common root.
* `422` – malformed LLM output.
* `424` – backend failure (missing key, timeout).
* `500` – unexpected.

## Running tests
```bash
pytest -q
```
