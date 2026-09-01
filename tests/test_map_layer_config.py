from pathlib import Path

from APP.components.map_view import build_map_layer_specs


def test_visible_layers_prefer_pngs_and_hidden_layers_remain_tif_only():
    data_dir = Path("C:/Users/USER/Desktop/FLOODWATCH_KISSEMAN/FLOODWATCH_CODE/DATA")

    specs = build_map_layer_specs(str(data_dir))

    assert specs["visible"][0]["path"].endswith("png_data/lulc.png")
    assert specs["visible"][1]["path"].endswith("png_data/slope.png")
    assert specs["visible"][2]["path"].endswith("png_data/flowacc.png")
    assert specs["visible"][3]["path"].endswith("png_data/elevation.png")

    assert all(layer["opacity"] == 0.0 for layer in specs["hidden"])
    assert all(layer["control"] is False for layer in specs["hidden"])
    assert all(layer["path"].endswith(".tif") for layer in specs["hidden"])
