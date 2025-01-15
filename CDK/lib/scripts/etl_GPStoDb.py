import sys
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.transforms import *
from awsglue.utils import getResolvedOptions

# Initialize Glue job
args = getResolvedOptions(sys.argv, ['JOB_NAME', 's3_output_path'])  # Get the s3_output_path argument
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read from DynamoDB table
dynamo_frame = glueContext.create_dynamic_frame.from_options(
    connection_type="dynamodb",
    connection_options={
        "dynamodb.input.tableName": "GpsDataTable",  # Replace with your table name
        "dynamodb.throughput.read.percent": "0.5"   # Adjust throughput usage as needed
    }
)

# Step 3: Write the data to the S3 bucket in Parquet format (suitable for Athena queries)
s3_output_path = args['s3_output_path']  # Use the passed S3 output path
glueContext.write_dynamic_frame.from_options(
    frame=dynamo_frame,
    connection_type="s3",
    connection_options={
        "path": s3_output_path
    },
    format="parquet"
)

# Step 4: Commit the job to signal completion
job.commit()
