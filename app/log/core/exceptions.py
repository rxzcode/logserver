from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi import FastAPI, Request, status

def register_exception_handlers(app: FastAPI):
    @app.exception_handler(StarletteHTTPException)
    async def custom_http_exception_handler(request: Request, exc: StarletteHTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"code": exc.status_code, "msg": exc.detail, "data": None}
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        def sanitize_error(err):
            return {
                "loc": err.get("loc"),
                "msg": str(err.get("msg")),
                "type": str(err.get("type"))
            }

        sanitized_errors = [sanitize_error(err) for err in exc.errors()]
        code = status.HTTP_422_UNPROCESSABLE_ENTITY
        return JSONResponse(
            status_code=code,
            content={"code": code, "msg": "Validation error", "data": sanitized_errors}
        )