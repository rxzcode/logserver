from fastapi import APIRouter, Request, HTTPException, status
from uuid import uuid4
from typing import List
from datetime import datetime
import hashlib

from core.database import tenants as col
from core.utils import clean

from models.tenants import TenantEntry, Tenant, ResponseWrapper

router = APIRouter()

@router.get(
    "",
    response_model=ResponseWrapper[List[Tenant]],
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "List of tenants"}}
)
async def list_tenants(request: Request):
    cursor = col.find({})
    tenants = [clean(doc) async for doc in cursor]
    return ResponseWrapper(code=200, msg="ok", data=tenants)

@router.post(
    "",
    response_model=ResponseWrapper[Tenant],
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Tenant created"},
        400: {"description": "Tenant key already exists"},
    }
)
async def create_tenant(tenant: TenantEntry, request: Request):
    doc = tenant.model_dump()
    doc["created_at"] = datetime.utcnow()

    # Check uniqueness of key
    existing = await col.find_one({"key": doc["key"]})
    if existing:
        raise HTTPException(status_code=400, detail="Tenant key already exists")

    # Generate secret as MD5 of key + "secret"
    doc["secret"] = hashlib.md5((doc["key"] + "secret").encode("utf-8")).hexdigest()

    await col.insert_one(doc)
    return ResponseWrapper(code=200, msg="ok", data=clean(doc))