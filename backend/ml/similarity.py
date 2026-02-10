"""
Similarity matching using cosine similarity on feature vectors.

Provides cosine similarity computation and top-K reference matching,
plus vector serialization helpers for BLOB storage.

Similarity scores range from 0.0 (completely dissimilar) to 1.0 (identical).
"""

from typing import List, Tuple

import numpy as np


class SimilarityMatcher:
    """Computes cosine similarity between feature vectors and ranks matches.

    Similarity scores range from 0.0 (completely dissimilar / orthogonal)
    to 1.0 (identical feature vectors).
    """

    @staticmethod
    def compute_cosine_similarity(vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine similarity between two vectors.

        Args:
            vec1: First feature vector.
            vec2: Second feature vector.

        Returns:
            Cosine similarity in range [-1.0, 1.0]. For L2-normalized
            vectors this equals the dot product.
        """
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(vec1, vec2) / (norm1 * norm2))

    @staticmethod
    def find_similar_references(
        user_vector: np.ndarray,
        reference_vectors: List[Tuple[str, np.ndarray]],
        top_k: int = 10,
    ) -> List[Tuple[str, float]]:
        """Find the top-K most similar reference tracks.

        Args:
            user_vector: Feature vector from user's analysis.
            reference_vectors: List of (reference_id, feature_vector) tuples.
            top_k: Number of top matches to return.

        Returns:
            List of (reference_id, similarity_score) tuples sorted by
            similarity score in descending order.
        """
        scores: List[Tuple[str, float]] = []
        norm_user = np.linalg.norm(user_vector)
        if norm_user == 0:
            return []

        for ref_id, ref_vec in reference_vectors:
            norm_ref = np.linalg.norm(ref_vec)
            if norm_ref == 0:
                scores.append((ref_id, 0.0))
                continue
            sim = float(np.dot(user_vector, ref_vec) / (norm_user * norm_ref))
            scores.append((ref_id, sim))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]


def serialize_vector(vec: np.ndarray) -> bytes:
    """Serialize a numpy array to bytes for BLOB storage.

    Args:
        vec: Feature vector to serialize.

    Returns:
        Raw bytes representation of the float32 array.
    """
    return vec.astype(np.float32).tobytes()


def deserialize_vector(blob: bytes) -> np.ndarray:
    """Deserialize bytes from BLOB storage to a numpy array.

    Args:
        blob: Raw bytes from database BLOB column.

    Returns:
        Numpy float32 array reconstructed from the bytes.
    """
    return np.frombuffer(blob, dtype=np.float32)
