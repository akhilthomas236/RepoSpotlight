"""
Command-line utility for RepoSpotlight database management
"""
import argparse
import os
import sys

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description='RepoSpotlight Database Tools')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Migrate command
    migrate_parser = subparsers.add_parser('migrate', help='Migrate database from SQLite to Firebase')
    
    # Info command
    info_parser = subparsers.add_parser('info', help='Show database information')
    
    # Parse arguments
    args = parser.parse_args()
    
    if args.command == 'migrate':
        print("Starting migration from SQLite to Firebase...")
        try:
            from migrate_to_firebase import migrate_from_sqlite_to_firebase
            success = migrate_from_sqlite_to_firebase()
            if success:
                print("Migration completed successfully!")
            else:
                print("Migration failed. Check the logs for details.")
                sys.exit(1)
        except ImportError:
            print("Error: Could not import migration module.")
            sys.exit(1)
    
    elif args.command == 'info':
        print("RepoSpotlight Database Info:")
        
        # Check SQLite database
        sqlite_db_path = "github_projects.db"
        if os.path.exists(sqlite_db_path):
            size_mb = os.path.getsize(sqlite_db_path) / (1024 * 1024)
            print(f"- SQLite database: {sqlite_db_path} ({size_mb:.2f} MB)")
            
            # Try to get repository count
            try:
                import sqlite3
                conn = sqlite3.connect(sqlite_db_path)
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM repositories")
                repo_count = cursor.fetchone()[0]
                cursor.execute("SELECT COUNT(*) FROM technologies")
                tech_count = cursor.fetchone()[0]
                conn.close()
                print(f"  - Repositories: {repo_count}")
                print(f"  - Technologies: {tech_count}")
            except Exception as e:
                print(f"  - Could not query repository count: {e}")
        else:
            print(f"- SQLite database: Not found at {sqlite_db_path}")
        
        # Check Firebase configuration
        firebase_configured = False
        if os.environ.get("FIREBASE_CREDENTIALS") or os.environ.get("FIREBASE_CREDENTIALS_PATH"):
            firebase_configured = True
            print("- Firebase: Configured via environment variables")
        
        import streamlit as st
        if hasattr(st, "secrets"):
            if "FIREBASE_CREDENTIALS" in st.secrets or "FIREBASE_CREDENTIALS_PATH" in st.secrets:
                firebase_configured = True
                print("- Firebase: Configured via Streamlit secrets")
        
        if not firebase_configured:
            print("- Firebase: Not configured")
            print("  Please set up Firebase credentials to use cloud storage.")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
