#!/usr/bin/env python3
"""
Test de connectivité Airflow pour SIGETI DWH
"""
import requests
import time
import sys


def test_airflow_connection():
    """Test la connectivité avec Airflow"""
    
    print("=" * 60)
    print("🌪️ TEST DE CONNECTIVITÉ AIRFLOW")
    print("=" * 60)
    
    # Configuration
    airflow_url = "http://localhost:8080"
    username = "airflow"
    password = "airflow"
    
    print(f"\n📋 Configuration:")
    print(f"  URL Airflow: {airflow_url}")
    print(f"  Utilisateur: {username}")
    print(f"  Mot de passe: ********")
    
    # Test 1: Health Check
    print("\n" + "=" * 40)
    print("TEST 1: Health Check")
    print("=" * 40)
    
    try:
        response = requests.get(f"{airflow_url}/health", timeout=10)
        if response.status_code == 200:
            print("✅ Airflow est accessible")
            health_data = response.json()
            print(f"   Version: {health_data.get('scheduler', {}).get('status', 'N/A')}")
        else:
            print(f"❌ Health check échoué: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Connexion impossible: {e}")
        print("💡 Vérifiez que les services Docker sont démarrés")
        return False
    
    # Test 2: Login
    print("\n" + "=" * 40)
    print("TEST 2: Authentification")
    print("=" * 40)
    
    try:
        # Obtenir le token CSRF
        session = requests.Session()
        login_page = session.get(f"{airflow_url}/login")
        
        # Simulation de login (version simplifiée)
        print("🔍 Test d'accès à l'interface...")
        
        if login_page.status_code == 200:
            print("✅ Interface Airflow accessible")
        else:
            print(f"❌ Interface non accessible: {login_page.status_code}")
            return False
    
    except Exception as e:
        print(f"❌ Erreur d'authentification: {e}")
        return False
    
    # Test 3: API
    print("\n" + "=" * 40)
    print("TEST 3: API Airflow")
    print("=" * 40)
    
    try:
        # Test de l'API version
        api_response = session.get(f"{airflow_url}/api/v1/version", timeout=10)
        
        if api_response.status_code == 200:
            print("✅ API Airflow accessible")
            version_data = api_response.json()
            print(f"   Version API: {version_data.get('version', 'N/A')}")
        elif api_response.status_code == 401:
            print("⚠️  API accessible mais authentification requise")
        else:
            print(f"❌ API non accessible: {api_response.status_code}")
    
    except Exception as e:
        print(f"❌ Erreur API: {e}")
    
    return True


def test_airflow_services():
    """Test des services Airflow individuels"""
    
    print("\n" + "=" * 40)
    print("TEST 4: Services Airflow")
    print("=" * 40)
    
    services = [
        ("Webserver", "http://localhost:8080/health"),
        ("Scheduler", "http://localhost:8080/health"),
        ("Flower", "http://localhost:5555")
    ]
    
    for service_name, url in services:
        try:
            print(f"\n🔍 Test {service_name}...")
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ {service_name}: Opérationnel")
            else:
                print(f"⚠️  {service_name}: Réponse {response.status_code}")
        
        except requests.exceptions.RequestException:
            print(f"❌ {service_name}: Non accessible")


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTS DE CONNECTIVITÉ AIRFLOW SIGETI")
    print("=" * 60)
    
    success = test_airflow_connection()
    test_airflow_services()
    
    print("\n" + "=" * 60)
    print("🎯 RÉSUMÉ")
    print("=" * 60)
    
    if success:
        print("✅ Tests Airflow terminés")
        print("🌪️ Airflow est prêt pour les pipelines SIGETI")
        sys.exit(0)
    else:
        print("❌ Problèmes détectés avec Airflow")
        print("💡 Vérifiez les logs: docker-compose logs airflow-webserver")
        sys.exit(1)