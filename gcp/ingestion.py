import json
import boto3
import requests
from datetime import datetime, timedelta

#tokenmanager
TOKEN_URL = "https://auth.opensky-network.org/auth/realms/opensky-network/protocol/openid-connect/token"

INDIA_BBOX = {
    "lamin": 8.0,
    "lamax": 37.0,
    "lomin": 68.0,
    "lomax": 97.0,
}

OPENSKY_URL = "https://opensky-network.org/api/states/all"

FIELDS = [
    "icao24", "callsign", "origin_country",
    "time_position", "last_contact",
    "longitude", "latitude", "baro_altitude",
    "on_ground", "velocity", "true_track",
    "vertical_rate", "sensors", "geo_altitude",
    "squawk", "spi", "position_source",
    "aircraft_category"
]

class TokenManager:
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.expires_at = None

    def get_token(self):
        if self.token and datetime.now() < self.expires_at:
            return self.token
        return self._refresh()

    def _refresh(self):
        r = requests.post(TOKEN_URL, data={
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        })
        r.raise_for_status()
        data = r.json()
        self.token = data["access_token"]
        self.expires_at = datetime.now() + timedelta(
            seconds = data["expires_in"] - 30
        )
        return self.token


#secrets loader
def get_secrets(secret_name, region= "ap-southeast-1"):
    client = boto3.client("secretsmanager", region_name=region)
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response["SecretString"])

# flight parser
def parse_states(states, ingestion_ts):
    records = []
    for state in states:
        record = dict(zip(FIELDS, state))
        record["ingestion_timestamp"] = ingestion_ts

        # remove trailing spaces from the callsign
        if record.get("callsign"):
            record["callsign"] = record["callsign"].strip()
        else:
            record["callsign"] = "UNKNOWN"

        record.pop("sensors", None)  # remove sensors field as it's not needed
        records.append(record)
    return records

# writgn to s3
def write_to_s3(records, bucket, ingetsion_ts):
    s3 = boto3.client("s3", region_name="ap-southeast-1")
    now = datetime.utcfromtimestamp(ingetsion_ts)
    key = (
        f"raw/flights/"
        f"{now.year}/{now.month:02d}/{now.day:02d}/"
        f"{now.hour:02d}/{now.minute:02d}/"
        f"flights_{ingestion_ts}.json"
    )
    body = "\n".join(json.dumps(r) for r in records)
    s3.put_object(
        Bucket=bucket,
        Key=key,
        Body=body.encode("utf-8"),
        ContentType="application/json",
    )
    print(f"Written {len(records)} records to s3://{bucket}//{key}")
    return key

    
# main func
def main():
    # loading secrets
    creds = get_secrets("airspace/opensky")
    token_mgr = TokenManager(
        creds["client_id"],
        creds["client_secret"]
    )

    # gettin flights
    token = token_mgr.get_token()
    response = requests.get(
        OPENSKY_URL,
        params=INDIA_BBOX,
        headers={
            "Authorization": f"Bearer {token}"
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()

    states = data.get("states", [])
    ingestion_ts = data.get("time", int(datetime.utcnow().timestamp()))

    if not states:
        print("No flights found in ze given country box")
        return "OK", 200

    # parsing and writing
    records = parse_states(states, ingestion_ts)
    bucket = f"airspace-intelligence-ar"
    write_to_s3(records, bucket, ingestion_ts)

    return f"Ingested {len(records)} flight records at {datetime.utcfromtimestamp(ingestion_ts)}", 200