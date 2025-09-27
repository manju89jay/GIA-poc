# GIA Adapter API

## What this service does
Generates versioned adapters for C structs by calling an LLM. Given two preprocessed headers and a root struct name, it returns four files implementing conversion logic between versions.

## How to run

### Local workflow
1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```
2. **Provide LLM credentials**
   The default backend talks to OpenAI. Export the API key in the shell that
   starts Uvicorn so the process can discover it:
   ```bash
   # macOS/Linux
   export OPENAI_API_KEY="sk-your-secret"

   # Windows PowerShell (open a new terminal afterwards)
   setx OPENAI_API_KEY "sk-your-secret"
   ```
   The repository never stores the key; rotate it immediately if you suspect
   exposure.
3. **Start the FastAPI server**
   ```bash
   uvicorn app:app --reload
   ```
   The API listens on `http://localhost:8000`.
4. **Call the generator**
   With the server running you can execute the cross-platform helper script.
   The defaults use the bundled fixtures so the first run works out of the box:
   ```bash
   python scripts/run_generator.py
   ```
   Use `python scripts/run_generator.py --help` to inspect additional
   parameters (custom headers, backend overrides, dumping JSON, etc.).

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

### Local invocation helper
The repository ships with `scripts/run_generator.py`, a small CLI that
assembles the payload and posts it to the running FastAPI instance.  Because
our test-suite imports the same helper the automated checks exercise the exact
request that the script emits.

Quick start (uses the fixture headers and requests a ZIP bundle):
```bash
python scripts/run_generator.py
```

To target different headers or a different backend:
```bash
python scripts/run_generator.py \
  --root MyStruct \
  --old-header path/to/old.h \
  --new-header path/to/new.h \
  --backend offline
```

If you prefer manual requests you can still use `curl`:
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
