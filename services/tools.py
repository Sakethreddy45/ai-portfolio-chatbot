import json
import logging
from db.store import save_lead, log_unanswered
from services import push

log = logging.getLogger(__name__)


# ── tool implementations ─────────────────────────────────────

def record_user_details(email, name="", notes=""):
    save_lead(email, name, notes)
    push(f"New lead: {name or 'anon'} — {email}")
    log.info("saved lead: %s", email)
    return {"status": "ok"}


def record_unknown_question(question):
    log_unanswered(question)
    push(f"Unanswered: {question}")
    log.info("logged unanswered: %s", question)
    return {"status": "ok"}


# ── registry maps name → function ────────────────────────────

TOOLS = {
    "record_user_details": record_user_details,
    "record_unknown_question": record_unknown_question,
}

# ── schemas sent to the openai api ───────────────────────────

TOOL_DEFS = [
    {
        "type": "function",
        "function": {
            "name": "record_user_details",
            "description": "Record a visitor's email when they want to get in touch.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string", "description": "Visitor's email"},
                    "name": {"type": "string", "description": "Visitor's name if given"},
                    "notes": {"type": "string", "description": "Conversation context"},
                },
                "required": ["email"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "record_unknown_question",
            "description": "Log any question you couldn't answer from the provided context.",
            "parameters": {
                "type": "object",
                "properties": {
                    "question": {"type": "string", "description": "The unanswered question"},
                },
                "required": ["question"],
                "additionalProperties": False,
            },
        },
    },
]


# ── executor ─────────────────────────────────────────────────

def run_tool_calls(tool_calls):
    results = []
    for tc in tool_calls:
        fn = TOOLS.get(tc.function.name)
        if not fn:
            log.warning("unknown tool: %s", tc.function.name)
            out = {"error": "unknown tool"}
        else:
            try:
                args = json.loads(tc.function.arguments)
                out = fn(**args)
            except Exception as e:
                log.error("tool %s failed: %s", tc.function.name, e)
                out = {"error": str(e)}

        results.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "content": json.dumps(out),
        })
    return results