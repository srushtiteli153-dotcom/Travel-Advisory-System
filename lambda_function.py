
# lambda_function.py
# AWS Lambda entry point for Travel Advisory System

import json
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
import boto3

from config import (
    CITIES_CONFIG_FILE, 
    AWS_REGION, 
    SUBSCRIBERS_TABLE
)

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
subscribers_table = dynamodb.Table(SUBSCRIBERS_TABLE)

from services.weather_service import (
    get_weather,
    get_weather_alerts,
)

from services.aqi_service import (
    get_route_aqi_risk,
)

from services.traffic_service import (
    get_traffic_risk,
)

from engine.risk_engine import (
    compute_weather_risk,
    compute_alert_risk,
    compute_travel_risk_score,
    classify_risk,
    generate_advisory,
)

from services.notification_service import (
    store_advisory,
    send_notification,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

IST = ZoneInfo("Asia/Kolkata")


def get_active_routes() -> list[dict]:
    """
    Load active city-pair routes from current subscribers.
    """
    try:
        response = subscribers_table.scan()
        items = response.get('Items', [])
        
        unique_routes = set()
        active_routes = []
        
        for item in items:
            route_str = item.get('route')
            if route_str and route_str not in unique_routes:
                unique_routes.add(route_str)
                parts = route_str.split(" -> ")
                if len(parts) == 2:
                    active_routes.append({
                        "origin": parts[0].strip(),
                        "destination": parts[1].strip()
                    })
        return active_routes
    except Exception as e:
        logger.error(f"Failed to fetch active routes: {e}")
        return []


def process_route(route: dict, target_email: str = None) -> dict | None:
    """
    Process a single city-pair route and return advisory result.
    If target_email is provided, sends the email ONLY to that address.
    """

    origin = route["origin"]
    destination = route["destination"]

    logger.info("Processing route: %s -> %s", origin, destination)

    # fetch live weather
    origin_weather = get_weather(origin)
    dest_weather = get_weather(destination)

    if not origin_weather or not dest_weather:
        logger.warning(
            "Weather data unavailable for %s->%s; skipping.",
            origin,
            destination,
        )
        return None

    # Use destination weather as primary advisory weather
    weather = dest_weather

    weather["rain_1h"] = max(
        origin_weather.get("rain_1h", 0),
        dest_weather.get("rain_1h", 0),
    )

    # fetch weather alerts
    origin_alerts = get_weather_alerts(
        origin_weather["lat"],
        origin_weather["lon"],
    )

    dest_alerts = get_weather_alerts(
        dest_weather["lat"],
        dest_weather["lon"],
    )

    all_alerts = origin_alerts + dest_alerts

    # fetch air quality data
    aqi = get_route_aqi_risk(
        origin_weather["lat"],
        origin_weather["lon"],
        dest_weather["lat"],
        dest_weather["lon"],
    )

    # compute traffic delays
    traffic = get_traffic_risk(origin, destination)

    # calculate final risk score based on all factors
    weather_risk = compute_weather_risk(weather, all_alerts)
    alert_risk = compute_alert_risk(all_alerts)
    aqi_risk = aqi["aqi_risk"]
    traffic_risk = traffic["traffic_risk"]

    risk_score = compute_travel_risk_score(
        weather_risk,
        aqi_risk,
        traffic_risk,
        alert_risk,
    )

    risk_level = classify_risk(risk_score)

    # generate the text message
    advisory_text = generate_advisory(
        origin,
        destination,
        risk_score,
        risk_level,
        weather,
        aqi,
        traffic,
        all_alerts,
    )

    # save to database
    record_id = store_advisory(
        origin,
        destination,
        risk_score,
        risk_level,
        advisory_text,
        weather,
        aqi,
        traffic,
    )

    # email the users
    send_notification(
        origin,
        destination,
        risk_level,
        advisory_text,
        target_email,
    )

    return {
        "route": f"{origin} -> {destination}",
        "risk_score": risk_score,
        "risk_level": risk_level,
        "record_id": record_id,
    }


def process_new_subscription(origin: str, destination: str, email: str):
    """
    Process a route immediately for a new subscriber without triggering the hourly cron.
    """
    route = {"origin": origin, "destination": destination}
    # Pass the email so it ONLY sends to this specific person
    try:
        process_route(route, target_email=email)
    except Exception as e:
        print(f"Skipped instant email due to Render firewall: {e}")


def cleanup_subscriptions():
    """
    Remove expired subscriptions from DynamoDB.
    """
    logger.info("Starting subscription cleanup...")
    try:
        response = subscribers_table.scan()
        items = response.get('Items', [])
        
        today = datetime.now(IST).date().isoformat()
        now = datetime.now().isoformat()
            
        for item in items:
            expiration_time = item.get("expiration_time")
            end_date = item.get("end_date") # fallback for old records
            
            expired = False
            if expiration_time and expiration_time < now:
                expired = True
            elif end_date and end_date < today:
                expired = True
                
            if expired:
                email = item.get("email")
                logger.info(f"Subscription expired for {email}. Deleting from DynamoDB...")
                        
                # delete from db
                subscribers_table.delete_item(
                    Key={'subscription_id': item['subscription_id']}
                )
    except Exception as e:
        logger.error(f"Error during subscription cleanup: {e}")


def lambda_handler(event, context):
    """
    AWS Lambda entry point triggered by EventBridge schedule.
    """

    start_time = datetime.now(IST)

    logger.info(
        "Travel Advisory System invoked at %s",
        start_time.isoformat(),
    )

    try:
        # clean up old expired subscriptions first
        cleanup_subscriptions()

        routes = get_active_routes()

        results = []
        errors = 0

        for route in routes:
            try:
                result = process_route(route)

                if result:
                    results.append(result)

            except Exception as exc:
                logger.error(
                    "Unhandled error processing route %s->%s: %s",
                    route.get("origin"),
                    route.get("destination"),
                    exc,
                )
                errors += 1

        end_time = datetime.now(IST)

        duration = (end_time - start_time).total_seconds()

        logger.info(
            "Advisory cycle complete. Routes processed: %d, Errors: %d, Duration: %.1fs",
            len(results),
            errors,
            duration,
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Travel advisory cycle completed.",
                    "processed": len(results),
                    "errors": errors,
                    "duration_s": round(duration, 1),
                    "results": results,
                }
            ),
        }

    except Exception as exc:
        logger.critical("Fatal error in lambda_handler: %s", exc)

        return {
            "statusCode": 500,
            "body": json.dumps(
                {
                    "error": str(exc),
                }
            ),
        }
