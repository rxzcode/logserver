from fastapi import FastAPI, WebSocket
from routes import logs

from core.middleware import add_headers_to_request
from core.exceptions import register_exception_handlers
from core.broadcast import log_broadcaster
from core.queue import init_sqs_client_and_queue
from core.database import ensure_indexes

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    await ensure_indexes()
    init_sqs_client_and_queue()
    log_broadcaster.start_worker()

app.middleware("http")(add_headers_to_request)
register_exception_handlers(app)
app.include_router(logs.router, prefix="/api/v1/logs")

print("New code")