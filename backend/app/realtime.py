from __future__ import annotations

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import WebSocket


class RealtimeHub:
    def __init__(self) -> None:
        self._connections: dict[str, set[WebSocket]] = defaultdict(set)
        self._loop: asyncio.AbstractEventLoop | None = None

    def set_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        self._loop = loop

    async def connect(self, job_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[job_id].add(websocket)

    def disconnect(self, job_id: str, websocket: WebSocket) -> None:
        if job_id in self._connections:
            self._connections[job_id].discard(websocket)
            if not self._connections[job_id]:
                del self._connections[job_id]

    async def broadcast(self, job_id: str, payload: dict[str, Any]) -> None:
        connections = list(self._connections.get(job_id, set()))
        for ws in connections:
            try:
                await ws.send_json(payload)
            except Exception:
                self.disconnect(job_id, ws)

    def broadcast_threadsafe(self, job_id: str, payload: dict[str, Any]) -> None:
        if self._loop is None:
            return
        self._loop.call_soon_threadsafe(asyncio.create_task, self.broadcast(job_id, payload))

    def progress(self, job_id: str, value: float) -> None:
        self.broadcast_threadsafe(job_id, {"type": "progress", "value": value})

    def status(self, job_id: str, status: str) -> None:
        self.broadcast_threadsafe(job_id, {"type": "status", "status": status})

    def done(self, job_id: str) -> None:
        self.broadcast_threadsafe(job_id, {"type": "done", "timestamp": datetime.now(timezone.utc).isoformat()})

    def error(self, job_id: str, error: str) -> None:
        self.broadcast_threadsafe(
            job_id,
            {
                "type": "error",
                "error": error,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    def log(self, job_id: str, level: str, message: str) -> None:
        self.broadcast_threadsafe(
            job_id,
            {
                "type": "log",
                "level": level.lower(),
                "message": message,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )
