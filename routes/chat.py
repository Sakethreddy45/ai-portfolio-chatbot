from fastapi import APIRouter
from pydantic import BaseModel
from services.chat import get_reply

router = APIRouter(prefix="/api")


class ChatIn(BaseModel):
    message: str
    history: list[dict] = []


class ChatOut(BaseModel):
    reply: str


@router.post("/chat", response_model=ChatOut)
async def chat(body: ChatIn):
    reply = get_reply(body.message, body.history)
    return ChatOut(reply=reply)


@router.get("/health")
async def health():
    return {"status": "ok"}