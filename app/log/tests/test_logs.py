import pytest
from unittest.mock import patch, AsyncMock
from fastapi import status
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request

from routes.logs import router

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
@patch("routes.logs.collection.find")
@pytest.mark.asyncio
async def test_get_logs(mock_find, client):
    mock_find.return_value = AsyncCursor([msg_response, msg_response])
    res = client.get("/logs")
    assert res.status_code == 200
    assert isinstance(res.json()["data"], list)


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