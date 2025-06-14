"""
configuration.py

Handles IoT device configuration:
- Fetches MQTT topic and publish interval from AWS SSM Parameter Store
- Builds message payloads for transmission
"""

import boto3
from colorama import Fore, Style, init
import time
import uuid

CLIENT_ID = "GPSCollar"
GPS_TOPIC_NAME = None
LOG_GROUP = "/docker/GPS"
CERT_SECRET_NAME = "IoT/GPSThing/certs"
TESTING = False
LOG_STREAM = "mqtt_connect"

def setup_config():
    """Fetch GPS topic name from AWS SSM and store in a global variable."""
    global GPS_TOPIC_NAME
    # SSM = Simple Systems Manager - outdated name for what is now AWS Systems Manager
    ssm = boto3.client('ssm')
    # Get a parameter
    response = ssm.get_parameter(
        Name='/iot-topics/gps-topic-name',  # Name of the parameter you want to retrieve
        WithDecryption=False  # Set to True if it's a SecureString parameter
    )

    # Extract the value
    GPS_TOPIC_NAME = response['Parameter']['Value']
    print(f"{Fore.RED}*******************Retrieved {GPS_TOPIC_NAME}{Style.RESET_ALL}")


def get_fresh_publish_interval():
    """Fetch the current GPS publish interval from SSM (in seconds)."""
    try:
        ssm = boto3.client('ssm')
        response = ssm.get_parameter(Name='/iot-settings/gps-publish-interval', WithDecryption=False)
        return int(response['Parameter']['Value'])
    except Exception as e:
        print(f"⚠️ Failed to fetch publish interval, using default: {e}")
        return 15  # Fallback default

def create_topic(payload):
  """Format a payload of elk positions into a message for AWS IoT Core."""
  transformed_payload = [
    {"elk_id": elk_id, "lat": lat, "lon": lon}
    for elk_id, (lat, lon) in enumerate(payload)
  ]
  return {
    "messageId": str(uuid.uuid4()),
    "topic": GPS_TOPIC_NAME,
    "timestamp": time.time(),
    "payload": transformed_payload
  }
