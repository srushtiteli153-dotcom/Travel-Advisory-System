
# weather_service.py
# Fetch weather data and alerts from OpenWeatherMap

import logging

import requests

from config import (
    OWM_API_KEY,
    OWM_BASE_URL,
    OWM_ONECALL_URL,
    REQUEST_TIMEOUT,
)

def validate_city(city: str) -> bool:
    """
    Check if a city exists via OpenWeatherMap Geocoding API.
    """
    url = f"{OWM_BASE_URL}/weather"
    params = {
        "q": city,
        "appid": OWM_API_KEY,
    }
    try:
        response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
        return response.status_code == 200
    except Exception:
        return False

logger = logging.getLogger(__name__)


def get_weather(city: str) -> dict | None:
    """
    Fetch current weather data for a given city name.
    """

    url = f"{OWM_BASE_URL}/weather"

    params = {
        "q": city,
        "appid": OWM_API_KEY,
        "units": "metric",
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=REQUEST_TIMEOUT,
        )

        response.raise_for_status()

        data = response.json()

        return {
            "city": city,
            "temp": data["main"]["temp"],
            "feels_like": data["main"]["feels_like"],
            "humidity": data["main"]["humidity"],
            "pressure": data["main"]["pressure"],
            "wind_speed": data["wind"]["speed"],
            "rain_1h": data.get("rain", {}).get("1h", 0.0),
            "visibility": data.get("visibility", 10000),
            "weather_desc": data["weather"][0]["description"],
            "weather_code": data["weather"][0]["id"],
            "lat": data["coord"]["lat"],
            "lon": data["coord"]["lon"],
        }

    except requests.exceptions.RequestException as exc:
        logger.error(
            "Weather API error for %s: %s",
            city,
            exc,
        )
        return {
            "city": city,
            "temp": 25.0,
            "feels_like": 25.0,
            "humidity": 50,
            "pressure": 1013,
            "wind_speed": 5.0,
            "rain_1h": 0.0,
            "visibility": 10000,
            "weather_desc": "clear sky (fallback)",
            "weather_code": 800,
            "lat": 20.5937,
            "lon": 78.9629,
        }


def get_weather_alerts(lat: float, lon: float) -> list[dict]:
    """
    Fetch active weather alerts from One Call API.
    """

    url = OWM_ONECALL_URL

    params = {
        "lat": lat,
        "lon": lon,
        "exclude": "minutely,hourly,daily",
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

        alerts = data.get("alerts", [])

        return [
            {
                "event": a.get("event", "Unknown"),
                "sender_name": a.get("sender_name", ""),
                "description": a.get("description", ""),
                "severity": classify_alert_severity(
                    a.get("event", "")
                ),
            }
            for a in alerts
        ]

    except requests.exceptions.RequestException as exc:
        logger.error(
            "Alerts API error at (%.4f,%.4f): %s",
            lat,
            lon,
            exc,
        )
        return []


def classify_alert_severity(event: str) -> str:
    """
    Map alert event type to severity category.
    """

    event_lower = event.lower()

    if any(
        keyword in event_lower
        for keyword in [
            "cyclone",
            "extreme",
            "very heavy",
            "red alert",
        ]
    ):
        return "extreme"

    elif any(
        keyword in event_lower
        for keyword in [
            "heavy",
            "flood",
            "heat wave",
            "cold wave",
            "orange",
        ]
    ):
        return "severe"

    elif any(
        keyword in event_lower
        for keyword in [
            "moderate",
            "thunderstorm",
            "yellow",
        ]
    ):
        return "moderate"

    else:
        return "minor"

