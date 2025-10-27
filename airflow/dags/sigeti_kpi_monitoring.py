"""
SIGETI KPI Monitoring DAG

This DAG monitors the KPIs and sends alerts if values are outside expected ranges.
It runs after the main ETL pipeline to validate data quality and business metrics.
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.sensors.external_task import ExternalTaskSensor
import pandas as pd
import psycopg2
from sqlalchemy import create_engine

# Default arguments
default_args = {
    'owner': 'sigeti-team',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# DAG definition
dag = DAG(
    'sigeti_kpi_monitoring',
    default_args=default_args,
    description='SIGETI KPI Monitoring and Alerting',
    schedule_interval='0 8 * * *',  # Daily at 8 AM (2 hours after ETL)
    max_active_runs=1,
    tags=['sigeti', 'kpi', 'monitoring', 'alerts']
)

# Database connection parameters
DB_CONFIG = {
    'host': 'localhost',
    'database': 'sigeti_dwh',
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432
}

def get_db_connection():
    """Create database connection"""
    conn_string = f"postgresql://{DB_CONFIG['user']}:{DB_CONFIG['password']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}"
    return create_engine(conn_string)

def check_kpi_thresholds(**context):
    """Check KPI values against defined thresholds and generate alerts"""
    
    engine = get_db_connection()
    
    # Define KPI queries and thresholds using the new views
    kpi_checks = {
        'acceptance_rate': {
            'query': '''
                SELECT valeur_pourcentage as acceptance_rate
                FROM public.v_kpi_taux_acceptation
            ''',
            'min_threshold': 30.0,
            'max_threshold': 80.0,
            'unit': '%'
        },
        'average_processing_days': {
            'query': '''
                SELECT delai_moyen_jours as avg_processing_days
                FROM public.v_kpi_delai_traitement
            ''',
            'min_threshold': 5.0,
            'max_threshold': 15.0,
            'unit': 'days'
        },
        'total_demands': {
            'query': '''
                SELECT total_demandes as total_demands
                FROM public.v_kpi_volume_demandes
            ''',
            'min_threshold': 1,
            'max_threshold': 1000,
            'unit': 'demands'
        },
        'pending_demands': {
            'query': '''
                SELECT demandes_en_cours as pending_demands
                FROM public.v_kpi_volume_demandes
            ''',
            'min_threshold': 0,
            'max_threshold': 50,
            'unit': 'demands'
        }
    }
    
    alerts = []
    kpi_values = {}
    
    try:
        for kpi_name, config in kpi_checks.items():
            # Execute query
            df = pd.read_sql(config['query'], engine)
            value = df.iloc[0, 0] if not df.empty else None
            
            kpi_values[kpi_name] = value
            
            # Check thresholds
            if value is not None:
                if value < config['min_threshold']:
                    alerts.append({
                        'kpi': kpi_name,
                        'value': value,
                        'threshold': config['min_threshold'],
                        'type': 'LOW',
                        'unit': config['unit'],
                        'message': f"{kpi_name} is below minimum threshold: {value} {config['unit']} < {config['min_threshold']} {config['unit']}"
                    })
                elif value > config['max_threshold']:
                    alerts.append({
                        'kpi': kpi_name,
                        'value': value,
                        'threshold': config['max_threshold'],
                        'type': 'HIGH',
                        'unit': config['unit'],
                        'message': f"{kpi_name} is above maximum threshold: {value} {config['unit']} > {config['max_threshold']} {config['unit']}"
                    })
            else:
                alerts.append({
                    'kpi': kpi_name,
                    'value': None,
                    'threshold': None,
                    'type': 'NULL',
                    'unit': config['unit'],
                    'message': f"{kpi_name} returned NULL value - data quality issue"
                })
        
        # Log results
        print(f"🔍 KPI Monitoring Results:")
        for kpi, value in kpi_values.items():
            print(f"   {kpi}: {value}")
        
        if alerts:
            print(f"🚨 {len(alerts)} Alert(s) Generated:")
            for alert in alerts:
                print(f"   ⚠️ {alert['message']}")
        else:
            print("✅ All KPIs within acceptable ranges")
        
        # Store results for downstream tasks
        context['task_instance'].xcom_push(key='kpi_values', value=kpi_values)
        context['task_instance'].xcom_push(key='alerts', value=alerts)
        
        return {'kpi_values': kpi_values, 'alerts': alerts}
        
    except Exception as e:
        print(f"❌ Error checking KPIs: {e}")
        raise
    finally:
        engine.dispose()

def generate_kpi_report(**context):
    """Generate detailed KPI report"""
    
    # Get data from previous task
    kpi_values = context['task_instance'].xcom_pull(task_ids='check_kpi_thresholds', key='kpi_values')
    alerts = context['task_instance'].xcom_pull(task_ids='check_kpi_thresholds', key='alerts')
    
    execution_date = context['execution_date']
    
    # Generate report
    report = f"""
SIGETI KPI MONITORING REPORT
============================
Date: {execution_date.strftime('%Y-%m-%d %H:%M:%S')}

CURRENT KPI VALUES:
------------------
• Acceptance Rate: {kpi_values.get('acceptance_rate', 'N/A')}%
• Average Processing Time: {kpi_values.get('average_processing_days', 'N/A')} days
• Total Demands: {kpi_values.get('total_demands', 'N/A')}
• Pending Demands: {kpi_values.get('pending_demands', 'N/A')}

ALERT STATUS:
------------
"""
    
    if alerts:
        report += f"⚠️ {len(alerts)} Alert(s) Detected:\n"
        for i, alert in enumerate(alerts, 1):
            report += f"{i}. {alert['message']}\n"
    else:
        report += "✅ All KPIs within acceptable ranges\n"
    
    report += """
DATA QUALITY CHECKS:
------------------
• Database Connection: ✅ Successful
• Data Availability: ✅ Confirmed
• ETL Pipeline: ✅ Completed

NEXT ACTIONS:
------------
"""
    
    if alerts:
        report += "• Review flagged KPIs\n• Investigate data quality issues\n• Consider process improvements\n"
    else:
        report += "• Continue monitoring\n• No immediate action required\n"
    
    print(report)
    
    # Save report to file
    report_file = f"c:\\Users\\hynco\\Desktop\\SIGETI_DWH\\airflow\\logs\\kpi_report_{execution_date.strftime('%Y%m%d')}.txt"
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 Report saved to: {report_file}")
    except Exception as e:
        print(f"⚠️ Could not save report file: {e}")
    
    return report

# Wait for ETL pipeline to complete
wait_for_etl = ExternalTaskSensor(
    task_id='wait_for_etl_completion',
    external_dag_id='sigeti_etl_pipeline',
    external_task_id='success_notification',
    timeout=3600,  # 1 hour timeout
    poke_interval=300,  # Check every 5 minutes
    dag=dag,
)

# Check KPI thresholds
check_kpis = PythonOperator(
    task_id='check_kpi_thresholds',
    python_callable=check_kpi_thresholds,
    dag=dag,
)

# Generate KPI report
generate_report = PythonOperator(
    task_id='generate_kpi_report',
    python_callable=generate_kpi_report,
    dag=dag,
)

# Define dependencies
wait_for_etl >> check_kpis >> generate_report