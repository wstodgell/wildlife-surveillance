"""
setup_mqtt.py

Establishes a secure MQTT connection to AWS IoT Core using device certificates and credentials
retrieved from AWS Secrets Manager. Also provides utilities to log messages to CloudWatch Logs.

Key Features:
- Downloads the Amazon Root CA certificate
- Retrieves private key and certificate from Secrets Manager
- Establishes an MQTT connection using AWSIoTPythonSDK
- Logs connection and publish events to CloudWatch Logs
"""

import boto3
import time
import json
import logging
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
from botocore.exceptions import ClientError
import requests
import tempfile
import os
import configuration
from colorama import Fore, Style, init

# Set up logging
logging.basicConfig(level=logging.INFO)

# Initialize CloudWatch Logs client
logs_client = boto3.client('logs', region_name='us-east-1')

# Function to log errors to CloudWatch and create log group/stream if they don't exist
def log_to_cloudwatch(message):
    """
    Logs a message to AWS CloudWatch Logs. Automatically creates the log group and stream
    if they do not exist.
    """
    try:
        # Ensure the log group exists
        logs_client.create_log_group(logGroupName=configuration.LOG_GROUP)
    except logs_client.exceptions.ResourceAlreadyExistsException:
        # Log group already exists, continue
        pass

    try:
        # Ensure the log stream exists
        logs_client.create_log_stream(logGroupName=configuration.LOG_GROUP, logStreamName=configuration.LOG_STREAM)
    except logs_client.exceptions.ResourceAlreadyExistsException:
        # Log stream already exists, continue
        pass

    try:
        # Get the sequence token for the log stream (if exists)
        response = logs_client.describe_log_streams(logGroupName=configuration.LOG_GROUP, logStreamNamePrefix=configuration.LOG_STREAM)
        log_streams = response['logStreams']
        sequence_token = log_streams[0].get('uploadSequenceToken') if log_streams else None

        # Put log event with the correct sequence token (if required)
        if sequence_token:
            logs_client.put_log_events(
                logGroupName=configuration.LOG_GROUP,
                logStreamName=configuration.LOG_STREAM,
                logEvents=[
                    {
                        'timestamp': int(time.time() * 1000),
                        'message': message
                    }
                ],
                sequenceToken=sequence_token
            )
        else:
            # No sequence token needed for the first log
            logs_client.put_log_events(
                logGroupName=configuration.LOG_GROUP,
                logStreamName=configuration.LOG_STREAM,
                logEvents=[
                    {
                        'timestamp': int(time.time() * 1000),
                        'message': message
                    }
                ]
            )
    except ClientError as e:
        logging.error(f"Failed to log to CloudWatch: {e}")

# Function to download the Root CA certificate
def download_root_ca():
    """
    Downloads the Amazon Root CA certificate required for establishing TLS MQTT connections.
    """
    try:
        # sends an HTTP GET request to Amazon's trust repository and retrieves the AmazonRootCA1.pem file.
        url = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
        response = requests.get(url)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pem") as temp_file:
            temp_file.write(response.content)
            root_ca_path = temp_file.name

        return root_ca_path
    except Exception as e:
        log_to_cloudwatch(f"Failed to download Root CA: {e}")
        raise e

# Function to retrieve the IoT Endpoint from AWS IoT Core
def get_iot_endpoint():
    """
    Retrieves the AWS IoT Core Data endpoint for the account/region.
    """
    try:
        client = boto3.client('iot', region_name='us-east-1')
        response = client.describe_endpoint(endpointType='iot:Data-ATS')
        return response['endpointAddress']
    except ClientError as e:
        log_to_cloudwatch(f"Failed to get IoT endpoint: {e}")
        raise e

# Function to retrieve IoT certificates from AWS Secrets Manager (utilizes the IoTTaskRole ex: gpsTaskRole)
def get_secret():
    """
    Retrieves IoT device certificate and private key from AWS Secrets Manager.
    """
    secret_name = configuration.CERT_SECRET_NAME #not best practice, you shouldn't hardcore secret names
    region_name = "us-east-1"

    try:
        session = boto3.session.Session()
        client = session.client(service_name='secretsmanager', region_name=region_name)
        response = client.get_secret_value(SecretId=secret_name)
        return response.get('SecretString', None)
    except ClientError as e:
        log_to_cloudwatch(f"Failed to get IoT secret: {e}")
        raise e

# Function to parse the secret string into private key and certificate
def parse_secret(secret_string):
    """
    Parses a combined PEM secret string into its certificate and private key components.

    Parameters:
        secret_string (str): The combined PEM string.

    Returns:
        tuple: (private_key, certificate)
    """
    private_key_start = secret_string.find("-----BEGIN RSA PRIVATE KEY-----")
    private_key_end = secret_string.find("-----END RSA PRIVATE KEY-----") + len("-----END RSA PRIVATE KEY-----")
    private_key = secret_string[private_key_start:private_key_end]

    certificate_start = secret_string.find("-----BEGIN CERTIFICATE-----")
    certificate_end = secret_string.find("-----END CERTIFICATE-----") + len("-----END CERTIFICATE-----")
    certificate = secret_string[certificate_start:certificate_end]

    return private_key, certificate

# Function to write content (certificates/keys) to a temporary file
def write_to_temp_file(content, filename_prefix):
    """
    Writes PEM content (certificate or private key) to a temporary file.

    Parameters:
        content (str): PEM-formatted string content.
        filename_prefix (str): Prefix to use for the filename.

    Returns:
        str: Path to the written temporary file.
    """
    temp_file_path = f"./{filename_prefix}.pem"
    with open(temp_file_path, 'w') as f:
        f.write(content)
    return temp_file_path

# Function to establish MQTT connection
def mqtt_connect():
    """
    Establishes a secure MQTT connection to AWS IoT Core using X.509 certificates.

    Returns:
        AWSIoTMQTTClient: An initialized and connected MQTT client.
    """
    try:
        # Download Root CA
        root_ca = download_root_ca()

        # Get secret (private key and certificate)
        secret = get_secret()
        private_key, certificate = parse_secret(secret)

        # Write the private key and certificate to temp files
        cert_file = write_to_temp_file(certificate, 'cert')
        key_file = write_to_temp_file(private_key, 'private_key')

        # Get IoT Endpoint
        iot_endpoint = get_iot_endpoint()

        # Initialize MQTT Client
        mqtt_client = AWSIoTMQTTClient(configuration.CLIENT_ID)
        mqtt_client.configureEndpoint(iot_endpoint, 8883)
        mqtt_client.configureCredentials(root_ca, key_file, cert_file)

        # Configure MQTT client settings
        mqtt_client.configureOfflinePublishQueueing(-1)
        mqtt_client.configureDrainingFrequency(2)
        mqtt_client.configureConnectDisconnectTimeout(10)
        mqtt_client.configureMQTTOperationTimeout(5)

        # Attempt to connect to AWS IoT Core
        if mqtt_client.connect():
            logging.info("Connected to AWS IoT Core")
            log_to_cloudwatch("Connected to AWS IoT Core")
            return mqtt_client
        else:
            raise Exception("Failed to connect to AWS IoT Core")

    except Exception as e:
        log_to_cloudwatch(f"MQTT connection error: {e}")
        raise e
