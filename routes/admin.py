from fastapi import APIRouter, Request, Form, File, UploadFile, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from config import ADMIN_PASSWORD, PERSONA_NAME
from db import store
from db.vectors import index_entry, remove_entry, remove_doc_chunks, rebuild_index
from services.ingest import process_file

router = APIRouter(prefix="/admin")
templates = Jinja2Templates(directory="templates")


def _check_auth(request: Request):
    if request.cookies.get("admin_token") != ADMIN_PASSWORD:
        raise HTTPException(status_code=303, headers={"Location": "/admin/login"})


# ── login ────────────────────────────────────────────────────

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login(password: str = Form(...)):
    if password != ADMIN_PASSWORD:
        return RedirectResponse("/admin/login?error=1", status_code=303)
    resp = RedirectResponse("/admin", status_code=303)
    resp.set_cookie("admin_token", ADMIN_PASSWORD, httponly=True, max_age=86400)
    return resp


# ── dashboard ────────────────────────────────────────────────

@router.get("", response_class=HTMLResponse)
async def dashboard(request: Request):
    _check_auth(request)
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "name": PERSONA_NAME,
        "entries": store.get_all_entries(),
        "documents": store.get_documents(),
        "leads": store.get_leads(),
        "unanswered": store.get_unanswered(),
        "chats": store.get_chat_logs(limit=30),
    })


# ── manual Q&A entry ────────────────────────────────────────

@router.post("/entry/add")
async def add(request: Request, category: str = Form(...), question: str = Form(...), answer: str = Form(...)):
    _check_auth(request)
    eid = store.add_entry(category, question, answer)
    index_entry(eid, question, answer, category)
    return RedirectResponse("/admin", status_code=303)


@router.post("/entry/{entry_id}/delete")
async def delete_entry(request: Request, entry_id: int):
    _check_auth(request)
    store.delete_entry(entry_id)
    remove_entry(entry_id)
    return RedirectResponse("/admin", status_code=303)


# ── file upload ──────────────────────────────────────────────

@router.post("/upload")
async def upload(request: Request, file: UploadFile = File(...)):
    _check_auth(request)
    content = await file.read()
    try:
        doc_id, chunks = process_file(file.filename, content)
    except ValueError as e:
        return RedirectResponse(f"/admin?error={e}", status_code=303)
    return RedirectResponse(f"/admin?uploaded={file.filename}&chunks={chunks}", status_code=303)


@router.post("/doc/{doc_id}/delete")
async def delete_doc(request: Request, doc_id: int):
    _check_auth(request)
    store.delete_document(doc_id)
    remove_doc_chunks(doc_id)
    return RedirectResponse("/admin", status_code=303)


# ── rebuild ──────────────────────────────────────────────────

@router.post("/rebuild-index")
async def do_rebuild(request: Request):
    _check_auth(request)
    count = rebuild_index()
    return RedirectResponse(f"/admin?rebuilt={count}", status_code=303)