import os

def get_asset_path(filename: str) -> str:
    """Resolves a file inside APP/assets/, from any file under APP/ (components or services)."""
    app_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # services/ -> APP/
    return os.path.join(app_dir, "assets", filename)