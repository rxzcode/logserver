from fastapi import FastAPI, WebSocket
from core.middleware import add_headers_to_request
from core.exceptions import register_exception_handlers
from routes import tenants

app = FastAPI()

app.middleware("http")(add_headers_to_request)
register_exception_handlers(app)
app.include_router(tenants.router, prefix="/api/v1/tenants")