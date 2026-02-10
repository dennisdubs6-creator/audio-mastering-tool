"""
WebSocket progress endpoint for real-time analysis updates.

- ``WS /ws/progress/{analysis_id}`` – Stream per-band progress events
  to connected clients while an analysis is running.
"""

import asyncio
import logging
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

router = APIRouter(tags=["progress"])


class ConnectionManager:
    """Tracks active WebSocket connections keyed by analysis ID.

    Provides methods to connect, disconnect, and broadcast JSON
    messages to all clients subscribed to a given analysis.
    """

    def __init__(self) -> None:
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, analysis_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections.setdefault(analysis_id, []).append(websocket)
        logger.info("WebSocket connected for analysis %s", analysis_id)

    def disconnect(self, analysis_id: str, websocket: WebSocket) -> None:
        conns = self._connections.get(analysis_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(analysis_id, None)
        logger.info("WebSocket disconnected for analysis %s", analysis_id)

    async def broadcast(self, analysis_id: str, message: dict[str, Any]) -> None:
        """Send a JSON message to all clients subscribed to *analysis_id*."""
        conns = self._connections.get(analysis_id, [])
        dead: list[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(analysis_id, ws)

    async def cleanup(self, analysis_id: str) -> None:
        """Close and remove all connections for a completed/failed analysis."""
        conns = self._connections.pop(analysis_id, [])
        for ws in conns:
            try:
                await ws.close()
            except Exception:
                pass


# Singleton shared with the analyze router
manager = ConnectionManager()


@router.websocket("/ws/progress/{analysis_id}")
async def progress_websocket(websocket: WebSocket, analysis_id: str) -> None:
    """WebSocket endpoint that streams analysis progress events.

    The client connects and waits for JSON messages of the form::

        {type: 'progress', band: str, percent: int, message: str}
        {type: 'complete', analysis_id: str}
        {type: 'error', message: str}

    The connection stays open until a ``complete`` or ``error`` message
    is sent, or the client disconnects.
    """
    await manager.connect(analysis_id, websocket)
    try:
        # Keep connection alive; the analyze router pushes messages.
        while True:
            # Wait for client pings / close frames
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(analysis_id, websocket)
