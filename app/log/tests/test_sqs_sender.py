from unittest.mock import patch, MagicMock, ANY
import core.queue as queue
import json


@patch("core.queue.boto3.client")
def test_send_log(mock_boto_client):
    # Arrange
    mock_sqs = MagicMock()
    mock_boto_client.return_value = mock_sqs
    test_log = {"message": "test log"}

    # Act
    queue._sqs_client = None  # Reset singleton
    queue.sendLog(test_log)

    # Assert
    mock_boto_client.assert_called_once_with(
        "sqs",
        endpoint_url=queue.SQS_URL,
        region_name="us-east-1",
        aws_access_key_id="x",
        aws_secret_access_key="x",
        config=ANY  # Skip strict comparison of Config
    )

    mock_sqs.send_message.assert_called_once_with(
        QueueUrl=queue.QUEUE_URL,
        MessageBody=json.dumps(test_log, default=str)
    )
