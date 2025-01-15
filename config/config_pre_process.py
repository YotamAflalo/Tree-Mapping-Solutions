DEBUG = True
from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent
# Define all paths relative to project root
INPUT_FOLDER_PATH = PROJECT_ROOT / "data" / "input"
# PNG_FOLDER = PROJECT_ROOT / "data" / "processed_images" / "png"
SPLIT_FOLDER = PROJECT_ROOT / "data" / "processed_images" / "splited_images"
OFSETS_FOLDER = PROJECT_ROOT / "data" / "ofsets"
INPUT_PROCESSED_FOLDER_PATH = PROJECT_ROOT / "data" / "processed_images" / "input_preprocessed"
# INPUT_FOLDER_PATH = '/data/input'
# PNG_FOLDER = '/data/processed_images/png'
# SPLIT_FOLDER = '/data/processed_images/splited_images'
# OFSETS_FOLDER = '/data/processed_images/ofsets'

#f"tif_png_file.png"
OUTPUT_PNG_SPLIT = f'images_split'
OUTPUT_DSM_SPLIT = f'dsm_split'
IMAGE_NAME_PREFIX = "img"
IMAGE_SIZE = 1600
TIME_ZONE = 'Asia/Jerusalem'
RUN_H = 12