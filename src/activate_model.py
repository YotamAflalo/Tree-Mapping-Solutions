#########################################legacy##############################################
DIBUG=True

import numpy as np
from PIL import Image
from pathlib import Path
import detectree as dtr
import os
import pickle
from skimage.measure import find_contours
import tqdm
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection
from shapely.geometry import JOIN_STYLE
import sys
from datetime import datetime
from affine import Affine
import json
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from logger import logger  # Note: changed this to be explicit
from config.config_pre_process import SPLIT_FOLDER,OFSETS_FOLDER
# Add the 'src' directory to the Python path
from config.config_model import MODEL_PATH,OUTPUT_FOLDER, simplification_tolerance,min_polygon_points,min_contour_points,join_mitre_leange,contours_level,min_area

# TODO - fix with s3 or gatawy content
def load_offsets(date,DIBUG = False) ->dict:
    '''
    ths function load the offsets'''
    if DIBUG:
        path = os.path.join(OFSETS_FOLDER, '2025-01-11.json')
        with open(path, 'r') as f:
            offsets = json.load(f) 

    return offsets

def create_polygons(mask, simplification_tolerance = 1.0,min_polygon_points = 3,
                    min_contour_points = 3,join_mitre_leange = 1,contours_level = 0.5,min_area = 20.0):
    logger.info('Create polygons in processing...')


    contours = find_contours(mask, level=contours_level)
    polygons = []
    for contour in contours:
        if len(contour) >= min_contour_points:
            polygon = Polygon(contour[:, ::-1])
            if polygon.is_valid:
                polygons.append(polygon)

    buffered_polygons = [polygon.buffer(join_mitre_leange, join_style=JOIN_STYLE.mitre) for polygon in polygons]
    combined_polygons = unary_union(buffered_polygons)

    if isinstance(combined_polygons, MultiPolygon):
        combined_polygons = list(combined_polygons.geoms)
    elif isinstance(combined_polygons, Polygon):
        combined_polygons = [combined_polygons]
    else:
        combined_polygons = list(combined_polygons.geoms) if isinstance(combined_polygons, GeometryCollection) else []

    filtered_polygons = [polygon for polygon in combined_polygons
                         if len(polygon.exterior.coords) >= min_polygon_points and polygon.area >= min_area]

    simplified_polygons = [polygon.simplify(simplification_tolerance, preserve_topology=True) for polygon in filtered_polygons]

    final_polygons = []
    for polygon in simplified_polygons:
        if not polygon.is_empty and polygon.is_valid:
            final_polygons.append(polygon)

    logger.info('Create polygons has done.')
    return final_polygons
    # final_polygons now contains all the combined and simplified polygons, ensuring none are missing

def process_image(png_name, transform,OUTPUT_PNG_SPLIT, offsets,MODEL_PATH):
    logger.info(f"Predicting model: {png_name}")
    offset = offsets[png_name]

    clf = pickle.load(open(MODEL_PATH, 'rb'))
    clf_v1 = dtr.Classifier(clf=clf)

    # Predict models
    y_pred = clf_v1.predict_img(f'{OUTPUT_PNG_SPLIT}/{png_name}')

    # Process results
    vegetation_mask = np.where(y_pred == 0, 0, 255)

    polygons = create_polygons(vegetation_mask,simplification_tolerance=simplification_tolerance,
                               min_polygon_points=min_polygon_points,min_contour_points=min_contour_points,
                               join_mitre_leange=join_mitre_leange,contours_level=contours_level,
                               min_area=min_area)

    adjusted_polygons = []
    for polygon in polygons:
        exterior_coords = [(x + offset[0], y + offset[1]) for x, y in polygon.exterior.coords]
        interiors = []
        for interior in polygon.interiors:
            interior_coords = [(x + offset[0], y + offset[1]) for x, y in interior.coords]
            interiors.append(interior_coords)\

        exterior_coords = [transform * (x, y) for x, y in exterior_coords]
        interiors = [[transform * (x, y) for x, y in interior] for interior in interiors]
        adjusted_polygon = Polygon(exterior_coords, interiors)
        adjusted_polygons.append(adjusted_polygon)

    return adjusted_polygons

transform = Affine(1.0, 0.0, 0.0,
       0.0, 1.0, 0.0)
# crs = None
polygons_info = []

offsets = load_offsets(datetime.now().strftime("%Y-%m-%d"),DIBUG=DIBUG)

IMAGE_NAME = list(offsets.keys())[0]#will come from the ofset dict
offsets = offsets[IMAGE_NAME]

for png_image in offsets.keys():# tqdm.tqdm(os.listdir(SPLIT_FOLDER)):
    if '.png' in png_image:
        polygons = process_image(png_image, OUTPUT_PNG_SPLIT=SPLIT_FOLDER, transform=transform, offsets=offsets,MODEL_PATH=MODEL_PATH)
        polygons_info.extend(polygons)


output_shp_path = f'{OUTPUT_FOLDER}/{IMAGE_NAME}_shapefile.shp'
gdf = gpd.GeoDataFrame({'geometry': polygons_info})

gdf.to_file(output_shp_path)