"""Tests for the SimilarityMatcher class and serialization helpers."""

import numpy as np
import pytest

from ml.similarity import (
    SimilarityMatcher,
    deserialize_vector,
    serialize_vector,
)


class TestSimilarityMatcher:
    def test_identical_vectors_return_one(self):
        vec = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        vec = vec / np.linalg.norm(vec)
        score = SimilarityMatcher.compute_cosine_similarity(vec, vec)
        assert abs(score - 1.0) < 1e-5

    def test_orthogonal_vectors_return_zero(self):
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        score = SimilarityMatcher.compute_cosine_similarity(vec1, vec2)
        assert abs(score) < 1e-5

    def test_opposite_vectors_return_negative_one(self):
        vec1 = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        vec2 = np.array([-1.0, 0.0, 0.0], dtype=np.float32)
        score = SimilarityMatcher.compute_cosine_similarity(vec1, vec2)
        assert abs(score - (-1.0)) < 1e-5

    def test_zero_vector_returns_zero(self):
        vec1 = np.zeros(3, dtype=np.float32)
        vec2 = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        score = SimilarityMatcher.compute_cosine_similarity(vec1, vec2)
        assert score == 0.0

    def test_find_similar_references_ranking(self):
        user = np.array([1.0, 0.0, 0.0], dtype=np.float32)
        refs = [
            ("ref_a", np.array([0.5, 0.5, 0.0], dtype=np.float32)),
            ("ref_b", np.array([1.0, 0.0, 0.0], dtype=np.float32)),
            ("ref_c", np.array([0.0, 1.0, 0.0], dtype=np.float32)),
        ]
        results = SimilarityMatcher.find_similar_references(user, refs, top_k=3)

        assert len(results) == 3
        # ref_b should be first (identical direction)
        assert results[0][0] == "ref_b"
        assert abs(results[0][1] - 1.0) < 1e-5
        # ref_c should be last (orthogonal)
        assert results[2][0] == "ref_c"

    def test_find_similar_references_top_k_limit(self):
        user = np.array([1.0, 0.0], dtype=np.float32)
        refs = [
            ("a", np.array([1.0, 0.0], dtype=np.float32)),
            ("b", np.array([0.5, 0.5], dtype=np.float32)),
            ("c", np.array([0.0, 1.0], dtype=np.float32)),
        ]
        results = SimilarityMatcher.find_similar_references(user, refs, top_k=2)
        assert len(results) == 2

    def test_find_similar_empty_references(self):
        user = np.array([1.0, 0.0], dtype=np.float32)
        results = SimilarityMatcher.find_similar_references(user, [], top_k=5)
        assert results == []

    def test_find_similar_zero_user_vector(self):
        user = np.zeros(3, dtype=np.float32)
        refs = [("a", np.array([1.0, 0.0, 0.0], dtype=np.float32))]
        results = SimilarityMatcher.find_similar_references(user, refs)
        assert results == []


class TestSerialization:
    def test_round_trip(self):
        original = np.array([1.0, 2.5, -3.7, 0.0], dtype=np.float32)
        blob = serialize_vector(original)
        restored = deserialize_vector(blob)
        np.testing.assert_array_almost_equal(original, restored)

    def test_128_dim_round_trip(self):
        original = np.random.randn(128).astype(np.float32)
        blob = serialize_vector(original)
        restored = deserialize_vector(blob)
        np.testing.assert_array_almost_equal(original, restored)
        assert len(blob) == 128 * 4  # float32 = 4 bytes each
