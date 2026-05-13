"""
Embed Agent — PubMedBERT embeddings stored in PGVector.
Chunks text, embeds each chunk, upserts into trial_chunks.
Uses HuggingFace free Serverless Inference API.
"""
import logging
import asyncio
from db.session import AsyncSessionLocal
from db.models import TrialChunk
from config import settings
from sqlalchemy import delete

logger = logging.getLogger(__name__)


def _chunk_text(text: str, chunk_size: int, overlap: int) -> list[str]:
    """
    Semantic sentence-boundary chunking.
    Splits text into sentences first, then groups them into chunks
    up to chunk_size words. Overlaps by carrying the last sentence(s)
    into the next chunk for continuity.
    """
    import re
    # Split on sentence boundaries (., !, ? followed by whitespace or end)
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    sentences = [s.strip() for s in sentences if s.strip()]

    chunks = []
    current_words = []
    current_sentences = []

    for sentence in sentences:
        words = sentence.split()
        if current_words and len(current_words) + len(words) > chunk_size:
            # Flush current chunk
            chunk = " ".join(current_words)
            if chunk:
                chunks.append(chunk)
            # Overlap: carry last sentence(s) into next chunk
            overlap_sentences = []
            overlap_word_count = 0
            for s in reversed(current_sentences):
                s_words = s.split()
                if overlap_word_count + len(s_words) <= overlap:
                    overlap_sentences.insert(0, s)
                    overlap_word_count += len(s_words)
                else:
                    break
            current_sentences = overlap_sentences + [sentence]
            current_words = " ".join(current_sentences).split()
        else:
            current_sentences.append(sentence)
            current_words.extend(words)

    # Flush remaining
    if current_words:
        chunk = " ".join(current_words)
        if chunk:
            chunks.append(chunk)

    return chunks


# Load model lazily to avoid startup delay
_embed_model = None

def _get_model():
    global _embed_model
    if _embed_model is None:
        from sentence_transformers import SentenceTransformer
        logger.info(f"Loading local embedding model {settings.hf_embed_model}...")
        _embed_model = SentenceTransformer(settings.hf_embed_model)
    return _embed_model


async def _embed_text(text: str) -> list[float] | None:
    """
    Get embedding using local sentence-transformers model.
    """
    try:
        model = _get_model()
        # Run encode in a thread to avoid blocking the async event loop
        embedding = await asyncio.to_thread(model.encode, text)
        return embedding.tolist()
    except Exception as e:
        logger.error(f"Embed local model error: {e}")
    return None


async def run_embed(trial_id: str, text: str) -> int:
    """
    Chunk text, embed each chunk, write to PGVector.
    Returns number of chunks written.
    Uses ON CONFLICT replacement (idempotent).
    """
    chunks = _chunk_text(
        text,
        chunk_size=settings.embed_chunk_size // 4,  # word count ~= token count / 4
        overlap=settings.embed_chunk_overlap // 4,
    )

    if not chunks:
        return 0

    written = 0
    async with AsyncSessionLocal() as db:
        # Clear old chunks for this trial (for updates)
        await db.execute(delete(TrialChunk).where(TrialChunk.trial_id == trial_id))

        for idx, chunk in enumerate(chunks):
            embedding = await _embed_text(chunk)
            if embedding is None:
                logger.warning(f"Skipping chunk {idx} for {trial_id} — embed failed")
                continue

            db.add(TrialChunk(
                trial_id=trial_id,
                chunk_index=idx,
                chunk_text=chunk,
                embedding=embedding,
            ))
            written += 1

        await db.commit()

    logger.debug(f"Embedded {written}/{len(chunks)} chunks for {trial_id}")
    return written
