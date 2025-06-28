from pymongo import DESCENDING
from fastapi import APIRouter, Request, HTTPException, Query, WebSocket, WebSocketDisconnect, status
from uuid import uuid4
from typing import List, Optional, Dict
from datetime import datetime

from core.broadcast import log_broadcaster
from core.database import logs as collection
from core.utils import clean
from core.queue import sendLog
from models.logs import ResponseWrapper, Log, LogEntry, Severity

router = APIRouter()

@router.post(
    "",
    response_model=ResponseWrapper[Log],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Log created"},
        422: {"description": "Validation failed"}
    }
)
async def create_log(entry: LogEntry, request: Request):
    log = entry.model_dump()
    log.update({
        "id": str(uuid4()),
        "user_id": request.state.user_id,
        "tenant_id": request.state.tenant_id
    })
    reslog = clean(log)
    sendLog(reslog)
    log_broadcaster.broadcast(request.state.tenant_id, reslog)
    return ResponseWrapper(code=200, msg="ok", data=reslog)

@router.post(
    "/bulk",
    response_model=ResponseWrapper[List[Log]],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Logs created"},
        422: {"description": "Validation failed"}
    }
)
async def bulk_create(entries: List[LogEntry], request: Request):
    tenant_id = request.state.tenant_id
    user_id = request.state.user_id
    now = datetime.utcnow()
    logs = [
        {
            **entry.model_dump(),
            "id": str(uuid4()),
            "user_id": user_id,
            "tenant_id": tenant_id,
            "timestamp": now
        }
        for entry in entries
    ]
    # await collection.insert_many(logs)
    reslogs = []
    for log in logs:
        cleaned = clean(log)
        sendLog(cleaned)
        reslogs.append(cleaned)
        log_broadcaster.broadcast(tenant_id, cleaned)
    return ResponseWrapper(code=200, msg="ok", data=reslogs)

@router.get(
    "",
    response_model=ResponseWrapper[List[Log]],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Logs fetched"},
        422: {"description": "Validation failed"}
    }
)
async def get_logs(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(50, ge=1, le=100),
    search: Optional[str] = None,
):
    query = {"tenant_id": request.state.tenant_id}

    # Optional search across text fields
    if search:
        regex = {"$regex": search, "$options": "i"}
        query["$or"] = [
            {"action": regex},
            {"resource_type": regex},
            {"resource_id": regex},
            {"ip_address": regex},
            {"user_agent": regex},
            {"metadata": regex},
            {"before": regex},
            {"after": regex},
        ]

    cursor = collection.find(query).sort("timestamp", DESCENDING)
    total = await collection.count_documents(query)
    cursor.skip((page - 1) * size).limit(size)
    logs = [clean(doc) async for doc in cursor]

    return ResponseWrapper(
        code=200,
        msg="ok",
        data=logs,
        meta={
            "total": total,
            "page": page,
            "size": size,
            "pages": (total + size - 1) // size
        }
    )

@router.get("/stats",
    response_model=ResponseWrapper[Dict[str, int]],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Logs created"},
        422: {"description": "Validation failed"}
    }
)
async def log_stats(request: Request):
    pipeline = [
        {"$match": {"tenant_id": request.state.tenant_id}},
        {"$group": {"_id": "$severity", "count": {"$sum": 1}}}
    ]
    stats = await collection.aggregate(pipeline).to_list(length=10)
    formatted = {item["_id"] or "UNKNOWN": item["count"] for item in stats}
    return ResponseWrapper(code=200, msg="ok", data=formatted)

@router.get(
    "/{log_id}",
    response_model=ResponseWrapper[Log],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Log created"},
        404: {"description": "Log not found"},
        422: {"description": "Validation failed"}
    }
)
async def get_log(log_id: str, request: Request):
    log = await collection.find_one({"id": log_id, "tenant_id": request.state.tenant_id})
    if not log:
        raise HTTPException(status_code=404, detail="Log not found")
    return ResponseWrapper(code=200, msg="ok", data=clean(log))

@router.delete(
    "/cleanup",
    response_model=ResponseWrapper[Dict[str, int]],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Log created"}
    }
)
async def cleanup_logs(request: Request):
    result = await collection.delete_many({
        "tenant_id": request.state.tenant_id,
    })
    return ResponseWrapper(code=200, msg="ok", data={"deleted_count": result.deleted_count})


@router.websocket("/stream")
async def log_stream(ws: WebSocket):
    tenant_id = ws.headers.get("x-auth-tenant")
    if not tenant_id:
        await ws.close(code=4001)
        return
    await log_broadcaster.connect(tenant_id, ws)