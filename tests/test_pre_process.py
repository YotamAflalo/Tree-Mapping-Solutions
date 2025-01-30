import pytest
import os
import numpy as np
from PIL import Image
import rasterio
from rasterio.transform import from_origin
import shutil
from pathlib import Path

import sys
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

from src.pre_process import tif_to_png, split_image

@pytest.fixture
def test_directories():
    """Create and clean up test directories"""
    test_dir = Path("test_data")
    test_input = test_dir / "input"
    test_output = test_dir / "output"
    test_split = test_dir / "split"
    
    # Create test directories
    for directory in [test_input, test_output, test_split]:
        directory.mkdir(parents=True, exist_ok=True)
    
    yield {
        "input": test_input,
        "output": test_output,
        "split": test_split
    }
    
    # Cleanup after tests
    shutil.rmtree(test_dir)

@pytest.fixture
def sample_tif(test_directories):
    """Create a sample TIF file for testing"""
    # Create a simple 100x100 RGB image
    data = np.random.randint(0, 255, (3, 100, 100), dtype=np.uint8)
    
    tif_path = test_directories["input"] / "test_image.tif"
    
    transform = from_origin(0, 0, 1, 1)
    
    with rasterio.open(
        tif_path,
        'w',
        driver='GTiff',
        height=100,
        width=100,
        count=3,
        dtype=data.dtype,
        transform=transform
    ) as dst:
        dst.write(data)
    
    return str(tif_path)

@pytest.fixture
def sample_png(test_directories):
    """Create a sample PNG file for testing"""
    # Create a simple 100x100 RGB image
    data = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    img = Image.fromarray(data)
    
    png_path = test_directories["input"] / "test_image.png"
    img.save(png_path)
    
    return str(png_path)

def test_tif_to_png_successful_conversion(test_directories, sample_tif):
    """Test successful conversion from TIF to PNG"""
    output_dir = str(test_directories["output"])
    result = tif_to_png(sample_tif, output_dir, "test_output.png")
    
    assert result is True
    assert os.path.exists(os.path.join(output_dir, "test_output.png"))
    
    # Verify the output is a valid image
    img = Image.open(os.path.join(output_dir, "test_output.png"))
    assert img.format == "PNG"
    assert len(img.getbands()) == 3  # RGB image

def test_tif_to_png_invalid_input(test_directories):
    """Test conversion with invalid input file"""
    output_dir = str(test_directories["output"])
    result = tif_to_png("nonexistent.tif", output_dir, "test_output.png")
    
    assert result is False
    assert not os.path.exists(os.path.join(output_dir, "test_output.png"))

def test_split_image_correct_splitting(test_directories, sample_png):
    """Test that image splitting works correctly"""
    split_size = 50
    output_dir = str(test_directories["split"])
    
    offsets = split_image(sample_png, output_dir, split_size)
    
    # For a 100x100 image split into 50x50 pieces, we should get 4 pieces
    assert len(offsets) == 4
    
    # Check if all split images exist
    for filename in offsets.keys():
        assert os.path.exists(os.path.join(output_dir, filename))
    
    # Verify correct offsets
    expected_offsets = {
        f"test_image.png_0_0.png": (0, 0),
        f"test_image.png_0_50.png": (0, 50),
        f"test_image.png_50_0.png": (50, 0),
        f"test_image.png_50_50.png": (50, 50)
    }
    assert offsets == expected_offsets

def test_split_image_size_verification(test_directories, sample_png):
    """Test that split images have correct dimensions"""
    split_size = 50
    output_dir = str(test_directories["split"])
    
    offsets = split_image(sample_png, output_dir, split_size)
    
    # Verify dimensions of split images
    for filename in offsets.keys():
        img_path = os.path.join(output_dir, filename)
        with Image.open(img_path) as img:
            assert img.size == (split_size, split_size)

def test_split_image_invalid_input(test_directories):
    """Test splitting with invalid input file"""
    with pytest.raises(Exception):
        split_image("nonexistent.png", str(test_directories["split"]), 50)

def test_split_image_larger_than_original(test_directories, sample_png):
    """Test splitting with size larger than original image"""
    output_dir = str(test_directories["split"])
    split_size = 200  # Larger than original 100x100 image
    
    offsets = split_image(sample_png, output_dir, split_size)
    
    # Should only create one image
    assert len(offsets) == 1
    
    # Check the created image
    filename = list(offsets.keys())[0]
    img_path = os.path.join(output_dir, filename)
    
    with Image.open(img_path) as img:
        # Image should be padded to split_size
        assert img.size == (split_size, split_size)
        # Check if offset is (0, 0) since it's the only image
        assert offsets[filename] == (0, 0)

def test_split_image_partial_splits(test_directories, sample_png):
    """Test splitting with size that doesn't evenly divide the image"""
    output_dir = str(test_directories["split"])
    split_size = 60  # Doesn't evenly divide 100x100 image
    
    offsets = split_image(sample_png, output_dir, split_size)
    
    # Should create 4 images (2x2 grid)
    assert len(offsets) == 4
    
    # Check all images
    for filename in offsets.keys():
        img_path = os.path.join(output_dir, filename)
        with Image.open(img_path) as img:
            # Images should be either split_size or the remainder
            width, height = img.size
            assert width <= split_size and width > 0
            assert height <= split_size and height > 0
