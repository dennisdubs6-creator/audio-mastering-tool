"""API-level integration tests for ``POST /api/analyze`` SSE streaming.

Mocks ``AnalysisRepository`` so no real database is needed, and verifies
that the SSE stream emits one ``band_progress`` event per band followed
by a single ``complete`` event.
"""

import io
import json
import os
import tempfile
import wave
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient

from api.main import app
from api.models import BandMetrics, OverallMetrics
from config.constants import BAND_NAMES

SAMPLE_RATE = 48000
DURATION = 1.0
NUM_SAMPLES = int(SAMPLE_RATE * DURATION)


def _make_wav_bytes() -> bytes:
    """Return raw bytes of a short mono WAV with broadband content."""
    t = np.linspace(0, DURATION, NUM_SAMPLES, endpoint=False)
    sine = 0.5 * np.sin(2.0 * np.pi * 440.0 * t)
    rng = np.random.default_rng(seed=42)
    noise = 0.1 * rng.uniform(-1.0, 1.0, size=NUM_SAMPLES)
    samples = (sine + noise).astype(np.float32)
    pcm = (samples * 32767).astype(np.int16)

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm.tobytes())
    return buf.getvalue()


def _parse_sse(raw: str) -> list[tuple[str, dict]]:
    """Parse an SSE text stream into ``(event_type, data_dict)`` pairs."""
    events: list[tuple[str, dict]] = []
    current_event = None
    for line in raw.splitlines():
        if line.startswith("event: "):
            current_event = line[len("event: "):]
        elif line.startswith("data: ") and current_event is not None:
            data = json.loads(line[len("data: "):])
            events.append((current_event, data))
            current_event = None
    return events


@pytest.fixture()
def client():
    """FastAPI TestClient with lifespan events disabled."""
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestAnalyzeSSEStream:
    """Tests for the SSE event stream returned by ``POST /api/analyze``."""

    @patch("api.routers.analyze.AnalysisRepository")
    def test_emits_band_progress_per_band_then_complete(self, mock_repo_cls, client):
        """The stream must contain one ``band_progress`` per band and one ``complete``."""
        # Make the repository a no-op mock
        mock_repo = MagicMock()
        mock_repo.save_complete_analysis.return_value = MagicMock()
        mock_repo_cls.return_value = mock_repo

        wav_bytes = _make_wav_bytes()

        response = client.post(
            "/api/analyze",
            files={"file": ("test.wav", wav_bytes, "audio/wav")},
            data={"recommendation_level": "suggestive"},
        )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

        events = _parse_sse(response.text)

        # Separate event types
        band_events = [(e, d) for e, d in events if e == "band_progress"]
        complete_events = [(e, d) for e, d in events if e == "complete"]
        error_events = [(e, d) for e, d in events if e == "error"]

        assert len(error_events) == 0, f"Unexpected errors: {error_events}"
        assert len(band_events) == 5, (
            f"Expected 5 band_progress events, got {len(band_events)}"
        )
        assert len(complete_events) == 1, (
            f"Expected 1 complete event, got {len(complete_events)}"
        )

        # Verify all five band names appear
        received_bands = {d["band_name"] for _, d in band_events}
        assert received_bands == set(BAND_NAMES)

    @patch("api.routers.analyze.AnalysisRepository")
    def test_band_progress_events_precede_complete(self, mock_repo_cls, client):
        """All ``band_progress`` events must appear before ``complete``."""
        mock_repo = MagicMock()
        mock_repo.save_complete_analysis.return_value = MagicMock()
        mock_repo_cls.return_value = mock_repo

        wav_bytes = _make_wav_bytes()

        response = client.post(
            "/api/analyze",
            files={"file": ("test.wav", wav_bytes, "audio/wav")},
            data={"recommendation_level": "suggestive"},
        )

        events = _parse_sse(response.text)
        event_types = [e for e, _ in events]

        # Find the position of the complete event
        complete_idx = event_types.index("complete")
        for i, etype in enumerate(event_types):
            if etype == "band_progress":
                assert i < complete_idx, (
                    "band_progress event appeared after complete event"
                )

    @patch("api.routers.analyze.AnalysisRepository")
    def test_band_progress_contains_metrics(self, mock_repo_cls, client):
        """Each ``band_progress`` data payload must contain metric keys."""
        mock_repo = MagicMock()
        mock_repo.save_complete_analysis.return_value = MagicMock()
        mock_repo_cls.return_value = mock_repo

        wav_bytes = _make_wav_bytes()

        response = client.post(
            "/api/analyze",
            files={"file": ("test.wav", wav_bytes, "audio/wav")},
            data={"recommendation_level": "suggestive"},
        )

        events = _parse_sse(response.text)
        band_events = [(e, d) for e, d in events if e == "band_progress"]

        for _, data in band_events:
            assert "band_name" in data
            # At least some core metric should be present
            assert "band_rms_dbfs" in data
            assert "dynamic_range_db" in data

    @patch("api.routers.analyze.AnalysisRepository")
    def test_complete_event_contains_band_metrics_and_overall(self, mock_repo_cls, client):
        """The ``complete`` event must include band_metrics list and overall_metrics."""
        mock_repo = MagicMock()
        mock_repo.save_complete_analysis.return_value = MagicMock()
        mock_repo_cls.return_value = mock_repo

        wav_bytes = _make_wav_bytes()

        response = client.post(
            "/api/analyze",
            files={"file": ("test.wav", wav_bytes, "audio/wav")},
            data={"recommendation_level": "suggestive"},
        )

        events = _parse_sse(response.text)
        complete_events = [d for e, d in events if e == "complete"]
        assert len(complete_events) == 1

        result = complete_events[0]
        assert "band_metrics" in result
        assert len(result["band_metrics"]) == 5
        assert "overall_metrics" in result
        assert "integrated_lufs" in result["overall_metrics"]

    @patch("api.routers.analyze.AnalysisRepository")
    def test_repository_called_with_band_metrics(self, mock_repo_cls, client):
        """``AnalysisRepository.save_complete_analysis`` must be called with band metrics."""
        mock_repo = MagicMock()
        mock_repo.save_complete_analysis.return_value = MagicMock()
        mock_repo_cls.return_value = mock_repo

        wav_bytes = _make_wav_bytes()

        response = client.post(
            "/api/analyze",
            files={"file": ("test.wav", wav_bytes, "audio/wav")},
            data={"recommendation_level": "suggestive"},
        )

        # Drain the stream to ensure the background thread completes
        _ = response.text

        mock_repo.save_complete_analysis.assert_called_once()
        call_args = mock_repo.save_complete_analysis.call_args
        _, band_metrics_arg, overall_arg = call_args.args

        assert len(band_metrics_arg) == 5
        for bm in band_metrics_arg:
            assert isinstance(bm, BandMetrics)
        assert isinstance(overall_arg, OverallMetrics)
