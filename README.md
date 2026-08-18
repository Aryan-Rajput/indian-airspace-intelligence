# Indian Airspace Intelligence Platform

Real-time ingestion and analytics platform for Indian airspace, built on live ADS-B flight telemetry from the OpenSky Network. **In progress — Bronze, Silver, and Gold layers complete. MLflow models and Streamlit dashboard remaining.**

---

## Why this project exists

I wanted to work with a real streaming data source instead of a static dataset, and pick something with an actual constraintd to solve rather than a clean tutorial setup so a live flight telemetry over India was picked by me.

---

## Status

**Bronze, Silver, and Gold layers are complete.** Ingestion is live and producing data. All four Gold tables are built and confirmed working. What's left is the ML layer (MLflow) and the Streamlit dashboard.

- Bronze (`bronze_flights`) - complete
- Silver (`silver_flights_phases`) - complete
- Gold (`gold_hourly_metrics`) - complete
- Gold (`gold_traffic_summary`) - complete
- Gold (`gold_route_network`) - complete
- Gold (`gold_delay_propagation`) - complete
- MLflow (delay regression + flight phase classifier) - not started
- Streamlit dashboard - not started

## Stack

```
OpenSky Network API
  → local machine ingestion (Python, polling every 2 min)
  → AWS S3 (raw storage, ap-southeast-1)
  → Databricks Community Edition — Lakeflow Spark Declarative Pipelines
      (Bronze → Silver → Gold, medallion architecture)
  → MLflow (planned: delay regression model + flight phase classifier)
  → Databricks Workflows (planned: orchestration)
  → Streamlit Cloud (planned: live flight map + route network dashboard)
  → Databricks Asset Bundles / DABS (planned: CI/CD)
```

Infrastructure (S3, IAM, Secrets Manager) is provisioned via Terraform.

## What's actually working

- Ingestion script polling OpenSky's `/api/states/all` every 2 minutes, writing partitioned JSONL to S3
- 25,000+ flight records collected, 19 fields per record (18 OpenSky state vector fields + an `ingestion_timestamp` added at write time, since OpenSky's own `time_position` can be null when an aircraft's GPS isn't transmitting)
- S3 → Databricks Auto Loader connection confirmed
- Bronze Lakeflow pipeline (`bronze_flights`) - raw ingestion via Auto Loader, using `@dp.table` (the Community Edition equivalent of `@dlt.table`, since native Delta Live Tables decorators aren't available on the free tier)
- Silver pipeline (`silver_flights_phases`) - filters null coordinates, casts `ingestion_timestamp` to a proper timestamp, derives `velocity_kmh` and `carrier_code`, and classifies each record into a `flight_phase` (GROUND / CLIMBING / DESCENDING / CRUISING), with data quality expectations enforced on velocity, altitude, and India bounding-box coordinates
- Gold layer - four materialized views:
  - `gold_hourly_metrics` - flight count, avg velocity, avg altitude, peak traffic hour, ground-vs-airborne ratio, by hour
  - `gold_traffic_summary` - per-carrier traffic broken down by flight phase, with share of total traffic
  - `gold_route_network` - infers airport pairs from trajectory data (takeoff/landing detected via `on_ground` state flips, matched to nearest known Indian airport by coordinates), with route-level flight count, average duration, speed, and altitude
  - `gold_delay_propagation` - links consecutive legs flown by the same aircraft (`icao24`), compares actual landing time against the historical route average, and flags downstream legs as at-risk when a leg lands more than 15 minutes late

## Known architectural constraints

OpenSky blocklists datacenter IP ranges from major cloud providers. This was diagnosed through direct testing, not assumption:

- AWS (EC2) - blocked
- GCP (dynamic IP) - blocked
- GCP (static NAT IP) - also blocked

A residential ISP IP is not blocklisted, which is why ingestion currently runs from a local machine rather than a cloud VM. This is a known limitation, not an oversight - the production fix is a non-hyperscaler host (e.g. a Hetzner VPS), which sits outside the blocked CIDR ranges, However I have yet to confirm if it will work on it or no.

## Design decisions

- **Medallion architecture (Bronze → Silver → Gold)** - raw data stays immutable in Bronze; any reprocessing happens downstream without re-touching the source.
- **No Kafka** - OpenSky is a polled REST API, not an event stream, so a scheduled pull into S3 is the correct shape, not a compromise.
- **HTTP Basic Auth, not OAuth** - the `/api/states/all` endpoint doesn't require OAuth, and OAuth was actually causing connection timeouts.
- **Delay propagation over z-score anomaly detection** - my earlier CC Fraud pipeline already uses z-score anomaly detection on transaction data. Reusing that approach here would make this project look like a duplicate. Flight data is also fundamentally a network with time dependencies - delay at one node propagates downstream - which z-score's row-independence assumption misses entirely. Modeling delay propagation across linked legs matches the actual shape of the problem.
- **Linear Regression over Isolation Forest** - Isolation Forest is unsupervised and produces anomaly scores with no direct business interpretation. `gold_delay_propagation` gives labelled delay data, so a supervised regression producing "this flight will be X minutes late" is both more accurate for the problem and avoids duplicating the CC Fraud pipeline's unsupervised approach.
- **XGBoost flight phase classifier (secondary model)** - Silver already assigns `flight_phase` using rule-based logic; training a classifier on raw telemetry to predict the same label is a way to validate that rule-based logic against a learned model.
- **Streamlit over a Databricks SQL dashboard** - the dashboard needs to render a live flight map and a route network graph, which Databricks SQL Dashboard can't do. Streamlit Cloud is free and gives a public URL to link from the resume.

## Next steps 

1. Build the MLflow layer: a Linear Regression model predicting cascading delay in minutes from `gold_delay_propagation`, and an XGBoost flight phase classifier trained on Silver telemetry. Track both with MLflow experiment tracking and register in the Model Registry.
2. Build the Streamlit dashboard: live flight map (color-coded by flight phase), carrier performance panel, route network graph (from `gold_route_network`), and a delay propagation risk panel (from `gold_delay_propagation`).

## Setup (high-level)

- AWS account (S3 bucket, IAM user, Secrets Manager) - provisioned via Terraform in `/terraform`
- Databricks Community Edition workspace
- OpenSky Network account (for authenticated polling)
- Python 3 + `boto3`, `requests` locally for the ingestion script in `/inj_scr`

No secrets are hardcoded - AWS credentials come from an IAM profile locally and from Databricks pipeline settings in the cloud.
