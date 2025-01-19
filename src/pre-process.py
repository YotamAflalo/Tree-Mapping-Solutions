
### get the tip, png it, ad split it, return split images + ofset
import json
import sys
import rasterio as rio
import numpy as np
from PIL import Image
from pathlib import Path
import os
import pytz
from datetime import datetime, timedelta
import time


project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from logger import logger  # Note: changed this to be explicit
from config.config_pre_process import DEBUG,INPUT_FOLDER_PATH,IMAGE_SIZE,SPLIT_FOLDER,OFSETS_FOLDER,INPUT_PROCESSED_FOLDER_PATH,TIME_ZONE,RUN_H
# Add the 'src' directory to the Python path
import shutil

from s3_upload import upload_to_s3
from config.config_aws import BUCKET_NAME, AWS_REGION
from cloudwatch import logs_client,log_to_cloudwatch
def tif_to_png(tif_path, png_path,image_name):
    """
    Converts a TIF image to PNG format.
    
    Args:
        tif_path: str, path to source TIF file
        png_path: str, destination directory for PNG
        image_name: str, name for output PNG file
        
    Returns:
        bool: True if conversion successful, False otherwise
    """
    logger.info('Convert tif to png in processing...')
    log_to_cloudwatch(logs_client=logs_client,message="Convert tif to png in processing")
    try:
        with rio.open(tif_path) as src:
            array = src.read([1, 2, 3])  # Read the first three bands (R, G, B)
            rgb_array = np.dstack(array)  # Stack bands along the third dimension
            image = Image.fromarray(rgb_array, 'RGB')
            image.save(os.path.join(png_path,image_name))
        logger.info(f'Convert tif to png has been saved to {os.path.join(png_path,image_name)}')
        log_to_cloudwatch(logs_client=logs_client,message=f'Convert tif to png has been saved to {os.path.join(png_path,image_name)}')

        return True
    except Exception as e:
        logger.error(f"Not able to convert {tif_path} to image: {str(e)}")
        log_to_cloudwatch(logs_client=logs_client,message=f"Not able to convert {tif_path} to image: {str(e)}")

        return False
        


def split_image(image_path, out_folder, size: int, skip_empty: bool = False):
    """
    Splits an image into smaller squares and saves them individually.
    
    Args:
        image_path: str, path to source image
        out_folder: str, output directory for split images
        size: int, size of split squares in pixels
        skip_empty: bool, whether to skip empty image sections
        
    Returns:
        dict: Mapping of split image filenames to their offset coordinates
    """
    logger.info('Split images in processing...')

    if not Path(out_folder).exists():
        Path(out_folder).mkdir(parents=True, exist_ok=True)

    image_name = Path(image_path).name
    offsets = {}  # Dictionary to track offsets
    with Image.open(image_path) as img:
        width, height = img.size

        for i in range(0, width, size):
            for j in range(0, height, size):
                box = (i, j, i + size, j + size)
                crop = img.crop(box)
                if skip_empty and np.sum(np.array(crop)) == 0:
                    continue
                crop_filename = f"{image_name}_{i}_{j}.png" #IMAGE_NAME_PREFIX
                crop.save(os.path.join(out_folder, crop_filename))
                offsets[crop_filename] = (i, j)  # Track the offset
    logger.info(f'{image_path} splited images have been saved to {out_folder}')
    log_to_cloudwatch(logs_client=logs_client,message=f'{image_path} splited images have been saved to {out_folder}')
    return offsets  # Return the offsets for further use

if __name__ == "__main__":
    while True:
        israel_tz = pytz.timezone(TIME_ZONE)
        israel_time = datetime.now(israel_tz)
        if israel_time.hour == RUN_H or DEBUG:# and israel_time.minute == 00:
            if len(os.listdir(INPUT_FOLDER_PATH)):
                offsets_dict = {}
                for file_name in os.listdir(INPUT_FOLDER_PATH):
                    file_path = os.path.join(INPUT_FOLDER_PATH, file_name)
                    tif_to_png(tif_path=file_path,png_path=INPUT_FOLDER_PATH,image_name=file_name)
                    try:
                        offsets = split_image(image_path=os.path.join(INPUT_FOLDER_PATH,file_name),out_folder=SPLIT_FOLDER,size=IMAGE_SIZE)
                        offsets_dict[file_name] = offsets
                        # Create preprocessed folder path
                        preprocessed_path = os.path.join(INPUT_PROCESSED_FOLDER_PATH, file_name)
                        # Copy the original file to preprocessed folder
                        shutil.copy2(file_path, preprocessed_path)
                        # Remove the original file
                        os.remove(file_path)
                    except Exception as e:
                        logger.error(f"got this exaption: {str(e)}")
                        log_to_cloudwatch(logs_client=logs_client,message=f"got this exaption: {str(e)}")
                # Generate the file name with the current date
                current_date = datetime.now().strftime("%Y-%m-%d")  # Format: YYYY-MM-DD
                json_name = f"{current_date}.json"
                json_path = os.path.join(OFSETS_FOLDER, json_name)
                with open(json_path, "w") as json_file:
                    json.dump(offsets_dict, json_file, indent=4)  # `indent` makes the JSON more readable
                try:
                    upload_to_s3(SPLIT_FOLDER, OFSETS_FOLDER,BUCKET_NAME, AWS_REGION)
                    log_to_cloudwatch(logs_client=logs_client,message=f"upload to s3 sucssesfully")
                except Exception as e:
                        logger.error(f"faild to upload to s3: {str(e)}")   
                        log_to_cloudwatch(logs_client=logs_client,message=f"faild to upload to s3: {str(e)}")
            now = datetime.now()
            tomorrow = datetime.now() + timedelta(days=1)
            next_run = tomorrow.replace(hour=RUN_H, minute=0, second=0, microsecond=0)
            sleep_seconds = (next_run - now).total_seconds()
            log_to_cloudwatch(logs_client=logs_client,message=f"going to sleep {sleep_seconds}")
            logger.info(f"going to sleep {sleep_seconds}")
            time.sleep(sleep_seconds)

        time.sleep(5*60)



