import boto3
import logging
from datetime import datetime
import sys
from pathlib import Path
import os

project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from logger import logger
from config.config_aws import  AWS_REGION, log_group_name
import dotenv
dotenv.load_dotenv()

logs_client = boto3.client('logs', region_name=AWS_REGION,
                                      aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))

try:
    logs_client.create_log_group(logGroupName=log_group_name)
except logs_client.exceptions.ResourceAlreadyExistsException:
    pass

# Create log stream if it doesn't exist
try:
    log_stream_name = f'yotam-finel-mlops-log-stream-{datetime.now().strftime("%Y-%m-%d")}'
    logs_client.create_log_stream(logGroupName=log_group_name, logStreamName=log_stream_name)
except logs_client.exceptions.ResourceAlreadyExistsException:
    pass

# response = logs_client.describe_log_streams(logGroupName=log_group_name, logStreamNamePrefix=log_stream_name)
# upload_sequence_token = response['logStreams'][0].get('uploadSequenceToken', None)
# if upload_sequence_token:
#     log_event['sequenceToken'] = upload_sequence_token



def log_to_cloudwatch(logs_client, message):
    """
    Sends a log message to AWS CloudWatch with current timestamp.
    Args:
        logs_client: boto3 CloudWatch logs client
        message: str, message to be logged
        
    Returns:
        dict: AWS CloudWatch API response
    """
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