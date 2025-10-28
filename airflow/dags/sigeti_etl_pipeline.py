"""
SIGETI Data Warehouse ETL Pipeline DAG

This DAG orchestrates the complete SIGETI data pipeline:
1. Extract data from sigeti_node_db
2. Load to sigeti_dwh staging tables
3. Transform using dbt to create star schema
4. Generate KPI reports

Schedule: Daily at 6:00 AM
"""

from datetime import datetime, timedelta, timezone
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.email import EmailOperator
from airflow.utils.dates import days_ago
import os

# Default arguments for all tasks
default_args = {
    'owner': 'sigeti-team',
    'depends_on_past': False,
    'start_date': datetime(2025, 10, 28, tzinfo=timezone.utc),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 2,
    'retry_delay': timedelta(minutes=15),
    'catchup': False,
}

# DAG definition
dag = DAG(
    'sigeti_etl_pipeline',
    default_args=default_args,
    description='SIGETI Data Warehouse ETL Pipeline',
    schedule_interval='0 6 * * *',  # Daily at 6 AM
    max_active_runs=1,
    tags=['sigeti', 'etl', 'dbt', 'dwh']
)

# Initialize database and user if needed
def initialize_database():
    """Initialize SIGETI DWH database and user if they don't exist"""
    import sys
    import os
    
    # Add scripts directory to Python path
    scripts_path = '/opt/airflow/scripts'
    if scripts_path not in sys.path:
        sys.path.append(scripts_path)
    
    # Import and run database initializer
    try:
        from init_database import DatabaseInitializer
        
        initializer = DatabaseInitializer()
        success = initializer.initialize_all()
        
        if success:
            return "✅ Database initialization completed successfully"
        else:
            raise Exception("❌ Database initialization failed")
            
    except Exception as e:
        raise Exception(f"Database initialization error: {str(e)}")

# Set environment variables for the pipeline
def set_environment_vars():
    """Set required environment variables for ETL execution"""
    import os
    os.environ['SIGETI_DWH_PATH'] = '/opt/airflow'
    os.environ['DBT_PROFILES_DIR'] = '/opt/airflow/dbt_sigeti'
    return "Environment variables set successfully"

# Task 0: Initialize Database and User
# Option 1: Python script (plus de contrôle)
init_database_python = PythonOperator(
    task_id='initialize_database_python',
    python_callable=initialize_database,
    dag=dag,
    retries=3,
    retry_delay=timedelta(minutes=5),
)

# Option 2: Bash script (plus robuste dans Docker)
init_database_bash = BashOperator(
    task_id='initialize_database',
    bash_command="""
    chmod +x /opt/airflow/scripts/init_database.sh
    /opt/airflow/scripts/init_database.sh
    """,
    dag=dag,
    retries=3,
    retry_delay=timedelta(minutes=5),
    env={
        'SIGETI_NODE_DB_HOST': '{{ var.value.get("sigeti_node_host", "host.docker.internal") }}',
        'SIGETI_NODE_DB_PORT': '{{ var.value.get("sigeti_node_port", "5432") }}',
        'SIGETI_NODE_DB_USER': '{{ var.value.get("sigeti_node_user", "postgres") }}',
        'SIGETI_NODE_DB_PASSWORD': '{{ var.value.get("sigeti_node_password", "postgres") }}',
        'SIGETI_DB_NAME': '{{ var.value.get("sigeti_db_name", "sigeti_dwh") }}',
        'SIGETI_DB_USER': '{{ var.value.get("sigeti_db_user", "sigeti_user") }}',
        'SIGETI_DB_PASSWORD': '{{ var.value.get("sigeti_db_password", "sigeti123") }}',
    }
)

# Utiliser la version Bash par défaut (plus stable)
init_database_task = init_database_bash

# Task 1: Set Environment Variables
set_env_task = PythonOperator(
    task_id='set_environment_variables',
    python_callable=set_environment_vars,
    dag=dag,
)

# Task 2: Run ETL Script (Extract & Load)
etl_extract_load = BashOperator(
    task_id='etl_extract_load',
    bash_command="""
    cd /opt/airflow/scripts
    python etl_sigeti.py
    """,
    dag=dag,
)

# Task 3: dbt Debug (Check connections)
dbt_debug = BashOperator(
    task_id='dbt_debug',
    bash_command="""
    pip install dbt-postgres > /dev/null 2>&1 || true
    cd /opt/airflow/dbt_sigeti
    dbt debug --profiles-dir . --target docker
    """,
    dag=dag,
)

# Task 4: dbt Deps (Install packages if any)
dbt_deps = BashOperator(
    task_id='dbt_deps',
    bash_command="""
    pip install dbt-postgres > /dev/null 2>&1 || true
    cd /opt/airflow/dbt_sigeti
    dbt deps --profiles-dir . --target docker
    """,
    dag=dag,
)

# Task 5: dbt Seed (Load reference data if any)
dbt_seed = BashOperator(
    task_id='dbt_seed',
    bash_command="""
    pip install dbt-postgres > /dev/null 2>&1 || true
    cd /opt/airflow/dbt_sigeti
    dbt seed --profiles-dir . --target docker
    """,
    dag=dag,
)

# Task 6: dbt Run (Transform staging to marts)
dbt_run = BashOperator(
    task_id='dbt_run',
    bash_command="""
    pip install dbt-postgres > /dev/null 2>&1 || true
    cd /opt/airflow/dbt_sigeti
    dbt run --profiles-dir . --target docker
    """,
    dag=dag,
)

# Task 7: dbt Test (Data quality tests)
dbt_test = BashOperator(
    task_id='dbt_test',
    bash_command="""
    pip install dbt-postgres > /dev/null 2>&1 || true
    cd /opt/airflow/dbt_sigeti
    dbt test --profiles-dir . --target docker
    """,
    dag=dag,
)

# Task 8: Create KPI Views
create_kpi_views = BashOperator(
    task_id='create_kpi_views',
    bash_command="""
    cd /opt/airflow/scripts
    python create_kpi_views.py
    """,
    dag=dag,
)

# Task 9: Generate KPI Report
generate_kpi_report = BashOperator(
    task_id='generate_kpi_report',
    bash_command="""
    pip install dbt-postgres > /dev/null 2>&1 || true
    cd /opt/airflow/dbt_sigeti
    dbt docs generate --profiles-dir . --target docker
    """,
    dag=dag,
)

# Task 10: Success Notification (Optional)
def send_success_notification(**context):
    """Send success notification with pipeline metrics"""
    execution_date = context['execution_date']
    dag_run = context['dag_run']
    
    print(f"SIGETI ETL Pipeline completed successfully!")
    print(f"Execution Date: {execution_date}")
    print(f"DAG Run ID: {dag_run.run_id}")
    
    return "Success notification sent"

success_notification = PythonOperator(
    task_id='success_notification',
    python_callable=send_success_notification,
    dag=dag,
)

# Define task dependencies
init_database_task >> set_env_task >> etl_extract_load
etl_extract_load >> dbt_debug
dbt_debug >> dbt_deps
dbt_deps >> dbt_seed
dbt_seed >> dbt_run
dbt_run >> dbt_test
dbt_test >> create_kpi_views
create_kpi_views >> generate_kpi_report
generate_kpi_report >> success_notification

# Optional: Add failure notification
def send_failure_notification(**context):
    """Send failure notification with error details"""
    task_instance = context['task_instance']
    dag_run = context['dag_run']
    
    print(f"SIGETI ETL Pipeline failed!")
    print(f"Failed Task: {task_instance.task_id}")
    print(f"DAG Run ID: {dag_run.run_id}")
    print(f"Error: Check logs for details")
    
    return "Failure notification sent"

# Add failure callback to critical tasks
etl_extract_load.on_failure_callback = send_failure_notification
dbt_run.on_failure_callback = send_failure_notification
create_kpi_views.on_failure_callback = send_failure_notification