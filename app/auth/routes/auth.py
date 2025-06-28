import hashlib
import base64
import json
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel
import jwt

router = APIRouter()
SECRET = "secret"


class TokenPayload(BaseModel):
    sub: str
    tenant: str
    role: str = "viewer"
    aud: str = "logserver"
    iss: str = "issuer"


@router.get("/auth/{full_path:path}")
async def validate_token(request: Request):
    auth = request.headers.get("Authorization")
    path = request.headers.get("x-auth-request-redirect", "")
    token = None

    if auth and auth.startswith("Bearer "):
        token = auth[7:]
    else:
        token = request.query_params.get("token")

    unverified_payload = extract_unverified_claims(token)
    tenant_id = unverified_payload.get("tenant")
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Missing tenant claim")

    try:
        secret = hashlib.md5((tenant_id + SECRET).encode("utf-8")).hexdigest()
        payload = jwt.decode(token, secret, algorithms=["HS256"], audience="logserver", issuer="issuer")
        user_id = payload.get("sub")
        tenant_id = payload.get("tenant")
        role = payload.get("role")

        if not user_id or not tenant_id:
            raise HTTPException(status_code=401, detail="Missing required claims")

        check_rbac(path, role)

        response = Response(status_code=200)
        response.headers["x-auth-sub"] = user_id
        response.headers["x-auth-tenant"] = tenant_id
        response.headers["x-auth-role"] = role or "viewer"

        return response
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.get("/")
def custom_401():
    return JSONResponse(status_code=401, content={"code": 401, "msg": "Unauthorized"})


def check_rbac(path: str, role: str):
    if path.startswith("/api/v1/tenant") and role != "admin":
        raise HTTPException(status_code=401, detail="Admin role required")


def extract_unverified_claims(token: str) -> dict:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            raise ValueError("Malformed token")
        payload_b64 = parts[1] + '=='  # add padding
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        return json.loads(payload_bytes)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token format")