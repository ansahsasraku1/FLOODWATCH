import os
from PIL import Image

input_folder = "ALL PHOTOS"
output_folder = "APP/assets/compressed_photos"

# Create output folder if it doesn't exist
os.makedirs(output_folder, exist_ok=True)

# Max width/height for web display
MAX_SIZE = (1080, 1080)

for filename in os.listdir(input_folder):
    if filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        img_path = os.path.join(input_folder, filename)
        
        with Image.open(img_path) as img:
            # Resize image maintaining aspect ratio
            img.thumbnail(MAX_SIZE)
            
            # Save compressed image with 70% JPEG quality
            output_path = os.path.join(output_folder, filename)
            img.save(output_path, "JPEG", optimize=True, quality=70)

print("Compression complete! Check APP/assets/compressed_photos")