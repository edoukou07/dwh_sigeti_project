"""
Airflow Setup Script for SIGETI ETL Pipeline
"""

import os
import sys
import subprocess
from pathlib import Path

def setup_airflow():
    """Initialize Airflow environment and database"""
    print("🚀 Setting up Airflow for SIGETI ETL Pipeline...")
    
    # Set Airflow home
    airflow_home = r"c:\Users\hynco\Desktop\SIGETI_DWH\airflow"
    os.environ['AIRFLOW_HOME'] = airflow_home
    
    print(f"📁 Airflow Home: {airflow_home}")
    
    try:
        # Check if Airflow is installed
        result = subprocess.run(['airflow', 'version'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Airflow not found. Installing...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'apache-airflow==2.8.0'], check=True)
        else:
            print("✅ Airflow already installed")
            print(f"Version: {result.stdout.strip()}")
        
        # Initialize Airflow database
        print("🔧 Initializing Airflow database...")
        subprocess.run(['airflow', 'db', 'init'], check=True, cwd=airflow_home)
        
        # Create admin user
        print("👤 Creating admin user...")
        user_command = [
            'airflow', 'users', 'create',
            '--username', 'admin',
            '--firstname', 'Admin',
            '--lastname', 'User',
            '--role', 'Admin',
            '--email', 'admin@sigeti.com',
            '--password', 'admin123'
        ]
        
        result = subprocess.run(user_command, capture_output=True, text=True, cwd=airflow_home)
        if "already exists" in result.stdout or result.returncode == 0:
            print("✅ Admin user created/exists")
        else:
            print(f"⚠️ User creation result: {result.stdout}")
        
        print("\n🎉 Airflow setup completed!")
        print("\nNext steps:")
        print("1. Start Airflow scheduler: airflow scheduler")
        print("2. Start Airflow webserver: airflow webserver")
        print("3. Open browser: http://localhost:8080")
        print("4. Login with admin/admin123")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error during setup: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def create_startup_scripts():
    """Create convenience scripts to start Airflow services"""
    
    # Windows batch file to start scheduler
    scheduler_script = """@echo off
echo Starting Airflow Scheduler for SIGETI ETL Pipeline...
set AIRFLOW_HOME=c:\\Users\\hynco\\Desktop\\SIGETI_DWH\\airflow
cd /d "%AIRFLOW_HOME%"
airflow scheduler
pause"""
    
    with open(r"c:\Users\hynco\Desktop\SIGETI_DWH\airflow\start_scheduler.bat", "w") as f:
        f.write(scheduler_script)
    
    # Windows batch file to start webserver
    webserver_script = """@echo off
echo Starting Airflow Webserver for SIGETI ETL Pipeline...
set AIRFLOW_HOME=c:\\Users\\hynco\\Desktop\\SIGETI_DWH\\airflow
cd /d "%AIRFLOW_HOME%"
airflow webserver --port 8080
pause"""
    
    with open(r"c:\Users\hynco\Desktop\SIGETI_DWH\airflow\start_webserver.bat", "w") as f:
        f.write(webserver_script)
    
    print("✅ Startup scripts created:")
    print("   - start_scheduler.bat")
    print("   - start_webserver.bat")

if __name__ == "__main__":
    print("=" * 60)
    print("   SIGETI ETL Pipeline - Airflow Setup")
    print("=" * 60)
    
    if setup_airflow():
        create_startup_scripts()
        print("\n✅ Setup completed successfully!")
    else:
        print("\n❌ Setup failed. Please check the errors above.")
        sys.exit(1)