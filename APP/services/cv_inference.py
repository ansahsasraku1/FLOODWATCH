import os
from PIL import Image
import streamlit as st
from pathlib import Path

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
MODEL_PATH = os.path.join(BASE_DIR, "MODELS", "drain_classifier.pth")

CLASS_MAPPING = {
    0: {"condition": "Not a Drain / Invalid Photo", "score": 0.0, "code": 0, "is_drain": False},
    1: {"condition": "Clear / Low Blockage (0–25%)", "score": 0.25, "code": 1, "is_drain": True},
    2: {"condition": "Minor Blockage (25–50%)", "score": 0.50, "code": 2, "is_drain": True},
    3: {"condition": "Partially Blocked (50–75%)", "score": 0.75, "code": 3, "is_drain": True},
    4: {"condition": "Severely Blocked (75–100%)", "score": 1.00, "code": 4, "is_drain": True}
}

@st.cache_resource(show_spinner=False)
def load_trained_model():
    import torch
    import torch.nn as nn
    from torchvision import models

    if not os.path.exists(MODEL_PATH):
        return None
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    model = models.mobilenet_v3_small(weights=None)
    num_features = model.classifier[3].in_features
    model.classifier[3] = nn.Linear(num_features, 5)
    model.load_state_dict(torch.load(MODEL_PATH, map_location=device, weights_only=True))
    model.to(device)
    model.eval()
    return model

@st.cache_resource(show_spinner=False)
def get_image_transform():
    from torchvision import transforms

    return transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

@st.cache_data(show_spinner=False)
def _photo_index(folder: str) -> dict[str, str]:
    path = Path(folder)
    if not path.is_dir():
        return {}
    return {
        file.stem.lower(): str(file)
        for file in path.iterdir()
        if file.is_file()
    }

def get_photo_path_by_id(photo_id: str) -> str:
    """Locates photo path safely across repository folders on Linux/Windows."""
    if not photo_id or str(photo_id).strip() == "" or str(photo_id).lower() == "nan":
        return ""

    photo_id_str = str(photo_id).strip()

    # Anchor properly to project root
    # cv_inference.py -> services/ -> APP/ -> project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent

    search_dirs = [
        project_root / "ALL PHOTOS",
        project_root / "APP" / "uploads"
    ]

    # Strip existing extensions
    clean_id = photo_id_str
    for ext in ['.jpg', '.jpeg', '.png', '.JPG', '.PNG', '.JPEG']:
        if clean_id.lower().endswith(ext.lower()):
            clean_id = clean_id[:-len(ext)]
            break

    for folder in search_dirs:
        if not folder.exists():
            continue

        # 1. Exact string match
        direct = folder / photo_id_str
        if direct.exists():
            return str(direct)

        # 2. Use a cached index for case-insensitive matches.
        indexed_path = _photo_index(str(folder)).get(clean_id.lower())
        if indexed_path:
            return indexed_path

    return ""

def analyze_drain_image(image_input) -> dict:
    try:
        import torch

        if isinstance(image_input, (str, bytes)):
            img = Image.open(image_input).convert("RGB")
        elif hasattr(image_input, "read"):
            img = Image.open(image_input).convert("RGB")
        elif isinstance(image_input, Image.Image):
            img = image_input.convert("RGB")
        else:
            raise ValueError("Unsupported image format.")

        model = load_trained_model()
        if model is None:
            return {
                "success": False,
                "is_drain": False,
                "error": "Computer vision model is unavailable. Please try again later.",
                "block_score": 0.0,
                "choke_code": 0,
                "predicted_condition": "Model unavailable",
                "confidence": 0.0
            }

        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        input_tensor = get_image_transform()(img).unsqueeze(0).to(device)
        with torch.no_grad():
            outputs = model(input_tensor)
            probabilities = torch.nn.functional.softmax(outputs, dim=1)[0]
        
        top_prob, pred_class = torch.max(probabilities, 0)
        confidence = top_prob.item()
        class_idx = pred_class.item()

        class_info = CLASS_MAPPING.get(class_idx, CLASS_MAPPING[0])
        is_drain = class_info["is_drain"]

        if not is_drain:
            return {
                "success": False,
                "is_drain": False,
                "error": "⚠️ Invalid photo detected. Image does not appear to feature drainage infrastructure.",
                "block_score": 0.0,
                "choke_code": 0,
                "predicted_condition": class_info["condition"],
                "confidence": confidence
            }

        return {
            "success": True,
            "is_drain": True,
            "block_score": class_info["score"],
            "choke_code": class_info["code"],
            "predicted_condition": class_info["condition"],
            "confidence": confidence
        }


    except Exception as e:
        return {
            "success": False,
            "is_drain": False,
            "error": str(e),
            "block_score": 0.0,
            "choke_code": 0,
            "predicted_condition": "Error",
            "confidence": 0.0
        }