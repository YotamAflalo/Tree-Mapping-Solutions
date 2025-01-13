import json
import boto3
import logging
import os
from affine import Affine

from model_functions import process_image,load_model,load_image,delete_temp_image
from config_model import MODEL_PATH,OUTPUT_FOLDER_S3
# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
aws_access_key_id = os.environ['aws_access_key_id']
aws_secret_access_key = os.environ['aws_secret_access_key']
import geopandas as gpd
import tempfile


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


    transform = Affine(1.0, 0.0, 0.0,
       0.0, 1.0, 0.0)
    model = load_model(MODEL_PATH)
    # crs = None
    folder = f"images/{json_key[json_key.find('/')+1:][:json_key[json_key.find('/')+1:].find('/')]}"

    for tif_file, png_dict in offsets_dict.items(): #now there is only one tif per offset, but in the futer maybe more
        polygons_info = []
        IMAGE_NAME = tif_file
        offsets = png_dict

        for png_image in offsets.keys():
            if '.png' in png_image: 
                image_path = os.path.join(folder, png_image)
                temp_image= load_image(s3_client=s3,BUCKET_NAME=bucket,image_path=image_path) # i chackted this part in lambada and it is working :) 
                polygons = process_image(png_image, temp_image_path=temp_image, transform=transform, offsets=offsets,model=model) #TODO chack on lambada
                polygons_info.extend(polygons)
                delete_temp_image(temp_image)

        gdf = gpd.GeoDataFrame({'geometry': polygons_info})

        output_shp_key = f'{OUTPUT_FOLDER_S3}/{json_key[json_key.find('/')+1:][:json_key[json_key.find('/')+1:].find('/')]}/{IMAGE_NAME}_shapefile.shp'
                # Create a temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            # Define temporary file path
            temp_shp_path = os.path.join(tmpdir, 'temp.shp')
            
            # Save GeoDataFrame to temporary file
            gdf.to_file(temp_shp_path)
            
            # Upload all related files (.shp, .shx, .dbf, .prj)
            temp_files = []
            for file in os.listdir(tmpdir):
                if file.startswith('temp'):
                    # Get file extension
                    _, ext = os.path.splitext(file)
                    
                    # Create corresponding S3 key with original name
                    s3_key = output_shp_key.replace('.shp', ext)
                    file_path = os.path.join(tmpdir, file)
                    temp_files.append(file_path)

                    # Upload file to S3
                    with open(os.path.join(tmpdir, file), 'rb') as f:
                        s3.upload_fileobj(f, bucket, s3_key)
                        logger.info(f"Uploaded {s3_key} to S3")
                # Explicitly delete temporary files
            for file_path in temp_files:
                try:
                    os.remove(file_path)
                    logger.info(f"Deleted temporary file: {file_path}")
                except OSError as e:
                    logger.warning(f"Error deleting {file_path}: {e}")


    return {
        'statusCode': 200,
        'body': json.dumps(f"{json_key} is processed")
    }
