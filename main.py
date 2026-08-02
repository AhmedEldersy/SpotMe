import importlib.util
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

BASE_DIR = Path(__file__).resolve().parent


def _load_module(unique_name: str, file_path: Path):
    """Import a .py file as a module under a unique name (several services
    each have their own main.py / app.py; loading by explicit unique names
    avoids sys.modules collisions between them)."""
    spec = importlib.util.spec_from_file_location(unique_name, str(file_path))
    module = importlib.util.module_from_spec(spec)
    sys.modules[unique_name] = module
    spec.loader.exec_module(module)
    return module


def _ensure_on_sys_path(directory: Path):
    directory_str = str(directory)
    if directory_str in sys.path:
        sys.path.remove(directory_str)
    sys.path.insert(0, directory_str)



chatbot_module = _load_module("spotme_svc_chatbot", BASE_DIR / "chatbot" / "app.py")


_ensure_on_sys_path(BASE_DIR / "comperssion")
compression_module = _load_module("spotme_svc_compression", BASE_DIR / "comperssion" / "main.py")

# cv: NOTEBOOK_PATH is resolved via __file__ inside the module itself, and
# the notebook's own relative paths are handled internally (temporary
# chdir). No sys.path changes needed.
cv_module = _load_module("spotme_svc_cv", BASE_DIR / "cv" / "main.py")

# scout: only stdlib/pip imports.
scout_module = _load_module("spotme_svc_scout", BASE_DIR / "scout" / "main.py")

# vision: `from computer_vision import (...)` and `import knowledge_base`
# are sibling modules inside vision/, so vision/ must be importable.
_ensure_on_sys_path(BASE_DIR / "vision")
vision_module = _load_module("spotme_svc_vision", BASE_DIR / "vision" / "main.py")

# team_builder: `import team_builder as tb` must resolve to
# team_builder/team_builder.py (the sibling file), not to the
# team_builder/ folder itself as an implicit namespace package. Inserting
# the team_builder/ directory at the front of sys.path guarantees the file
# is found first.
_ensure_on_sys_path(BASE_DIR / "team_builder")
team_builder_module = _load_module("spotme_svc_team_builder", BASE_DIR / "team_builder" / "app.py")

# recomendtion: every internal file uses `from app.xxx import ...`, where
# `app` is the recomendtion/app package. Adding recomendtion/ to sys.path
# makes that package importable as top-level `app`.
_ensure_on_sys_path(BASE_DIR / "recomendtion")
recommendation_module = _load_module("spotme_svc_recommendation", BASE_DIR / "recomendtion" / "app" / "main.py")


# ---------------------------------------------------------------------------
# Assemble the single root application.
# ---------------------------------------------------------------------------

app = FastAPI(
    title="SpotMe Unified API",
    description=(
        "Single merged backend for SpotMe: chatbot, compression/comparison, "
        "CV builder, recommendation, scout, team builder and vision services."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chatbot_module.router, prefix="/chatbot", tags=["chatbot"])
app.include_router(compression_module.router, prefix="/compression", tags=["compression"])
app.include_router(cv_module.router, prefix="/cv", tags=["cv"])
app.include_router(recommendation_module.router, prefix="/recommendation", tags=["recommendation"])
app.include_router(scout_module.router, prefix="/scout", tags=["scout"])
app.include_router(team_builder_module.router, prefix="/team-builder", tags=["team-builder"])
app.include_router(vision_module.router, prefix="/vision", tags=["vision"])



@app.exception_handler(Exception)
async def _scoped_unhandled_exception_handler(request, exc):
    if request.url.path.startswith("/team-builder"):
        return await team_builder_module.unhandled_exception_handler(request, exc)

    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})


@app.get("/", tags=["system"])
def root():
    return {
        "status": "running",
        "message": "SpotMe unified backend is running",
        "services": {
            "chatbot": "/chatbot",
            "compression": "/compression",
            "cv": "/cv",
            "recommendation": "/recommendation",
            "scout": "/scout",
            "team_builder": "/team-builder",
            "vision": "/vision",
        },
        "docs": "/docs",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
