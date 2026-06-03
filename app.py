import json
import logging
from flask import Flask, request, jsonify
import boto3
from boto3.dynamodb.conditions import Key
import uuid
from datetime import datetime, timedelta
from flask_cors import CORS

from config import AWS_REGION, DYNAMODB_TABLE, SUBSCRIBERS_TABLE, CITIES_CONFIG_FILE
import lambda_function
from services.weather_service import validate_city

app = Flask(__name__)
CORS(app) # Allow cross-origin requests

# setup aws resources
dynamodb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = dynamodb.Table(DYNAMODB_TABLE)
subscribers_table = dynamodb.Table(SUBSCRIBERS_TABLE)


@app.route("/api/advisories", methods=["GET"])
def get_advisories():
    advisories = []
    # get all advisories from db
    try:
        response = table.scan()
        all_items = response.get('Items', [])
    except Exception as e:
        logging.error(f"Error scanning table: {e}")
        all_items = []

    # sort newest first
    all_items.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    # get only the latest advisory per route
    seen_routes = set()
    for item in all_items:
        route_id = item.get('route_id')
        if route_id and route_id not in seen_routes:
            advisories.append(item)
            seen_routes.add(route_id)
            
    return jsonify({"advisories": advisories})

@app.route("/api/subscribe", methods=["POST"])
def subscribe():
    data = request.json
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400
        
    email = data.get("email")
    route_origin = data.get("origin", "").strip()
    route_dest = data.get("destination", "").strip()
    
    if not validate_city(route_origin):
        return jsonify({"error": f"Could not find the city '{route_origin}'. Please check your spelling."}), 400
        
    if not validate_city(route_dest):
        return jsonify({"error": f"Could not find the city '{route_dest}'. Please check your spelling."}), 400
    
    route_str = f"{route_origin} -> {route_dest}"
    expiration_time = (datetime.now() + timedelta(hours=24)).isoformat()
    
    try:
        # save sub to db
        sub_id = str(uuid.uuid4())
        subscribers_table.put_item(
            Item={
                "subscription_id": sub_id,
                "email": email,
                "route": route_str,
                "expiration_time": expiration_time
            }
        )
        
        success_msg = f"Successfully added {route_str} to your active alerts for the next 24 hours!"
        # send email to the new subscriber
        lambda_function.process_new_subscription(route_origin, route_dest, email)
        
        return jsonify({"message": success_msg})
                    
    except Exception as e:
        return jsonify({"error": f"Failed to subscribe: {str(e)}"}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000)
