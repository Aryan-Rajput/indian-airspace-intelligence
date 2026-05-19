import dlt
from pyspark.sql.functions import col, when

@dlt.table
def silver_flights():
    return (
        dlt.read_stream("bronze_flights")
        .filter(col("latitude").isNotNull() & col("longitude").isNotNull())
        .withColumn("velocity_kmh", col("velocity") * 3.6)
        .withColumn("carrier_code", col("callsign").substr(1, 3))
        .withColumn(
            "flight_phase",
            when(col("on_ground") == True, "GROUND")
            .when(col("vertical_rate") > 1.0, "CLIMBING")
            .when(col("vertical_rate") < -1.0, "DESCENDING")
            .otherwise("CRUISING")
        )
    )