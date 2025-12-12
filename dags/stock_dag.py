# dags/stock_dag.py
from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.operators.bash import BashOperator

SCHEDULE = os.environ.get("PIPELINE_SCHEDULE_INTERVAL", "@hourly")

DEFAULT_ARGS = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="stock_fetch_and_store",
    default_args=DEFAULT_ARGS,
    description="Fetch stock prices and store them in Postgres",
    schedule_interval=SCHEDULE,
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["stocks", "example"],
) as dag:

    # Run the script from the mounted scripts folder inside the container
    run_fetch_script = BashOperator(
        task_id="run_fetch_and_update_script",
        bash_command="python /opt/airflow/scripts/fetch_and_update.py",
    )

    run_fetch_script
