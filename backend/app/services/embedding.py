import numpy as np
from sentence_transformers import SentenceTransformer
from app.config import settings


class EmbeddingService:
    def __init__(self):
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(settings.embedding_model)
        return self._model

    def embed(self, text: str) -> list[float]:
        vector = self.model.encode(text, normalize_embeddings=True)
        return vector.tolist()

    def embed_batch(self, texts: list[str], batch_size: int = 256) -> list[list[float]]:
        vectors = self.model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=True,
        )
        return vectors.tolist()

    def text_for_embedding(self, title: str, tags: dict) -> str:
        """Build the text string we embed: title + key fields from extracted tags."""
        features = " ".join(tags.get("key_features", []))
        return f"{title} {tags.get('category', '')} {tags.get('subcategory', '')} {features} {tags.get('use_case', '')}"


embedding_service = EmbeddingService()
