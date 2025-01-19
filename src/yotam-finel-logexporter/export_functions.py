import boto3
import csv
import datetime
from io import StringIO
import json
import os

BUCKET_NAME = "yotam-finel"
AWS_REGION = "us-east-1"
aws_access_key_id = os.environ['aws_access_key_id']
aws_secret_access_key = os.environ['aws_secret_access_key']

def parse_report_log(message, function_name):
    """Parse the REPORT log message into structured data"""
    try:
        parts = message.split('\t')
        data = {
            'function_name': function_name,
            'date': datetime.datetime.now().strftime('%Y-%m-%d')
        }
        
        for part in parts:
            if 'RequestId:' in part:
                data['request_id'] = part.split('RequestId:')[1].strip()
            elif 'Duration:' in part:
                data['duration'] = float(part.split('Duration:')[1].split('ms')[0].strip())
            elif 'Billed Duration:' in part:
                data['billed_duration'] = int(part.split('Billed Duration:')[1].split('ms')[0].strip())
            elif 'Memory Size:' in part:
                data['memory_size'] = int(part.split('Memory Size:')[1].split('MB')[0].strip())
            elif 'Max Memory Used:' in part:
                data['max_memory_used'] = int(part.split('Max Memory Used:')[1].split('MB')[0].strip())
            elif 'Init Duration:' in part:
                data['init_duration'] = float(part.split('Init Duration:')[1].split('ms')[0].strip()) if 'Init Duration:' in message else None
        
        return data
    except Exception as e:
        print(f"Error parsing log message: {str(e)}")
        print(f"Message content: {message}")
        return None

def export_to_s3(reports):
    """Export reports to CSV in S3"""
    if not reports:  # Skip if no reports
        return False
        
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key_id,
            aws_secret_access_key=aws_secret_access_key,
            region_name=AWS_REGION
        )
        
        # Create CSV in memory
        csv_buffer = StringIO()
        fieldnames = ['function_name', 'date', 'request_id', 'duration', 
                     'billed_duration', 'memory_size', 
                     'max_memory_used', 'init_duration']
        
        writer = csv.DictWriter(csv_buffer, fieldnames=fieldnames)
        writer.writeheader()
        
        for report in reports:
            if report is not None:  # Skip any failed parses
                writer.writerow(report)
        
        # Upload to S3
        date_str = datetime.datetime.now().strftime('%Y-%m-%d')
        s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=f'lambda-reports/{date_str}.csv',
            Body=csv_buffer.getvalue()
        )
        return True
        
    except Exception as e:
        print(f"Error exporting to S3: {str(e)}")
        return False

def export_to_sql(reports):
    """Export reports to SQL database"""
    pass  # SQL implementation placeholder