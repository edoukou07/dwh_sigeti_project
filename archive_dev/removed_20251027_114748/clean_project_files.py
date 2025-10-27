"""
Script de nettoyage des fichiers obsolètes du projet SIGETI DWH
Supprime les scripts de développement, tests et fichiers temporaires devenus inutiles
"""

import os
import shutil
from datetime import datetime

def print_header(title):
    """Afficher un titre formaté"""
    print("\n" + "="*60)
    print(f"🗂️  {title}")
    print("="*60)

def print_action(action, status="INFO"):
    """Afficher une action"""
    if status == "DELETE":
        print(f"🗑️  {action}")
    elif status == "KEEP":
        print(f"✅ {action}")
    elif status == "MOVE":
        print(f"📁 {action}")
    else:
        print(f"ℹ️  {action}")

def create_archive_folder():
    """Créer un dossier d'archive pour les fichiers supprimés"""
    archive_dir = r"c:\Users\hynco\Desktop\SIGETI_DWH\archive_dev"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_path = f"{archive_dir}\\removed_{timestamp}"
    
    try:
        os.makedirs(archive_path, exist_ok=True)
        return archive_path
    except Exception as e:
        print(f"❌ Erreur création archive: {e}")
        return None

def clean_development_scripts():
    """Identifier et traiter les scripts de développement"""
    print_header("NETTOYAGE DES SCRIPTS DE DÉVELOPPEMENT")
    
    base_dir = r"c:\Users\hynco\Desktop\SIGETI_DWH"
    
    # Scripts obsolètes à supprimer
    obsolete_files = [
        "etl_sigeti_spark.py",      # Version Spark abandonnée au profit de la version pandas
        "test_kpis.sql",            # Tests manuels remplacés par les scripts automatisés
        "test_kpis_fixed.sql",      # Tests temporaires corrigés
        "test_kpi_views.py",        # Tests individuels remplacés par validate_final_system.py
        "validate_pipeline.py",     # Validation partielle remplacée par la validation finale
        "demo_finale.py",           # Démonstration ponctuelle non nécessaire en production
        "kpi_manager.bat",          # Script batch obsolète
        "sigeti_structure.sql",     # Structure ancienne, maintenant dans dbt
    ]
    
    # Scripts de développement à archiver (pas supprimer complètement)
    archive_files = [
        "queries/indicateurs_demandes_attribution.sql",  # Requêtes de développement
    ]
    
    # Scripts à conserver (essentiels pour la production)
    keep_files = [
        "etl_sigeti.py",                    # ETL principal en production
        "create_kpi_views.py",              # Déploiement des vues KPI
        "cleanup_databases.py",             # Script de maintenance
        "validate_final_system.py",         # Validation système
        "requirements.txt",                 # Dépendances Python
        "DOCUMENTATION_COMPLETE.md",        # Documentation principale
        "RAPPORT_NETTOYAGE_FINAL.md",      # Rapport final
        "RESUME_EXECUTIF.md",               # Résumé exécutif
        "README_VALIDATION.md",             # Documentation validation
    ]
    
    archive_path = create_archive_folder()
    if not archive_path:
        print("❌ Impossible de créer le dossier d'archive")
        return False
    
    deleted_count = 0
    archived_count = 0
    
    # Supprimer les fichiers obsolètes
    for file_name in obsolete_files:
        file_path = os.path.join(base_dir, file_name)
        if os.path.exists(file_path):
            try:
                # Copier dans l'archive avant de supprimer
                archive_file_path = os.path.join(archive_path, file_name)
                os.makedirs(os.path.dirname(archive_file_path), exist_ok=True)
                shutil.copy2(file_path, archive_file_path)
                
                # Supprimer le fichier original
                os.remove(file_path)
                print_action(f"Supprimé: {file_name}", "DELETE")
                deleted_count += 1
            except Exception as e:
                print_action(f"Erreur suppression {file_name}: {e}", "ERROR")
    
    # Archiver les fichiers de développement
    for file_name in archive_files:
        file_path = os.path.join(base_dir, file_name)
        if os.path.exists(file_path):
            try:
                archive_file_path = os.path.join(archive_path, file_name)
                os.makedirs(os.path.dirname(archive_file_path), exist_ok=True)
                shutil.move(file_path, archive_file_path)
                print_action(f"Archivé: {file_name}", "MOVE")
                archived_count += 1
            except Exception as e:
                print_action(f"Erreur archivage {file_name}: {e}", "ERROR")
    
    # Confirmer les fichiers conservés
    for file_name in keep_files:
        file_path = os.path.join(base_dir, file_name)
        if os.path.exists(file_path):
            print_action(f"Conservé: {file_name}", "KEEP")
    
    return deleted_count, archived_count, archive_path

def clean_empty_directories():
    """Supprimer les dossiers vides ou obsolètes"""
    print_header("NETTOYAGE DES DOSSIERS")
    
    base_dir = r"c:\Users\hynco\Desktop\SIGETI_DWH"
    
    # Dossiers potentiellement à nettoyer
    check_dirs = [
        "spark_jars",       # Jars Spark non utilisés
        "airbyte",          # Configuration Airbyte abandonnée
        "queries",          # Après archivage, peut être vide
    ]
    
    removed_dirs = 0
    
    for dir_name in check_dirs:
        dir_path = os.path.join(base_dir, dir_name)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            try:
                # Vérifier si le dossier est vide ou ne contient que des fichiers temporaires
                contents = os.listdir(dir_path)
                
                if not contents:
                    # Dossier vide
                    os.rmdir(dir_path)
                    print_action(f"Dossier vide supprimé: {dir_name}", "DELETE")
                    removed_dirs += 1
                elif all(f.startswith('.') or f.endswith('.tmp') for f in contents):
                    # Contient seulement des fichiers temporaires
                    shutil.rmtree(dir_path)
                    print_action(f"Dossier temporaire supprimé: {dir_name}", "DELETE")
                    removed_dirs += 1
                elif dir_name in ["spark_jars", "airbyte"]:
                    # Dossiers spécifiquement obsolètes
                    archive_path = os.path.join(base_dir, "archive_dev", f"removed_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                    os.makedirs(archive_path, exist_ok=True)
                    shutil.move(dir_path, os.path.join(archive_path, dir_name))
                    print_action(f"Dossier obsolète archivé: {dir_name}", "MOVE")
                    removed_dirs += 1
                else:
                    print_action(f"Dossier conservé (contient des fichiers): {dir_name}", "KEEP")
            except Exception as e:
                print_action(f"Erreur traitement dossier {dir_name}: {e}", "ERROR")
    
    return removed_dirs

def optimize_sql_views_folder():
    """Optimiser le dossier sql_views"""
    print_header("OPTIMISATION SQL_VIEWS")
    
    sql_views_dir = r"c:\Users\hynco\Desktop\SIGETI_DWH\sql_views"
    
    # Les vues SQL individuelles ne sont plus nécessaires car intégrées dans create_kpi_views.py
    # Mais on les garde pour référence et maintenance future
    
    if os.path.exists(sql_views_dir):
        contents = os.listdir(sql_views_dir)
        sql_files = [f for f in contents if f.endswith('.sql') and f != 'deploy_views.sql']
        
        if len(sql_files) > 0:
            print_action(f"Conservé {len(sql_files)} fichiers SQL de référence", "KEEP")
        
        # Supprimer deploy_views.sql si il existe (remplacé par create_kpi_views.py)
        deploy_file = os.path.join(sql_views_dir, "deploy_views.sql")
        if os.path.exists(deploy_file):
            try:
                os.remove(deploy_file)
                print_action("Supprimé: deploy_views.sql (remplacé par create_kpi_views.py)", "DELETE")
                return True
            except Exception as e:
                print_action(f"Erreur suppression deploy_views.sql: {e}", "ERROR")
    
    return False

def create_cleanup_summary():
    """Créer un résumé du nettoyage"""
    print_header("RÉSUMÉ DU NETTOYAGE")
    
    # Fichiers essentiels restants
    essential_files = [
        "etl_sigeti.py",
        "create_kpi_views.py", 
        "cleanup_databases.py",
        "validate_final_system.py",
        "requirements.txt",
        "dbt_sigeti/",
        "airflow/",
        "sql_views/",
        "backups/",
        "*.md (documentation)"
    ]
    
    print("📂 STRUCTURE FINALE DU PROJET:")
    print("-" * 40)
    
    for item in essential_files:
        print(f"   ✅ {item}")
    
    print("\n💡 FICHIERS SUPPRIMÉS:")
    print("-" * 40)
    print("   🗑️  etl_sigeti_spark.py (version Spark abandonnée)")
    print("   🗑️  test_*.py/sql (tests manuels)")
    print("   🗑️  demo_finale.py (démonstration ponctuelle)")
    print("   🗑️  validate_pipeline.py (validation partielle)")
    print("   🗑️  kpi_manager.bat (script batch obsolète)")
    print("   🗑️  spark_jars/ (dépendances Spark inutiles)")
    print("   🗑️  airbyte/ (configuration abandonnée)")
    
    print(f"\n📅 Nettoyage effectué: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Fonction principale de nettoyage"""
    print("🗂️  NETTOYAGE DES SCRIPTS OBSOLÈTES - SIGETI DWH")
    print("=" * 80)
    print(f"🕐 Début: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Demander confirmation
    print("\n⚠️  ATTENTION: Cette opération va supprimer des fichiers!")
    print("   - Scripts de développement obsolètes")
    print("   - Tests manuels anciens")
    print("   - Dossiers vides ou inutiles")
    print("   - Fichiers temporaires")
    print("\n💡 Les fichiers supprimés seront archivés dans 'archive_dev/'")
    
    response = input("\nContinuer le nettoyage? (oui/non): ").lower().strip()
    if response not in ['oui', 'o', 'yes', 'y']:
        print("🚫 Nettoyage annulé par l'utilisateur")
        return
    
    # Exécuter le nettoyage
    deleted_count, archived_count, archive_path = clean_development_scripts()
    removed_dirs = clean_empty_directories()
    optimize_sql_views_folder()
    
    # Résumé final
    create_cleanup_summary()
    
    print_header("RÉSULTAT FINAL")
    print(f"✅ Fichiers supprimés: {deleted_count}")
    print(f"📁 Fichiers archivés: {archived_count}")
    print(f"📂 Dossiers supprimés: {removed_dirs}")
    
    if archive_path and os.path.exists(archive_path):
        print(f"💾 Archive créée: {archive_path}")
    
    print("\n🎉 NETTOYAGE TERMINÉ!")
    print("💡 Le projet est maintenant optimisé pour la production")
    print("📁 Seuls les scripts essentiels sont conservés")
    print("🔄 Les fichiers supprimés sont disponibles dans l'archive")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⏹️  Nettoyage interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")