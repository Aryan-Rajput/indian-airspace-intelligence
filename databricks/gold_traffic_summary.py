from pyspark import pipelines as dp
from pyspark.sql import functions as F, Window

@dp.materialized_view(
    name="gold_traffic_summary",
    comment="Traffic summary for each flight carrier"
)
def gold_traffic_summary():
    df =(
        spark.read.table("silver_flights_phases")
        .groupBy(F.col("carrier_code"))
        .agg(
            F.count("*").alias("total_traffic"),
            F.sum(F.when(F.col("flight_phase") == "CLIMBING", 1).otherwise(0)).alias("climb_traffic"),
            F.sum(F.when(F.col("flight_phase") == "DESCENDING", 1).otherwise(0)).alias("descent_traffic"),
            F.sum(F.when(F.col("flight_phase") == "CRUISING", 1).otherwise(0)).alias("crusing_traffic"),
            F.sum(F.when(F.col("flight_phase") == "GROUND", 1).otherwise(0)).alias("ground_traffic"),
            F.avg(F.col("velocity_kmh")).alias("avg_speed"),
            F.avg(F.col("baro_altitude")).alias("avg_baro_altitude")

        )
    )
    return (
        df
        .withColumn(
            "pct_of_total_traffic", F.round(((F.col("total_traffic")/F.sum("total_traffic").over(Window.partitionBy(F.lit(1))))*100), 2)
        )
    )