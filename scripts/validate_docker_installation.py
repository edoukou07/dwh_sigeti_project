#!/usr/bin/env python3
"""
Script de vérification post-installation Docker SIGETI DWH
Vérifie que tous les services sont fonctionnels après déploiement Docker
"""

import sys
import time
import requests
import psycopg2
from typing import Dict, List, Tuple
import json

class ColoredOutput:
    """Classe pour l'affichage coloré"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def success(text: str) -> None:
        print(f"{ColoredOutput.GREEN}✅ {text}{ColoredOutput.END}")
    
    @staticmethod
    def error(text: str) -> None:
        print(f"{ColoredOutput.RED}❌ {text}{ColoredOutput.END}")
    
    @staticmethod
    def warning(text: str) -> None:
        print(f"{ColoredOutput.YELLOW}⚠️  {text}{ColoredOutput.END}")
    
    @staticmethod
    def info(text: str) -> None:
        print(f"{ColoredOutput.BLUE}ℹ️  {text}{ColoredOutput.END}")
    
    @staticmethod
    def header(text: str) -> None:
        print(f"\n{ColoredOutput.CYAN}{ColoredOutput.BOLD}🔍 {text}{ColoredOutput.END}")

class SIGETIDockerValidator:
    """Validateur pour l'installation Docker SIGETI DWH"""
    
    def __init__(self):
        self.results: List[Tuple[str, bool, str]] = []
        self.db_config = {
            'host': 'localhost',
            'port': '5432',
            'database': 'sigeti_dwh',
            'user': 'sigeti_user',
            'password': 'sigeti123'
        }
    
    def add_result(self, test_name: str, success: bool, message: str = "") -> None:
        """Ajouter un résultat de test"""
        self.results.append((test_name, success, message))
        if success:
            ColoredOutput.success(f"{test_name}: {message}")
        else:
            ColoredOutput.error(f"{test_name}: {message}")
    
    def test_database_connection(self) -> None:
        """Test de connexion à la base SIGETI DWH locale"""
        ColoredOutput.header("Test de Connexion Base de Données")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            # Test de base
            cursor.execute("SELECT version();")
            version = cursor.fetchone()[0]
            self.add_result("Connexion PostgreSQL", True, f"Version: {version[:50]}...")
            
            # Test des tables principales
            cursor.execute("""
                SELECT table_name FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cursor.fetchall()]
            self.add_result("Tables détectées", len(tables) > 0, f"{len(tables)} tables trouvées")
            
            # Test des vues KPI
            cursor.execute("""
                SELECT table_name FROM information_schema.views 
                WHERE table_schema = 'public' AND table_name LIKE 'v_kpi_%'
                ORDER BY table_name;
            """)
            kpi_views = [row[0] for row in cursor.fetchall()]
            expected_kpis = [
                'v_kpi_demandes_par_statut',
                'v_kpi_demandes_par_type', 
                'v_kpi_demandes_par_entite',
                'v_kpi_demandes_prioritaires',
                'v_kpi_delai_traitement',
                'v_kpi_taux_acceptation',
                'v_kpi_evolution_prioritaires'
            ]
            
            missing_kpis = set(expected_kpis) - set(kpi_views)
            if not missing_kpis:
                self.add_result("Vues KPI", True, f"Toutes les 7 vues KPI présentes")
            else:
                self.add_result("Vues KPI", False, f"Vues manquantes: {missing_kpis}")
            
            conn.close()
            
        except Exception as e:
            self.add_result("Connexion Base", False, f"Erreur: {str(e)}")
    
    def test_web_services(self) -> None:
        """Test des services web Docker"""
        ColoredOutput.header("Test des Services Web")
        
        services = {
            'Airflow Webserver': 'http://localhost:8080/health',
            'Grafana': 'http://localhost:3000/api/health',
            'Jupyter': 'http://localhost:8888',
            'Prometheus': 'http://localhost:9090/-/healthy',
            'Flower': 'http://localhost:5555'
        }
        
        for service_name, url in services.items():
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    self.add_result(f"Service {service_name}", True, f"Réponse HTTP {response.status_code}")
                else:
                    self.add_result(f"Service {service_name}", False, f"HTTP {response.status_code}")
            except requests.exceptions.RequestException as e:
                self.add_result(f"Service {service_name}", False, f"Connexion impossible: {str(e)[:50]}...")
    
    def test_docker_containers(self) -> None:
        """Test du statut des conteneurs Docker"""
        ColoredOutput.header("Test des Conteneurs Docker")
        
        import subprocess
        
        try:
            # Vérifier que Docker est accessible
            result = subprocess.run(['docker', 'ps', '--format', 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'], 
                                  capture_output=True, text=True, check=True)
            
            containers_output = result.stdout
            expected_containers = [
                'sigeti_airflow_webserver',
                'sigeti_airflow_scheduler', 
                'sigeti_airflow_worker',
                'sigeti_grafana',
                'sigeti_jupyter',
                'sigeti_prometheus',
                'sigeti_redis'
            ]
            
            running_containers = []
            for line in containers_output.split('\n')[1:]:  # Skip header
                if line.strip():
                    container_name = line.split('\t')[0]
                    if 'sigeti' in container_name.lower():
                        running_containers.append(container_name)
            
            for expected in expected_containers:
                if expected in running_containers:
                    self.add_result(f"Conteneur {expected}", True, "En cours d'exécution")
                else:
                    self.add_result(f"Conteneur {expected}", False, "Non démarré ou arrêté")
            
        except subprocess.CalledProcessError as e:
            self.add_result("Docker PS", False, f"Erreur Docker: {str(e)}")
        except FileNotFoundError:
            self.add_result("Docker", False, "Docker non installé ou non accessible")
    
    def test_airflow_functionality(self) -> None:
        """Test des fonctionnalités Airflow spécifiques"""
        ColoredOutput.header("Test Fonctionnalités Airflow")
        
        try:
            # Test API Airflow
            auth = ('admin', 'admin123')
            api_url = 'http://localhost:8080/api/v1'
            
            # Test authentification
            response = requests.get(f"{api_url}/dags", auth=auth, timeout=10)
            if response.status_code == 200:
                dags = response.json()
                self.add_result("API Airflow", True, f"{dags.get('total_entries', 0)} DAGs détectés")
            else:
                self.add_result("API Airflow", False, f"HTTP {response.status_code}")
            
            # Test présence DAG SIGETI
            response = requests.get(f"{api_url}/dags/sigeti_etl_dag", auth=auth, timeout=10)
            if response.status_code == 200:
                self.add_result("DAG SIGETI", True, "DAG sigeti_etl_dag trouvé")
            else:
                self.add_result("DAG SIGETI", False, "DAG sigeti_etl_dag non trouvé")
                
        except Exception as e:
            self.add_result("API Airflow", False, f"Erreur: {str(e)[:50]}...")
    
    def test_kpi_data(self) -> None:
        """Test de la présence et validité des données KPI"""
        ColoredOutput.header("Test Données KPI")
        
        try:
            conn = psycopg2.connect(**self.db_config)
            cursor = conn.cursor()
            
            kpi_tests = [
                ("v_kpi_demandes_par_statut", "SELECT COUNT(*) FROM v_kpi_demandes_par_statut"),
                ("v_kpi_demandes_par_type", "SELECT COUNT(*) FROM v_kpi_demandes_par_type"),
                ("v_kpi_demandes_par_entite", "SELECT COUNT(*) FROM v_kpi_demandes_par_entite"),
                ("v_kpi_taux_acceptation", "SELECT taux_acceptation FROM v_kpi_taux_acceptation LIMIT 1")
            ]
            
            for kpi_name, query in kpi_tests:
                try:
                    cursor.execute(query)
                    result = cursor.fetchone()
                    if result and result[0] is not None:
                        self.add_result(f"Données {kpi_name}", True, f"Valeur: {result[0]}")
                    else:
                        self.add_result(f"Données {kpi_name}", False, "Aucune donnée")
                except Exception as e:
                    self.add_result(f"Données {kpi_name}", False, f"Erreur requête: {str(e)[:30]}...")
            
            conn.close()
            
        except Exception as e:
            self.add_result("Test Données KPI", False, f"Erreur connexion: {str(e)}")
    
    def generate_report(self) -> None:
        """Génération du rapport final"""
        ColoredOutput.header("Rapport de Validation")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for _, success, _ in self.results if success)
        failed_tests = total_tests - passed_tests
        
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n📊 {ColoredOutput.BOLD}Résultats de Validation SIGETI DWH Docker{ColoredOutput.END}")
        print("=" * 60)
        print(f"Tests Exécutés: {total_tests}")
        print(f"Tests Réussis:  {ColoredOutput.GREEN}{passed_tests}{ColoredOutput.END}")
        print(f"Tests Échoués:  {ColoredOutput.RED}{failed_tests}{ColoredOutput.END}")
        print(f"Taux de Réussite: {ColoredOutput.GREEN if success_rate >= 80 else ColoredOutput.RED}{success_rate:.1f}%{ColoredOutput.END}")
        
        if failed_tests > 0:
            print(f"\n{ColoredOutput.RED}❌ Tests en Échec:{ColoredOutput.END}")
            for test_name, success, message in self.results:
                if not success:
                    print(f"  • {test_name}: {message}")
        
        print(f"\n{ColoredOutput.CYAN}📋 Actions Recommandées:{ColoredOutput.END}")
        if success_rate >= 95:
            print("  🎉 Installation parfaite ! Tous les services sont opérationnels.")
        elif success_rate >= 80:
            print("  ✅ Installation globalement réussie, quelques ajustements mineurs à prévoir.")
        else:
            print("  ⚠️  Installation incomplète, révision nécessaire:")
            print("     - Vérifier les logs: docker-compose logs")
            print("     - Redémarrer les services: .\\docker-sigeti.ps1 restart")
            print("     - Consulter DOCKER_README.md pour le troubleshooting")
    
    def run_all_tests(self) -> None:
        """Exécuter tous les tests de validation"""
        print(f"{ColoredOutput.CYAN}{ColoredOutput.BOLD}")
        print("🐳 SIGETI DWH - Validation Installation Docker")
        print("=" * 50)
        print(f"{ColoredOutput.END}")
        
        ColoredOutput.info("Démarrage des tests de validation...")
        
        # Attendre que les services soient prêts
        ColoredOutput.info("Attente du démarrage complet des services (30s)...")
        time.sleep(30)
        
        # Exécution des tests
        self.test_docker_containers()
        self.test_database_connection()
        self.test_web_services()
        self.test_airflow_functionality()
        self.test_kpi_data()
        
        # Rapport final
        self.generate_report()

def main():
    """Point d'entrée principal"""
    validator = SIGETIDockerValidator()
    
    try:
        validator.run_all_tests()
        
        # Code de sortie basé sur le taux de succès
        total_tests = len(validator.results)
        passed_tests = sum(1 for _, success, _ in validator.results if success)
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        if success_rate >= 80:
            sys.exit(0)  # Succès
        else:
            sys.exit(1)  # Échec
            
    except KeyboardInterrupt:
        ColoredOutput.warning("Validation interrompue par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        ColoredOutput.error(f"Erreur inattendue: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()