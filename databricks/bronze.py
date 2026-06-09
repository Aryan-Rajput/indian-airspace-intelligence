from pyspark import pipelines as dp 
from pyspark.sql import functions as F
from pyspark.sql.types import StructType, StructField, StringType, LongType, DoubleType, BooleanType, IntegerType

@dp.table(
    name="bronze_flights",
    comment="Raw flights data imported from S3"
)
def bronze_flights():
    return (
        spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "json")
        .option("cloudFiles.inferColumnTypes", "true")
        .load("s3a://airspace-intelligence-ar/raw/flights/")
        .withColumn("_ingested_at", F.current_timestamp())
    )
