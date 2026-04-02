import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from config import PERSONA_NAME, PERSONA_TITLE
from db.store import init_db
from db.vectors import rebuild_index
from routes.chat import router as chat_router
from routes.admin import router as admin_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(name)-24s  %(levelname)-7s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    rebuild_index()
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
    return templates.TemplateResponse("index.html", {
        "request": request,
        "name": PERSONA_NAME,
        "title": PERSONA_TITLE,
    })