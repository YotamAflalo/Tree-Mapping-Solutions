import os
import sys
from pathlib import Path

# Set test mode and environment variables before imports
os.environ['TEST_MODE'] = 'true'
os.environ['aws_access_key_id'] = 'test_key'
os.environ['aws_secret_access_key'] = 'test_secret'

# Set up path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'src', 'finel_activator'))

import pytest
import json
from unittest.mock import MagicMock, patch

from src.finel_activator.lambda_function import lambda_handler
from src.finel_activator.lambada_custom_logger import log_to_cloudwatch

@pytest.fixture
def sample_s3_event():
    """Create a sample S3 event"""
    return {
        'Records': [{
            's3': {
                'bucket': {
                    'name': 'test-bucket'
                },
                'object': {
                    'key': 'offsets/2024-01-28.json'
                }
            }
        }]
    }

@pytest.fixture
def sample_offsets_data():
    """Create sample offsets data"""
    return {
        'image1.tif': {
            'split1.png': (0, 0),
            'split2.png': (100, 0)
        },
        'image2.tif': {
            'split3.png': (0, 0),
            'split4.png': (100, 0)
        }
    }

@pytest.fixture
def mock_s3_client():
    """Create a mock S3 client"""
    with patch('boto3.client') as mock_boto:
        s3_client = MagicMock()
        mock_boto.return_value = s3_client
        yield s3_client

@pytest.fixture
def mock_logger():
    """Mock the logger"""
    with patch('logging.getLogger') as mock_logger:
        logger = MagicMock()
        mock_logger.return_value = logger
        yield logger

def test_lambda_handler_successful_processing(sample_s3_event, 
                                           sample_offsets_data, mock_s3_client, mock_logger):
    """Test successful processing of offsets file"""
    # Mock S3 get_object response
    mock_s3_client.get_object.return_value = {
        'Body': MagicMock(read=lambda: json.dumps(sample_offsets_data).encode('UTF-8'))
    }

    # Execute lambda handler
    response = lambda_handler(sample_s3_event, None)

    # Verify the response
    assert response['statusCode'] == 200
    assert 'offsets/2024-01-28.json is processed' in response['body']

    # Verify S3 interactions
    mock_s3_client.get_object.assert_called_once_with(
        Bucket='test-bucket',
        Key='offsets/2024-01-28.json'
    )

    # Verify put_object calls (one for each image in the offsets data)
    assert mock_s3_client.put_object.call_count == len(sample_offsets_data)

    # Verify the format of uploaded data
    calls = mock_s3_client.put_object.call_args_list
    for i, (image_name, _) in enumerate(sample_offsets_data.items()):
        call = calls[i]
        args, kwargs = call
        assert kwargs['Bucket'] == 'test-bucket'
        assert kwargs['Key'].startswith('small_offsets/2024-01-28/offsets_')
        uploaded_data = json.loads(kwargs['Body'].decode('UTF-8'))
        assert len(uploaded_data) == 1  # Should contain only one image data
        assert list(uploaded_data.keys())[0] in sample_offsets_data  # Should be one of our original images

def test_lambda_handler_s3_error(sample_s3_event, mock_s3_client, mock_logger):
    """Test handling of S3 get_object error"""
    # Mock S3 get_object to raise an exception
    mock_s3_client.get_object.side_effect = Exception("S3 Error")

    # Execute lambda handler and expect exception
    with pytest.raises(Exception) as exc_info:
        lambda_handler(sample_s3_event, None)
    
    assert str(exc_info.value) == "S3 Error"

def test_log_to_cloudwatch_no_aws_calls():
    """Test log_to_cloudwatch function with mocked AWS client"""
    mock_logs_client = MagicMock()
    response = log_to_cloudwatch(mock_logs_client, "Test message")
    
    # Verify the logs_client was called with correct parameters
    mock_logs_client.put_log_events.assert_called_once()
    call_args = mock_logs_client.put_log_events.call_args[1]
    
    assert call_args['logGroupName'] == 'yotam-finel-log-group'
    assert 'logStreamName' in call_args
    assert len(call_args['logEvents']) == 1
    assert call_args['logEvents'][0]['message'] == "Test message"

@pytest.fixture
def invalid_s3_event():
    """Create an invalid S3 event"""
    return {
        'Records': [{
            's3': {
                'bucket': {},  # Missing name
                'object': {}   # Missing key
            }
        }]
    }

def test_lambda_handler_invalid_event(invalid_s3_event, mock_s3_client, mock_logger):
    """Test handling of invalid S3 event"""
    with pytest.raises(KeyError):
        lambda_handler(invalid_s3_event, None)

def test_lambda_handler_empty_offsets(sample_s3_event, mock_s3_client, mock_logger):
    """Test handling of empty offsets data"""
    # Mock S3 get_object to return empty dict
    mock_s3_client.get_object.return_value = {
        'Body': MagicMock(read=lambda: json.dumps({}).encode('UTF-8'))
    }

    # Execute lambda handler
    response = lambda_handler(sample_s3_event, None)

    # Verify response
    assert response['statusCode'] == 200
    
    # Verify no put_object calls were made
    assert mock_s3_client.put_object.call_count == 0