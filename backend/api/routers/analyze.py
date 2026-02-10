"""
Analysis API endpoints.

- ``POST /api/analyze`` – Submit a WAV file for mastering analysis.
  Returns ``{analysis_id}`` immediately and runs analysis in a
  background thread, streaming progress over WebSocket.
- ``GET /api/analysis/{analysis_id}`` – Retrieve analysis results by UUID.
"""

import asyncio
import logging
import os
import shutil
import threading
import uuid

import numpy as np

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from analysis.engine import AnalysisEngine
from api.database import get_session_dependency, SessionFactory
from api.models import Analysis, BandMetrics
from api.repositories.analysis_repo import AnalysisRepository
from api.routers.progress import manager as ws_manager
from api.schemas import AnalysisResponse
from config.constants import FREQUENCY_BANDS, UPLOAD_DIR
from dsp.audio_loader import AudioLoader
from dsp.band_integrator import BandIntegrator
from dsp.stft_processor import STFTProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["analysis"])

_main_loop = None


def set_main_loop(loop) -> None:
    """Capture the main asyncio event loop for thread-safe broadcasting."""
    global _main_loop
    _main_loop = loop

# Band name → percent mapping for progress reporting
_BAND_PERCENT: dict[str, int] = {
    "low": 20,
    "low_mid": 40,
    "mid": 60,
    "high_mid": 80,
    "high": 100,
}


def _build_engine() -> AnalysisEngine:
    """Construct an ``AnalysisEngine`` with default DSP components."""
    return AnalysisEngine(
        stft_processor=STFTProcessor(),
        band_integrator=BandIntegrator(FREQUENCY_BANDS),
        audio_loader=AudioLoader(),
    )


def _broadcast_sync(analysis_id: str, message: dict) -> None:
    """Fire-and-forget broadcast from a synchronous thread."""
    if _main_loop and not _main_loop.is_closed():
        asyncio.run_coroutine_threadsafe(
            ws_manager.broadcast(analysis_id, message), _main_loop
        )


@router.post("/analyze")
def create_analysis(
    file: UploadFile = File(...),
    genre: str | None = Form(None),
    recommendation_level: str = Form("suggestive"),
) -> dict:
    """Submit a WAV file for audio mastering analysis.

    Returns ``{analysis_id}`` immediately. The analysis runs in a
    background thread and streams progress events over the WebSocket
    at ``/ws/progress/{analysis_id}``.
    """
    analysis_id = str(uuid.uuid4())

    # Validate WAV file extension
    if not file.filename or not file.filename.lower().endswith('.wav'):
        raise HTTPException(status_code=400, detail="Only WAV files are supported")

    # Save uploaded file to a durable location keyed by analysis ID
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    suffix = os.path.splitext(file.filename or "upload.wav")[1]
    durable_path = os.path.join(UPLOAD_DIR, f"{analysis_id}{suffix}")
    with open(durable_path, "wb") as f_out:
        shutil.copyfileobj(file.file, f_out)

    file_name = file.filename or "unknown.wav"

    # Create pending Analysis record so GET returns 202 while processing
    session = SessionFactory()
    try:
        pending_analysis = Analysis(
            id=analysis_id,
            file_path=durable_path,
            file_name=file_name,
            file_size=os.path.getsize(durable_path),
            status="pending",
            genre=genre,
            recommendation_level=recommendation_level,
        )
        session.add(pending_analysis)
        session.commit()
    finally:
        session.close()

    def _run_analysis() -> None:
        """Run the analysis pipeline in a background thread."""
        worker_session = SessionFactory()
        try:
            engine = _build_engine()
            repo = AnalysisRepository(worker_session)

            repo.update_status(analysis_id, "processing")

            # Broadcast start
            _broadcast_sync(analysis_id, {
                "type": "band_progress",
                "band": "",
                "progress": 0,
                "status": "Starting analysis...",
            })

            def _on_band_progress(band_name: str, metrics: dict) -> None:
                percent = _BAND_PERCENT.get(band_name, 0)
                _broadcast_sync(analysis_id, {
                    "type": "band_progress",
                    "band": band_name,
                    "progress": percent,
                    "status": f"Analyzing {band_name.replace('_', ' ').title()}...",
                })

            band_metrics, overall_metrics, analysis_warnings = engine.analyze_audio(
                file_path=durable_path,
                analysis_id=analysis_id,
                progress_callback=_on_band_progress,
            )

            # Extract audio metadata from the loader for persistence
            loader = AudioLoader()
            audio_data = loader.load_wav(durable_path)

            # Update the existing pending record with full analysis data
            analysis = worker_session.get(Analysis, analysis_id)
            analysis.sample_rate = audio_data.sample_rate
            analysis.bit_depth = audio_data.bit_depth
            analysis.duration_seconds = audio_data.duration
            analysis.analysis_engine_version = "1.0.0"

            repo.save_complete_analysis(analysis, band_metrics, overall_metrics)
            repo.update_status(analysis_id, "completed")
            worker_session.commit()

            _broadcast_sync(analysis_id, {
                "type": "complete",
                "analysis_id": analysis_id,
            })

            if _main_loop and not _main_loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    ws_manager.cleanup(analysis_id), _main_loop
                )

        except ValueError as exc:
            logger.exception("Validation error during analysis")
            worker_session.rollback()
            repo.update_status(analysis_id, "failed")
            _broadcast_sync(analysis_id, {
                "type": "error",
                "message": str(exc),
            })
            if _main_loop and not _main_loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    ws_manager.cleanup(analysis_id), _main_loop
                )
        except Exception:
            logger.exception("Analysis failed for %s", file_name)
            worker_session.rollback()
            try:
                repo.update_status(analysis_id, "failed")
            except Exception:
                pass
            _broadcast_sync(analysis_id, {
                "type": "error",
                "message": "Analysis failed",
            })
            if _main_loop and not _main_loop.is_closed():
                asyncio.run_coroutine_threadsafe(
                    ws_manager.cleanup(analysis_id), _main_loop
                )
        finally:
            worker_session.close()

    worker = threading.Thread(target=_run_analysis, daemon=True)
    worker.start()

    return {"analysis_id": analysis_id}


@router.get("/analysis/{analysis_id}", response_model=AnalysisResponse)
def get_analysis(
    analysis_id: str,
    session: Session = Depends(get_session_dependency),
) -> AnalysisResponse:
    """Retrieve analysis results by UUID.

    Returns the analysis record with band metrics, overall metrics,
    and recommendations eagerly loaded.

    Raises:
        HTTPException: 404 if no analysis exists with the given ID.
    """
    repo = AnalysisRepository(session)
    analysis = repo.get_with_metrics(analysis_id)
    if analysis is None:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis.status in ("pending", "processing"):
        raise HTTPException(status_code=202, detail="Analysis in progress")
    return AnalysisResponse.model_validate(analysis)
