#!/usr/bin/env python3
"""
Test des services Jupyter pour SIGETI DWH
"""
import requests
import time
import sys


def test_jupyter_connection():
    """Test la connectivité avec Jupyter"""
    
    print("=" * 60)
    print("📓 TEST DE CONNECTIVITÉ JUPYTER")
    print("=" * 60)
    
    # Configuration
    jupyter_url = "http://localhost:8888"
    
    print(f"\n📋 Configuration:")
    print(f"  URL Jupyter: {jupyter_url}")
    print(f"  Token: Configuré dans docker-compose")
    
    # Test 1: Accessibility
    print("\n" + "=" * 40)
    print("TEST 1: Accessibilité")
    print("=" * 40)
    
    try:
        print("🔍 Test d'accès à Jupyter...")
        response = requests.get(jupyter_url, timeout=10, allow_redirects=True)
        
        if response.status_code == 200:
            print("✅ Jupyter est accessible")
            if "jupyter" in response.text.lower() or "notebook" in response.text.lower():
                print("✅ Interface Jupyter détectée")
            else:
                print("⚠️  Réponse inattendue du serveur")
        else:
            print(f"❌ Jupyter non accessible: {response.status_code}")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Connexion impossible: {e}")
        print("💡 Vérifiez que le conteneur jupyter est démarré")
        return False
    
    # Test 2: API
    print("\n" + "=" * 40)
    print("TEST 2: API Jupyter")
    print("=" * 40)
    
    try:
        # Test de l'API (sans token pour test basique)
        api_url = f"{jupyter_url}/api"
        api_response = requests.get(api_url, timeout=5)
        
        if api_response.status_code in [200, 401, 403]:
            print("✅ API Jupyter répond")
            if api_response.status_code == 401:
                print("   (Authentification requise - normal)")
        else:
            print(f"⚠️  API réponse: {api_response.status_code}")
    
    except Exception as e:
        print(f"⚠️  Test API: {e}")
    
    return True


def test_grafana_connection():
    """Test la connectivité avec Grafana"""
    
    print("\n" + "=" * 60)
    print("📊 TEST DE CONNECTIVITÉ GRAFANA")
    print("=" * 60)
    
    # Configuration
    grafana_url = "http://localhost:3000"
    
    print(f"\n📋 Configuration:")
    print(f"  URL Grafana: {grafana_url}")
    print(f"  Utilisateur par défaut: admin")
    
    try:
        print("\n🔍 Test d'accès à Grafana...")
        response = requests.get(grafana_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Grafana est accessible")
            if "grafana" in response.text.lower():
                print("✅ Interface Grafana détectée")
        else:
            print(f"❌ Grafana non accessible: {response.status_code}")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Connexion impossible: {e}")
        return False
    
    # Test API
    try:
        api_response = requests.get(f"{grafana_url}/api/health", timeout=5)
        if api_response.status_code == 200:
            print("✅ API Grafana opérationnelle")
        else:
            print(f"⚠️  API Grafana: {api_response.status_code}")
    except:
        print("⚠️  API Grafana non testée")
    
    return True


def test_prometheus_connection():
    """Test la connectivité avec Prometheus"""
    
    print("\n" + "=" * 60)
    print("📈 TEST DE CONNECTIVITÉ PROMETHEUS")
    print("=" * 60)
    
    prometheus_url = "http://localhost:9090"
    
    try:
        print("🔍 Test d'accès à Prometheus...")
        response = requests.get(prometheus_url, timeout=10)
        
        if response.status_code == 200:
            print("✅ Prometheus est accessible")
        else:
            print(f"❌ Prometheus non accessible: {response.status_code}")
            return False
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Connexion impossible: {e}")
        return False
    
    # Test API
    try:
        api_response = requests.get(f"{prometheus_url}/api/v1/query?query=up", timeout=5)
        if api_response.status_code == 200:
            print("✅ API Prometheus opérationnelle")
            data = api_response.json()
            if data.get('status') == 'success':
                print("✅ Métriques disponibles")
        else:
            print(f"⚠️  API Prometheus: {api_response.status_code}")
    except Exception as e:
        print(f"⚠️  Test API Prometheus: {e}")
    
    return True


if __name__ == "__main__":
    print("=" * 60)
    print("🧪 TESTS DES SERVICES SIGETI")
    print("=" * 60)
    
    services_ok = []
    
    # Test chaque service
    if test_jupyter_connection():
        services_ok.append("Jupyter")
    
    if test_grafana_connection():
        services_ok.append("Grafana")
        
    if test_prometheus_connection():
        services_ok.append("Prometheus")
    
    # Résumé
    print("\n" + "=" * 60)
    print("🎯 RÉSUMÉ DES SERVICES")
    print("=" * 60)
    
    if len(services_ok) == 3:
        print("✅ TOUS LES SERVICES SONT OPÉRATIONNELS")
        print(f"🚀 Services disponibles: {', '.join(services_ok)}")
        print("\n📋 URLs d'accès:")
        print("  🔗 Jupyter: http://localhost:8888")
        print("  🔗 Grafana: http://localhost:3000")
        print("  🔗 Prometheus: http://localhost:9090")
        sys.exit(0)
    else:
        print(f"⚠️  Services opérationnels: {len(services_ok)}/3")
        print(f"✅ Disponibles: {', '.join(services_ok) if services_ok else 'Aucun'}")
        print("💡 Vérifiez les logs Docker pour les services manquants")
        sys.exit(1)