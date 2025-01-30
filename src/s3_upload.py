import boto3
import os
from pathlib import Path
import json
import sys
from datetime import datetime
from botocore.exceptions import ClientError # AWS exceptions from botocore.exceptions import ClientError # AWS exceptions 
# Add project root to path
import dotenv
dotenv.load_dotenv()


project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.logger import Logger
from config.config_pre_process import SPLIT_FOLDER, OFSETS_FOLDER
from config.config_aws import BUCKET_NAME, AWS_REGION
logger = Logger(logger_name='pre-process',logs_dir=os.path.join(project_root,'logs'),log_mode='DEBUG')

class S3Uploader:
    def __init__(self, bucket_name, aws_region='us-east-1'):
        """Initialize S3 client and bucket configuration."""
        self.s3_client = boto3.client('s3', region_name=aws_region,
                                      aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'))
        self.bucket_name = bucket_name

    def upload_file(self, file_path, s3_path):
        """
        Uploads a single file to S3 bucket.
        
        Args:
            file_path: str, local path of file to upload
            s3_path: str, destination path in S3
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        try:
            self.s3_client.upload_file(file_path, self.bucket_name, s3_path)
            logger.info(f"Successfully uploaded {file_path} to s3://{self.bucket_name}/{s3_path}")
            return True
        except Exception as e:
            logger.error(f"Error uploading {file_path}: {str(e)}")
            return False

    def upload_images(self, images_folder):
        """
        Uploads all PNG images from a folder to S3, organizing by date.
        
        Args:
            images_folder: str, local folder containing images
            
        Returns:
            bool: True if all uploads successful, False otherwise
        """
        logger.info(f"Starting upload of images from {images_folder}")
        
        if not os.path.exists(images_folder):
            logger.error(f"Images folder {images_folder} does not exist")
            return False

        success = True
        # Create a subfolder with current date
        current_date = datetime.now().strftime("%Y-%m-%d")
        base_s3_path = f"images/{current_date}/"

        for image_name in os.listdir(images_folder):
            if image_name.endswith('.png'):
                local_path = os.path.join(images_folder, image_name)
                s3_path = base_s3_path + image_name
                if not self.upload_file(local_path, s3_path):
                    success = False

        return success

    def upload_offsets(self, offsets_folder):
        """
        Uploads the latest JSON file containing image offsets to S3.
        
        Args:
            offsets_folder: str, folder containing offset JSON files
            
        Returns:
            bool: True if upload successful, False otherwise
        """
        logger.info(f"Starting upload of offsets from {offsets_folder}")
        
        if not os.path.exists(offsets_folder):
            logger.error(f"Offsets folder {offsets_folder} does not exist")
            return False

        # Get the latest JSON file
        json_files = [f for f in os.listdir(offsets_folder) if f.endswith('.json')]
        if not json_files:
            logger.error("No JSON files found in offsets folder")
            return False

        latest_json = max(json_files)
        local_path = os.path.join(offsets_folder, latest_json)
        s3_path = f"offsets/{latest_json}"

        return self.upload_file(local_path, s3_path)
def upload_to_s3(SPLIT_FOLDER, OFSETS_FOLDER,BUCKET_NAME, AWS_REGION):
    # Configure these values

    uploader = S3Uploader(BUCKET_NAME, AWS_REGION)

    # First upload all images
    logger.info("Starting image upload process")
    images_success = uploader.upload_images(SPLIT_FOLDER)
    
    if images_success:
        logger.info("All images uploaded successfully")
        
        # Then upload the offsets file
        logger.info("Starting offsets upload process")
        offsets_success = uploader.upload_offsets(OFSETS_FOLDER)
        
        if offsets_success:
            logger.info("Offsets file uploaded successfully")
        else:
            logger.error("Failed to upload offsets file")
    else:
        logger.error("Failed to upload all images")

def main():
    # Configure these values

    uploader = S3Uploader(BUCKET_NAME, AWS_REGION)

    # First upload all images
    logger.info("Starting image upload process")
    images_success = uploader.upload_images(SPLIT_FOLDER)
    
    if images_success:
        logger.info("All images uploaded successfully")
        
        # Then upload the offsets file
        logger.info("Starting offsets upload process")
        offsets_success = uploader.upload_offsets(OFSETS_FOLDER)
        
        if offsets_success:
            logger.info("Offsets file uploaded successfully")
        else:
            logger.error("Failed to upload offsets file")
    else:
        logger.error("Failed to upload all images")

if __name__ == "__main__":
    main()