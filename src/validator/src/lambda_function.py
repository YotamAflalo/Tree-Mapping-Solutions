import boto3
import json
import logging
import os
import pickle
from pre_process import tif_to_png, split_image
from model_functions import process_image
from sklearn.metrics import jaccard_score
from pathlib import Path

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# S3 client
s3 = boto3.client('s3')

def lambda_handler(event, context):
    # Parse event
    bucket = event['Records'][0]['s3']['bucket']['name']
    input_key = event['Records'][0]['s3']['object']['key']
    logger.info(f"Processing {input_key} from bucket {bucket}")
    
    # Set paths for intermediate files
    temp_dir = "/tmp"
    tif_file_path = os.path.join(temp_dir, "input.tif")
    png_file_path = os.path.join(temp_dir, "converted_image.png")
    split_folder = os.path.join(temp_dir, "split_images")
    os.makedirs(split_folder, exist_ok=True)
    
    # Download input .tif file
    s3.download_file(bucket, input_key, tif_file_path)
    
    # Convert .tif to .png
    tif_to_png(tif_file_path, png_file_path)
    
    # Split .png into smaller tiles
    offsets = split_image(png_file_path, split_folder, size=1600, skip_empty=True)
    
    # Download validation pickle
    validation_pickle_key = os.environ['VALIDATION_PICKLE_KEY']
    validation_pickle_path = os.path.join(temp_dir, "validation.pickle")
    s3.download_file(bucket, validation_pickle_key, validation_pickle_path)
    validation_data = pickle.load(open(validation_pickle_path, 'rb'))
    validation_data = validation_data == 255  # Binary conversion
    
    # Process each tile and calculate Jaccard score
    scores = []
    for split_image_file in Path(split_folder).glob("*.png"):
        pred_matrix = process_image(split_image_file)
        pred_matrix = pred_matrix == 255
        score = jaccard_score(pred_matrix.flatten(), validation_data.flatten(), average='micro')
        logger.info(f"Jaccard score for {split_image_file.name}: {score}")
        scores.append(score)
    
    # Compute average score
    avg_score = sum(scores) / len(scores) if scores else 0
    logger.info(f"Average Jaccard score: {avg_score}")
    
    # Save results to S3
    results_key = f"validation_results/{Path(input_key).stem}_results.json"
    results_data = {
            "average_score": avg_score,
            "scores": scores
    }
    s3.put_object(
            Bucket=bucket,
            Key=results_key,
            Body=json.dumps(results_data),
            ContentType="application/json"
    )
    logger.info(f"Validation results saved to {results_key}")
    
    return {
            "statusCode": 200,
            "body": json.dumps({"average_score": avg_score, "results_key": results_key})
    }