# Data Pipeline — Airflow + Postgres (Stock Fetch Example)

This project implements a Dockerized data pipeline using Apache Airflow and PostgreSQL to fetch, process, and store stock price data.
It includes an Airflow DAG, custom ingestion script, Postgres integration, and complete end-to-end orchestration.

---
Features

Apache Airflow DAG orchestrating the ETL pipeline

Python ingestion script to fetch and store stock data

PostgreSQL database for persistent storage

Docker Compose setup for easy deployment

Secure configuration using .env.example

Clean, modular project folder structure

## Project Structure
Data-Pipeline-Assessment/
│
├── dags/
│   └── stock_dag.py          # Airflow DAG for scheduling the pipeline
│
├── scripts/
│   └── fetch_and_update.py   # Script to fetch API data & load into Postgres
│
├── docker-compose.yml        # Container setup for Airflow + Postgres
├── dockerfile                # Used for installing dependencies in Airflow
├── requirements.txt          # Python dependencies
├── .env.example              # Env variables (sample template)
├── README.md                 # Project documentation
└── generate_fernet.py        # Script to generate Airflow Fernet key


Tech Stack
Apache Airflow 2.7.x

PostgreSQL 13

Python 3.8+

Docker & Docker Compose

Pandas, Requests, psycopg2


## Environment Setup

### 
git clone https://github.com/Prathiksha25/Data-Pipeline-Assessment
cd Data-Pipeline-Assessment

1. Create `.env`
cp .env.example .env
Important values inside .env:

POSTGRES_PASSWORD=yourpassword

AIRFLOW__CORE__FERNET_KEY=<generated_key>

POSTGRES_HOST=postgres (for Docker)

STOCK_API_KEY= (optional; script generates sample data without it)

2. Generate Fernet Key (if needed)

python -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"
Paste into .env.

First-Time Setup
1. Start Postgres
docker-compose up -d postgres

2. Initialize Airflow Metadata DB
docker-compose run --rm airflow-webserver airflow db init

3. Create Airflow Admin User
docker-compose run --rm airflow-webserver airflow users create ^
  --username admin --firstname Admin --lastname User ^
  --role Admin --email admin@example.com --password admin

4. Build Custom Airflow Images (installs requirements.txt)
docker-compose build --no-cache airflow-webserver airflow-scheduler

5. Start Airflow Services
docker-compose exec airflow-webserver airflow db init
docker-compose exec airflow-webserver airflow users create \
    --username admin \
    --firstname airflow \
    --lastname admin \
    --role Admin \
    --email admin@example.com

docker-compose up -d airflow-webserver airflow-scheduler
Access Airflow Web UI
Open in browser:
http://localhost:8080
Login:
Username: admin
Password: admin

6. Access Airflow UI
Open:

👉 http://localhost:8080

Login with the credentials you created

7️. Enable the DAG

In Airflow UI:

Locate stock_fetch_and_store

Toggle the switch to ON

Trigger manually or wait for scheduled run

Pipeline Overview
Task Flow

Airflow triggers the DAG based on schedule

Python script fetches stock data (either via API or sample fallback)

Data is validated & transformed using Pandas

Postgres table is created (if not exists)

Data is inserted into the database

