import boto3
import os
import json
from botocore.config import Config

sqs = boto3.client(
    "sqs",
    endpoint_url=os.getenv("SQS_URL", "http://elasticmq:9324"),
    region_name="us-east-1",
    aws_access_key_id="x",
    aws_secret_access_key="x"
)

queue_url = os.getenv("SQS_QUEUE", "http://elasticmq:9324/queue/log-queue")
sqs.create_queue(QueueName="log-queue")

def sendLog(log: dict):
    sqs.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(log, default=str)
    )