# Dockerfile (project root)
FROM apache/airflow:2.7.3

# Copy requirements into the image
COPY requirements.txt /tmp/requirements.txt

# Ensure root for filesystem ops, then switch to airflow user to install packages
USER root

# Make sure home dir exists and is owned by airflow
RUN mkdir -p /home/airflow/.local && chown -R airflow: /home/airflow

# Switch to the airflow user and install the python packages into user site
USER airflow

# Install packages into the user site 
RUN python -m pip install --no-cache-dir --user -r /tmp/requirements.txt

# Ensure user-local bin is on PATH 
ENV PATH="/home/airflow/.local/bin:${PATH}"

# Return to airflow (already set) — keep default user
USER airflow
