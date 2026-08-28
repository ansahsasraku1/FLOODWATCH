import pandas as pd
from pathlib import Path

# --------------------------------------------------
# 1. SET PROJECT PATHS
# --------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent
DATA_FOLDER = BASE_DIR / "DATA"

# Path to NEW_DATA.csv containing master coordinates
new_data_file = DATA_FOLDER / "NEW_DATA.csv"

# Target files where Latitude and Longitude need to be replaced
target_files = [
    "FloodWatch_Computer_Vision.csv",
    "FloodWatch_App_Data.csv",
    "FloodWatch_Risk_Model.csv"
]

# --------------------------------------------------
# 2. READ & PREPARE MASTER COORDINATES
# --------------------------------------------------
if not new_data_file.exists():
    raise FileNotFoundError(f"❌ Master file not found at: {new_data_file}")

# Load NEW_DATA.csv
new_df = None
for enc in ['utf-8-sig', 'latin1', 'cp1252']:
    try:
        new_df = pd.read_csv(new_data_file, encoding=enc)
        break
    except Exception:
        continue

if new_df is None:
    raise ValueError("❌ Failed to read NEW_DATA.csv")

# Clean column names and convert Photo_ID to string
new_df.columns = new_df.columns.str.strip()
new_df["Survey_ID"] = new_df["Survey_ID"].astype(str).str.strip()

# Coerce coordinates to numbers
new_df["Latitude"] = pd.to_numeric(new_df["Latitude"], errors="coerce")
new_df["Longitude"] = pd.to_numeric(new_df["Longitude"], errors="coerce")

# Keep clean reference map of Photo_ID -> Latitude, Longitude
master_coords = new_df.dropna(subset=["Survey_ID", "Latitude", "Longitude"])[
    ["Survey_ID", "Latitude", "Longitude"]
].drop_duplicates(subset="Survey_ID", keep="first")

print(f"📍 Loaded {len(master_coords)} valid master coordinate pairs from NEW_DATA.csv.\n")

# --------------------------------------------------
# 3. UPDATE EACH TARGET FILE SEPARATELY
# --------------------------------------------------
for filename in target_files:
    file_path = DATA_FOLDER / filename
    
    if not file_path.exists():
        print(f"⚠️ File skipped (not found): {filename}")
        continue
    
    # Load target dataset
    target_df = None
    for enc in ['utf-8-sig', 'latin1', 'cp1252']:
        try:
            target_df = pd.read_csv(file_path, encoding=enc)
            break
        except Exception:
            continue
            
    if target_df is None:
        print(f"❌ Could not read {filename}")
        continue

    target_df.columns = target_df.columns.str.strip()
    initial_rows = len(target_df)

    # Ensure Survey_ID exists in target dataset
    if "Survey_ID" not in target_df.columns:
        print(f"⚠️ Skipped {filename}: 'Survey_ID' column missing!")
        continue

    target_df["Survey_ID"] = target_df["Survey_ID"].astype(str).str.strip()

    # Drop old Latitude and Longitude columns from target file
    cols_to_drop = [c for c in ["Latitude", "Longitude"] if c in target_df.columns]
    target_df = target_df.drop(columns=cols_to_drop)

    # Match Survey_ID with master coordinates to attach new Latitude and Longitude
    updated_df = target_df.merge(master_coords, on="Survey_ID", how="inner")

    # Filter out invalid geographic coordinates
    valid_mask = (
        updated_df["Latitude"].between(-90, 90) &
        updated_df["Longitude"].between(-180, 180)
    )
    cleaned_df = updated_df[valid_mask].copy()

    # Save output (saving with '_Updated.csv' extension; change file_path to overwrite original)
    out_path = DATA_FOLDER / filename.replace(".csv", "_Updated.csv")
    cleaned_df.to_csv(out_path, index=False)

    removed_rows = initial_rows - len(cleaned_df)
    print(f"✅ Updated: {out_path.name}")
    print(f"   - Valid records written: {len(cleaned_df)}")
    print(f"   - Invalid/Unmatched rows removed: {removed_rows}\n")

print("🎉 Coordinate update complete for all target datasets!")