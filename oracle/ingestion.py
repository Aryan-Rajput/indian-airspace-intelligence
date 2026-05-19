import json
import boto3
import requests
from datetime import datetime, timezone
import logging
import sys
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    handlers=[
        logging.FileHandler(r"C:\Users\aryrajpu\Desktop\All_folders\vs_py\indian-airspace-intelligence\oracle\ingestion.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
log = logging.getLogger(__name__)

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
OPENSKY_URL = "https://opensky-network.org/api/states/all"
AWS_REGION = "ap-southeast-1"


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
    session = boto3.Session(profile_name="airspace")
    s3 = session.client("s3", region_name=AWS_REGION)
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=jsonl_body.encode("utf-8"),
        ContentType="application/json"
    )
    log.info(f"Written {len(records)} records to s3://{S3_BUCKET}/{s3_key}")


def main():
    try:
        log.info("STEP 1: Hitting OpenSky API")
        response = requests.get(
            OPENSKY_URL,
            params=INDIA_BBOX,
            timeout=30,
            verify=False
        )
        log.info(f"STEP 2: OpenSky status: {response.status_code}")
        response.raise_for_status()

        data = response.json()
        raw_states = data.get("states") or []
        ingestion_ts = data.get("time") or datetime.now(timezone.utc).timestamp()
        log.info(f"STEP 3: Got {len(raw_states)} states")

        if not raw_states:
            log.info("No states returned. Skipping.")
            return

        records = parse_states(raw_states, ingestion_ts)
        log.info(f"STEP 4: Parsed {len(records)} records, writing to S3")
        write_to_s3(records, ingestion_ts)
        log.info("STEP 5: Success")

    except Exception as e:
        import traceback
        log.error(f"ERROR: {e}")
        log.error(traceback.format_exc())


if __name__ == "__main__":
    main()