import os
from functools import lru_cache

import numpy as np
import rasterio
from rasterio.warp import transform

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
LULC_PATH = os.path.join(BASE_DIR, "DATA", "Kisseman_lulc.tif")
SLOPE_PATH = os.path.join(BASE_DIR, "DATA", "Kisseman_slope.tif")
FACC_PATH = os.path.join(BASE_DIR, "DATA", "Kisseman_facc.tif")
DEM_PATH = os.path.join(BASE_DIR, "DATA", "Kisseman_dem.tif")

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
        value = _sample_raster(LULC_PATH, lat, lng)
        return LULC_MAP.get(int(value), "NULL") if value is not None else "NULL"
    except Exception:
        return "NULL"


def _sample_raster(path: str, lat: float, lng: float):
    if not os.path.exists(path):
        return None

    with rasterio.open(path) as src:
        x, y = transform("EPSG:4326", src.crs, [lng], [lat])
        if not (src.bounds.left <= x[0] <= src.bounds.right and src.bounds.bottom <= y[0] <= src.bounds.top):
            return None
        value = next(src.sample([(x[0], y[0])]))[0]
        if src.nodata is not None and value == src.nodata:
            return None
        if np.ma.is_masked(value) or not np.isfinite(value):
            return None
        return float(value)


@lru_cache(maxsize=8)
def _raster_min_max(path: str) -> tuple[float, float] | None:
    if not os.path.exists(path):
        return None
    with rasterio.open(path) as src:
        values = src.read(1, masked=True).compressed().astype(float)
    values = values[np.isfinite(values)]
    if values.size == 0:
        return None
    return float(values.min()), float(values.max())


def get_terrain_at_point(lat: float, lng: float) -> dict[str, float | None]:
    """Sample DEM, slope, and flow accumulation rasters at a WGS84 point."""
    dem = _sample_raster(DEM_PATH, lat, lng)
    slope = _sample_raster(SLOPE_PATH, lat, lng)
    facc = _sample_raster(FACC_PATH, lat, lng)

    slope_score = None if slope is None else max(0.0, min(1.0, 1.0 - slope / 20.0))
    facc_range = _raster_min_max(FACC_PATH)
    if facc is None or facc_range is None or facc_range[1] <= facc_range[0]:
        flow_score = None
    else:
        flow_score = max(0.0, min(1.0, (facc - facc_range[0]) / (facc_range[1] - facc_range[0])))

    return {
        "DEM_Value": dem,
        "Slope_Score": slope_score,
        "FlowAcc_Score": flow_score,
        "FlowAccumulation": facc,
        "Slope": slope,
    }