import os
import csv
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
STAGING_CSV = os.path.join(BASE_DIR, "APP", "uploads", "pending_submissions.csv")

HEADERS = [
    "Survey_ID", "Timestamp", "Photo_ID", "Latitude", "Longitude",
    "AI_Suggested_Blockage", "Choke_Code",
    "Drain_Type", "LULC_Class", "Landmark_Notes", "Status"
]

def save_pending_submission(photo_filename: str, lat: float, lng: float, 
                           ai_suggested: str, choke_code: int,
                           drain_type: str, lulc_class: str, landmark: str) -> bool:
    try:
        os.makedirs(os.path.dirname(STAGING_CSV), exist_ok=True)
        file_exists = os.path.exists(STAGING_CSV)
        
        survey_id = f"SRV_{int(datetime.now().timestamp())}"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        row = [
            survey_id, timestamp, photo_filename, lat, lng,
            ai_suggested, choke_code,
            drain_type, lulc_class, landmark, "Pending Approval"
        ]

        with open(STAGING_CSV, mode="a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(HEADERS)
            writer.writerow(row)
            
        return True
    except Exception as e:
        print(f"Failed to save staging entry: {e}")
        return False