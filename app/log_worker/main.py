from fastapi import FastAPI
import boto3
import json
import asyncio
import os
import logging
import clickhouse_connect
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime
from typing import Dict, List, Any

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
    aws_access_key_id="x",
    aws_secret_access_key="x"
)
queue_url = os.getenv("SQS_QUEUE", "http://elasticmq:9324/queue/log-queue")

# ClickHouse setup
clickhouse_host = os.getenv("CLICKHOUSE_HOST", "disabled")
clickhouse_enabled = clickhouse_host.lower() != "disabled"
client = None
if clickhouse_enabled:
    client = clickhouse_connect.get_client(
        host=clickhouse_host,
        port=int(os.getenv("CLICKHOUSE_PORT", 8123)),
        username=os.getenv("CLICKHOUSE_USER"),
        password=os.getenv("CLICKHOUSE_PASSWORD"),
        database=os.getenv("CLICKHOUSE_DATABASE", "default")
    )

# Stats store
stats: Dict[str, Any] = {
    "messages_received": 0,
    "messages_failed": 0,
    "last_received_at": None,
}


@app.on_event("startup")
async def start_workers():
    ensure_sqs_queue()
    if clickhouse_enabled:
        ensure_clickhouse_database_and_table()

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
                        stats["messages_received"] += len(result.inserted_ids)
                        stats["last_received_at"] = datetime.utcnow().isoformat()

                        for handle in receipt_handle_to_log:
                            success_receipts.append(handle)

                        if clickhouse_enabled:
                            insert_into_clickhouse(logs)

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
@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/stats")
def get_stats():
    return stats


def insert_into_clickhouse(logs: List[Dict[str, Any]]):
    if not clickhouse_enabled or not client:
        return

    try:
        rows = []
        for log in logs:
            rows.append((
                log.get("id", ""),
                log.get("tenant_id", ""),
                log.get("user_id", ""),
                log.get("action", ""),
                log.get("resource_type", ""),
                log.get("resource_id", ""),
                datetime.fromisoformat(log.get("timestamp").replace("Z", "+00:00")) if isinstance(log.get("timestamp"), str) else log.get("timestamp"),
                log.get("ip_address"),
                log.get("user_agent"),
                json.dumps(log.get("before")) if log.get("before") else None,
                json.dumps(log.get("after")) if log.get("after") else None,
                json.dumps(log.get("metadata")) if log.get("metadata") else None,
                log.get("severity", "")
            ))

        client.insert(
            table="logdb.logs",
            data=rows,
            column_names=[
                "id", "tenant_id", "user_id", "action", "resource_type", "resource_id",
                "timestamp", "ip_address", "user_agent", "before", "after", "metadata", "severity"
            ]
        )
    except Exception as e:
        logger.error(f"ClickHouse insert failed: {e}")
        stats["messages_failed"] += len(logs)


def ensure_clickhouse_database_and_table():
    if not clickhouse_enabled or not client:
        return

    try:
        client.command("CREATE DATABASE IF NOT EXISTS logdb")
        logger.info("ClickHouse database 'logdb' ensured.")

        client.command("""
        CREATE TABLE IF NOT EXISTS logdb.logs (
            id String,
            tenant_id String,
            user_id String,
            action String,
            resource_type String,
            resource_id String,
            timestamp DateTime,
            ip_address Nullable(String),
            user_agent Nullable(String),
            before Nullable(String),
            after Nullable(String),
            metadata Nullable(String),
            severity String
        )
        ENGINE = MergeTree
        ORDER BY (tenant_id, timestamp)
        """)
        logger.info("ClickHouse table 'logdb.logs' ensured.")
    except Exception as e:
        logger.error(f"Failed to ensure ClickHouse DB/table: {e}")


def ensure_sqs_queue():
    try:
        response = sqs.create_queue(QueueName="log-queue")
        global queue_url
        queue_url = response['QueueUrl']
        logger.info(f"SQS queue ensured: {queue_url}")
    except Exception as e:
        logger.error(f"Failed to create/verify SQS queue: {e}")
