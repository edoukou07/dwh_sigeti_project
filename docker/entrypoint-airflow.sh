#!/bin/bash
set -e

# Fonction d'attente pour la base de données
wait_for_db() {
    echo "Waiting for Airflow database..."
    while ! airflow db check; do
        sleep 5
    done
    echo "Database is ready!"
}

# Initialisation d'Airflow selon le service
case "$1" in
    webserver)
        # Attendre que la DB soit prête
        wait_for_db
        
        # Initialiser la DB si nécessaire (seulement pour le webserver)
        if [ ! -f /opt/airflow/airflow_initialized ]; then
            echo "Initializing Airflow database..."
            airflow db init
            
            # Créer un utilisateur admin par défaut
            echo "Creating admin user..."
            airflow users create \
                --username admin \
                --firstname Admin \
                --lastname User \
                --role Admin \
                --email admin@sigeti.local \
                --password admin123
            
            # Marquer comme initialisé
            touch /opt/airflow/airflow_initialized
        fi
        
        echo "Starting Airflow webserver..."
        exec airflow webserver
        ;;
    scheduler)
        wait_for_db
        echo "Starting Airflow scheduler..."
        exec airflow scheduler
        ;;
    worker)
        wait_for_db
        echo "Starting Airflow worker..."
        exec airflow celery worker
        ;;
    flower)
        echo "Starting Airflow flower..."
        exec airflow celery flower
        ;;
    *)
        # Commande personnalisée
        exec "$@"
        ;;
esac