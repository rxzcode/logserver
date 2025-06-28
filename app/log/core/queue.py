import boto3
import os
import json
from botocore.config import Config

# Config
SQS_URL = os.getenv("SQS_URL", "http://elasticmq:9324")
QUEUE_NAME = os.getenv("SQS_QUEUE_NAME", "log-queue")
QUEUE_URL = f"{SQS_URL}/queue/{QUEUE_NAME}"

# Singleton holder
_sqs_client = None

def get_sqs_client():
    global _sqs_client
    if _sqs_client is None:
        _sqs_client = boto3.client(
            "sqs",
            endpoint_url=SQS_URL,
            region_name="us-east-1",
            aws_access_key_id="x",
            aws_secret_access_key="x",
            config=Config(retries={"max_attempts": 0})  # optional: disable retry noise
        )
    return _sqs_client

def sendLog(log: dict):
    sqs = get_sqs_client()
    sqs.send_message(
        QueueUrl=QUEUE_URL,
        MessageBody=json.dumps(log, default=str)
    )