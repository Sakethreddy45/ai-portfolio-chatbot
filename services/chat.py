import logging
from openai import OpenAI
from config import PERSONA_NAME, OPENAI_MODEL, TEMPERATURE, MAX_TOKENS, TOP_K
from db.vectors import search as vector_search
from db.store import log_chat
from services.tools import TOOL_DEFS, run_tool_calls

log = logging.getLogger(__name__)

client = OpenAI()

MAX_ROUNDS = 5


def _build_prompt(query):
    """pull relevant context from chroma and stitch it into the system prompt."""

    hits = vector_search(query, top_k=TOP_K)

    context_block = ""
    if hits:
        pieces = []
        for h in hits:
            pieces.append(h["content"])
        context_block = "\n---\n".join(pieces)

    prompt = (
        f"You are {PERSONA_NAME}, answering questions on your personal website. "
        f"A visitor just landed on your site — they might be a recruiter, a hiring manager, "
        f"or someone curious about your work. Be confident but real. "
        f"Don't make stuff up. If the context below doesn't cover something, say you're not sure "
        f"and use the record_unknown_question tool to log it.\n\n"
        f"If someone wants to connect or shows hiring interest, offer to take their email. "
        f"Otherwise just focus on answering their questions well.\n"
    )

    if context_block:
        prompt += f"\n--- CONTEXT FROM KNOWLEDGE BASE ---\n{context_block}\n--- END CONTEXT ---\n"
    else:
        prompt += (
            f"\nNo relevant context was found for this query. "
            f"Answer based on general knowledge about {PERSONA_NAME}'s profile if you can, "
            f"otherwise let them know and log the question.\n"
        )

    return prompt


def get_reply(user_msg, history):
    system_prompt = _build_prompt(user_msg)

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_msg})

    for _ in range(MAX_ROUNDS):
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=messages,
            tools=TOOL_DEFS,
            temperature=TEMPERATURE,
            max_tokens=MAX_TOKENS,
        )

        choice = resp.choices[0]

        if choice.finish_reason != "tool_calls":
            reply = choice.message.content or ""
            log_chat(user_msg, reply)
            return reply

        msg = choice.message
        tool_results = run_tool_calls(msg.tool_calls)
        messages.append(msg)
        messages.extend(tool_results)

    return "Something went wrong on my end — could you try that again?"