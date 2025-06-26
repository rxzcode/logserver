from typing import Dict, List
from fastapi.encoders import jsonable_encoder
from starlette.websockets import WebSocket

class LogBroadcaster:
    def __init__(self):
        # Mapping tenant_id -> list of WebSocket connections
        self.connections: Dict[str, List[WebSocket]] = {}

    async def connect(self, tenant_id: str, websocket: WebSocket):
        await websocket.accept()
        if tenant_id not in self.connections:
            self.connections[tenant_id] = []
        self.connections[tenant_id].append(websocket)

    def disconnect(self, tenant_id: str, websocket: WebSocket):
        if tenant_id in self.connections:
            if websocket in self.connections[tenant_id]:
                self.connections[tenant_id].remove(websocket)
            if not self.connections[tenant_id]:
                del self.connections[tenant_id]

    async def broadcast(self, tenant_id: str, data: dict):
        encoded = jsonable_encoder(data)
        to_remove = []

        for ws in self.connections.get(tenant_id, []):
            try:
                await ws.send_json(encoded)
            except Exception:
                # Possibly disconnected, queue for removal
                to_remove.append(ws)

        for ws in to_remove:
            self.disconnect(tenant_id, ws)

log_broadcaster = LogBroadcaster()