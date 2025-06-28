from typing import Dict, List, Tuple, Optional
import asyncio
from fastapi import WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from starlette.websockets import WebSocket


class LogBroadcaster:
    def __init__(self):
        self.connections: Dict[str, List[WebSocket]] = {}
        self.queue: asyncio.Queue[Tuple[str, dict]] = asyncio.Queue()
        self._worker_started = False
        self._worker_task: asyncio.Task | None = None

    async def connect(self, tenant_id: str, websocket: WebSocket):
        await websocket.accept()
        self.connections.setdefault(tenant_id, []).append(websocket)
        try:
            while True:
                msg = await websocket.receive_text()
                if msg == "ping":
                    await websocket.send_text("pong")
        except WebSocketDisconnect:
            self.disconnect(tenant_id, websocket)

    def disconnect(self, tenant_id: str, websocket: WebSocket):
        if tenant_id in self.connections:
            if websocket in self.connections[tenant_id]:
                self.connections[tenant_id].remove(websocket)
            if not self.connections[tenant_id]:
                del self.connections[tenant_id]

    async def _worker(self):
        try:
            while True:
                tenant_id, data = await self.queue.get()
                await self._broadcast(tenant_id, data)
                self.queue.task_done()
        except asyncio.CancelledError:
            pass  # Prevent exception when test ends

    async def _broadcast(self, tenant_id: str, data: dict):
        encoded = jsonable_encoder(data)
        to_remove = []

        for ws in self.connections.get(tenant_id, []):
            try:
                await ws.send_json(encoded)
            except Exception:
                to_remove.append(ws)

        for ws in to_remove:
            self.disconnect(tenant_id, ws)

    def broadcast(self, tenant_id: str, data: dict):
        self.queue.put_nowait((tenant_id, data))

    def start_worker(self):
        if not self._worker_started:
            self._worker_task = asyncio.create_task(self._worker())
            self._worker_started = True

    async def shutdown(self):
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass


log_broadcaster = LogBroadcaster()
