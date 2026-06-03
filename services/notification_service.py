# notification_service.py
# Store advisories in DynamoDB and notify via Gmail (smtplib)

import logging
import uuid
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from zoneinfo import ZoneInfo
import boto3
from boto3.dynamodb.conditions import Attr

from config import (
    AWS_REGION,
    DYNAMODB_TABLE,
    SUBSCRIBERS_TABLE,
    GMAIL_USER,
    GMAIL_APP_PASSWORD,
    RISK_LOW,
)

logger = logging.getLogger(__name__)
IST = ZoneInfo("Asia/Kolkata")

dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)
subscribers_table = dynamodb.Table(SUBSCRIBERS_TABLE)

def store_advisory(
    origin: str,
    destination: str,
    risk_score: float,
    risk_level: str,
    advisory_text: str,
    weather: dict,
    aqi: dict,
    traffic: dict,
) -> str:
    """
    Persist travel advisory record to DynamoDB.
    """
    record_id = str(uuid.uuid4())
    timestamp = datetime.now(IST).isoformat()
    # create a unique id for this route pair
    route_id = f"{origin.replace(' ', '_')}_{destination.replace(' ', '_')}"

    try:
        table.put_item(
            Item={
                "record_id": record_id,
                "route_id": route_id,
                "timestamp": timestamp,
                "origin": origin,
                "destination": destination,
                "risk_score": str(round(risk_score, 1)),
                "risk_level": risk_level,
                "advisory_text": advisory_text,
                "temp": str(weather.get("temp", "")),
                "rain_1h": str(weather.get("rain_1h", 0)),
                "wind_speed": str(weather.get("wind_speed", 0)),
                "aqi_index": str(aqi.get("aqi_index", "")),
                "aqi_label": aqi.get("aqi_label", ""),
                "traffic_score": str(traffic.get("traffic_risk", "")),
            }
        )
        logger.info("Advisory stored: %s route=%s level=%s", record_id, route_id, risk_level)
        return record_id
    except Exception as exc:
        logger.error("DynamoDB put_item failed: %s", exc)
        return ""

def get_subscribers_for_route(route_str: str) -> list:
    """
    Query DynamoDB for all active subscribers for a specific route.
    """
    try:
        response = subscribers_table.scan(
            FilterExpression=Attr('route').eq(route_str)
        )
        return list(set([item.get('email') for item in response.get('Items', []) if item.get('email')]))
    except Exception as e:
        logger.error("Failed to query subscribers: %s", e)
        return []

def send_notification(
    origin: str,
    destination: str,
    risk_level: str,
    advisory_text: str,
    target_email: str = None
) -> None:
    """
    Send email notification via Gmail SMTP to all subscribers of this route,
    or to a specific target_email if provided.
    """
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        logger.warning("GMAIL_USER or GMAIL_APP_PASSWORD not set. Skipping email.")
        return

    route_str = f"{origin} -> {destination}"
    
    if target_email:
        subscribers = [target_email]
    else:
        subscribers = get_subscribers_for_route(route_str)
    
    if not subscribers:
        logger.info("No active subscribers for route %s", route_str)
        return

    subject = f"[{risk_level.upper()} TRAVEL RISK] {origin} to {destination} Advisory"
    
    # Format a beautiful HTML email
    html_content = f"""
    <html>
      <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
        <div style="background-color: #2563eb; color: white; padding: 20px; border-radius: 8px 8px 0 0; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">Travel Advisory System</h1>
        </div>
        <div style="border: 1px solid #e5e7eb; border-top: none; padding: 20px; border-radius: 0 0 8px 8px;">
            <h2 style="color: #1e40af; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px;">{origin} ➔ {destination}</h2>
            <div style="background-color: {'#fee2e2' if risk_level == 'High' else '#fef3c7' if risk_level == 'Moderate' else '#dcfce7'}; 
                        padding: 15px; border-radius: 6px; margin: 20px 0;">
                <strong>Risk Level: </strong><span style="font-size: 1.1em;">{risk_level.upper()}</span>
            </div>
            <div style="white-space: pre-wrap; font-size: 15px;">{advisory_text}</div>
            <p style="margin-top: 30px; font-size: 12px; color: #6b7280; text-align: center;">
                You are receiving this because you subscribed to alerts for {route_str}.<br>
                Alerts automatically expire after 24 hours.
            </p>
        </div>
      </body>
    </html>
    """

    try:
        # connect to gmail
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)

        for email in subscribers:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"Travel Advisory System <{GMAIL_USER}>"
            msg['To'] = email
            
            # bundle text and html versions together
            part1 = MIMEText(advisory_text, 'plain')
            part2 = MIMEText(html_content, 'html')
            msg.attach(part1)
            msg.attach(part2)

            server.send_message(msg)
            logger.info("Sent email to %s for %s", email, route_str)

        server.quit()
        logger.info("Successfully sent %d emails for route %s", len(subscribers), route_str)

    except Exception as exc:
        logger.error("Failed to send Gmail SMTP notification: %s", exc)
