def calculate_flood_risk(
    block_score: float,
    rainfall_mm: float,
    slope_score: float = 0.3,
    flow_acc_score: float = 0.3,
    capacity_risk: float = 0.5,
    lulc_risk: float = 1.0,
    is_daily_rainfall: bool = True
) -> dict:
    
    # Use the same reference as the existing seven-day dataset.
    max_rain_baseline = 80.0 if is_daily_rainfall else 200.0
    rainfall_score = round(min(float(rainfall_mm), max_rain_baseline) / max_rain_baseline, 4)

    risk_score = (
        #(0.1 * float(block_score)) +
        (0.5 * rainfall_score) +
        (0.125 * float(1 -slope_score)) +
        (0.125 * float(flow_acc_score)) +
        (0.125 * float(capacity_risk)) +
        (0.125 * float(lulc_risk))
    )
    
    risk_score = round(min(max(risk_score, 0.0), 1.0), 4)
   
    # Keep boundaries aligned with the published FloodWatch categories.
    if risk_score >= 0.84:
        category = "High"
        label = "High Flood Risk - please encourage community members to clear debris and other material from drains near you. This is important to ensure a safe environment before you leave home today."
    elif risk_score > 0.67:
        category = "Moderately High"
        label = "Moderately High Flood Risk - please encourage community members to clear debris and other material from drains near you. This is important to ensure a safe environment before you leave home today."
    elif risk_score > 0.5:
        category = "Moderately Low"
        label = "Moderately Low Flood Risk - clear debris and other material from drains near you"
    else:
        category = "Low"
        label = "Low Flood Risk"

    return {
        'score': risk_score,
        'category': category,
        'label': label
    }