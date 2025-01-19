import boto3
import csv
import datetime
from io import StringIO
import json
# import pymysql
import os
BUCKET_NAME = "yotam-finel"  # Replace with your actual bucket name
AWS_REGION = "us-east-1"          # Replace with your desired region
aws_access_key_id = os.environ['aws_access_key_id']
aws_secret_access_key = os.environ['aws_secret_access_key']

def parse_report_log(message, function_name):
        """Parse the REPORT log message into structured data"""
        parts = message.split('\t') #mayby change it to "   "
        data = {
            'function_name': function_name,  # Add function name to distinguish between the two,
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
                data['init_duration'] = float(part.split('Init Duration:')[1].split('ms')[0].strip())
        
        return data

def export_to_s3(reports):
    """Export reports to CSV in S3"""
    s3_client = boto3.client('s3',aws_access_key_id=aws_access_key_id,aws_secret_access_key=aws_secret_access_key)
        
    # Create CSV in memory
    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, 
                              fieldnames=['function_name','date', 'request_id', 'duration', 
                                        'billed_duration', 'memory_size', 
                                        'max_memory_used', 'init_duration'])
        
    writer.writeheader()
    for report in reports:
        writer.writerow(report)
            
        # Upload to S3
    date_str = datetime.datetime.now().strftime('%Y-%m-%d')
    s3_client.put_object(
            Bucket=BUCKET_NAME,
            Key=f'lambda-reports/{date_str}.csv',
            Body=csv_buffer.getvalue()
        )

def export_to_sql(reports):
    """Export reports to SQL database"""
    pass
    # conn = pymysql.connect(
    #         host='YOUR_DB_HOST',
    #         user='YOUR_DB_USER',
    #         password='YOUR_DB_PASSWORD',
    #         db='YOUR_DB_NAME'
    #     )
        
    # try:
    #     with conn.cursor() as cursor:
    #         for report in reports:
    #             sql = """INSERT INTO lambda_reports 
    #                     (function_name, request_id, duration, billed_duration, 
    #                      memory_size, max_memory_used, init_duration)
    #                     VALUES (%s, %s, %s, %s, %s, %s, %s)"""
    #             cursor.execute(sql, (
    #                 report['function_name'],
    #                 report['request_id'],
    #                 report['duration'],
    #                 report['billed_duration'],
    #                 report['memory_size'],
    #                 report['max_memory_used'],
    #                 report.get('init_duration', None)
    #             ))
    #     conn.commit()
    # finally:
    #     conn.close()