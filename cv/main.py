import os
import time
import uuid
import contextlib
from types import ModuleType

import nbformat
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

_CV_DIR = os.path.dirname(os.path.abspath(__file__))
NOTEBOOK_PATH = os.path.join(_CV_DIR, "CV_Builder.ipynb")


@contextlib.contextmanager
def _cwd(path):
    """Temporarily switch the process CWD. The CV_Builder notebook cells use
    relative paths (knowledge.txt, chroma_db, output) that must resolve
    inside cv/ regardless of where the merged app's uvicorn process was
    launched from."""
    previous = os.getcwd()
    os.chdir(path)
    try:
        yield
    finally:
        os.chdir(previous)

SKIP_MARKERS = [
    "input(",
    "first_message =",
    "while True:",
    "player = get_player_data(conversation_history",
    "summary = generate_cv_summary(player)",
]


def load_notebook_as_module(path, module_name="cv_builder_nb"):
    nb = nbformat.read(path, as_version=4)
    mod = ModuleType(module_name)
    mod.__file__ = path
    sources = []
    for cell in nb.cells:
        if cell.cell_type != "code":
            continue
        source = cell.source
        if any(marker in source for marker in SKIP_MARKERS):
            continue
        sources.append(source)
    full_source = "\n\n".join(sources)
    exec(compile(full_source, path, "exec"), mod.__dict__)
    return mod


with _cwd(_CV_DIR):
    nb = load_notebook_as_module(NOTEBOOK_PATH)

if not os.path.isabs(getattr(nb, "OUTPUT_FOLDER", "output")):
    nb.OUTPUT_FOLDER = os.path.join(_CV_DIR, nb.OUTPUT_FOLDER)
    os.makedirs(nb.OUTPUT_FOLDER, exist_ok=True)

SESSIONS = {}


def new_session_state():
    return {"history": [], "sport": {"value": None}}


RATE_LIMIT_WINDOW_SECONDS = 60
RATE_LIMIT_MAX_REQUESTS = 20
_RATE_LIMIT_BUCKETS: dict[str, list[float]] = {}


def check_rate_limit(key: str):
    now = time.time()
    bucket = _RATE_LIMIT_BUCKETS.setdefault(key, [])
    while bucket and now - bucket[0] > RATE_LIMIT_WINDOW_SECONDS:
        bucket.pop(0)
    if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail=(
                f"Rate limit exceeded: max {RATE_LIMIT_MAX_REQUESTS} requests "
                f"per {RATE_LIMIT_WINDOW_SECONDS}s for this session/IP. "
                "Please slow down and try again shortly."
            ),
        )
    bucket.append(now)


def call_groq_safely(fn, *args, **kwargs):
    """Run a notebook function that calls the Groq API and translate any
    failure (auth error, network error, timeout, rate limit on Groq's side,
    etc.) into a clean 503 instead of a raw, unhandled 500."""
    try:
        return fn(*args, **kwargs)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"AI service (Groq) is currently unavailable or timed out: {e}",
        )


router = APIRouter()


class StartResponse(BaseModel):
    session_id: str
    message: str
    is_done: bool


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    message: str
    is_done: bool


class GenerateRequest(BaseModel):
    session_id: str


class GenerateResponse(BaseModel):
    player: dict
    summary: str
    pdf_url: str


@router.get("/health")
def health_check():
    checks = {
        "vector_db_loaded": getattr(nb, "vector_db", None) is not None,
        "embedding_model_loaded": getattr(nb, "embedding_model", None) is not None,
        "groq_client_ready": getattr(nb, "client", None) is not None,
    }
    ok = all(checks.values())
    return {"status": "ok" if ok else "degraded", "checks": checks}


@router.post("/start", response_model=StartResponse)
def start_session(request: Request):
    client_key = request.client.host if request.client else "unknown"
    check_rate_limit(client_key)

    session_id = str(uuid.uuid4())
    session = new_session_state()
    SESSIONS[session_id] = session

    first_message = """
Start the interview.
Ask the first question — determine which of the 4 supported sports the athlete plays.
Do not generate JSON.
"""
    message, is_done = call_groq_safely(
        nb.chat, first_message, session["history"], session["sport"]
    )
    return StartResponse(session_id=session_id, message=message, is_done=is_done)


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(req: ChatRequest):
    check_rate_limit(req.session_id)

    session = SESSIONS.get(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    message, is_done = call_groq_safely(
        nb.chat, req.message, session["history"], session["sport"]
    )
    return ChatResponse(message=message, is_done=is_done)


@router.post("/generate", response_model=GenerateResponse)
def generate_endpoint(req: GenerateRequest):
    check_rate_limit(req.session_id)

    session = SESSIONS.get(req.session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    player = call_groq_safely(nb.get_player_data, session["history"], session["sport"])
    if not player:
        raise HTTPException(status_code=422, detail="failed to extract player data")

    json_path = os.path.join(nb.OUTPUT_FOLDER, f"{req.session_id}.json")
    nb.save_json(player, json_path)

    summary = call_groq_safely(nb.generate_cv_summary, player)

    pdf_path = os.path.join(nb.OUTPUT_FOLDER, f"{req.session_id}.pdf")
    nb.create_pdf(player, summary, pdf_path)

    return GenerateResponse(player=player, summary=summary, pdf_url=f"/download/{req.session_id}")


@router.get("/download/{session_id}")
def download_pdf(session_id: str):
    pdf_path = os.path.join(nb.OUTPUT_FOLDER, f"{session_id}.pdf")
    if not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="pdf not found")
    return FileResponse(pdf_path, media_type="application/pdf", filename=f"{session_id}.pdf")
