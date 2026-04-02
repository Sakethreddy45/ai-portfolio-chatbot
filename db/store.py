import sqlite3
import os
import logging
from config import DB_PATH

log = logging.getLogger(__name__)


def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS knowledge (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            chunk_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS chat_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visitor_msg TEXT,
            bot_reply TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS unanswered (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            name TEXT DEFAULT '',
            notes TEXT DEFAULT '',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    log.info("database initialized at %s", DB_PATH)


# ── knowledge CRUD ───────────────────────────────────────────

def add_entry(category, question, answer):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO knowledge (category, question, answer) VALUES (?, ?, ?)",
        (category, question, answer)
    )
    entry_id = c.lastrowid
    conn.commit()
    conn.close()
    return entry_id


def get_all_entries():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM knowledge ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_entry(entry_id):
    conn = get_conn()
    row = conn.execute("SELECT * FROM knowledge WHERE id = ?", (entry_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_entry(entry_id, category, question, answer):
    conn = get_conn()
    conn.execute(
        "UPDATE knowledge SET category = ?, question = ?, answer = ? WHERE id = ?",
        (category, question, answer, entry_id)
    )
    conn.commit()
    conn.close()


def delete_entry(entry_id):
    conn = get_conn()
    conn.execute("DELETE FROM knowledge WHERE id = ?", (entry_id,))
    conn.commit()
    conn.close()


# ── logging helpers ──────────────────────────────────────────

def log_chat(visitor_msg, bot_reply):
    conn = get_conn()
    conn.execute(
        "INSERT INTO chat_logs (visitor_msg, bot_reply) VALUES (?, ?)",
        (visitor_msg, bot_reply)
    )
    conn.commit()
    conn.close()


def log_unanswered(question):
    conn = get_conn()
    conn.execute("INSERT INTO unanswered (question) VALUES (?)", (question,))
    conn.commit()
    conn.close()


def save_lead(email, name="", notes=""):
    conn = get_conn()
    conn.execute(
        "INSERT INTO leads (email, name, notes) VALUES (?, ?, ?)",
        (email, name, notes)
    )
    conn.commit()
    conn.close()


def get_unanswered():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM unanswered ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_leads():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM leads ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_chat_logs(limit=50):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM chat_logs ORDER BY id DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ── document tracking ───────────────────────────────────────

def add_document(filename, chunk_count):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "INSERT INTO documents (filename, chunk_count) VALUES (?, ?)",
        (filename, chunk_count)
    )
    doc_id = c.lastrowid
    conn.commit()
    conn.close()
    return doc_id


def get_documents():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM documents ORDER BY id DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_document(doc_id):
    conn = get_conn()
    conn.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
    conn.commit()
    conn.close()