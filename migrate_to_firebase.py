"""
Migration script to transfer data from SQLite to Firebase Firestore

This script helps users migrate their existing SQLite database to
Firebase Firestore for cloud deployment.

Usage:
1. Set up Firebase credentials in your environment or .streamlit/secrets.toml
2. Run this script: python migrate_to_firebase.py
"""

import os
import sys
import json
import sqlite3
import streamlit as st

# Add the current directory to the path so we can import our modules
sys.path.append('.')

def migrate_from_sqlite_to_firebase():
    """Migrate all data from local SQLite database to Firebase Firestore"""
    # Import our database modules
    import database as sqlite_db
    import firebase_database as firebase_db
    
    print("🚀 Starting migration from SQLite to Firebase...")
    
    # Check if Firebase is properly configured
    try:
        firebase_db.init_firebase()
    except Exception as e:
        print(f"❌ Firebase initialization failed: {e}")
        print("Please set up your Firebase credentials before running this script.")
        return False
    
    # Check if SQLite database exists
    if not os.path.exists(sqlite_db.DB_PATH):
        print(f"❌ SQLite database not found at {sqlite_db.DB_PATH}")
        return False
    
    try:
        # Get repositories from SQLite
        print("📊 Reading repositories from SQLite...")
        repositories = sqlite_db.get_all_repositories()
        print(f"Found {len(repositories)} repositories")
        
        # Migrate repositories to Firebase
        print("🔄 Migrating repositories to Firebase...")
        for repo in repositories:
            # Get the repo URL
            repo_url = repo["repo_url"]
            
            # Check if repo already exists in Firebase
            existing_repo = firebase_db.get_repository(repo_url)
            if existing_repo:
                print(f"- Repository already exists in Firebase: {repo['name']}")
                continue
            
            # Convert metadata back to dict for storage
            try:
                if isinstance(repo["metadata"], str):
                    repo["metadata"] = json.loads(repo["metadata"])
            except:
                repo["metadata"] = {}
            
            # Create repo_data structure similar to what add_repository expects
            repo_data = {
                "name": repo["name"],
                "owner": {"login": repo["owner"]},
                "description": repo["description"],
                "stars": repo["stars"],
                "forks": repo["forks"],
                "language": repo["language"],
                "updated_at": repo["last_updated"],
                "custom_metadata": repo["metadata"]
            }
            
            # Add to Firebase
            if firebase_db.add_repository(repo_url, repo_data):
                print(f"✅ Migrated: {repo['name']}")
            else:
                print(f"❌ Failed to migrate: {repo['name']}")
        
        # Get technologies from SQLite
        print("\n📊 Reading technologies from SQLite...")
        conn = sqlite_db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name, count FROM technologies")
        technologies = [{"name": row[0], "count": row[1]} for row in cursor.fetchall()]
        conn.close()
        
        print(f"Found {len(technologies)} technologies")
        
        # Migrate technologies to Firebase
        print("🔄 Migrating technologies to Firebase...")
        db = firebase_db.get_db()
        for tech in technologies:
            # Check if technology exists in Firebase
            tech_ref = db.collection('technologies').where('name', '==', tech["name"]).limit(1)
            docs = list(tech_ref.stream())
            
            if docs:
                # Update count
                doc = docs[0]
                db.collection('technologies').document(doc.id).update({
                    'count': tech["count"]
                })
            else:
                # Insert new technology
                db.collection('technologies').add({
                    'name': tech["name"], 
                    'count': tech["count"]
                })
            print(f"✅ Migrated technology: {tech['name']} (count: {tech['count']})")
        
        print("\n🎉 Migration completed successfully!")
        print("\nYou can now deploy your app to Streamlit Cloud with Firebase storage.")
        return True
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        return False

if __name__ == "__main__":
    migrate_from_sqlite_to_firebase()
