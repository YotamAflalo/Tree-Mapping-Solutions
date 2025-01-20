import boto3
import datetime
import json
from export_functions import parse_report_log, export_to_s3

def lambda_handler(event, context):
    # Initialize CloudWatch Logs client
    logs_client = boto3.client('logs')
    
    # Get yesterday's date range
    end_time = datetime.datetime.now()
    start_time = end_time - datetime.timedelta(days=1)
    date_str = start_time.strftime('%Y-%m-%d')
    
    # Convert to milliseconds timestamp
    start_ts = int(start_time.timestamp() * 1000)
    end_ts = int(end_time.timestamp() * 1000)
    
    # Specific log groups to monitor
    LOG_GROUPS = [
        '/aws/lambda/yotam-finel-model',
        '/aws/lambda/final-activator'
    ]
    
    # Collect reports from specified log groups
    all_reports = []
    
    for log_group_name in LOG_GROUPS:
        function_name = log_group_name.split('/')[-1]
        
        try:
            # Use filterLogEvents instead of StartQuery
            paginator = logs_client.get_paginator('filter_log_events')
            
            for page in paginator.paginate(
                logGroupName=log_group_name,
                startTime=start_ts,
                endTime=end_ts,
                filterPattern='REPORT'
            ):
                for event in page['events']:
                    if 'REPORT' in event['message']:
                        parsed_report = parse_report_log(event['message'], function_name)
                        if parsed_report:  # Only add successfully parsed reports
                            all_reports.append(parsed_report)
                        
        except logs_client.exceptions.ResourceNotFoundException:
            print(f"Log group {log_group_name} not found")
            continue
        except Exception as e:
            print(f"Error processing log group {log_group_name}: {str(e)}")
            continue
    
    # If no reports found, return early
    if not all_reports:
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'No lambda records on {date_str}'
            })
        }
    
    # Export the collected reports
    export_success = export_to_s3(all_reports)
    
    # Sort reports by function for counting
    model_reports = [r for r in all_reports if r['function_name'] == 'yotam-finel-model']
    activator_reports = [r for r in all_reports if r['function_name'] == 'final-activator']
    
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': f'Processed {len(all_reports)} reports',
            'date': date_str,
            'export_success': export_success,
            'reports_by_function': {
                'yotam-finel-model': len(model_reports),
                'final-activator': len(activator_reports)
            },
            'details': {
                'yotam-finel-model': [{'request_id': r['request_id'], 'duration': r['duration']} for r in model_reports],
                'final-activator': [{'request_id': r['request_id'], 'duration': r['duration']} for r in activator_reports]
            }
        })
    }