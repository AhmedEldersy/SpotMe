# AI Sports Scout — CV Builder API

FastAPI wrapper around `CV_Builder.ipynb`: an AI scout that interviews an
athlete (football / basketball / volleyball / handball) in Arabic or English,
then generates a structured player profile, a short professional summary, and
a downloadable PDF CV.

## 1. Run it locally

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up your environment file
cp .env.example .env
# then edit .env and paste your real GROQ_API_KEY

# 4. Run the API
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The first startup will take a little while: it builds the RAG vector store
from `knowledge.txt` and downloads the embedding model
(`BAAI/bge-large-en-v1.5`) if it isn't cached yet.

Interactive API docs (Swagger UI) will be available at
`http://localhost:8000/docs` once it's running.

### Arabic text in the generated PDF

The PDF renderer needs a real Arabic-capable TTF font to draw Arabic
characters correctly (shaping + right-to-left). Create a `fonts/` folder next
to `main.py` and drop in a font such as **Amiri** or **Noto Naskh Arabic**,
e.g.:

```
fonts/
  Amiri-Regular.ttf
  Amiri-Bold.ttf
```

If no such font is found, the PDF still generates successfully, but Arabic
characters are stripped out of it (English/numeric content is unaffected).

## 2. Endpoints

### `POST /start`
Starts a new interview session.

**Request body:** none

**Response:**
```json
{
  "session_id": "3f9a2e10-8b2b-4b1a-9b3e-1a2b3c4d5e6f",
  "message": "Hi! Great to meet you. Which sport do you play — football, basketball, volleyball, or handball?",
  "is_done": false
}
```

### `POST /chat`
Sends the athlete's next answer and gets the scout's next question.

**Request body:**
```json
{
  "session_id": "3f9a2e10-8b2b-4b1a-9b3e-1a2b3c4d5e6f",
  "message": "I play football, I'm a striker"
}
```

**Response:**
```json
{
  "message": "Nice! What's your full name?",
  "is_done": false
}
```

Keep calling `/chat` until `is_done` is `true` — that means the interview
collected everything it needs and the CV is ready to generate.

### `POST /generate`
Extracts the structured player profile from the finished interview and
builds the PDF CV.

**Request body:**
```json
{
  "session_id": "3f9a2e10-8b2b-4b1a-9b3e-1a2b3c4d5e6f"
}
```

**Response:**
```json
{
  "player": {
    "full_name": "Ahmed Samir",
    "sport": "football",
    "position": "Striker",
    "age": "21",
    "...": "..."
  },
  "summary": "Ahmed is a pacey, clinical striker with a strong finishing instinct...",
  "pdf_url": "/download/3f9a2e10-8b2b-4b1a-9b3e-1a2b3c4d5e6f"
}
```

Use `pdf_url` directly as the download link (see below) — don't try to read
a local file path, since that's a server-side path the frontend has no
access to.

### `GET /download/{session_id}`
Returns the generated PDF file for that session (`application/pdf`).

### `GET /health`
Quick health/readiness check.

**Response:**
```json
{
  "status": "ok",
  "checks": {
    "vector_db_loaded": true,
    "embedding_model_loaded": true,
    "groq_client_ready": true
  }
}
```

## 3. Known limitations (please read before deploying)

- **Sessions are in-memory.** `SESSIONS` is a plain Python dict living inside
  one process. This works fine for local dev and single-instance deployments,
  but it will **not** work correctly if you run more than one worker/instance
  (e.g. `uvicorn --workers 4`, or multiple containers behind a load
  balancer) — a session started on worker A won't be visible from worker B.
  If you need multi-worker/multi-instance scaling, move session state to
  Redis or a database before going further.
- **CORS is fully open (`allow_origins=["*"]`)** for now, to make local
  frontend development easy. Before shipping to production, lock this down
  to the real frontend domain(s) in `main.py`.
- **Rate limiting is a simple in-memory sliding window** (20 requests / 60s
  per session id or IP). It resets if the process restarts and doesn't share
  state across multiple workers/instances — same caveat as sessions above.

## 4. Decisions / info still needed from you

- A real `GROQ_API_KEY` for any non-local environment (staging/production).
- The frontend team's actual domain(s), to replace `allow_origins=["*"]` in
  the CORS config once you know them.
- Arabic font files (Amiri or Noto Naskh Arabic) if you want proper Arabic
  rendering in the generated PDF — not included in this repo for licensing/
  size reasons.
