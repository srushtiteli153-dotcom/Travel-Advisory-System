
# aqi_service.py
# Fetch Air Quality Index data from OpenWeatherMap

import logging

import requests

from config import (
    OWM_API_KEY,
    OWM_BASE_URL,
    REQUEST_TIMEOUT,
)

logger = logging.getLogger(__name__)

# OpenWeatherMap AQI:
# 1 = Good
# 2 = Fair
# 3 = Moderate
# 4 = Poor
# 5 = Very Poor

AQI_TO_RISK = {
    1: 0,
    2: 25,
    3: 50,
    4: 75,
    5: 100,
}


def get_aqi(lat: float, lon: float) -> dict:
    """
    Fetch air pollution data and compute normalized AQI risk score.
    """

    url = f"{OWM_BASE_URL}/air_pollution"

    params = {
        "lat": lat,
        "lon": lon,
        "appid": OWM_API_KEY,
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        components = data["list"][0]["components"]
        owm_aqi = data["list"][0]["main"]["aqi"]

        return {
            "aqi_index": owm_aqi,
            "aqi_label": {
                1: "Good",
                2: "Fair",
                3: "Moderate",
                4: "Poor",
                5: "Very Poor",
            }[owm_aqi],
            "aqi_risk": AQI_TO_RISK.get(owm_aqi, 50),
            "pm25": components.get("pm2_5", 0),
            "pm10": components.get("pm10", 0),
            "o3": components.get("o3", 0),
            "no2": components.get("no2", 0),
        }

    except requests.exceptions.RequestException as exc:
        logger.error(
            "AQI API error at (%.4f, %.4f): %s",
            lat,
            lon,
            exc,
        )

        return {
            "aqi_index": 2,
            "aqi_label": "Unknown",
            "aqi_risk": 25,
            "pm25": 0,
            "pm10": 0,
        }


def get_route_aqi_risk(
    origin_lat,
    origin_lon,
    dest_lat,
    dest_lon,
) -> dict:
    """
    Return the higher AQI risk between origin and destination.
    """

    origin_aqi = get_aqi(origin_lat, origin_lon)
    dest_aqi = get_aqi(dest_lat, dest_lon)

    if dest_aqi["aqi_risk"] >= origin_aqi["aqi_risk"]:
        worst = dest_aqi
        worst["location"] = "destination"
    else:
        worst = origin_aqi
        worst["location"] = "origin"

    return worst
