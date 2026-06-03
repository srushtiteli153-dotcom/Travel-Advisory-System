
# risk_engine.py
# Compute Travel Risk Score and generate advisory text

import logging

from config import (
    WEIGHT_WEATHER,
    WEIGHT_AQI,
    WEIGHT_TRAFFIC,
    WEIGHT_ALERT,
    RISK_LOW,
    RISK_MODERATE,
    RISK_HIGH,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Weather Sub-Score (0-100)
# ──────────────────────────────────────────────────────────────

def compute_weather_risk(weather: dict, alerts: list) -> float:
    score = 0.0

    temp = weather.get("temp", 25)
    rain = weather.get("rain_1h", 0)
    wind = weather.get("wind_speed", 0)
    vis = weather.get("visibility", 10000)

    # Temperature component (0-40)
    if temp > 45 or temp < 5:
        score += 40
    elif temp > 42 or temp < 8:
        score += 30
    elif temp > 38 or temp < 12:
        score += 20
    elif temp > 35 or temp < 15:
        score += 10

    # Precipitation component (0-35)
    if rain > 30:
        score += 35
    elif rain > 15:
        score += 25
    elif rain > 7:
        score += 15
    elif rain > 2:
        score += 8

    # Wind component (0-15)
    wind_kmh = wind * 3.6

    if wind_kmh > 90:
        score += 15
    elif wind_kmh > 60:
        score += 10
    elif wind_kmh > 40:
        score += 5

    # Visibility component (0-10)
    if vis < 500:
        score += 10
    elif vis < 1500:
        score += 7
    elif vis < 3000:
        score += 4

    return min(100, score)


# ──────────────────────────────────────────────────────────────
# Alert Severity Sub-Score (0-100)
# ──────────────────────────────────────────────────────────────

def compute_alert_risk(alerts: list) -> float:
    if not alerts:
        return 0.0

    severity_map = {
        "minor": 25,
        "moderate": 50,
        "severe": 75,
        "extreme": 100,
    }

    return max(
        severity_map.get(
            alert.get("severity", "minor"),
            0,
        )
        for alert in alerts
    )


# ──────────────────────────────────────────────────────────────
# Composite Risk Score
# ──────────────────────────────────────────────────────────────

def compute_travel_risk_score(
    weather_risk: float,
    aqi_risk: float,
    traffic_risk: float,
    alert_risk: float,
) -> float:

    score = (
        weather_risk * WEIGHT_WEATHER
        + aqi_risk * WEIGHT_AQI
        + traffic_risk * WEIGHT_TRAFFIC
        + alert_risk * WEIGHT_ALERT
    )

    return round(
        min(100, max(0, score)),
        1,
    )


def classify_risk(score: float) -> str:
    if score <= RISK_LOW:
        return "Low"
    elif score <= RISK_MODERATE:
        return "Moderate"
    elif score <= RISK_HIGH:
        return "High"
    else:
        return "Critical"


# ──────────────────────────────────────────────────────────────
# Advisory Text Generation
# ──────────────────────────────────────────────────────────────

def generate_advisory(
    origin: str,
    destination: str,
    score: float,
    risk_level: str,
    weather: dict,
    aqi: dict,
    traffic: dict,
    alerts: list,
) -> str:

    lines = [
        f"TRAVEL ADVISORY: {origin} -> {destination}",
        f"Travel Risk Score: {score:.0f} / 100  |  Risk Level: {risk_level}",
        "",
    ]

    if risk_level == "Low":
        lines.append(
            "Status: CONDITIONS FAVORABLE. Safe to travel with standard precautions."
        )
    elif risk_level == "Moderate":
        lines.append(
            "Status: EXERCISE CAUTION. Monitor conditions before and during travel."
        )
    elif risk_level == "High":
        lines.append(
            "Status: HIGH RISK. Delay non-essential travel. Plan for contingencies."
        )
    else:
        lines.append(
            "Status: CRITICAL RISK. Avoid travel if possible. Follow official advisories."
        )

    lines.append("--- CURRENT CONDITIONS ---")

    lines.append(
        f"Weather:     {weather.get('weather_desc', 'N/A').title()}"
    )

    lines.append(
        f"Temperature: {weather.get('temp', 'N/A'):.1f}°C "
        f"(feels like {weather.get('feels_like', 'N/A'):.1f}°C)"
    )

    lines.append(
        f"Wind Speed:  {weather.get('wind_speed', 0) * 3.6:.1f} km/h"
    )

    lines.append(
        f"Rainfall:    {weather.get('rain_1h', 0):.1f} mm/hr"
    )

    lines.append(
        f"Visibility:  {weather.get('visibility', 10000) / 1000:.1f} km"
    )

    lines.append(
        f"Air Quality: {aqi.get('aqi_label', 'N/A')} "
        f"(AQI Index: {aqi.get('aqi_index', 'N/A')})"
    )

    lines.append(
        f"PM2.5:       {aqi.get('pm25', 0):.1f} µg/m³"
    )

    lines.append(
        f"Traffic:     {traffic.get('traffic_label', 'N/A')} "
        f"(Score: {traffic.get('traffic_risk', 0):.0f}/100)"
    )

    if alerts:
        lines.append("--- ACTIVE ALERTS ---")

        for alert in alerts:
            lines.append(
                f"  [{alert['severity'].upper()}] {alert['event']}"
            )

            if alert.get("description"):
                lines.append(
                    f"  {alert['description'][:200]}..."
                )

    lines.append("--- RECOMMENDATIONS ---")

    recommendations = build_recommendations(
        risk_level,
        weather,
        aqi,
        traffic,
        alerts,
    )

    for recommendation in recommendations:
        lines.append(f"  • {recommendation}")

    lines.append("")

    return "\n".join(lines)


def build_recommendations(
    risk_level,
    weather,
    aqi,
    traffic,
    alerts,
):

    recommendations = []

    rain = weather.get("rain_1h", 0)
    temp = weather.get("temp", 25)
    wind_kmh = weather.get("wind_speed", 0) * 3.6
    vis = weather.get("visibility", 10000)

    aqi_idx = aqi.get("aqi_index", 1)
    traffic_score = traffic.get("traffic_risk", 0)

    if risk_level in ("High", "Critical"):
        recommendations.append(
            "Consider postponing non-essential travel until conditions improve."
        )

    if rain > 15:
        recommendations.append(
            "Heavy rainfall expected: reduce speed, increase following distance."
        )
        recommendations.append(
            "Carry rain gear and waterproof bags for luggage."
        )

    if rain > 30:
        recommendations.append(
            "Flash flood risk: avoid low-lying roads and river crossings."
        )

    if temp > 40:
        recommendations.append(
            "Extreme heat: carry at least 3 litres of water; check vehicle coolant."
        )

    if temp < 10:
        recommendations.append(
            "Cold conditions: check brakes, carry warm clothing and emergency blanket."
        )

    if wind_kmh > 60:
        recommendations.append(
            "Strong winds: high-sided vehicles should exercise extreme caution."
        )

    if vis < 2000:
        recommendations.append(
            "Poor visibility: use fog lights, reduce speed significantly."
        )

    if aqi_idx >= 4:
        recommendations.append(
            "Poor air quality: use N95 mask; keep vehicle cabin air on recirculate."
        )

    if aqi_idx == 5:
        recommendations.append(
            "Very poor AQI: vulnerable individuals (elderly, children, respiratory conditions) should avoid travel."
        )

    if traffic_score > 60:
        recommendations.append(
            "Heavy traffic expected: depart earlier or later to avoid peak congestion."
        )

    if alerts:
        recommendations.append(
            "Active weather alerts in effect: monitor IMD and local authority updates."
        )

    if not recommendations:
        recommendations.append(
            "Standard road safety precautions apply."
        )

    return recommendations
