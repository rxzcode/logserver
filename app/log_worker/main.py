from fastapi import FastAPI
import boto3
import json
import asyncio
import os
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Dict

# Setup FastAPI app
app = FastAPI()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("log-worker")

# MongoDB setup
mongo_uri = os.getenv("MONGODB_URI", "mongodb://mongodb:27017")
mongo = AsyncIOMotorClient(mongo_uri)
collection = mongo.logdb.logs

# SQS setup
sqs = boto3.client(
    "sqs",
    endpoint_url=os.getenv("SQS_URL", "http://elasticmq:9324"),
    region_name="us-east-1",
    aws_access_key_id="x",  # local dev dummy values
    aws_secret_access_key="x"
)
queue_url = os.getenv("SQS_QUEUE", "http://elasticmq:9324/queue/log-queue")

# Stats store
stats: Dict[str, any] = {
    "messages_received": 0,
    "messages_failed": 0,
    "last_received_at": None,
}


@app.on_event("startup")
async def start_workers():
    # Worker 1: Poll and process messages from SQS
    async def poll_sqs():
        logger.info("Starting SQS poller...")
        while True:
            try:
                res = sqs.receive_message(
                    QueueUrl=queue_url,
                    MaxNumberOfMessages=10,
                    WaitTimeSeconds=20,
                    VisibilityTimeout=30,
                    MessageAttributeNames=["All"],
                )

                messages = res.get("Messages", [])
                if not messages:
                    continue

                logs = []
                receipt_handle_to_log = {}

                for msg in messages:
                    try:
                        body = json.loads(msg["Body"])
                        logs.append(body)
                        receipt_handle_to_log[msg["ReceiptHandle"]] = body
                    except Exception as e:
                        stats["messages_failed"] += 1
                        logger.warning(f"Failed to parse message: {e}")

                success_receipts = []

                if logs:
                    try:
                        result = await collection.insert_many(logs, ordered=False)
                        inserted_logs = set(result.inserted_ids)
                        stats["messages_received"] += len(inserted_logs)
                        stats["last_received_at"] = datetime.utcnow().isoformat()

                        # Match inserted logs back to their receipt handles
                        for handle, log in receipt_handle_to_log.items():
                            # Only delete if inserted; assumes no _id before insert
                            # If _id is not user-set, we can't match inserted_ids to logs
                            # So assume success = all logs inserted
                            success_receipts.append(handle)

                        # Delete successfully inserted messages
                        if success_receipts:
                            entries = [{"Id": str(i), "ReceiptHandle": h} for i, h in enumerate(success_receipts)]
                            sqs.delete_message_batch(QueueUrl=queue_url, Entries=entries)

                    except Exception as e:
                        stats["messages_failed"] += len(logs)
                        logger.error(f"Mongo insert failed: {e}")

            except Exception as e:
                logger.error(f"SQS polling error: {e}")
                await asyncio.sleep(5)

    # Worker 2: Print stats every 5s
    async def print_stats():
        while True:
            logger.info(f"Stats: {json.dumps(stats)}")
            await asyncio.sleep(5)

    asyncio.create_task(poll_sqs())
    asyncio.create_task(print_stats())


@app.get("/healthz")
def health():
    return {"status": "ok"}


@app.get("/stats")
def get_stats():
    return stats
