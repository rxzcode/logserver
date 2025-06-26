import hashlib
from pydantic import BaseModel
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import Response, JSONResponse
import jwt
import base64
import json

app = FastAPI()
SECRET = "secret"

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == 401:
        return JSONResponse(
            status_code=401,
            content={"code": 401, "msg": str(exc.detail), "data": None}
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "msg": str(exc.detail), "data": None}
    )

@app.get("/auth/{full_path:path}")
async def validate_token(request: Request):
    auth = request.headers.get("Authorization")
    path = request.headers.get("x-auth-request-redirect", "")
    token = None

    # Bypass
    if auth and auth.startswith("Bearer "):
        token = auth[7:]
    else:
        token = request.query_params.get("token")

    # Decode only payload to get tenant
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
            print("❌ Token missing required claims. sub:", user_id, "tenant:", tenant_id)
            raise HTTPException(status_code=401, detail="Missing required claims")

        check_rbac(path, role)

        # Build response with headers
        response = Response(status_code=200)
        response.headers["x-auth-sub"] = user_id
        response.headers["x-auth-tenant"] = tenant_id
        response.headers["x-auth-role"] = role or "viewer"

        return response
    except jwt.ExpiredSignatureError:
        print("❌ Token has expired:", token)
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        print("❌ Invalid token:", token, "🔍 Decode error:", str(e))
        raise HTTPException(status_code=401, detail="Invalid token")

class TokenPayload(BaseModel):
    sub: str
    tenant: str
    role: str = "viewer"
    aud: str = "logserver"
    iss: str = "issuer"

@app.post("/auth/token")
async def get_token(payload: TokenPayload):
    try:
        claims = {
            "sub": payload.sub,
            "tenant": payload.tenant,
            "role": payload.role,
            "aud": payload.aud,
            "iss": payload.iss,
            # "exp": datetime.utcnow() + timedelta(hours=1)  # token expires in 1 hour
        }
        token = jwt.encode(claims, SECRET, algorithm="HS256")
        return {"token": token}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token format")
