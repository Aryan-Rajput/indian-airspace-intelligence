from pyspark import pipelines as dp
from pyspark.sql import functions as F

@dp.materialized_view(
    name="gold_hourly_metrics",
    comment="Hourly flight metrics aggregated from silver layer"
)
def gold_hourly_metrics():
    return (
        spark.read.table("silver_flights_phases")
        .groupBy(
            F.hour(F.col("ingestion_time")).alias("hour_of_day")
        )
        .agg(
            F.count("*").alias("total_flights"),
            F.countDistinct("icao24").alias("unique_aircrafts"),
            F.avg("velocity_kmh").alias("avg_velocity_kmh"),
            F.min("velocity_kmh").alias("min_velocity_kmh"),
            F.max("velocity_kmh").alias("max_velocity_kmh"),
            F.avg("baro_altitude").alias("avg_altitude"),
            F.max("baro_altitude").alias("max_altitude"),
            F.round(F.sum(F.when(F.col("flight_phase") == "GROUND", 1).otherwise(0)) / F.count("*") * 100, 2).alias("pct_on_ground"),
            F.round(F.sum(F.when(F.col("flight_phase") == "CLIMBING", 1).otherwise(0)) / F.count("*") * 100, 2).alias("pct_climbing"),
            F.round(F.sum(F.when(F.col("flight_phase") == "CRUISING", 1).otherwise(0)) / F.count("*") * 100, 2).alias("pct_cruising"),
            F.round(F.sum(F.when(F.col("flight_phase") == "DESCENDING", 1).otherwise(0)) / F.count("*") * 100, 2).alias("pct_descending")
        )
    )



























# Define schema for flights data
# flights_schema = StructType([
#     StructField("icao24", StringType()),
#     StructField("callsign", StringType()),
#     StructField("origin_country", StringType()),
#     StructField("time_position", LongType()),
#     StructField("last_contact", LongType()),
#     StructField("longitude", DoubleType()),
#     StructField("latitude", DoubleType()),
#     StructField("baro_altitude", DoubleType()),
#     StructField("on_ground", BooleanType()),
#     StructField("velocity", DoubleType()),
#     StructField("true_track", DoubleType()),
#     StructField("vertical_rate", DoubleType()),
#     StructField("sensors", StringType()),
#     StructField("geo_altitude", DoubleType()),
#     StructField("squawk", StringType()),
#     StructField("spi", BooleanType()),
#     StructField("position_source", IntegerType()),
#     StructField("aircraft_category", IntegerType()),
#     StructField("ingestion_timestamp", LongType()),
#     StructField("_ingested_at", StringType())
# ])