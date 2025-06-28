import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi import status
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect, WebSocketState
from fastapi import FastAPI, Request, WebSocket

from routes.logs import router
from core.broadcast import log_broadcaster

# Setup FastAPI test app with required middleware
app = FastAPI()

@app.middleware("http")
async def add_state(request: Request, call_next):
    request.state.user_id = "test-user"
    request.state.tenant_id = "test-tenant"
    return await call_next(request)

app.include_router(router, prefix="/logs")

@pytest.fixture
def client():
    return TestClient(app)

msg = {
    "action": "update",
    "resource_type": "product",
    "resource_id": "abc-456",
    "ip_address": "127.0.0.1",
    "user_agent": "pytest-agent",
    "before": {"name": "Old"},
    "after": {"name": "New"},
    "metadata": {"source": "unittest"},
    "severity": "WARNING"
}

msg_response = {
    "id": "log-1",
    "user_id": "test-user",
    "tenant_id": "test-tenant",
    "action": "update",
    "resource_type": "product",
    "resource_id": "abc-456",
    "ip_address": "127.0.0.1",
    "user_agent": "pytest-agent",
    "before": {"name": "Old"},
    "after": {"name": "New"},
    "metadata": {"source": "unittest"},
    "severity": "WARNING",
    "timestamp": "2024-01-01T00:00:00Z"
}

# --- POST /logs ---
@patch("routes.logs.sendLog")
@patch("routes.logs.log_broadcaster.broadcast")
def test_create_log(mock_broadcast, mock_sendLog, client):
    payload = msg
    res = client.post("/logs", json=payload)
    assert res.status_code == 200
    assert res.json()["code"] == 200
    assert res.json()["msg"] == "ok"
    mock_sendLog.assert_called_once()
    mock_broadcast.assert_called_once()


# --- POST /logs/bulk ---
@patch("routes.logs.sendLog")
@patch("routes.logs.log_broadcaster.broadcast")
def test_bulk_create(mock_broadcast, mock_sendLog, client):
    payload = [msg, msg]
    res = client.post("/logs/bulk", json=payload)
    assert res.status_code == 200
    assert len(res.json()["data"]) == 2
    assert mock_sendLog.call_count == 2
    assert mock_broadcast.call_count == 2


# --- GET /logs ---
@pytest.fixture
def mock_motor_cursor():
    # This mock will simulate the chained calls: find().sort().skip().limit()
    mock_cursor = MagicMock()
    mock_cursor.sort.return_value = mock_cursor
    mock_cursor.skip.return_value = mock_cursor
    mock_cursor.limit.return_value = mock_cursor
    mock_cursor.__aiter__.return_value = [
        msg_response,
        msg_response,
    ]
    return mock_cursor

_client = TestClient(app)
@patch("routes.logs.collection")
def test_get_logs(mock_collection, mock_motor_cursor):
    app.dependency_overrides = {}
    mock_collection.find.return_value = mock_motor_cursor
    mock_collection.count_documents = AsyncMock(return_value=2)

    headers = {"x-auth-tenant": "tenant123"}
    response = _client.get("/logs", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert len(data["data"]) == 2
    assert data["meta"]["total"] == 2
    assert data["meta"]["pages"] == 1

    mock_collection.find.assert_called_once()
    mock_collection.count_documents.assert_awaited_once()

@patch("routes.logs.collection")
def test_get_logs_search(mock_collection, mock_motor_cursor):
    app.dependency_overrides = {}
    mock_collection.find.return_value = mock_motor_cursor
    mock_collection.count_documents = AsyncMock(return_value=2)

    headers = {"x-auth-tenant": "tenant123"}
    response = _client.get("/logs?severity=ERROR&search=login", headers=headers)

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert len(data["data"]) == 2
    assert data["meta"]["total"] == 2
    assert data["meta"]["pages"] == 1

    mock_collection.find.assert_called_once()
    mock_collection.count_documents.assert_awaited_once()

# --- GET /logs/stats ---
@patch("routes.logs.collection")
@pytest.mark.asyncio
async def test_log_stats(mock_collection, client):
    mock_agg_cursor = AsyncMock()
    mock_agg_cursor.to_list.return_value = [
        {"_id": "info", "count": 10},
        {"_id": "warning", "count": 5},
    ]
    mock_collection.aggregate.return_value = mock_agg_cursor

    res = client.get("/logs/stats")

    assert res.status_code == 200
    assert res.json()["data"] == {"info": 10, "warning": 5}
    mock_collection.aggregate.assert_called_once()
    mock_agg_cursor.to_list.assert_called_once_with(length=10)

# --- GET /logs/{log_id} ---
@patch("routes.logs.clean")
@patch("routes.logs.collection.find_one", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_get_log(mock_find_one, mock_clean, client):
    mock_find_one.return_value = msg_response
    mock_clean.side_effect = lambda doc: doc
    res = client.get("/logs/abc-id")
    assert res.status_code == 200

@patch("routes.logs.collection.find_one", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_get_log_not_found(mock_find_one, client):
    mock_find_one.return_value = None
    res = client.get("/logs/not-found")
    assert res.status_code == 404


# --- DELETE /logs/cleanup ---
@patch("routes.logs.collection.delete_many", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_cleanup_logs(mock_delete_many, client):
    mock_delete_many.return_value.deleted_count = 5
    res = client.delete("/logs/cleanup")
    assert res.status_code == 200
    assert res.json()["data"]["deleted_count"] == 5
    mock_delete_many.assert_called_once_with({"tenant_id": "test-tenant"})


# --- WEBSOCKET /stream ---
# Define test client directly
_client = TestClient(app)
@patch("routes.logs.log_broadcaster.connect", new_callable=AsyncMock)
@patch("routes.logs.log_broadcaster.disconnect", new_callable=AsyncMock)
def test_websocket_missing_tenant_header(mock_disconnect, mock_connect):
    with pytest.raises(WebSocketDisconnect) as exc_info:
        with _client.websocket_connect("/logs/stream", headers={"x-auth-role": "admin"}) as ws:
            ws.send_text("should not work")
    assert exc_info.value.code == 4001
    mock_connect.assert_not_called()
    mock_disconnect.assert_not_called()

class AsyncCursor:
    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        self.iter = iter(self.items)
        return self

    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration:
            raise StopAsyncIteration