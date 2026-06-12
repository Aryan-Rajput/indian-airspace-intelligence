from pyspark import pipelines as dp
from pyspark.sql import functions as F, Window
from pyspark.sql.Types import DoubleType
import math

@F.udf(returnType=DoubleType())
def haversine(lon1, lat1, lon2, lat2):
  R = 6371
  phi1 = math.radians(lat1)
  phi2 = math.radians(lat2)
  dphi = phi2 - phi1
  dlambda = math.radians(lon2 - lon1)
  dist = R * 2 * math.atan(
    math.sqrt(
      math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    ), 
    math.sqrt(
      1 -  math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    )
  )
  return dist


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
    spark.read.table("india_only_airports")
    .withColumnRenamed("Latitude", "lat")
    .withColumnRenamed("Longitude", "lon")
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