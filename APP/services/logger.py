import csv
import os
from datetime import datetime

TRAINING_LOG_PATH = os.path.join("DATA", "training_log.csv")

def log_prediction(user_lat, user_lng, survey_point, rainfall_data, risk_res):
    row = {
        "timestamp": datetime.utcnow().isoformat(),
        "user_lat": user_lat,
        "user_lng": user_lng,
        "matched_survey_photo_id": survey_point.get("Photo_ID", ""),
        "distance_m": survey_point.get("distance_m", ""),
        "block_score": survey_point.get("BlockScore", ""),
        "slope_score": survey_point.get("Slope_Score", ""),
        "flow_acc_score": survey_point.get("FlowAcc_Score", ""),
        "capacity_risk": survey_point.get("Capacity_Risk", ""),
        "lulc_risk": survey_point.get("LULC_Risk", ""),
        "rainfall_7day_mm": rainfall_data.get("total_7day", ""),
        "rainfall_source": rainfall_data.get("source", ""),
        "predicted_score": risk_res.get("score", ""),
        "predicted_category": risk_res.get("category", ""),
    }

    file_exists = os.path.exists(TRAINING_LOG_PATH)
    os.makedirs(os.path.dirname(TRAINING_LOG_PATH), exist_ok=True)

    with open(TRAINING_LOG_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=row.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(row)