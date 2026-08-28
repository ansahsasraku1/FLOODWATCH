import os
import rasterio

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LULC_PATH = os.path.join(BASE_DIR, "DATA", "Kisseman_lulc.tif")

LULC_MAP = {
    0: "Built-up",
    1: "Vegetation"
}

def get_lulc_at_point(lat: float, lng: float) -> str:
    """
    Extracts LULC class from Kisseman_lulc.tif for a (lat, lng) point.
    Returns 'Built-up', 'Vegetation', or 'NULL' if outside raster bounds.
    """
    if not os.path.exists(LULC_PATH):
        return "NULL"

    try:
        with rasterio.open(LULC_PATH) as src:
            # Check bounding box extent of the raster
            bounds = src.bounds
            if not (bounds.left <= lng <= bounds.right and bounds.bottom <= lat <= bounds.top):
                return "NULL"

            # Sample pixel at location
            sample_gen = src.sample([(lng, lat)])
            pixel_val = int(list(sample_gen)[0][0])

            if src.nodata is not None and pixel_val == src.nodata:
                return "NULL"

            return LULC_MAP.get(pixel_val, "NULL")
    except Exception:
        return "NULL"