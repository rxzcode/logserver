import pytest
import asyncio
from unittest.mock import AsyncMock, patch

from starlette.websockets import WebSocketDisconnect
from core.broadcast import LogBroadcaster  # adjust import as needed


@pytest.fixture
async def broadcaster():
    b = LogBroadcaster()
    yield b
    await b.shutdown()

@pytest.mark.asyncio
async def test_connect_and_disconnect(broadcaster):
    websocket = AsyncMock()
    websocket.receive_text = AsyncMock(side_effect=[WebSocketDisconnect()])
    tenant_id = "tenant1"

    await broadcaster.connect(tenant_id, websocket)

    assert tenant_id not in broadcaster.connections


@pytest.mark.asyncio
async def test_ping_pong(broadcaster):
    websocket = AsyncMock()
    websocket.receive_text = AsyncMock(side_effect=["ping", WebSocketDisconnect()])
    websocket.send_text = AsyncMock()
    tenant_id = "tenant1"

    await broadcaster.connect(tenant_id, websocket)

    websocket.send_text.assert_called_with("pong")
    assert tenant_id not in broadcaster.connections


@pytest.mark.asyncio
async def test_broadcast_message(broadcaster):
    websocket = AsyncMock()
    tenant_id = "tenant1"
    data = {"message": "hello"}

    # Manually add websocket to connections
    broadcaster.connections[tenant_id] = [websocket]

    await broadcaster._broadcast(tenant_id, data)

    websocket.send_json.assert_called_once_with({"message": "hello"})


@pytest.mark.asyncio
async def test_broadcast_exception_removes_ws(broadcaster):
    bad_ws = AsyncMock()
    good_ws = AsyncMock()
    bad_ws.send_json = AsyncMock(side_effect=Exception("fail"))
    good_ws.send_json = AsyncMock()
    tenant_id = "tenant1"
    data = {"event": "log"}

    broadcaster.connections[tenant_id] = [bad_ws, good_ws]

    await broadcaster._broadcast(tenant_id, data)

    assert broadcaster.connections[tenant_id] == [good_ws]


@pytest.mark.asyncio
async def test_queue_worker_processes_broadcast(broadcaster):
    websocket = AsyncMock()
    tenant_id = "tenant1"
    data = {"msg": "queued"}

    broadcaster.connections[tenant_id] = [websocket]

    broadcaster.start_worker()
    broadcaster.broadcast(tenant_id, data)

    await asyncio.sleep(0.1)  # allow processing
    await broadcaster.shutdown()  # stop the worker

    websocket.send_json.assert_called_once_with({"msg": "queued"})


@pytest.mark.asyncio
async def test_start_worker_idempotent():
    broadcaster = LogBroadcaster()

    # Patch _worker so it won't run forever
    async def dummy_worker():
        await asyncio.sleep(0.1)

    with patch.object(broadcaster, "_worker", dummy_worker):
        broadcaster.start_worker()
        broadcaster.start_worker()

        # Check that only one task was created
        assert broadcaster._worker_started is True
        task1 = broadcaster._worker_task

        # Allow dummy_worker to complete
        await asyncio.sleep(0.2)
        await broadcaster.shutdown()
        assert broadcaster._worker_task is task1