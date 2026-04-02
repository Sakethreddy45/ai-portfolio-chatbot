import logging
from pypdf import PdfReader
from db.store import add_document
from db.vectors import index_chunks

log = logging.getLogger(__name__)

CHUNK_SIZE = 500  # rough character count per chunk
OVERLAP = 50      # overlap between chunks so we don't cut mid-sentence


def read_pdf(file_bytes):
    """extract text from pdf bytes."""
    import io
    reader = PdfReader(io.BytesIO(file_bytes))
    text = ""
    for page in reader.pages:
        t = page.extract_text()
        if t:
            text += t + "\n"
    return text.strip()


def read_text(file_bytes):
    """decode plain text / markdown bytes."""
    return file_bytes.decode("utf-8", errors="ignore").strip()


READERS = {
    ".pdf": read_pdf,
    ".txt": read_text,
    ".md": read_text,
}


def chunk_text(text, size=CHUNK_SIZE, overlap=OVERLAP):
    """split text into overlapping chunks. keeps it simple — splits on whitespace."""
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = start + size
        chunk = " ".join(words[start:end])
        if chunk:
            chunks.append(chunk)
        start += size - overlap

    return chunks


def process_file(filename, file_bytes):
    """
    read a file, chunk it, store in sqlite + chroma.
    returns (doc_id, chunk_count) or raises ValueError if unsupported.
    """
    ext = "." + filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    reader = READERS.get(ext)

    if not reader:
        raise ValueError(f"unsupported file type: {ext}")

    text = reader(file_bytes)
    if not text:
        raise ValueError("file was empty or unreadable")

    chunks = chunk_text(text)
    doc_id = add_document(filename, len(chunks))
    index_chunks(doc_id, chunks)

    log.info("processed %s — %d chunks", filename, len(chunks))
    return doc_id, len(chunks)