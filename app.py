import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from config import PERSONA_NAME, PERSONA_TITLE
from db.store import init_db
from db.vectors import rebuild_index, _get_collection
from services.ingest import process_file
from routes.chat import router as chat_router
from routes.admin import router as admin_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-24s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

KNOWLEDGE_DIR = "knowledge"


def _auto_load_knowledge():
    """if chroma is empty and knowledge/ folder has files, ingest them automatically."""
    col = _get_collection()
    if col.count() > 0:
        log.info("chroma already has %d docs, skipping auto-load", col.count())
        return

    if not os.path.exists(KNOWLEDGE_DIR):
        log.info("no knowledge/ folder found, skipping auto-load")
        return

    for fname in os.listdir(KNOWLEDGE_DIR):
        fpath = os.path.join(KNOWLEDGE_DIR, fname)
        if not os.path.isfile(fpath):
            continue

        try:
            with open(fpath, "rb") as f:
                content = f.read()
            doc_id, chunks = process_file(fname, content)
            log.info("auto-loaded %s — %d chunks", fname, chunks)
        except Exception as e:
            log.error("failed to auto-load %s: %s", fname, e)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    rebuild_index()
    _auto_load_knowledge()
    log.info("app ready — serving %s's portfolio", PERSONA_NAME)
    yield
    log.info("shutting down")


app = FastAPI(title=f"{PERSONA_NAME} Portfolio Chat", lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

app.include_router(chat_router)
app.include_router(admin_router)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"name": PERSONA_NAME, "title": PERSONA_TITLE},
    )