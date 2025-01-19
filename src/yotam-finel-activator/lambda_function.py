import json
import boto3
import logging
import os
# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
from lambada_custom_logger import log_to_cloudwatch,logs_client
aws_access_key_id = os.environ['aws_access_key_id']
aws_secret_access_key = os.environ['aws_secret_access_key']


#input - json with dicts for diffrent photos and sliced, output - triger diffrent lamdas and give them:
# (1)an ofset file (2)rellevant information for finding the images in the bucket
# i need to do same test on how mach can be done in one lambada, and aggragate base on this (/split more in the earlyer stages)
def lambda_handler(event, context):
    # TODO implement


    bucket = event['Records'][0]['s3']['bucket']['name']
    json_key = event['Records'][0]['s3']['object']['key']
    print(json_key)
    s3 = boto3.client('s3', aws_access_key_id=aws_access_key_id,
                      aws_secret_access_key=aws_secret_access_key)


    response = s3.get_object(Bucket=bucket, Key=json_key)
    json_data = response['Body'].read()
    offsets_dict = json.loads(json_data)

    print(offsets_dict)
    logger.info(f"Processing new file: {json_key} from bucket: {bucket}")
    log_to_cloudwatch(logs_client=logs_client,message=f"Processing new file: {json_key} from bucket: {bucket}")
    #In the future, additional aggregation should be examined according to calculation power and lambda costs
    i=0
    for tif_file, png_dict in offsets_dict.items():
        temp_offsets = {}
        temp_offsets[tif_file] = offsets_dict[tif_file] 
        upload_byte_stream = bytes(json.dumps(temp_offsets).encode('UTF-8'))
        file_name = f"small_offsets/{json_key[json_key.find('/')+1:json_key.find('.json')]}/offsets_{i}.json"
        s3.put_object(Bucket=bucket,Key=file_name,Body = upload_byte_stream)
        logger.info(f'{tif_file} offsets uploaded')
        log_to_cloudwatch(logs_client=logs_client,message=f'{tif_file} offsets uploaded')
        i+=1
    

    return {
        'statusCode': 200,
        'body': json.dumps(f"{json_key} is processed")
    }
