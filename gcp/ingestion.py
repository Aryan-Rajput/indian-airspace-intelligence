import json
import boto3
import requests
from datetime import datetime, timezone

FIELDS = [
    "icao24", "callsign", "origin_country", "time_position", "last_contact",
    "longitude", "latitude", "baro_altitude", "on_ground", "velocity",
    "true_track", "vertical_rate", "sensors", "geo_altitude", "squawk",
    "spi", "position_source", "aircraft_category"
]

INDIA_BBOX = {
    "lamin": 8.0, "lomin": 68.0,
    "lamax": 37.0, "lomax": 97.0
}

S3_BUCKET = "airspace-intelligence-ar"
OPENSKY_SECRET = "airspace/opensky"
OPENSKY_URL = "https://opensky-network.org/api/states/all"


def get_opensky_creds():
    client = boto3.client("secretsmanager", region_name="ap-southeast-1")
    secret = client.get_secret_value(SecretId=OPENSKY_SECRET)
    creds = json.loads(secret["SecretString"])
    return creds["username"], creds["password"]


def parse_states(raw_states, ingestion_ts):
    records = []
    for state in raw_states:
        record = dict(zip(FIELDS, state))
        callsign = record.get("callsign") or "UNKNOWN"
        record["callsign"] = callsign.strip() or "UNKNOWN"
        record["ingestion_timestamp"] = ingestion_ts
        records.append(record)
    return records


def write_to_s3(records, ingestion_ts):
    now = datetime.fromtimestamp(ingestion_ts, tz=timezone.utc)
    s3_key = (
        f"raw/flights/{now.strftime('%Y/%m/%d/%H/%M')}/"
        f"flights_{int(ingestion_ts)}.json"
    )
    jsonl_body = "\n".join(json.dumps(r) for r in records)

    s3 = boto3.client("s3")
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=jsonl_body.encode("utf-8"),
        ContentType="application/json"
    )
    print(f"Written {len(records)} records to s3://{S3_BUCKET}/{s3_key}")


def main(request):
    try:
        username, password = get_opensky_creds()

        response = requests.get(
            OPENSKY_URL,
            params=INDIA_BBOX,
            auth=(username, password),
            timeout=25
        )
        response.raise_for_status()

        data = response.json()
        raw_states = data.get("states") or []
        ingestion_ts = data.get("time") or datetime.now(timezone.utc).timestamp()

        if not raw_states:
            print("No states returned from OpenSky. Returning 200.")
            return ("OK", 200)

        records = parse_states(raw_states, ingestion_ts)
        write_to_s3(records, ingestion_ts)

        print(f"Success: {len(records)} flights ingested.")
        return ("OK", 200)

    except Exception as e:
        print(f"ERROR: {e}")
        return ("OK", 200)