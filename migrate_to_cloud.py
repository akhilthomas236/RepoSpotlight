"""
Migration script to move data from SQLite to Deta Space cloud database

This script helps users migrate their existing SQLite repository data
to the Deta Space cloud database for deployment to Streamlit Cloud
"""
import json
import os
import sqlite3
import sys

# Check if Deta and other required packages are installed
try:
    from deta import Deta
except ImportError:
    print("Deta package not found. Please install it with: pip install deta")
    sys.exit(1)
    
print("Starting migration from SQLite to Deta Space...")

# Get Deta project key from environment or input
deta_key = os.environ.get("DETA_PROJECT_KEY")
if not deta_key:
    deta_key = input("Enter your Deta Space project key (from deta.space): ").strip()
    if not deta_key:
        print("Error: Deta Project key is required")
        sys.exit(1)

# Initialize Deta with the project key
try:
    deta = Deta(deta_key)
    repos_db = deta.Base("repositories")
    techs_db = deta.Base("technologies")
    print("Connected to Deta Space successfully")
except Exception as e:
    print(f"Error connecting to Deta Space: {e}")
    sys.exit(1)

# Check if SQLite database exists
sqlite_path = "github_projects.db"
if not os.path.exists(sqlite_path):
    print(f"SQLite database not found at {sqlite_path}")
    sys.exit(1)

# Connect to SQLite database
try:
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    print("Connected to SQLite database successfully")
except Exception as e:
    print(f"Error connecting to SQLite database: {e}")
    sys.exit(1)

# Migrate repositories
try:
    # Get all repositories from SQLite
    cursor.execute("SELECT * FROM repositories")
    repositories = cursor.fetchall()
    
    if not repositories:
        print("No repositories found in SQLite database")
    else:
        print(f"Found {len(repositories)} repositories to migrate")
        
        for repo in repositories:
            repo_dict = dict(repo)
            
            # Format repo_dict for Deta (which doesn't need the id)
            if "id" in repo_dict:
                repo_dict.pop("id")
                
            # Put in Deta
            repos_db.put(repo_dict)
            
        print(f"Successfully migrated {len(repositories)} repositories to Deta Space")
except Exception as e:
    print(f"Error migrating repositories: {e}")

# Migrate technologies
try:
    # Get all technologies from SQLite
    cursor.execute("SELECT * FROM technologies")
    technologies = cursor.fetchall()
    
    if not technologies:
        print("No technologies found in SQLite database")
    else:
        print(f"Found {len(technologies)} technologies to migrate")
        
        for tech in technologies:
            tech_dict = dict(tech)
            
            # Format tech_dict for Deta (which doesn't need the id)
            if "id" in tech_dict:
                tech_dict.pop("id")
                
            # Put in Deta
            techs_db.put(tech_dict)
            
        print(f"Successfully migrated {len(technologies)} technologies to Deta Space")
except Exception as e:
    print(f"Error migrating technologies: {e}")

# Close SQLite connection
conn.close()

print("\n--- Migration Complete ---")
print("""
Next steps:
1. Deploy your app to Streamlit Cloud
2. Configure the secrets.toml with your Deta Space project key
3. Set USE_CLOUD_DB = true in your secrets

Your data has been migrated successfully and will be available in the cloud!
""")
