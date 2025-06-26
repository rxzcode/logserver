from fastapi import Request
from fastapi.responses import JSONResponse

async def add_headers_to_request(request: Request, call_next):
    request.state.user_id = request.headers.get("x-auth-sub")
    request.state.tenant_id = request.headers.get("x-auth-tenant")
    request.state.role = request.headers.get("x-auth-role", "viewer")

    if not request.state.user_id or not request.state.tenant_id:
        return JSONResponse(
            status_code=401,
            content={"code": 401, "msg": "Unauthorized", "data": None}
        )

    return await call_next(request)