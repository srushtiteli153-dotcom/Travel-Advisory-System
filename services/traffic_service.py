
# traffic_service.py
# Compute traffic risk score for city pairs

import logging
from datetime import datetime
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")

# Base congestion indices per route (0-100 scale)
BASE_CONGESTION = {
    ("Mumbai", "Pune"): 65,
    ("Delhi", "Agra"): 55,
    ("Bangalore", "Chennai"): 50,
    ("Hyderabad", "Vijayawada"): 45,
    ("Kolkata", "Bhubaneswar"): 40,
    ("Ahmedabad", "Surat"): 50,
    ("Jaipur", "Jodhpur"): 35,
    ("Delhi", "Chandigarh"): 55,
}

# Time-of-day multipliers
HOUR_MULTIPLIERS = {
    range(0, 5): 0.3,     # Late night
    range(5, 8): 0.6,     # Early morning
    range(8, 10): 1.4,    # Morning peak
    range(10, 17): 0.9,   # Off-peak day
    range(17, 21): 1.5,   # Evening peak
    range(21, 24): 0.5,   # Night
}


def get_hour_multiplier(hour: int) -> float:
    """
    Return traffic multiplier based on hour of day.
    """

    for hour_range, multiplier in HOUR_MULTIPLIERS.items():
        if hour in hour_range:
            return multiplier

    return 1.0


def get_traffic_risk(origin: str, destination: str) -> dict:
    """
    Compute a traffic risk score (0-100) for a given route.
    """

    now = datetime.now(IST)

    hour = now.hour
    weekday = now.weekday()  # 0=Monday, 6=Sunday

    base = BASE_CONGESTION.get(
        (origin, destination),
        BASE_CONGESTION.get((destination, origin), 50)
    )

    multiplier = get_hour_multiplier(hour)

    if weekday >= 5:
        # Weekend
        multiplier *= 0.7

    if weekday == 4:
        # Friday
        multiplier *= 1.1

    raw_score = min(100, base * multiplier)

    if raw_score < 30:
        label = "Light"
    elif raw_score < 55:
        label = "Moderate"
    elif raw_score < 75:
        label = "Heavy"
    else:
        label = "Severe"

    logger.info(
        "Traffic risk for %s->%s: %.1f (%s) at hour %d",
        origin,
        destination,
        raw_score,
        label,
        hour,
    )

    return {
        "traffic_risk": round(raw_score, 1),
        "traffic_label": label,
        "hour": hour,
        "weekday": weekday,
    }
