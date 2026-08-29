import os
import csv
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd

from services.gis_service import get_lulc_at_point, get_terrain_at_point

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAGING_CSV = os.path.join(BASE_DIR, "APP", "uploads", "pending_submissions.csv")
APP_DATA_CSV = os.path.join(BASE_DIR, "DATA", "FloodWatch_App_Data.csv")
UPLOADS_DIR = os.path.join(BASE_DIR, "APP", "uploads")
PHOTOS_DIR = os.path.join(BASE_DIR, "ALL PHOTOS")

HEADERS = [
    "Survey_ID", "Timestamp", "Photo_ID", "Latitude", "Longitude",
    "AI_Suggested_Blockage", "Choke_Code",
    "Drain_Type", "LULC_Class", "DEM_Value", "Slope", "Slope_Score",
    "FlowAccumulation", "FlowAcc_Score", "Landmark_Notes", "Status"
]

def save_pending_submission(photo_filename: str, lat: float, lng: float, 
                           ai_suggested: str, choke_code: int,
                           drain_type: str, lulc_class: str, landmark: str) -> bool:
    try:
        os.makedirs(os.path.dirname(STAGING_CSV), exist_ok=True)
        survey_id = f"SRV_{int(datetime.now().timestamp())}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        terrain = get_terrain_at_point(lat, lng)
        raster_value = lambda key: terrain.get(key) if terrain.get(key) is not None else "NULL"
        row = {
            "Survey_ID": survey_id, "Timestamp": timestamp, "Photo_ID": photo_filename,
            "Latitude": lat, "Longitude": lng, "AI_Suggested_Blockage": ai_suggested,
            "Choke_Code": choke_code, "Drain_Type": drain_type, "LULC_Class": lulc_class,
            "DEM_Value": raster_value("DEM_Value"), "Slope": raster_value("Slope"),
            "Slope_Score": raster_value("Slope_Score"),
            "FlowAccumulation": raster_value("FlowAccumulation"),
            "FlowAcc_Score": raster_value("FlowAcc_Score"),
            "Landmark_Notes": landmark, "Status": "Pending Approval"
        }
        existing = []
        if os.path.exists(STAGING_CSV):
            with open(STAGING_CSV, newline="", encoding="utf-8") as f:
                existing = list(csv.DictReader(f))
        with open(STAGING_CSV, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=HEADERS)
            writer.writeheader()
            writer.writerows({header: old.get(header, "") for header in HEADERS} for old in existing)
            writer.writerow(row)
            
        return True
    except Exception as e:
        print(f"Failed to save staging entry: {e}")
        return False


def migrate_pending_submissions() -> list[dict]:
    """Upgrade legacy pending rows and fill raster fields for existing submissions."""
    if not os.path.exists(STAGING_CSV):
        return []
    with open(STAGING_CSV, newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))

    # Never rewrite a queue that cannot be identified reliably.
    if any(not row.get("Survey_ID") or not row.get("Photo_ID") for row in rows):
        return rows

    changed = False
    for row in rows:
        terrain = get_terrain_at_point(_number(row.get("Latitude")), _number(row.get("Longitude")))
        for key in ("DEM_Value", "Slope", "Slope_Score", "FlowAccumulation", "FlowAcc_Score"):
            if not row.get(key):
                row[key] = terrain[key] if terrain.get(key) is not None else "NULL"
                changed = True
        for header in HEADERS:
            if header not in row:
                row[header] = ""
                changed = True

    if changed:
        with open(STAGING_CSV, "w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=HEADERS)
            writer.writeheader()
            writer.writerows({header: row.get(header, "") for header in HEADERS} for row in rows)
    return rows


def _number(value, default=0.0):
    try:
        number = float(value)
        return default if pd.isna(number) else number
    except (TypeError, ValueError):
        return default


def _estimate_dimensions(gutter_type: str, data: pd.DataFrame) -> tuple[float, float]:
    name = (gutter_type or "").lower()
    if "small" in name or "roadside" in name or "earthen" in name or "soil" in name:
        defaults = (0.4, 0.5)
    elif "large" in name or "outfall" in name:
        defaults = (0.8, 0.9)
    elif "medium" in name or "collector" in name:
        defaults = (0.6, 0.7)
    else:
        defaults = (0.5, 0.6)

    if data.empty or "Gutter_Type" not in data.columns:
        return defaults

    matching = data[data["Gutter_Type"].astype(str).str.lower().str.contains(name, regex=False)]
    if matching.empty:
        matching = data

    width = pd.to_numeric(matching.get("Width_m"), errors="coerce").median()
    depth = pd.to_numeric(matching.get("Depth_m"), errors="coerce").median()
    return (_number(width, defaults[0]), _number(depth, defaults[1]))


def _nearest_terrain(lat: float, lng: float, data: pd.DataFrame) -> dict[str, float]:
    defaults = {"DEM_Value": 50.0, "Slope_Score": 0.85, "FlowAcc_Score": 0.0}
    if data.empty or "Latitude" not in data.columns or "Longitude" not in data.columns:
        return defaults

    latitudes = pd.to_numeric(data["Latitude"], errors="coerce")
    longitudes = pd.to_numeric(data["Longitude"], errors="coerce")
    valid = data[latitudes.notna() & longitudes.notna()].copy()
    if valid.empty:
        return defaults

    distance = (latitudes.loc[valid.index] - lat) ** 2 + (longitudes.loc[valid.index] - lng) ** 2
    nearest = valid.loc[distance.idxmin()]
    return {
        "DEM_Value": _number(nearest.get("DEM_Value"), defaults["DEM_Value"]),
        "Slope_Score": _number(nearest.get("Slope_Score"), defaults["Slope_Score"]),
        "FlowAcc_Score": _number(nearest.get("FlowAcc_Score"), defaults["FlowAcc_Score"]),
    }


def _risk_level(score: float) -> str:
    if score <= 0.25:
        return "Low"
    if score <= 0.50:
        return "Moderately Low"
    if score <= 0.75:
        return "Moderately High"
    return "High"


def approve_submission(submission: dict) -> None:
    """Move an approved image and append one formula-compliant app-data row."""
    data = pd.read_csv(APP_DATA_CSV, dtype=str) if os.path.exists(APP_DATA_CSV) else pd.DataFrame()
    lat = _number(submission.get("Latitude"))
    lng = _number(submission.get("Longitude"))
    gutter_type = submission.get("Drain_Type") or "Small roadside drain"
    width_m, depth_m = _estimate_dimensions(gutter_type, data)
    cross_section = width_m * depth_m
    choke_code = int(_number(submission.get("Choke_Code"), 2))
    block_score = max(0.0, min(choke_code / 4.0, 1.0))
    raster_terrain = get_terrain_at_point(lat, lng)
    fallback_terrain = _nearest_terrain(lat, lng, data)
    terrain = {
        key: _number(raster_terrain.get(key), fallback_terrain[key])
        for key in ("DEM_Value", "Slope_Score", "FlowAcc_Score")
    }

    lulc = get_lulc_at_point(lat, lng)
    if str(lulc).upper() == "NULL":
        lulc_risk = 0.5
    else:
        lulc_risk = 1.0 if str(lulc).lower() == "built-up" else 0.0

    rainfall_values = pd.to_numeric(data.get("Rainfall_Score", pd.Series(dtype=float)), errors="coerce")
    rainfall_score = _number(rainfall_values.median(), 0.301)
    capacities = pd.to_numeric(data.get("CrossSec_m2", pd.Series(dtype=float)), errors="coerce")
    min_capacity = _number(capacities.min(), cross_section)
    max_capacity = _number(capacities.max(), cross_section)
    if max_capacity > min_capacity:
        capacity_index = (cross_section - min_capacity) / (max_capacity - min_capacity)
        capacity_risk = 1.0 - max(0.0, min(capacity_index, 1.0))
    else:
        capacity_risk = 0.5

    risk_score = round(max(0.0, min(
        (0.30 * block_score) + (0.20 * rainfall_score) +
        (0.15 * terrain["Slope_Score"]) + (0.15 * terrain["FlowAcc_Score"]) +
        (0.10 * capacity_risk) + (0.10 * lulc_risk), 1.0
    )), 6)

    photo_name = Path(str(submission.get("Photo_ID", ""))).name
    source = Path(UPLOADS_DIR) / photo_name
    destination_dir = Path(PHOTOS_DIR)
    destination_dir.mkdir(parents=True, exist_ok=True)
    destination = destination_dir / photo_name
    if source.exists():
        shutil.move(str(source), str(destination))

    row = {
        "Survey_ID": submission.get("Survey_ID", f"SRV_{int(datetime.now().timestamp())}"),
        "Nearest_Landmark": submission.get("Landmark_Notes", "Unknown Landmark"),
        "Gutter_Type": gutter_type,
        "BlockScore": block_score,
        "Width_m": round(width_m, 3),
        "Depth_m": round(depth_m, 3),
        "CrossSec_m2": round(cross_section, 3),
        "DEM_Value": terrain["DEM_Value"],
        "Slope_Score": terrain["Slope_Score"],
        "FlowAcc_Score": terrain["FlowAcc_Score"],
        "LULC_Risk": lulc_risk,
        "Capacity_Risk": round(capacity_risk, 6),
        "Rainfall_Score": rainfall_score,
        "Risk_Score": risk_score,
        "Risk_Level": _risk_level(risk_score),
        "Photo_ID": photo_name,
        "Latitude": lat,
        "Longitude": lng,
    }
    columns = list(data.columns) if not data.empty else list(row)
    for column in row:
        if column not in columns:
            columns.append(column)
    pd.DataFrame([row], columns=columns).to_csv(APP_DATA_CSV, mode="a", header=not os.path.exists(APP_DATA_CSV), index=False)


def reject_submission(submission: dict) -> None:
    """Remove a rejected pending row and its uploaded image."""
    photo_name = Path(str(submission.get("Photo_ID", ""))).name
    photo_path = Path(UPLOADS_DIR) / photo_name
    if photo_path.exists():
        photo_path.unlink()