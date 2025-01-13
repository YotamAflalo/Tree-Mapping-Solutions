from pathlib import Path

# Get project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Define all paths relative to project root
MODEL_PATH = PROJECT_ROOT / "models" / "v1"/ "tree_model_new"

SPLIT_FOLDER = PROJECT_ROOT / "data" / "processed_images" / "splited_images"
OUTPUT_FOLDER = PROJECT_ROOT / "data" / "processed_images" / "output"

simplification_tolerance = 1.0
min_polygon_points = 3
min_contour_points = 3
join_mitre_leange = 1
contours_level = 0.5
min_area = 20.0