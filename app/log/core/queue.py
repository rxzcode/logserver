import boto3
import os
import json
from botocore.config import Config
from botocore.exceptions import ClientError

# Config
SQS_URL = os.getenv("SQS_URL", "http://elasticmq:9324")
QUEUE_NAME = os.getenv("SQS_QUEUE_NAME", "log-queue")

# Singleton holders
_sqs_client = None
_queue_url = None

def init_sqs_client_and_queue():
    global _sqs_client, _queue_url

    if _sqs_client is not None and _queue_url is not None:
        return  # Already initialized

    _sqs_client = boto3.client(
        "sqs",
        endpoint_url=SQS_URL,
        region_name="us-east-1",
        aws_access_key_id="x",
        aws_secret_access_key="x",
        config=Config(retries={"max_attempts": 0})
    )

    try:
        response = _sqs_client.get_queue_url(QueueName=QUEUE_NAME)
        _queue_url = response["QueueUrl"]
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ("AWS.SimpleQueueService.NonExistentQueue", "QueueDoesNotExist"):
            # Fallback: create the queue
            response = _sqs_client.create_queue(
                QueueName=QUEUE_NAME,
                Attributes={
                    "VisibilityTimeout": "30"
                }
            )
            _queue_url = response["QueueUrl"]
        else:
            raise

def sendLog(log: dict):
    _sqs_client.send_message(
        QueueUrl=_queue_url,
        MessageBody=json.dumps(log, default=str)
    )
