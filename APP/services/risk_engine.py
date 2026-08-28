def calculate_flood_risk(
    block_score: float,
    rainfall_mm: float,
    slope_score: float = 0.3,
    flow_acc_score: float = 0.3,
    capacity_risk: float = 0.5,
    lulc_risk: float = 1.0,
    is_daily_rainfall: bool = True
) -> dict:
    
    # Dynamic rainfall normalization (80mm for daily storm, 200mm for cumulative 7-day)
    max_rain_baseline = 80.0 if is_daily_rainfall else 200.0
    rainfall_score = round(min(float(rainfall_mm), max_rain_baseline) / max_rain_baseline, 4)

    risk_score = (
        (0.2 * float(block_score)) +      # Blockage is primary localized cause
        (0.35 * rainfall_score) +          # Rainfall drive
        (0.20 * float(slope_score)) +
        (0.1 * float(flow_acc_score)) +
        (0.1 * float(capacity_risk)) +
        (0.05 * float(lulc_risk))
    )
    
    risk_score = round(min(max(risk_score, 0.0), 1.0), 4)
   
    print("Rain_Slope",rainfall_score)
    print("SlopeScore",slope_score)
    print("BlockScore",block_score)
    print("CapaRisk",capacity_risk)
    print("Lulc",lulc_risk)
    print("Flow accumulation",flow_acc_score)
    print("Risk_Score",risk_score)
    # Re-calibrated Classification Boundaries
    if risk_score >= 0.75:
        category = "High"
        label = "High Flood Risk - please encourage community members to clear debris and other material from drains near you. This is important to ensure a safe environment before you leave home today."
    elif risk_score >= 0.5:
        category = "Moderately High"
        label = "Moderately High Flood Risk - please encourage community members to clear debris and other material from drains near you. This is important to ensure a safe environment before you leave home today."
    elif risk_score >= 0.25:
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