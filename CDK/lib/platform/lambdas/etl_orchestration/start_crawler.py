import boto3

def handler(event, context):
    """
    Expects input: { "crawler_name": "DynamoDBenv" }
    """
    crawler_name = event['crawler_name']
    glue = boto3.client('glue')

    print(f"🚀 Starting crawler: {crawler_name}")

    try:
        glue.start_crawler(Name=crawler_name)
        print(f"✅ Successfully started crawler: {crawler_name}")
        return {
            'status': 'STARTED',
            'crawler': crawler_name
        }
    except glue.exceptions.CrawlerRunningException:
        print(f"⚠️ Crawler already running: {crawler_name}")
        return {
            'status': 'ALREADY_RUNNING',
            'crawler': crawler_name
        }
    except Exception as e:
        print(f"❌ Failed to start crawler: {crawler_name} — {str(e)}")
        return {
            'status': 'ERROR',
            'crawler': crawler_name,
            'error': str(e)
        }
