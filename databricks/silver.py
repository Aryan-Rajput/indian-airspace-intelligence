from pyspark import pipelines as dp 
from pyspark.sql import functions as F

@dp.table(
    name="silver_flights_phases",
    comment="phased data for flights"
)
def silver_flights():
    return (
        spark.readStream.table("bronze_flights")
        .filter(F.col("icao24").isNotNull())
        .filter(F.col("latitude").isNotNull())
        .filter(F.col("longitude").isNotNull())
        .withColumn("last_contact_ts", F.from_unixtime(F.col("last_contact")))
        .withColumn("time_position_ts", F.from_unixtime(F.col("time_position")))
        .withColumn("flight_phase",
            F.when(F.col("on_ground"), "GROUND")
            .when(F.col("vertical_rate") > 1.0, "CLIMBING")
            .when(F.col("vertical_rate") < -1.0, "DESCENDING")
            .otherwise("CRUISING")
        )
        .withColumn("velocity_kmh", F.col("velocity") * 3.6)
        .withColumn("carrier_code", F.substring(F.col("callsign"), 1, 3))
        .withColumn("ingestion_time", F.to_timestamp(F.from_unixtime(F.col("ingestion_timestamp"))))
    )





