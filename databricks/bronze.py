import dlt
from pyspark.sql.types import (
    StructType, StructField, StringType, LongType,
    DoubleType, BooleanType, IntegerType
)

schema = StructType([
    StructField("icao24", StringType()),
    StructField("callsign", StringType()),
    StructField("origin_country", StringType()),
    StructField("time_position", LongType()),
    StructField("last_contact", LongType()),
    StructField("longitude", DoubleType()),
    StructField("latitude", DoubleType()),
    StructField("baro_altitude", DoubleType()),
    StructField("on_ground", BooleanType()),
    StructField("velocity", DoubleType()),
    StructField("true_track", DoubleType()),
    StructField("vertical_rate", DoubleType()),
    StructField("sensors", StringType()),
    StructField("geo_altitude", DoubleType()),
    StructField("squawk", StringType()),
    StructField("spi", BooleanType()),
    StructField("position_source", IntegerType()),
    StructField("aircraft_category", IntegerType()),
    StructField("ingestion_timestamp", LongType())
])

@dlt.table
def bronze_flights():
    return spark.readStream.format("cloudFiles") \
        .option("cloudFiles.format", "json") \
        .option("cloudFiles.schemaLocation", "dbfs:/checkpoints/bronze_flights") \
        .schema(schema) \
        .load("s3a://airspace-intelligence-ar/raw/flights/")






























# STATE VECTOR FIELDS (18 total, by index):   
# 0:icao24, 
# 1:callsign, 
# 2:origin_country, 
# 3:time_position,   
# 4:last_contact, 
# 5:longitude, 
# 6:latitude, 
# 7:baro_altitude,   
# 8:on_ground, 
# 9:velocity(m/s), 
# 10:true_track, 
# 11:vertical_rate, 
# 12:sensors(null), 
# 13:geo_altitude, 
# 14:squawk, 
# 15:spi, 
# 16:position_source, 
# 17:aircraft_category

