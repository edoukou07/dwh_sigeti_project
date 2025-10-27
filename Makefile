# Makefile pour SIGETI DWH Docker
.PHONY: help build up down logs clean restart status test

# Variables
COMPOSE_FILE = docker-compose.yml
PROJECT_NAME = sigeti_dwh

help: ## Afficher l'aide
	@echo "Commandes disponibles pour SIGETI DWH Docker:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

build: ## Construire tous les conteneurs
	@echo "🔨 Construction des images Docker..."
	docker-compose -f $(COMPOSE_FILE) build --no-cache

up: ## Démarrer tous les services
	@echo "🚀 Démarrage de SIGETI DWH..."
	docker-compose -f $(COMPOSE_FILE) up -d
	@echo "✅ Services démarrés!"
	@echo "📊 Airflow Webserver: http://localhost:8080 (admin/admin123)"
	@echo "📈 Grafana: http://localhost:3000 (admin/admin123)"
	@echo "📓 Jupyter: http://localhost:8888 (token: sigeti123)"
	@echo "🌸 Flower: http://localhost:5555"

down: ## Arrêter tous les services
	@echo "⏹️  Arrêt des services..."
	docker-compose -f $(COMPOSE_FILE) down

stop: ## Arrêter sans supprimer
	@echo "⏸️  Pause des services..."
	docker-compose -f $(COMPOSE_FILE) stop

restart: down up ## Redémarrer tous les services

logs: ## Voir les logs de tous les services
	docker-compose -f $(COMPOSE_FILE) logs -f

logs-airflow: ## Voir les logs Airflow seulement
	docker-compose -f $(COMPOSE_FILE) logs -f airflow-webserver airflow-scheduler airflow-worker

status: ## Voir le statut des services
	@echo "📊 Statut des services SIGETI DWH:"
	@docker-compose -f $(COMPOSE_FILE) ps

clean: ## Nettoyer (arrêter et supprimer volumes)
	@echo "🧹 Nettoyage complet..."
	docker-compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker system prune -f

clean-all: ## Nettoyage complet + images
	@echo "🧹 Nettoyage complet avec images..."
	docker-compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker system prune -af

# Services individuels
airflow-up: ## Démarrer seulement Airflow
	docker-compose -f $(COMPOSE_FILE) up -d postgres-airflow redis airflow-webserver airflow-scheduler airflow-worker

dbt-shell: ## Accéder au shell dbt
	docker-compose -f $(COMPOSE_FILE) exec dbt-service bash

jupyter-up: ## Démarrer seulement Jupyter
	docker-compose -f $(COMPOSE_FILE) up -d jupyter

monitoring-up: ## Démarrer seulement le monitoring
	docker-compose -f $(COMPOSE_FILE) up -d grafana prometheus

# Tests et validation
test-db-connection: ## Tester la connexion aux DB locales
	@echo "🔍 Test de connexion aux bases locales..."
	docker-compose -f $(COMPOSE_FILE) exec airflow-webserver python -c "import psycopg2; conn = psycopg2.connect(host='host.docker.internal', port=5432, database='sigeti_dwh', user='sigeti_user', password='sigeti123'); print('✅ Connexion SIGETI DWH OK'); conn.close()"

test-kpi: ## Tester les KPI views
	@echo "🎯 Test des vues KPI..."
	docker-compose -f $(COMPOSE_FILE) exec dbt-service python /opt/airflow/scripts/create_kpi_views.py

test-init: ## Tester l'initialisation DB
	@echo "🧪 Test de l'initialisation de la base..."
	python scripts/test_database_init.py

init-db: ## Initialiser la base manuellement
	@echo "🔧 Initialisation de la base..."
	python scripts/init_database.py

test-dbt: ## Valider la configuration dbt
	@echo "🧪 Validation de la configuration dbt..."
	python scripts/validate_dbt_config.py

test-dbt-docker: ## Tester dbt dans Docker
	@echo "🐳 Test dbt dans Docker..."
	bash scripts/test_dbt_docker.sh

run-etl: ## Exécuter l'ETL manuellement
	@echo "⚙️ Exécution ETL SIGETI..."
	docker-compose -f $(COMPOSE_FILE) exec airflow-worker python /opt/airflow/scripts/etl_sigeti.py

# Développement
dev: ## Mode développement (avec rebuild)
	@echo "🔧 Mode développement..."
	docker-compose -f $(COMPOSE_FILE) up -d --build

init-airflow: ## Initialiser Airflow (premier démarrage)
	@echo "🔑 Initialisation Airflow..."
	docker-compose -f $(COMPOSE_FILE) exec airflow-webserver airflow db init
	docker-compose -f $(COMPOSE_FILE) exec airflow-webserver airflow users create --username admin --firstname Admin --lastname User --role Admin --email admin@sigeti.local --password admin123

backup: ## Sauvegarde des volumes
	@echo "💾 Sauvegarde des données..."
	mkdir -p ./backups/$(shell date +%Y%m%d_%H%M%S)
	docker run --rm -v sigeti_dwh_airflow_postgres_data:/data -v $(PWD)/backups:/backup alpine tar czf /backup/airflow_$(shell date +%Y%m%d_%H%M%S).tar.gz -C /data .

# Informations
info: ## Informations sur l'installation
	@echo "📋 SIGETI DWH Docker - Informations"
	@echo "===================================="
	@echo "🏗️  Projet: $(PROJECT_NAME)"
	@echo "📁 Compose: $(COMPOSE_FILE)"
	@echo ""
	@echo "🌐 URLs d'accès:"
	@echo "   Airflow:    http://localhost:8080"
	@echo "   Grafana:    http://localhost:3000"
	@echo "   Jupyter:    http://localhost:8888"
	@echo "   Flower:     http://localhost:5555"
	@echo "   Prometheus: http://localhost:9090"
	@echo ""
	@echo "🔐 Identifiants par défaut:"
	@echo "   Airflow:  admin / admin123"
	@echo "   Grafana:  admin / admin123"
	@echo "   Jupyter:  token sigeti123"