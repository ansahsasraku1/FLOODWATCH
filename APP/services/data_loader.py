import os
import pandas as pd
import streamlit as st
from pathlib import Path
from pyproj import Transformer

# Initialize UTM 30N (Ghana EPSG:32630) to WGS84 Lat/Lon (EPSG:4326) Transformer
transformer = Transformer.from_crs("EPSG:32630", "EPSG:4326", always_xy=True)

def load_csv_safely(file_path: str) -> pd.DataFrame:
    if not os.path.exists(file_path):
        return pd.DataFrame()

    encodings = ['utf-8-sig', 'latin1', 'cp1252']
    df = None
    for enc in encodings:
        try:
            df = pd.read_csv(
                file_path,
                encoding=enc,
                on_bad_lines='skip',
                dtype=str,
                keep_default_na=False
            )
            break
        except (UnicodeDecodeError, Exception):
            continue

    if df is None:
        df = pd.read_csv(
            file_path,
            encoding='utf-8',
            encoding_errors='replace',
            on_bad_lines='skip',
            dtype=str,
            keep_default_na=False
        )

    # Convert UTM coordinates (Northing/Easting) to WGS84 Lat/Lng degrees
    if "Latitude" in df.columns and "Longitude" in df.columns:
        # Convert numeric values
        lat_vals = pd.to_numeric(df["Latitude"], errors='coerce').fillna(0.0)
        lng_vals = pd.to_numeric(df["Longitude"], errors='coerce').fillna(0.0)
        
        # Check if coordinates are in UTM meters (Northing > 1000)
        is_utm = lat_vals > 1000.0
        
        if is_utm.any():
            # Vectorized transformation for speed
            transformed_lngs, transformed_lats = transformer.transform(
                lng_vals[is_utm].values, 
                lat_vals[is_utm].values
            )
            df.loc[is_utm, "lat"] = transformed_lats
            df.loc[is_utm, "lng"] = transformed_lngs
            
            # Pass-through regular Lat/Lng coordinates
            df.loc[~is_utm, "lat"] = lat_vals[~is_utm]
            df.loc[~is_utm, "lng"] = lng_vals[~is_utm]
        else:
            df["lat"] = lat_vals
            df["lng"] = lng_vals

    return df

def load_app_dataset() -> pd.DataFrame:
    current_file = Path(__file__).resolve()
    base_dir = current_file.parent.parent.parent
    path = base_dir / "DATA" / "FloodWatch_App_Data.csv"
    return load_csv_safely(str(path))

@st.cache_data(ttl=3600)
def get_unified_survey_points() -> list[dict]:
    df = load_app_dataset()

    if df.empty:
        return []

    df = df.fillna("")
    return df.to_dict(orient="records")
# def load_cv_dataset() -> pd.DataFrame:
#     base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#     path = os.path.join(base_dir, "DATA", "FloodWatch_Computer_Vision.csv")
#     return load_csv_safely(path)

# def load_risk_model_dataset() -> pd.DataFrame:
#     base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#     path = os.path.join(base_dir, "DATA", "FloodWatch_Risk_Model.csv")
#     return load_csv_safely(path)

# # Decorator caches the loaded points in memory for 1 hour to prevent tab navigation lag
# @st.cache_data(ttl=3600)
# def get_unified_survey_points() -> list[dict]:
#     cv_df = load_cv_dataset()
#     risk_df = load_risk_model_dataset()

#     if cv_df.empty and risk_df.empty:
#         return []

#     if not cv_df.empty and not risk_df.empty and "Photo_ID" in cv_df.columns and "Photo_ID" in risk_df.columns:
#         merged_df = pd.merge(cv_df, risk_df, on="Photo_ID", how="outer", suffixes=('', '_risk'))
#     elif not cv_df.empty:
#         merged_df = cv_df
#     else:
#         merged_df = risk_df

#     merged_df = merged_df.fillna("")
#     return merged_df.to_dict(orient="records")