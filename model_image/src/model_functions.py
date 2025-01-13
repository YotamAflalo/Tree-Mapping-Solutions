import numpy as np
import detectree as dtr
import os
import pickle
from skimage.measure import find_contours
import geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection
from shapely.geometry import JOIN_STYLE
from config_model import MODEL_PATH,OUTPUT_FOLDER, simplification_tolerance,min_polygon_points,min_contour_points,join_mitre_leange,contours_level,min_area
from tempfile import NamedTemporaryFile

# TODO - צריך דרך לעדכן את הקונפיג מבחוץ בקלות, אולי להוסיף שלב של משיכה של קובץ קונפיג מאס3

def load_image(s3_client,BUCKET_NAME,image_path):

    with NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
            temp_image_path = temp_file.name
            
            # Download the file from S3 to the temporary file
            s3_client.download_file(
                Bucket=BUCKET_NAME,
                Key=image_path,
                Filename=temp_image_path
            )
    return temp_image_path

def delete_temp_image(temp_image_path):
        if os.path.exists(temp_image_path):
            os.remove(temp_image_path)
            return True
        else: return False



def create_polygons(mask, simplification_tolerance = 1.0,min_polygon_points = 3,
                    min_contour_points = 3,join_mitre_leange = 1,contours_level = 0.5,min_area = 20.0):
    # logger.info('Create polygons in processing...')


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

    # logger.info('Create polygons has done.')
    return final_polygons
    # final_polygons now contains all the combined and simplified polygons, ensuring none are missing

def load_model(MODEL_PATH):
    clf = pickle.load(open(MODEL_PATH, 'rb'))
    clf_v1 = dtr.Classifier(clf=clf)
    return clf_v1

def process_image(png_name, transform,temp_image_path, offsets,model,
                  simplification_tolerance=simplification_tolerance,
                  min_polygon_points=min_polygon_points,min_contour_points=min_contour_points,
                  join_mitre_leange=join_mitre_leange,contours_level=contours_level,min_area=min_area):
    # logger.info(f"Predicting model: {png_name}")
    offset = offsets[png_name]

    
    # Predict models
    y_pred = model.predict_img(temp_image_path)

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