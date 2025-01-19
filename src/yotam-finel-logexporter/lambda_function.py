import boto3
import csv
import datetime
from io import StringIO
import json
# import pymysql
from export_functions import parse_report_log, export_to_s3
def lambda_handler(event, context):
    # Initialize CloudWatch Logs client
    logs_client = boto3.client('logs')
    
    # Get yesterday's date range
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(days=1)
    
    # Convert to milliseconds timestamp
    start_ts = int(start_time.timestamp() * 1000)
    end_ts = int(end_time.timestamp() * 1000)
    
    # Specific log groups to monitor
    LOG_GROUPS = [
        '/aws/lambda/yotam-finel-model',
        '/aws/lambda/yotam-finel-activator'
    ]
    
    

    # Collect reports from specified log groups
    all_reports = []
    
    for log_group_name in LOG_GROUPS:
        # Extract function name from log group
        function_name = log_group_name.split('/')[-1]
        
        # Query for REPORT logs
        query = "fields @timestamp, @message | filter @message like 'REPORT'"
        
        query_response = logs_client.start_query(
            logGroupName=log_group_name,
            startTime=start_ts,
            endTime=end_ts,
            queryString=query
        )
        
        # Wait for query to complete and get results
        query_id = query_response['queryId']
        results = None
        while results is None or results['status'] == 'Running':
            results = logs_client.get_query_results(queryId=query_id)
            
        # Parse each report log
        for result in results.get('results', []):
            message = next(field['value'] for field in result if field['field'] == '@message')
            parsed_report = parse_report_log(message, function_name)
            all_reports.append(parsed_report)
    
    # Export the collected reports (uncomment the desired export method)
    export_to_s3(all_reports)
    # export_to_sql(all_reports)
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Processed {len(all_reports)} reports',
            'reports_by_function': {
                'yotam-finel-model': len([r for r in all_reports if r['function_name'] == 'yotam-finel-model']),
                'yotam-finel-activator': len([r for r in all_reports if r['function_name'] == 'yotam-finel-activator'])
            }
        })
    }