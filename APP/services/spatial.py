import math

def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the great-circle distance between two points on Earth 
    in meters using the Haversine formula.
    """
    R = 6371000.0  # Earth's radius in meters

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (math.sin(delta_phi / 2.0) ** 2 +
         math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2)
    
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return R * c

def find_nearby_survey_points(user_lat: float, user_lng: float, survey_points: list[dict], max_distance_m: float = 200.0) -> list[dict]:
    """
    Filters and returns survey points located within max_distance_m (meters) 
    of the user's coordinates, sorted by closest proximity.
    """
    nearby_points = []

    for pt in survey_points:
        try:
            pt_lat = float(pt.get("lat") or pt.get("Latitude", 0))
            pt_lng = float(pt.get("lng") or pt.get("Longitude", 0))
        except (ValueError, TypeError):
            continue

        if pt_lat == 0 or pt_lng == 0:
            continue

        distance = calculate_haversine_distance(user_lat, user_lng, pt_lat, pt_lng)

        if distance <= max_distance_m:
            point_copy = pt.copy()
            point_copy["distance_m"] = round(distance, 1)
            nearby_points.append(point_copy)

    # Sort by distance (closest first)
    nearby_points.sort(key=lambda x: x["distance_m"])
    return nearby_points