import os
import logging
import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from config import CHROMA_DIR, EMBEDDING_MODEL
from db.store import get_all_entries

log = logging.getLogger(__name__)

_client = None
_collection = None


def _get_collection():
    global _client, _collection

    if _collection is not None:
        return _collection

    os.makedirs(CHROMA_DIR, exist_ok=True)

    embed_fn = OpenAIEmbeddingFunction(
    model_name=EMBEDDING_MODEL,
    api_key=os.getenv("OPENAI_API_KEY"),
    )
    _client = chromadb.PersistentClient(path=CHROMA_DIR)
    _collection = _client.get_or_create_collection(
        name="knowledge_base",
        embedding_function=embed_fn,
    )
    log.info("chroma collection ready — %d docs", _collection.count())
    return _collection


def index_entry(entry_id, question, answer, category):
    """embed a single knowledge entry and upsert it into chroma."""
    col = _get_collection()

    # combine question + answer so the embedding captures both
    doc_text = f"Q: {question}\nA: {answer}"

    col.upsert(
        ids=[str(entry_id)],
        documents=[doc_text],
        metadatas=[{"category": category, "question": question}],
    )
    log.info("indexed entry %d into chroma", entry_id)


def remove_entry(entry_id):
    """remove a single entry from the vector store."""
    col = _get_collection()
    try:
        col.delete(ids=[str(entry_id)])
        log.info("removed entry %d from chroma", entry_id)
    except Exception as e:
        log.warning("could not remove entry %d: %s", entry_id, e)


def index_chunks(doc_id, chunks):
    """embed and store a list of text chunks from an uploaded file."""
    col = _get_collection()

    ids = [f"doc_{doc_id}_chunk_{i}" for i in range(len(chunks))]
    metas = [{"source": f"document_{doc_id}", "category": "uploaded"} for _ in chunks]

    col.upsert(ids=ids, documents=chunks, metadatas=metas)
    log.info("indexed %d chunks for document %d", len(chunks), doc_id)


def remove_doc_chunks(doc_id):
    """remove all chunks belonging to an uploaded document."""
    col = _get_collection()
    existing = col.get(where={"source": f"document_{doc_id}"})
    if existing["ids"]:
        col.delete(ids=existing["ids"])
        log.info("removed %d chunks for document %d", len(existing["ids"]), doc_id)


def search(query, top_k=5):
    """search for the most relevant knowledge entries given a query."""
    col = _get_collection()

    if col.count() == 0:
        return []

    results = col.query(query_texts=[query], n_results=min(top_k, col.count()))

    docs = []
    for i, doc in enumerate(results["documents"][0]):
        meta = results["metadatas"][0][i]
        dist = results["distances"][0][i] if results.get("distances") else None
        docs.append({
            "content": doc,
            "category": meta.get("category", ""),
            "question": meta.get("question", ""),
            "distance": dist,
        })

    return docs


def rebuild_index():
    """wipe and rebuild the entire chroma index from sqlite entries."""
    col = _get_collection()

    # clear existing
    existing = col.get()
    if existing["ids"]:
        col.delete(ids=existing["ids"])

    entries = get_all_entries()
    if not entries:
        log.info("no entries to index")
        return 0

    ids = [str(e["id"]) for e in entries]
    docs = [f"Q: {e['question']}\nA: {e['answer']}" for e in entries]
    metas = [{"category": e["category"], "question": e["question"]} for e in entries]

    col.upsert(ids=ids, documents=docs, metadatas=metas)
    log.info("rebuilt chroma index — %d entries", len(entries))
    return len(entries)