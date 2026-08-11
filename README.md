# Indian Airspace Intelligence Platform

Real-time ingestion and analytics platform for Indian airspace, built on live ADS-B flight telemetry from the OpenSky Network. **In progress â€” Bronze layer, paused before completion.**

---

## Why this project exists

I wanted to work with a real streaming data source instead of a static dataset, and pick something with an actual production constraint to solve rather than a clean tutorial setup. Live flight telemetry over India turned out to have exactly that: a genuine infrastructure blocker (below) that had to be diagnosed and worked around, not just read about.

---

## Status

**Paused at: Bronze layer, unconfirmed.** Ingestion is live and producing data. The Bronze Lakeflow pipeline was written and a test load succeeded, but the production `bronze_flights` pipeline run was never confirmed complete. Silver and Gold layers were not started. Paused due to time constraints, not a technical dead end â€” the next step is written down below exactly as it was left.

## Stack

```
OpenSky Network API
  â†’ local machine ingestion (Python, polling every 2 min)
  â†’ AWS S3 (raw storage, ap-southeast-1)
  â†’ Databricks Community Edition â€” Lakeflow Spark Declarative Pipelines
      (Bronze â†’ Silver â†’ Gold, medallion architecture)
  â†’ MLflow (planned: Isolation Forest anomaly detection)
  â†’ Databricks Workflows (planned: orchestration)
  â†’ Streamlit Cloud (planned: live flight map dashboard)
```

Infrastructure (S3, IAM, Secrets Manager) is provisioned via Terraform.

## What's actually working

- Ingestion script polling OpenSky's `/api/states/all` every 2 minutes, writing partitioned JSONL to S3
- 25,000+ flight records collected, 19 fields per record (18 OpenSky state vector fields + an `ingestion_timestamp` added at write time, since OpenSky's own `time_position` can be null when an aircraft's GPS isn't transmitting)
- S3 â†’ Databricks Auto Loader connection confirmed â€” a test table read all 25k rows across all 19 columns cleanly
- Bronze Lakeflow pipeline (`bronze_flights`) written, using Auto Loader with `@dp.table` (the Community Edition equivalent of `@dlt.table`, since native Delta Live Tables decorators aren't available on the free tier)

## Known architectural constraint (the actual interesting part)

OpenSky blocklists datacenter IP ranges from major cloud providers. This was diagnosed through direct testing, not assumption:

- AWS (EC2) â€” blocked
- GCP (dynamic IP) â€” blocked
- GCP (static NAT IP) â€” also blocked

A residential ISP IP is not blocklisted, which is why ingestion currently runs from a local machine rather than a cloud VM. This is a known limitation, not an oversight â€” the production fix is a non-hyperscaler host (e.g. a Hetzner VPS), which sits outside the blocked CIDR ranges.

## Design decisions

- **Medallion architecture (Bronze â†’ Silver â†’ Gold)** â€” raw data stays immutable in Bronze; any reprocessing happens downstream without re-touching the source.
- **No Kafka** â€” OpenSky is a polled REST API, not an event stream, so a scheduled pull into S3 is the correct shape, not a compromise.
- **HTTP Basic Auth, not OAuth** â€” the `/api/states/all` endpoint doesn't require OAuth, and OAuth was actually causing connection timeouts.
- **Isolation Forest planned for anomaly detection** â€” there's no labelled anomaly data for this problem, so it has to be unsupervised.

## Next step (exactly where I left off)

1. Run `bronze_flights` in Lakeflow and confirm it completes with records showing.
2. Then build Silver: reading from Bronze inside Lakeflow is `spark.readStream.table("bronze_flights")` â€” Lakeflow manages the dependency automatically, no need to re-read from S3.

## Setup (high-level)

- AWS account (S3 bucket, IAM user, Secrets Manager) â€” provisioned via Terraform in `/terraform`
- Databricks Community Edition workspace
- OpenSky Network account (for authenticated polling)
- Python 3 + `boto3`, `requests` locally for the ingestion script in `/inj_scr`

No secrets are hardcoded â€” AWS credentials come from an IAM profile locally and from Databricks pipeline settings in the cloud.