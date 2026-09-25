# Grain

**Grain** rewrites stiff, AI-patterned text so it reads more like a person wrote it — natural rhythm, contractions, fewer classic AIisms. It does **not** claim to make text “undetectable.”

Local multi-pass engine by default. Optional OpenAI-compatible LLM mode if `OPENAI_API_KEY` is set.

## Quick start (local)

```bash
cd text-humanizer
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8000
```

Or:

```bash
./start.sh
```

Open **http://localhost:8000**

- UI: `GET /`
- Health: `GET /health`
- Humanize: `POST /api/humanize`

### API example

```bash
curl -s http://localhost:8000/api/humanize \
  -H 'Content-Type: application/json' \
  -d '{"text":"In today'\''s world, it is important to note that AI plays a crucial role.","mode":"casual","strength":2}'
```

Response:

```json
{ "output": "...", "changes": ["Cleared N AI-pattern phrase(s)", "..."] }
```

| Field | Values |
|-------|--------|
| `mode` | `casual` (default), `professional`, `academic-light` |
| `strength` | `1` light · `2` moderate · `3` aggressive |

## Optional LLM mode

If the server has an API key, Grain prefers the LLM, then falls back to the local engine on failure:

```bash
export OPENAI_API_KEY=sk-...
# optional:
export OPENAI_BASE_URL=https://api.openai.com/v1
export OPENAI_MODEL=gpt-4o-mini
uvicorn main:app --host 0.0.0.0 --port 8000
```

Compatible with any OpenAI-style `/chat/completions` endpoint.

## Deploy (Railway / Render / Fly / VPS)

The app binds `0.0.0.0` and reads `$PORT` — ready for PaaS.

### Generic / VPS

```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port $PORT
```

Or use `./start.sh` / the included **Procfile**.

### Docker

```bash
docker build -t grain .
docker run -p 8000:8000 -e PORT=8000 grain
# with LLM:
docker run -p 8000:8000 -e PORT=8000 -e OPENAI_API_KEY=sk-... grain
```

### Railway

1. New project → deploy from this folder (or connect the repo).
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Or rely on the **Procfile**.

### Render

1. Web Service from this directory.
2. Build: `pip install -r requirements.txt`
3. Start: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Fly.io

```bash
fly launch   # use the Dockerfile
fly deploy
```

Set secrets as needed: `fly secrets set OPENAI_API_KEY=...`

The frontend calls **relative** `/api/humanize` — no hardcoded localhost — so it works behind any public URL.

## Project layout

```
text-humanizer/
  main.py           # FastAPI app
  engine.py         # Local rewrite pipeline (+ optional LLM)
  static/index.html # Single-page UI (inline CSS/JS)
  requirements.txt
  Procfile
  Dockerfile
  start.sh
  README.md
```

## Limitations

- Local engine is rule/heuristic-based: strong on common AIisms and rhythm, not a full paraphrase model.
- Meaning is preserved as best-effort; always skim the output.
- Not a plagiarism or detector-evasion tool — use it to sound clearer and more natural.

## License

Use freely for your own hosting and projects.
