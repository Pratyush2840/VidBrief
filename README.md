# VidBrief

Paste a YouTube URL and get an AI-generated summary, structured study notes, a
multiple-choice quiz, and flashcards — powered by Gemini.

## Tech stack

- **Backend:** FastAPI (Python), `youtube-transcript-api`, Gemini (`google-genai` SDK)
- **Frontend:** React + Vite, plain CSS
- **Rate limiting:** slowapi
- **Caching:** in-memory TTL cache keyed by video ID (swappable for Redis later)

## Project structure

```
backend/
  main.py              FastAPI app, CORS, rate limiter wiring
  config.py             Settings (env vars)
  limiter.py            slowapi Limiter instance
  routers/summarize.py  POST /api/summarize
  services/youtube.py   URL parsing + transcript fetching
  services/gemini.py    Gemini prompt pipeline, map-reduce chunking, retry/validation
  services/cache.py     In-memory result cache behind a swappable interface
  models/schemas.py     Pydantic request/response models
  Dockerfile
frontend/
  src/App.jsx            App shell: URL form, loading/error states
  src/api.js              Backend API client
  src/components/         UrlForm, ResultsTabs, Summary/Notes/Quiz/FlashcardsTab
```

## Backend setup

```bash
cd backend
python -m venv venv
source venv/Scripts/activate   # Windows Git Bash; use venv\Scripts\activate on cmd/PowerShell
pip install -r requirements.txt
cp .env.example .env
```

Edit `backend/.env` and set `GEMINI_API_KEY` (get one at
https://aistudio.google.com/apikey).

Run the dev server:

```bash
uvicorn main:app --reload --port 8000
```

Test it:

```bash
curl -X POST http://localhost:8000/api/summarize \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Environment variables (backend/.env)

| Variable | Required | Default | Description |
|---|---|---|---|
| `GEMINI_API_KEY` | yes | — | Gemini API key |
| `GEMINI_MODEL` | no | `gemini-flash-latest` | Gemini model to use |
| `CORS_ORIGINS` | no | `http://localhost:5173` | Comma-separated allowed frontend origins |
| `RATE_LIMIT` | no | `5/minute` | Rate limit for `POST /api/summarize`, per IP |
| `CACHE_TTL_SECONDS` | no | `86400` | How long cached results stay valid |
| `CACHE_MAX_SIZE` | no | `500` | Max cached results held in memory |

> **Note on `GEMINI_MODEL`:** the original spec targeted `gemini-2.5-flash`,
> but as of mid-2026 that model is no longer available to new API
> keys/projects. `gemini-flash-latest` is Google's auto-updating alias for
> the current recommended fast/cheap model. Pin a specific version instead
> (e.g. `gemini-3.5-flash`) if you want reproducible behavior over time.

## Frontend setup

```bash
cd frontend
npm install
cp .env.example .env
```

Edit `frontend/.env` and point `VITE_API_BASE_URL` at your backend (default
assumes the backend is running locally on port 8000).

Run the dev server:

```bash
npm run dev
```

Open the printed local URL (typically http://localhost:5173).

## API

### `POST /api/summarize`

Request:

```json
{ "youtube_url": "https://www.youtube.com/watch?v=..." }
```

Accepts `watch?v=`, `youtu.be/`, `/shorts/`, `/embed/`, and `/live/` URL forms.

Response `200`:

```json
{
  "summary": "string",
  "notes": [{ "heading": "string", "points": ["string"] }],
  "quiz": [{ "question": "string", "options": ["string"], "correct_index": 0 }],
  "flashcards": [{ "front": "string", "back": "string" }],
  "video_id": "string",
  "cached": false
}
```

Error responses:

| Status | Meaning |
|---|---|
| `400` | URL could not be parsed as a valid YouTube URL |
| `422` | Video has no available transcript/captions |
| `429` | Rate limit exceeded |
| `502` | Transcript fetch or Gemini generation failed |

## Deployment

### Backend → Render/Railway (Docker)

The backend ships with a `Dockerfile` that reads the `PORT` env var (both
platforms set this automatically) and installs everything it needs — no
extra build config required.

1. Push this repo to GitHub.
2. Create a new Web Service on Render (or a service on Railway), point it at
   `backend/` as the root/build directory, and let it build from the
   Dockerfile.
3. Set the environment variables from the table above (`GEMINI_API_KEY` is
   the only required one) in the platform's dashboard.
4. Once deployed, set `CORS_ORIGINS` to your deployed frontend URL.

### Frontend → Vercel

1. Import the repo into Vercel, set the project root to `frontend/`.
2. Framework preset: Vite. Build command `npm run build`, output dir `dist`.
3. Set `VITE_API_BASE_URL` to your deployed backend URL in Vercel's
   environment variable settings.

## Notes on design decisions

- **Caching:** results are cached in-process, keyed by video ID, via a small
  `ResultCache` interface (`services/cache.py`). Swapping in Redis later means
  writing one new class against that interface — no changes to the API layer.
- **Long transcripts:** transcripts under ~60k characters go straight to
  Gemini in one call. Longer ones are split into chunks, each map-summarized
  by Gemini, then the combined chunk summaries are fed through the same
  structured-output prompt (reduce step) — no blind truncation.
- **Output validation:** Gemini is asked for strict JSON; the response is
  parsed and validated against a Pydantic model, with one retry (adding an
  explicit "invalid JSON" correction to the prompt) if parsing/validation
  fails on the first attempt.
