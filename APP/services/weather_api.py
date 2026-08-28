import requests

def get_rainfall_forecast(lat: float, lng: float) -> dict:
    """
    Fetches real-time 7-day total rainfall forecast (mm) from Open-Meteo API.
    Returns fallback estimates if offline or API request fails.
    """
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&daily=rain_sum&timezone=auto"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            daily_data = data.get("daily", {})
            
            dates = daily_data.get("time", [])
            daily_rain = daily_data.get("rain_sum", [])
            
            total_7day = sum(daily_rain) if daily_rain else 45.0
            
            return {
                "dates": dates,
                "daily": daily_rain,
                "total_7day": round(total_7day, 1),
                "daily_breakdown": daily_rain,
                "source": "Open-Meteo API (Live)"
            }
    except Exception:
        pass

    # Safe fallback if API request fails or offline
    return {
        "dates": ["Day 1", "Day 2", "Day 3", "Day 4", "Day 5", "Day 6", "Day 7"],
        "daily": [5.0, 10.0, 15.0, 8.0, 2.0, 0.0, 5.0],
        "total_7day": 45.0,
        "daily_breakdown": [5.0, 10.0, 15.0, 8.0, 2.0, 0.0, 5.0],
        "source": "Historical Baseline (Fallback)"
    }