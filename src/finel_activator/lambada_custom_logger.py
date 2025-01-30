import boto3
from datetime import datetime
import sys
import os

log_group_name = 'yotam-finel-log-group'
BUCKET_NAME = "yotam-finel"  # Replace with your actual bucket name
AWS_REGION = "us-east-1"          # Replace with your desired region

# Add test mode flag
is_test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'

if not is_test_mode:
    aws_access_key_id = os.environ['aws_access_key_id']
    aws_secret_access_key = os.environ['aws_secret_access_key']
    logs_client = boto3.client('logs', region_name=AWS_REGION,
                                      aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
    try:
        logs_client.create_log_group(logGroupName=log_group_name)
    except logs_client.exceptions.ResourceAlreadyExistsException:
        pass

    # Create log stream if it doesn't exist
    try:
        log_stream_name = f'lambada-activator-{datetime.now().strftime("%Y-%m-%d")}'
        logs_client.create_log_stream(logGroupName=log_group_name, logStreamName=log_stream_name)
    except logs_client.exceptions.ResourceAlreadyExistsException:
        pass
else:
    # Mock client for test mode
    from unittest.mock import MagicMock
    logs_client = MagicMock()
    log_stream_name = f'lambada-activator-{datetime.now().strftime("%Y-%m-%d")}'

def log_to_cloudwatch(logs_client, message):
    timestamp = int(datetime.now().timestamp() * 1000) # Current time.
    log_event = {
    'logGroupName': log_group_name,
    'logStreamName': log_stream_name,
    'logEvents': [
        {
            'timestamp': timestamp,
            'message': message
        }
    ]}
    response = logs_client.put_log_events(**log_event)
    return response