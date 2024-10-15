import os
import boto3

s3 = boto3.client('s3')

def handler(event, context):
    # Get the bucket name from the environment variable
    bucket_name = os.getenv('S3_BUCKET_NAME')
    
    # Directory where the images are stored locally (inside the Lambda asset bundle)
    image_dir = '/mnt/images'  # Change this to match your Lambda packaging path if necessary
    
    # Loop through files in the image directory and upload them to S3 if they don't already exist
    for filename in os.listdir(image_dir):
        if filename.endswith((".jpg", ".png")):
            s3_key = f"images/{filename}"
            
            # Check if the file already exists in S3
            try:
                s3.head_object(Bucket=bucket_name, Key=s3_key)
                print(f"{filename} already exists in {bucket_name}, skipping upload.")
            except s3.exceptions.ClientError:
                # Upload the file if it doesn't exist
                file_path = os.path.join(image_dir, filename)
                s3.upload_file(file_path, bucket_name, s3_key)
                print(f"Uploaded {filename} to {bucket_name}")
    
    return {"statusCode": 200, "body": "File upload check complete"}
