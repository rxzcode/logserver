from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from routes import auth

app = FastAPI()

# Custom error handler
@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.status_code, "msg": str(exc.detail), "data": None}
    )

# Register routes
app.include_router(auth.router)
