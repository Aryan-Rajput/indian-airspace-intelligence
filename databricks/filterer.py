import pandas as pd

def filter_indian_airports():
    df = pd.read_csv("airports.csv")
    df_india = df[df["iso_country"] == "IN"]
    df_india.to_csv("india_only.csv", index=False)
    df_india = df_india[df_india["type"].isin(['large_airport', 'medium_airport', 'small_airport'])]  # filter out rows where 'type' is NaN, seaplane_base, heliport, or closed
    return (
        df_india[["name", "ident", "iata_code", "latitude_deg", "longitude_deg", "type"]]
        .rename(columns={
            "name": "Name",
            "ident": "ICAO",
            "iata_code": "IATA",
            "latitude_deg": "Latitude",
            "longitude_deg": "Longitude",
            "type": "Type"
        })
    )


df_india = filter_indian_airports()
# print(df_india["Type"].drop_duplicates())
df_india.to_csv("india_only.csv", index=False)