# Data Pipeline — Airflow + Postgres (Stock Fetch Example)

This project implements a simple ETL data pipeline using Apache Airflow, Postgres and a Python fetch script that ingests stock price data into a database.  
Everything runs using Docker Compose and the entire environment is reproducible using the provided `Dockerfile` and `.env` file.

---

## Project Structure

data-pipeline/
├── Dockerfile
├── docker-compose.yml
├── .env
├── .gitignore
├── README.md
├── requirements.txt
├── dags/
│ └── stock_dag.py
├── scripts/
│ └── fetch_and_update.py
└── logs/


## Prerequisites

- Docker Desktop (must be running)
- Docker CLI + Docker Compose
- (Optional) Python 3.9 venv for local script testing


## Environment Setup

### 1. Create `.env`
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
docker-compose up -d airflow-webserver airflow-scheduler
Access Airflow Web UI
Open in browser:
http://localhost:8080
Login:
Username: admin
Password: admin

Trigger the DAG
Unpause & trigger:
docker-compose exec airflow-webserver airflow dags unpause stock_fetch_and_store
docker-compose exec airflow-webserver airflow dags trigger stock_fetch_and_store

List DAG runs:
docker-compose exec airflow-webserver airflow dags list-runs -d stock_fetch_and_store

View Task Logs
Find execution date:
docker-compose exec airflow-webserver airflow dags list-runs -d stock_fetch_and_store

Then view log file:
docker-compose exec airflow-webserver bash -lc "cat /opt/airflow/logs/stock_fetch_and_store/run_fetch_and_update_script/<EXEC_DATE>/1.log"
Replace <EXEC_DATE> with the folder you see in list-runs.

Check Latest Data
docker-compose exec postgres psql -U airflow -d stocks_db -c "SELECT id, symbol, timestamp, close, volume FROM stock_prices ORDER BY timestamp DESC LIMIT 10;"

Troubleshooting
Airflow says: "initialize the database"
Run:
docker-compose run --rm airflow-webserver airflow db init
DAG import errors
docker-compose exec airflow-webserver airflow dags list-import-errors
Task stuck in queued
Ensure scheduler is running:
docker-compose ps
docker-compose logs --tail=200 airflow-scheduler
Missing Python packages in Airflow
Rebuild custom images:
docker-compose build --no-cache airflow-webserver airflow-scheduler
docker-compose up -d --force-recreate airflow-webserver airflow-scheduler
Useful Commands Summary
Start everything:
docker-compose up -d
Rebuild images:
docker-compose build --no-cache
Trigger DAG:
docker-compose exec airflow-webserver airflow dags trigger stock_fetch_and_store
Check DB:
docker-compose exec postgres psql -U airflow -d stocks_db

Notes for Reviewers
.env is not committed — secrets stay local.

DAG uses BashOperator for isolation.

Airflow + Postgres fully dockerized for reproducibility.

Project includes a custom Airflow image for dependency consistency.