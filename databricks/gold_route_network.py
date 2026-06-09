from pyspark import pipelines as dp
from pyspark.sql import functions as F, Window
@dp.materialized_view(
  name="gold_route_network"
  comment="creating network between diff flights and connecting corridors for continuous flights"
)
def gold_route_network():
  window = Window.partitionBy("icao24").orderBy("ingestion_time")
  df = (
    spark.read.table("silver_flights_phases")
    .withColumn("prev_on_ground", F.lag("on_ground", 1).over(window))
  )
  df_airport = (
    
  )
  return ( 
    df
    .select(
      "icao24", "on_ground", "prev_on_ground",
      "latitude", "longitude", "ingestion_timestamp"
    )
    .filter(
      (F.col("on_ground") == True) & (F.col("prev_on_ground") == False)
    ) 
  )