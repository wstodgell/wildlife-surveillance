import sys
from pyspark.context import SparkContext
from awsglue.context import GlueContext
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from pyspark.sql.functions import col
from pyspark.sql.types import DoubleType, IntegerType, StringType

# Glue’s insane parameter dance — because it refuses to just take config like a normal job
args = getResolvedOptions(sys.argv, ['JOB_NAME', 's3_output_path'])

# SparkContext is required because Glue runs on Spark under the hood (and it's weirdly verbose about it)
sc = SparkContext()
glueContext = GlueContext(sc)
spark = glueContext.spark_session
job = Job(glueContext)
job.init(args['JOB_NAME'], args)

# Read from DynamoDB — and yes, Glue can't infer schema or flatten nested fields automatically, 
# so you're gonna suffer if your JSON isn't simple
dynamo_frame = glueContext.create_dynamic_frame.from_options(
    connection_type="dynamodb",
    connection_options={
        "dynamodb.input.tableName": "HeaDataTable",
        "dynamodb.throughput.read.percent": "1.0"
    }
)

# Convert Glue's bizarro DynamicFrame into a normal Spark DataFrame so you can actually work with it
df = dynamo_frame.toDF()


# 🔥 THIS is where the pain starts:
# DynamoDB stores nested JSON inside attributes like { "double": 38.5 }, so you must manually reach into each field.
# Glue won't flatten it for you. You have to `.select()` and `.cast()` like a surgeon.
# If you skip this, you'll get ANALYSIS EXCEPTION errors from Athena or Glue.
df_clean = df.select(
    col("SensorId").cast(StringType()),
    col("ElkId").cast(StringType()),
    col("Topic").cast(StringType()),
    col("Timestamp").cast(StringType()),
    col("Posture").cast(StringType()),
    col("HeartRate").cast(IntegerType()),
    col("RespirationRate").cast(IntegerType()),
    col("BodyTemperature.double").cast(DoubleType()).alias("BodyTemperature"),
    col("HydrationLevel.double").cast(DoubleType()).alias("HydrationLevel"),
    col("ActivityLevel.double").cast(DoubleType()).alias("ActivityLevel"),
    col("StressLevel.double").cast(DoubleType()).alias("StressLevel")
)

# Write cleaned data to S3 as compact JSON
df_clean.coalesce(1).write.mode('overwrite').json(args['s3_output_path'])

job.commit()
