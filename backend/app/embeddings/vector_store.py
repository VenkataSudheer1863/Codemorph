"""Vector Store Service for RAG retrieval.

Uses FAISS for vector storage and similarity search.
"""

import os
import logging
import pickle
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

STORE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "vector_stores")


class VectorStore:
    """FAISS-based vector store for code embeddings."""

    def __init__(self, project_id: str, dimension: int = 384):
        self.project_id = project_id
        self.dimension = dimension
        self.index = None
        self.documents: list[dict] = []
        self._init_store()

    def _init_store(self):
        """Initialize FAISS index."""
        try:
            import faiss
            self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine sim (normalized vectors)
            logger.info(f"Initialized FAISS index for project {self.project_id}")
        except ImportError:
            logger.warning("faiss-cpu not installed, vector store disabled")
            self.index = None

    def add_documents(self, texts: list[str], metadatas: list[dict], embeddings: list[list[float]]):
        """Add documents with their embeddings to the store."""
        if self.index is None:
            return

        vectors = np.array(embeddings, dtype=np.float32)
        self.index.add(vectors)

        for text, metadata in zip(texts, metadatas):
            self.documents.append({
                "text": text,
                "metadata": metadata,
            })

        logger.info(f"Added {len(texts)} documents to vector store")

    def search(self, query_embedding: list[float], top_k: int = 5) -> list[dict]:
        """Search for similar documents.

        Returns list of dicts with 'text', 'metadata', and 'score'.
        """
        if self.index is None or self.index.ntotal == 0:
            return []

        query_vec = np.array([query_embedding], dtype=np.float32)
        scores, indices = self.index.search(query_vec, min(top_k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.documents) and idx >= 0:
                doc = self.documents[idx]
                results.append({
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "score": float(score),
                })

        return results

    def save(self):
        """Persist the vector store to disk."""
        if self.index is None:
            return

        os.makedirs(STORE_DIR, exist_ok=True)
        store_path = os.path.join(STORE_DIR, self.project_id)
        os.makedirs(store_path, exist_ok=True)

        try:
            import faiss
            faiss.write_index(self.index, os.path.join(store_path, "index.faiss"))
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

        with open(os.path.join(store_path, "documents.pkl"), "wb") as f:
            pickle.dump(self.documents, f)

        logger.info(f"Saved vector store for project {self.project_id}")

    def load(self) -> bool:
        """Load vector store from disk."""
        store_path = os.path.join(STORE_DIR, self.project_id)
        index_path = os.path.join(store_path, "index.faiss")
        docs_path = os.path.join(store_path, "documents.pkl")

        if not os.path.exists(index_path) or not os.path.exists(docs_path):
            return False

        try:
            import faiss
            self.index = faiss.read_index(index_path)
        except Exception as e:
            logger.error(f"Failed to load FAISS index: {e}")
            return False

        try:
            with open(docs_path, "rb") as f:
                self.documents = pickle.load(f)  # noqa: S301
        except Exception as e:
            logger.error(f"Failed to load documents: {e}")
            return False

        logger.info(f"Loaded vector store for project {self.project_id} ({len(self.documents)} docs)")
        return True


def build_vector_store(
    project_id: str,
    files: list[dict],
    parse_results: list[dict],
) -> Optional[VectorStore]:
    """Build a vector store from parsed codebase files.

    Chunks file content and stores embeddings for RAG retrieval.
    """
    from app.embeddings.embedder import generate_embeddings

    store = VectorStore(project_id)
    if store.index is None:
        return None

    texts = []
    metadatas = []

    for file_info, parse_result in zip(files, parse_results):
        content = file_info.get("content", "")
        if not content:
            continue

        # Chunk by functions/classes or fixed size
        chunks = _chunk_content(content, file_info, parse_result)
        for chunk in chunks:
            texts.append(chunk["text"])
            metadatas.append(chunk["metadata"])

    if not texts:
        return store

    # Generate embeddings in batches
    batch_size = 64
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        embs = generate_embeddings(batch)
        if embs:
            all_embeddings.extend(embs)
        else:
            # If embeddings fail, skip
            return None

    if len(all_embeddings) == len(texts):
        store.add_documents(texts, metadatas, all_embeddings)
        store.save()

    return store


def _chunk_content(content: str, file_info: dict, parse_result: dict) -> list[dict]:
    """Chunk file content for embedding."""
    chunks = []
    path = file_info.get("path", "")
    language = file_info.get("language", "")

    # First, try to chunk by classes/functions
    classes = parse_result.get("classes", [])
    functions = parse_result.get("functions", [])

    if not classes and not functions:
        # Fall back to fixed-size chunking
        lines = content.split("\n")
        chunk_size = 50  # lines per chunk
        for i in range(0, len(lines), chunk_size):
            chunk_text = "\n".join(lines[i:i + chunk_size])
            if chunk_text.strip():
                chunks.append({
                    "text": f"File: {path}\nLanguage: {language}\n\n{chunk_text}",
                    "metadata": {
                        "file": path,
                        "language": language,
                        "start_line": i + 1,
                        "end_line": min(i + chunk_size, len(lines)),
                    },
                })
    else:
        # Chunk the whole file as one document if small enough
        if len(content) < 3000:
            chunks.append({
                "text": f"File: {path}\nLanguage: {language}\n\n{content}",
                "metadata": {
                    "file": path,
                    "language": language,
                    "classes": [c["name"] for c in classes],
                    "functions": [f["name"] for f in functions],
                },
            })
        else:
            # Split into reasonable chunks
            lines = content.split("\n")
            chunk_size = 80
            for i in range(0, len(lines), chunk_size):
                chunk_text = "\n".join(lines[i:i + chunk_size])
                if chunk_text.strip():
                    chunks.append({
                        "text": f"File: {path}\nLanguage: {language}\n\n{chunk_text}",
                        "metadata": {
                            "file": path,
                            "language": language,
                            "start_line": i + 1,
                        },
                    })

    return chunks


def get_rag_retriever(store: Optional[VectorStore]):
    """Create a RAG retriever function from a vector store."""
    if store is None:
        return None

    from app.embeddings.embedder import generate_embedding

    def retrieve(query: str, top_k: int = 5) -> str:
        query_emb = generate_embedding(query)
        if query_emb is None:
            return ""
        results = store.search(query_emb, top_k=top_k)
        return "\n\n---\n\n".join(r["text"] for r in results)

    return retrieve
