id="xg3m9n"
# config.py
# Configuration constants for Travel Advisory System

import os
import boto3
from dotenv import load_dotenv

# Load local .env file if it exists
load_dotenv()

# ──────────────────────────────────────────────────────────────
# AWS Configuration
# ──────────────────────────────────────────────────────────────

AWS_REGION = os.environ.get(
    "AWS_REGION",
    "ap-south-1",
)

# Auto-discover the real AWS names if running locally
DYNAMODB_TABLE_DEFAULT = "TravelAdvisories"
SUBSCRIBERS_TABLE_DEFAULT = "TravelSubscribers"
SNS_TOPIC_ARN_DEFAULT = "arn:aws:sns:ap-south-1:ACCOUNT_ID:TravelAdvisoryTopic"

try:
    cf = boto3.client('cloudformation', region_name=AWS_REGION)
    stack = cf.describe_stacks(StackName='travel-advisory-system')
    for out in stack['Stacks'][0].get('Outputs', []):
        if out['OutputKey'] == 'TravelAdvisoriesTableName':
            DYNAMODB_TABLE_DEFAULT = out['OutputValue']
        elif out['OutputKey'] == 'SubscribersTableName':
            SUBSCRIBERS_TABLE_DEFAULT = out['OutputValue']
except Exception as e:
    pass

GMAIL_USER = os.environ.get("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.environ.get("GMAIL_APP_PASSWORD", "")

DYNAMODB_TABLE = os.environ.get(
    "DYNAMODB_TABLE",
    DYNAMODB_TABLE_DEFAULT,
)

SUBSCRIBERS_TABLE = os.environ.get(
    "SUBSCRIBERS_TABLE",
    SUBSCRIBERS_TABLE_DEFAULT,
)

# ──────────────────────────────────────────────────────────────
# OpenWeatherMap API Configuration
# ──────────────────────────────────────────────────────────────

OWM_API_KEY = "1844647657e979fe8a46cf2730170256"

OWM_BASE_URL = "https://api.openweathermap.org/data/2.5"

OWM_ONECALL_URL = (
    "https://api.openweathermap.org/data/3.0/onecall"
)

# ──────────────────────────────────────────────────────────────
# Risk Score Weights
# ──────────────────────────────────────────────────────────────

WEIGHT_WEATHER = 0.40
WEIGHT_AQI = 0.25
WEIGHT_TRAFFIC = 0.25
WEIGHT_ALERT = 0.10

# ──────────────────────────────────────────────────────────────
# Risk Tier Thresholds
# ──────────────────────────────────────────────────────────────

RISK_LOW = 25
RISK_MODERATE = 50
RISK_HIGH = 75

# ──────────────────────────────────────────────────────────────
# City Pair Configuration
# ──────────────────────────────────────────────────────────────

CITIES_CONFIG_FILE = "cities.json"

# ──────────────────────────────────────────────────────────────
# Request Settings
# ──────────────────────────────────────────────────────────────

REQUEST_TIMEOUT = 10  # seconds
MAX_RETRIES = 2
