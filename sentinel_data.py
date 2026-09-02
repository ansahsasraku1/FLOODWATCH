import ee
import geemap
import os

ee.Initialize(project="smart-inn-464014-u3")

# Area of Interest (Kisseman / Legon area in Accra)
Aoi = ee.Geometry.BBox(-0.28566, 5.5555, -0.25884, 5.8766)

def mask_s2_clouds(image):
    """Masks clouds, cloud shadows, and cirrus using the SCL band."""
    scl = image.select("SCL")
    clear_pixels = scl.eq(4).Or(scl.eq(5)).Or(scl.eq(6)).Or(scl.eq(7))
    return image.updateMask(clear_pixels)

# Query, sort by cloud cover (lowest first), and pick the best image
try:
    print("Querying Sentinel-2 imagery...")
    best_scene = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(Aoi)
        .filterDate("2025-11-01", "2026-08-31")
        .sort("CLOUDY_PIXELS_PERCENTAGE")  # Sorts from least cloudy to most cloudy
        .first()                           # Selects the single best image
    )

    # Get info to check if scene exists
    scene_info = best_scene.getInfo()
    
    if scene_info and "properties" in scene_info:
        # Extract acquisition date for reference
        date = ee.Date(best_scene.get("system:time_start")).format("YYYY-MM-dd").getInfo()
        cloud_pct = best_scene.get("CLOUDY_PIXELS_PERCENTAGE").getInfo()
        print(f"✓ Found best scene from {date} (Scene Cloudiness: {cloud_pct}%)")

        # Mask remaining clouds on the single image and clip to AOI
        sentinel = mask_s2_clouds(best_scene).clip(Aoi)
        
        bands_10m = sentinel.select(
            ["B2", "B3", "B4", "B8"], ["Blue", "Green", "Red", "NIR"]
        )

        # Create output directory if it doesn't exist
        output_dir = "C:/Users/USER/Documents"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "sentinel_image.tif")

        print("Starting download...")
        geemap.ee_export_image(
            bands_10m,
            filename=output_path,
            scale=10,
            region=Aoi,
            file_per_band=False,
        )
        print(f"✓ Download completed successfully! File saved to {output_path}")
    else:
        print("✗ No scenes found in the specified collection for the given date range.")
        
except Exception as e:
    print(f"✗ Error during download: {str(e)}")