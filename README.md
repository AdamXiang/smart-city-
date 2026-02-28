# 🏙️ Smart City Realtime Streaming Pipeline

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![PySpark](https://img.shields.io/badge/PySpark-3.5.1-E25A1C?style=flat-square&logo=apache-spark&logoColor=white)
![Kafka](https://img.shields.io/badge/Kafka-7.4.0-231F20?style=flat-square&logo=apache-kafka&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-S3%20%7C%20Glue%20%7C%20Athena%20%7C%20Redshift-FF9900?style=flat-square&logo=amazon-aws&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)

> A production-pattern streaming pipeline that simulates a smart city vehicle sensor network — built as a **"heavy-equipment sandbox"** to master distributed data processing, cloud data lake design, and the operational realities of running Spark in Docker.

---

## 📖 Table of Contents

- [Architecture Overview](#-architecture-overview)
- [Tech Stack & Design Decisions](#-tech-stack--design-decisions)
- [Data Schema](#-data-schema)
- [Prerequisites](#-prerequisites)
- [Setup & Installation](#-setup--installation)
- [Running the Pipeline](#-running-the-pipeline)
- [AWS Configuration](#-aws-configuration)
- [Folder Structure](#-folder-structure)
- [Known Issues & Technical Debt](#️-known-issues--technical-debt)
- [Roadmap (V2)](#-roadmap-v2)

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        LOCAL (Docker)                           │
│                                                                 │
│   Python Simulator  ──►  Apache Kafka  ──►  Spark Structured    │
│   (main.py)               (5 Topics)        Streaming           │
│   London → Birmingham     Zookeeper         (spark_city.py)     │
│                                                                 │
└──────────────────────────────┬──────────────────────────────────┘
                               │ Parquet via s3a://
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                          AWS Cloud                              │
│                                                                 │
│   S3 Data Lake  ──►  Glue Crawler  ──►  Data Catalog            │
│                                              │                  │
│                              ┌───────────────┴──────────────┐   │
│                              ▼                              ▼   │
│                           Athena                        Redshift│
│                         (ad-hoc SQL)               (analytical) │
│                              │                              │   │
│                              └──────────────┬───────────────┘   │
│                                             ▼                   │
│                                   Power BI / Looker Studio      │
└─────────────────────────────────────────────────────────────────┘
```

**Data flow:** A Python simulator drives a vehicle from London to Birmingham, emitting 5 sensor streams every 30–60 seconds into Kafka. Spark Structured Streaming consumes each topic independently in micro-batch mode and writes raw Parquet files to S3. AWS Glue discovers the schema, and both Athena and Redshift serve as query layers for BI dashboards.

---

## ⚙️ Tech Stack & Design Decisions

| Layer | Technology | Why This Choice |
|---|---|---|
| **Simulation** | Python + `confluent-kafka` | Lightweight producer; simulates realistic GPS drift and randomized sensor values |
| **Message Broker** | Apache Kafka (Confluent 7.4.0) | Industry-standard for durable, ordered, replayable event streams |
| **Stream Processing** | Spark Structured Streaming 3.5.1 | Portable, distributed compute standard — transferable to Databricks / EMR at scale |
| **Storage Format** | Parquet on S3 | Columnar, compressed, natively supported by every downstream query engine |
| **Schema Catalog** | AWS Glue Crawler | Decouples schema evolution from pipeline logic; enables Athena and Redshift Spectrum |
| **Ad-hoc Queries** | AWS Athena | Serverless SQL over S3; zero infrastructure to manage |
| **Analytical Layer** | Amazon Redshift | Persistent, fast analytical queries via Redshift Spectrum (external schema over Glue) |
| **Container Orchestration** | Docker Compose | Single-command local cluster; mirrors production topology |

### Why Spark and not Kinesis Firehose?

For this data volume, Kinesis Firehose would be cheaper and simpler. Spark was a deliberate choice — this project is a **learning sandbox** designed to build muscle memory with distributed compute tools. The micro-batch execution model, Watermark configuration, and compute-storage separation patterns learned here transfer directly to TB-scale production pipelines.

### Why ELT and not ETL?

The Spark layer performs **ingestion only** — no joins, no enrichment, no business logic. Cross-topic joins (e.g., correlating vehicle telemetry with emergency incidents) are deferred to Athena and Redshift SQL. This keeps the streaming job stateless, operationally simple, and fully replayable. See [Known Issues](#️-known-issues--technical-debt) for the technical reasoning.

---

## 📊 Data Schema

Five Kafka topics are produced concurrently, one per sensor type:

| Topic | Key Fields | Description |
|---|---|---|
| `vehicle_data` | `id`, `device_id`, `timestamp`, `location`, `speed`, `make`, `fuel_type` | Core vehicle telemetry |
| `gps_data` | `id`, `device_id`, `timestamp`, `speed`, `direction`, `vehicle_type` | GPS receiver stream |
| `traffic_data` | `id`, `device_id`, `camera_id`, `location`, `timestamp`, `snapshot` | Traffic camera snapshots |
| `weather_data` | `id`, `device_id`, `location`, `temperature`, `weather_condition`, `airQualityIndex` | Environmental sensors |
| `emergency_data` | `id`, `device_id`, `incident_id`, `type`, `status`, `description` | Incident detection |

All topics share `device_id` and `timestamp` as join keys for downstream SQL correlation.

---

## 📋 Prerequisites

Ensure the following are installed before proceeding:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (v4.0+)
- [Python 3.11](https://www.python.org/downloads/) (for running the simulator locally)
- [uv](https://github.com/astral-sh/uv) (recommended) or `pip`
- AWS account with S3, Glue, Athena, and Redshift access
- AWS IAM user with credentials configured (see [AWS Configuration](#-aws-configuration))

---

## 🚀 Setup & Installation

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/smart-city-streaming.git
cd smart-city-streaming
```

### 2. Configure AWS credentials

Open `jobs/config.py` and add your IAM credentials:

```python
configuration = {
    'AWS_ACCESS_KEY': 'YOUR_ACCESS_KEY_ID',
    'AWS_SECRET_KEY': 'YOUR_SECRET_ACCESS_KEY',
}
```

> ⚠️ **Never commit this file with real credentials.** Add `jobs/config.py` to `.gitignore`, or use environment variables instead.

### 3. Set up the Python environment (for the simulator)

```bash
# Using uv (recommended)
uv python install 3.11
uv venv --python 3.11
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows

uv pip install -r requirements.txt
```

### 4. Build and start the Docker cluster

> ⚠️ **Important:** Always use `--build` when starting for the first time or after any change to `Dockerfile`. Without it, Docker will use a cached image and your installed packages (pandas, pyarrow, boto3) will not be present inside the containers.

```bash
docker-compose up -d --build
```

This starts 5 services: `zookeeper`, `kafka`, `spark-master`, `spark-worker-1`, `spark-worker-2`.

Verify all containers are healthy:

```bash
docker ps
```

**Spark UI** is available at `http://localhost:9090`

> 💡 **Note on the base image:** This project uses `bitnamilegacy/spark:3.5.1`. Bitnami migrated all versioned Spark images from the `bitnami/` to `bitnamilegacy/` namespace in late 2025. If you see a `not found` error on any `bitnami/spark` image, this is the reason — update the image name accordingly.

---

## ▶️ Running the Pipeline

The pipeline has two components that must be started in order.

### Step 1: Start the Spark Streaming job

Submit the Spark job to the running cluster:

```bash
docker exec -it smartcity-spark-master-1 spark-submit \
  --master spark://spark-master:7077 \
  --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,\
org.apache.hadoop:hadoop-aws:3.3.1,\
com.amazonaws:aws-java-sdk:1.11.469 \
  jobs/spark_city.py
```

Spark will begin listening on all 5 Kafka topics and writing micro-batches to S3.

### Step 2: Start the vehicle simulator

In a separate terminal, with your virtual environment activated:

```bash
python jobs/main.py
```

The simulator will log each Kafka message delivery to the console. The vehicle travels from London to Birmingham across ~100 steps. The simulation ends automatically when the vehicle reaches Birmingham's coordinates.

### Step 3: Verify data in S3

After a few minutes, confirm Parquet files are appearing in your S3 bucket under:

```
s3://your-bucket-name/data/vehicle_data/
s3://your-bucket-name/data/gps_data/
s3://your-bucket-name/data/traffic_data/
s3://your-bucket-name/data/weather_data/
s3://your-bucket-name/data/emergency_data/
```

---

## ☁️ AWS Configuration

### S3 Bucket

Create an S3 bucket and update the bucket name in `jobs/spark_city.py` (currently set to `spark-streaming-ching`).

**Block Public Access:** Keep all public access blocked. Use IAM credentials for access, not bucket policies.

### IAM Policy

Attach the following policy to your IAM user. Note that `s3:DeleteObject` is required — Spark Structured Streaming overwrites internal `_spark_metadata` checkpoint files and will fail with a `403` without delete permission.

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "AllowListBucket",
      "Effect": "Allow",
      "Action": ["s3:ListBucket", "s3:GetBucketLocation"],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME"
    },
    {
      "Sid": "AllowReadWriteDelete",
      "Effect": "Allow",
      "Action": ["s3:PutObject", "s3:GetObject", "s3:DeleteObject"],
      "Resource": "arn:aws:s3:::YOUR-BUCKET-NAME/*"
    }
  ]
}
```

### AWS Glue Crawler

1. Create a new crawler pointing to `s3://your-bucket-name/data/`
2. Under **Exclude patterns**, add `_spark_metadata` to prevent Glue from cataloging Spark's internal checkpoint folders
3. Create or select a Glue database (e.g., `smartcity`)
4. Run the crawler — it will create 5 tables matching the 5 topic directories

### Athena

On first use, configure a query result location under **Query Settings**:

```
s3://your-bucket-name/output/
```

### Redshift (Optional)

To connect Redshift to the Glue catalog via Redshift Spectrum:

```sql
CREATE EXTERNAL SCHEMA smartcity
FROM DATA CATALOG
DATABASE 'smartcity'
IAM_ROLE 'arn:aws:iam::YOUR_ACCOUNT_ID:role/YOUR_REDSHIFT_ROLE'
REGION 'YOUR_REGION';
```

Your Redshift IAM role must have `AWSGlueConsoleFullAccess` (or a scoped equivalent) attached.

---

## 📁 Folder Structure

```
smart-city-streaming/
│
├── docker-compose.yml        # Defines: Zookeeper, Kafka, Spark master + 2 workers
├── Dockerfile                # Extends bitnamilegacy/spark:3.5.1 with pandas, pyarrow, boto3
├── requirements.txt          # Python dependencies for local simulator environment
├── pyproject.toml            # Project metadata
│
└── jobs/
    ├── config.py             # AWS credentials (⚠️ do not commit with real values)
    ├── main.py               # Vehicle simulator — Kafka producer for all 5 topics
    └── spark_city.py         # Spark Structured Streaming consumer — reads Kafka, writes S3
```

---

## ⚠️ Known Issues & Technical Debt

These are documented trade-offs, not oversights.

### 1. Cross-Topic Join Not Implemented

```python
# jobs/spark_city.py
# Join all the dataframes with id and timestamp  ← intentionally deferred
```

Joining 5 concurrent streams inside Spark Structured Streaming requires careful **Watermark** and **State TTL** configuration. Without it, Spark's internal state grows unbounded and will eventually cause OOM errors on the executors. The join logic is intentionally deferred to Athena and Redshift SQL — a standard ELT pattern that trades streaming-layer complexity for downstream flexibility.

### 2. Small File Problem

Each Spark micro-batch trigger produces a new Parquet file per topic partition. Over a 10–15 minute simulation run, this generates hundreds of small files (3–5 KB each), which degrades Athena query performance at scale. Mitigation requires a periodic compaction job — see V2 Roadmap.

### 3. No Schema Registry

The Kafka producer and Spark consumer share an implicit JSON contract. A schema change in `main.py` (e.g., adding or renaming a field) will cause silent `null` values or runtime failures in the Spark job. A production deployment would enforce this contract with a **Confluent Schema Registry**.

### 4. No Dead Letter Queue

Malformed or unparseable Kafka messages are currently dropped silently. A production pipeline needs a dead letter queue (a separate Kafka topic or S3 prefix) to capture, inspect, and reprocess bad records.

---

## 🗺️ Roadmap (V2)

- [ ] **Data Compaction DAG** — Apache Airflow job to merge small Parquet files nightly (target: ~128 MB per file for optimal Athena performance)
- [ ] **dbt Models** — Implement the deferred cross-sensor joins as version-controlled, tested SQL models on Redshift
- [ ] **Anomaly Detection Branch** — Rule-based filter in Spark to route high-speed + active-emergency records to a separate alert topic
- [ ] **Schema Registry** — Confluent Schema Registry integration for producer/consumer contract enforcement
- [ ] **CI/CD** — GitHub Actions workflow for linting, testing, and Docker image validation

---

## 🙏 Acknowledgments

* CodeWithYu for providing this amazing [project tutorial](https://www.youtube.com/watch?v=Vv_fvwF41_0) [Linkedin](https://www.linkedin.com/in/yusuf-ganiyu-b90140107/)


---

## 📄 License

MIT License. See `LICENSE` for details.

---

*Built as a learning project to develop production-grade intuitions around distributed streaming systems. Read the full architecture deep-dive on [Medium](#).*
