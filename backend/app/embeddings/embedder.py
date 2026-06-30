"""HuggingFace Embedding Generation Service."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)

_model = None
_model_name = None


def get_embedding_model(model_name: str = "BAAI/bge-small-en"):
    """Load or return cached HuggingFace sentence-transformer model."""
    global _model, _model_name
    if _model is None or _model_name != model_name:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer(model_name)
            _model_name = model_name
            logger.info(f"Loaded embedding model: {model_name}")
        except ImportError:
            logger.warning("sentence-transformers not installed, embeddings disabled")
            return None
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            return None
    return _model


def generate_embeddings(texts: list[str], model_name: str = "BAAI/bge-small-en") -> Optional[list]:
    """Generate embeddings for a list of text strings.

    Returns list of numpy arrays or None if model unavailable.
    """
    model = get_embedding_model(model_name)
    if model is None:
        return None

    try:
        embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return embeddings.tolist()
    except Exception as e:
        logger.error(f"Error generating embeddings: {e}")
        return None


def generate_embedding(text: str, model_name: str = "BAAI/bge-small-en") -> Optional[list]:
    """Generate embedding for a single text string."""
    result = generate_embeddings([text], model_name)
    if result:
        return result[0]
    return None
