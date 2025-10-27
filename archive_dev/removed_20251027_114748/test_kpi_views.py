"""
Script de test des vues KPI SIGETI
Permet de tester et afficher le contenu des vues créées
"""

import psycopg2
import pandas as pd
from datetime import datetime
import sys

# Configuration de la base de données
DB_CONFIG = {
    'host': 'localhost',
    'database': 'sigeti_dwh',
    'user': 'postgres',
    'password': 'postgres',
    'port': 5432
}

def create_connection():
    """Créer une connexion à la base de données"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        return None

def test_view_data(view_name, description):
    """Tester et afficher les données d'une vue"""
    print(f"\n{'='*60}")
    print(f"📊 VUE: {view_name}")
    print(f"📋 DESCRIPTION: {description}")
    print(f"{'='*60}")
    
    conn = create_connection()
    if not conn:
        return False
    
    try:
        # Requête pour obtenir les données
        query = f"SELECT * FROM public.{view_name}"
        df = pd.read_sql(query, conn)
        
        if df.empty:
            print("⚠️ Aucune donnée trouvée dans la vue")
            return False
        
        print(f"📈 Nombre de lignes: {len(df)}")
        print(f"📝 Colonnes: {', '.join(df.columns.tolist())}")
        print(f"\n📊 Données:")
        
        # Afficher les données de manière formatée
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        pd.set_option('display.max_colwidth', 30)
        
        print(df.to_string(index=False))
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test de {view_name}: {e}")
        return False
    finally:
        conn.close()

def test_all_views():
    """Tester toutes les vues KPI"""
    print("🚀 TEST DES VUES KPI SIGETI")
    print("=" * 80)
    print(f"🕐 Début des tests: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    views_to_test = [
        ('v_kpi_taux_acceptation', 'Taux d\'acceptation des demandes d\'attribution'),
        ('v_kpi_delai_traitement', 'Métriques de délai de traitement'),
        ('v_kpi_volume_demandes', 'Volume et répartition des demandes'),
        ('v_kpi_performance_financiere', 'Performance financière et emploi'),
        ('v_kpi_analyse_temporelle', 'Analyse des tendances temporelles'),
        ('v_kpi_repartition_geographique', 'Répartition géographique par zone'),
        ('v_kpi_tableau_bord_executif', 'Tableau de bord exécutif consolidé')
    ]
    
    success_count = 0
    total_tests = len(views_to_test)
    
    for view_name, description in views_to_test:
        if test_view_data(view_name, description):
            success_count += 1
            print("✅ Test réussi")
        else:
            print("❌ Test échoué")
    
    # Résumé des tests
    print(f"\n{'='*80}")
    print(f"📊 RÉSUMÉ DES TESTS")
    print(f"{'='*80}")
    print(f"✅ Tests réussis: {success_count}/{total_tests}")
    print(f"❌ Tests échoués: {total_tests - success_count}/{total_tests}")
    print(f"🕐 Fin des tests: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if success_count == total_tests:
        print(f"\n🎉 Tous les tests ont réussi! Les vues KPI sont opérationnelles.")
        return True
    else:
        print(f"\n⚠️ {total_tests - success_count} test(s) ont échoué. Vérifiez la configuration.")
        return False

def show_kpi_summary():
    """Afficher un résumé des KPI principaux"""
    print(f"\n{'='*80}")
    print(f"📈 RÉSUMÉ EXÉCUTIF DES KPI SIGETI")
    print(f"{'='*80}")
    
    conn = create_connection()
    if not conn:
        return False
    
    try:
        # Récupérer les données du tableau de bord exécutif
        query = "SELECT * FROM public.v_kpi_tableau_bord_executif"
        df = pd.read_sql(query, conn)
        
        if not df.empty:
            row = df.iloc[0]
            
            print(f"📊 MÉTRIQUES GÉNÉRALES:")
            print(f"   • Total des demandes: {row.get('total_demandes', 'N/A')}")
            print(f"   • Demandes en cours: {row.get('demandes_en_cours', 'N/A')}")
            print(f"   • Demandes finalisées: {row.get('demandes_finalisees', 'N/A')}")
            
            print(f"\n📈 PERFORMANCE:")
            print(f"   • Taux d'acceptation: {row.get('taux_acceptation_pct', 'N/A')}%")
            print(f"   • Délai moyen de traitement: {row.get('delai_moyen_jours', 'N/A')} jours")
            print(f"   • Demandes prioritaires: {row.get('pourcentage_prioritaires', 'N/A')}%")
            
            print(f"\n💰 FINANCE & EMPLOI:")
            print(f"   • Montant total financé: {row.get('montant_total_finance', 'N/A'):,.0f} €")
            print(f"   • Montant moyen par demande: {row.get('montant_moyen_finance', 'N/A'):,.0f} €")
            print(f"   • Emplois totaux créés: {row.get('emplois_total_crees', 'N/A')}")
            
            print(f"\n🚨 STATUT:")
            print(f"   • Alerte: {row.get('statut_alerte', 'N/A')}")
            print(f"   • Dernière MAJ: {row.get('derniere_maj', 'N/A')}")
            
            return True
        else:
            print("⚠️ Aucune donnée disponible dans le tableau de bord exécutif")
            return False
            
    except Exception as e:
        print(f"❌ Erreur lors de l'affichage du résumé: {e}")
        return False
    finally:
        conn.close()

def main():
    """Fonction principale"""
    if len(sys.argv) > 1:
        if sys.argv[1] == '--summary':
            show_kpi_summary()
        elif sys.argv[1] == '--test':
            test_all_views()
        else:
            print("Usage: python test_kpi_views.py [--test|--summary]")
    else:
        # Par défaut, faire les deux
        test_all_views()
        show_kpi_summary()

if __name__ == "__main__":
    main()