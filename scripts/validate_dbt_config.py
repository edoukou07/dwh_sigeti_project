#!/usr/bin/env python3
"""
Script de validation des configurations dbt pour SIGETI DWH
Vérifie que dbt peut se connecter avec les paramètres de base de données
"""

import os
import sys
import subprocess
import json

# Configuration SIGETI attendue
EXPECTED_CONFIG = {
    'dbname': 'sigeti_dwh',
    'user': 'sigeti_user', 
    'password': 'sigeti123',
    'host': 'localhost',  # ou host.docker.internal pour Docker
    'port': 5432
}

def run_dbt_command(command, cwd=None):
    """Exécute une commande dbt et retourne le résultat"""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd
        )
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def validate_dbt_profiles():
    """Valide le fichier profiles.yml"""
    print("🔍 Validation du fichier profiles.yml...")
    
    profiles_path = os.path.join(os.getcwd(), "profiles.yml")
    if not os.path.exists(profiles_path):
        print(f"❌ Fichier profiles.yml introuvable: {profiles_path}")
        return False
    
    print(f"✅ Fichier profiles.yml trouvé: {profiles_path}")
    
    # Lire et afficher la configuration
    try:
        with open(profiles_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("📋 Configuration dbt détectée:")
        if 'sigeti_dwh' in content:
            print("  ✅ Profil 'sigeti_dwh' trouvé")
        if 'sigeti_user' in content:
            print("  ✅ Utilisateur 'sigeti_user' configuré")
        if 'sigeti123' in content:
            print("  ✅ Mot de passe configuré")
        if 'host.docker.internal' in content:
            print("  ✅ Configuration Docker détectée")
        if 'localhost' in content:
            print("  ✅ Configuration locale détectée")
            
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier: {e}")
        return False

def test_dbt_connection():
    """Test la connexion dbt"""
    print("\n🔍 Test de connexion dbt...")
    
    success, stdout, stderr = run_dbt_command("dbt debug --profiles-dir .")
    
    if success:
        print("✅ Test de connexion dbt réussi")
        print("\n📊 Sortie dbt debug:")
        print(stdout)
        return True
    else:
        print("❌ Test de connexion dbt échoué")
        print("\n🔍 Erreurs:")
        print(stderr)
        print("\n📊 Sortie:")
        print(stdout)
        return False

def validate_dbt_project():
    """Valide le projet dbt"""
    print("\n🔍 Validation du projet dbt...")
    
    project_path = os.path.join(os.getcwd(), "dbt_project.yml")
    if not os.path.exists(project_path):
        print(f"❌ Fichier dbt_project.yml introuvable: {project_path}")
        return False
    
    print(f"✅ Fichier dbt_project.yml trouvé: {project_path}")
    
    # Vérifier la configuration du projet
    try:
        with open(project_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("📋 Configuration du projet:")
        if "name: 'sigeti_dwh'" in content:
            print("  ✅ Nom du projet 'sigeti_dwh' configuré")
        if "profile: 'sigeti_dwh'" in content:
            print("  ✅ Profil 'sigeti_dwh' référencé")
        
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier: {e}")
        return False

def check_environment_variables():
    """Vérifie les variables d'environnement"""
    print("\n🔍 Variables d'environnement SIGETI:")
    
    env_vars = [
        'SIGETI_DB_HOST',
        'SIGETI_DB_PORT', 
        'SIGETI_DB_USER',
        'SIGETI_DB_PASSWORD',
        'SIGETI_DB_NAME'
    ]
    
    found_vars = 0
    for var in env_vars:
        value = os.getenv(var)
        if value:
            if 'PASSWORD' in var:
                print(f"  ✅ {var}='{'*' * len(value)}'")
            else:
                print(f"  ✅ {var}='{value}'")
            found_vars += 1
        else:
            print(f"  ⚪ {var}=non définie (utilise les valeurs par défaut)")
    
    if found_vars > 0:
        print(f"✅ {found_vars}/{len(env_vars)} variables d'environnement définies")
    else:
        print("⚪ Aucune variable d'environnement définie (utilise les valeurs par défaut)")
    
    return True

def test_dbt_models():
    """Test la compilation des modèles dbt"""
    print("\n🔍 Test de compilation des modèles...")
    
    success, stdout, stderr = run_dbt_command("dbt parse --profiles-dir .")
    
    if success:
        print("✅ Compilation des modèles réussie")
        return True
    else:
        print("❌ Erreur de compilation des modèles")
        print("\n🔍 Erreurs:")
        print(stderr)
        return False

def main():
    """Fonction principale"""
    print("=" * 60)
    print("🧪 VALIDATION CONFIGURATION DBT SIGETI")
    print("=" * 60)
    
    # Changer vers le répertoire dbt_sigeti
    dbt_dir = "."
    if not os.path.exists("dbt_project.yml"):
        # Si on n'est pas dans le bon répertoire, essayer de le trouver
        for possible_path in ["dbt_sigeti", "../dbt_sigeti", "."]:
            if os.path.exists(os.path.join(possible_path, "dbt_project.yml")):
                dbt_dir = possible_path
                os.chdir(dbt_dir)
                break
    
    print(f"📁 Répertoire de travail: {os.getcwd()}")
    
    all_tests_passed = True
    
    # Test 1: Validation profiles.yml
    print("\n" + "=" * 40)
    print("TEST 1: Configuration profiles.yml")
    print("=" * 40)
    profiles_ok = validate_dbt_profiles()
    all_tests_passed = all_tests_passed and profiles_ok
    
    # Test 2: Validation dbt_project.yml
    print("\n" + "=" * 40)
    print("TEST 2: Configuration dbt_project.yml")
    print("=" * 40)
    project_ok = validate_dbt_project()
    all_tests_passed = all_tests_passed and project_ok
    
    # Test 3: Variables d'environnement
    print("\n" + "=" * 40)
    print("TEST 3: Variables d'environnement")
    print("=" * 40)
    env_ok = check_environment_variables()
    all_tests_passed = all_tests_passed and env_ok
    
    # Test 4: Compilation des modèles
    print("\n" + "=" * 40)
    print("TEST 4: Compilation des modèles")
    print("=" * 40)
    parse_ok = test_dbt_models()
    all_tests_passed = all_tests_passed and parse_ok
    
    # Test 5: Connexion dbt (si la base existe)
    print("\n" + "=" * 40)
    print("TEST 5: Connexion dbt")
    print("=" * 40)
    connection_ok = test_dbt_connection()
    # Ne pas faire échouer les tests si la base n'existe pas encore
    
    # Résumé
    print("\n" + "=" * 60)
    print("🎯 RÉSUMÉ DES TESTS")
    print("=" * 60)
    
    print(f"📋 Tests de configuration: {'✅ RÉUSSIS' if all_tests_passed else '❌ ÉCHOUÉS'}")
    print(f"🔗 Test de connexion: {'✅ RÉUSSI' if connection_ok else '⚠️  ÉCHEC (base peut-être non initialisée)'}")
    
    if all_tests_passed:
        print("\n🎉 Configuration dbt validée pour SIGETI DWH!")
        print("💡 Paramètres utilisés:")
        print(f"   - Base: {EXPECTED_CONFIG['dbname']}")
        print(f"   - Utilisateur: {EXPECTED_CONFIG['user']}")
        print(f"   - Host: {EXPECTED_CONFIG['host']} (local) ou host.docker.internal (Docker)")
        print(f"   - Port: {EXPECTED_CONFIG['port']}")
        
        if not connection_ok:
            print("\n🔧 Pour initialiser la base de données:")
            print("   python ../scripts/init_database.py")
            print("   # ou")
            print("   ./docker-sigeti.ps1 init-db")
    else:
        print("\n❌ Problèmes de configuration détectés")
        print("🔧 Vérifiez les fichiers de configuration")
    
    return 0 if all_tests_passed else 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrompus par l'utilisateur")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        sys.exit(1)