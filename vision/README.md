# AI Performance Development System — integrated build

## What changed

Previously `main.py` (the AI/report server) and `computer_vision.py` (the video
analysis code) were two disconnected files — `computer_vision.py` even ran its
own separate FastAPI app (`cv_app`) that nothing called. Uploading a video did
not trigger any analysis.

Now there is **one server**: `main.py`. It:

1. Imports `computer_vision.py` directly as a Python module (no second server,
   no extra network hop) to turn an uploaded video into real metrics.
2. Imports the new `knowledge_base.py` to ground the LLM's benchmarking and
   exercise selection in a fixed, explainable reference dataset instead of
   letting the model invent numbers and drills.
3. Sends `{player_profile, video_analysis, previous_video_analysis, goals,
   historical_data, knowledge_base}` to the Groq model and returns its
   structured JSON report.

`computer_vision.py`'s own `cv_app` is still in the file (harmless, unused)
purely so you can still run `uvicorn computer_vision:cv_app` standalone if you
ever want to debug the CV pipeline in isolation — but it is never imported or
mounted by `main.py`, so in normal use only one process runs.

## Files

- `main.py` — the only server you run. FastAPI app with all endpoints.
- `computer_vision.py` — video → metrics extraction (OpenCV + MediaPipe), imported by `main.py`.
- `knowledge_base.py` — benchmark bands, exercise library, coaching principles (pure data + helper functions, no LLM calls, no network).
- `requirements.txt`, `.env.example`

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# put your real GROQ_API_KEY in .env
uvicorn main:app --reload --port 8000
```

## Endpoints

| Endpoint | Input | Use case |
|---|---|---|
| `GET /health` | – | sanity check, lists supported sports, KB version, upload limits |
| `POST /analyze` | JSON (metrics already computed elsewhere) | you already ran CV analysis yourself |
| `POST /adaptive-analyze` | JSON, requires `previous_video_analysis` | same, but comparing to a prior session |
| `POST /upload-and-analyze` | multipart: video file + form fields | **the real "upload a video and get analyzed" flow** |
| `POST /upload-and-adaptive-analyze` | multipart: new video + (previous video OR previous JSON) | follow-up session, model shows progress/decline |

### `POST /upload-and-analyze` — this is the one that answers "لما برفع الفيديو بيحصل التحليل"

`multipart/form-data` fields:

- `video` (file, required) — the athlete's video (`.mp4`, `.mov`, `.avi`, `.mkv`, `.webm`, `.m4v`)
- `player_profile` (string, required) — JSON matching the `PlayerProfile` model, e.g.
  `{"name":"Ahmed","age":17,"gender":"male","sport":"Football","position":"Winger","competition_level":"Academy","height_cm":175}`
- `goals` (string, required) — JSON, e.g. `{"goals":["improve acceleration","reduce fatigue late in matches"]}`
- `historical_data` (string, optional) — JSON matching `HistoricalData`
- `position`, `fps`, `pixels_per_meter`, `player_height_cm`, `ball_color`, `max_frames` (optional) — CV calibration overrides. Without `pixels_per_meter` or `player_height_cm`, distance/speed/jump metrics come back as `null` (the system is honest about missing calibration rather than guessing).

Example:

```bash
curl -X POST http://localhost:8000/upload-and-analyze \
  -F "video=@match_clip.mp4" \
  -F 'player_profile={"name":"Ahmed","age":17,"gender":"male","sport":"Football","position":"Winger","competition_level":"Academy","height_cm":175}' \
  -F 'goals={"goals":["improve acceleration","reduce late-match fatigue"]}' \
  -F "player_height_cm=175" \
  -F "ball_color=orange"
```

Response shape:

```json
{
  "video_analysis_raw": { "metrics": {...}, "confidence_score": 0.7, "video_quality_notes": "...", "capture_date": "..." },
  "ai_report": { "player_profile": {...}, "performance_summary": {...}, "...": "the 13 report sections" }
}
```

### `POST /upload-and-adaptive-analyze`

Same as above, plus either:
- `previous_video` (file) — a prior video, re-analyzed here for comparison, **or**
- `previous_video_analysis` (string) — a JSON `VideoAnalysisResults` you already have saved from a prior call.

## How the knowledge base grounds the model

For every request, `main.py`:
1. Resolves the closest benchmark tier for the athlete's `sport` / age group / `competition_level` from `knowledge_base.BENCHMARKS` (and tells the model if it had to approximate).
2. Classifies each raw metric against those bands to find which ones are weak.
3. Shortlists matching drills from `knowledge_base.EXERCISE_LIBRARY` for those weak skills.
4. Packs all of that — plus general coaching principles and a disclaimer — into a `knowledge_base` object in the payload sent to the model, and the system prompt requires the model to use it instead of inventing its own numbers/drills.

To extend coverage (more sports/positions/age tiers, more exercises), edit
`knowledge_base.py` — `BENCHMARKS` and `EXERCISE_LIBRARY` are plain Python
dicts/lists, no schema migration needed.
