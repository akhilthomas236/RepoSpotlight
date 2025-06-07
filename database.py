import sqlite3
import os
import json
from typing import List, Dict, Any, Optional
import datetime
import time

# Database file path
DB_PATH = "github_projects.db"

# Database lock timeout (in seconds)
DB_TIMEOUT = 20.0

def get_db_connection():
    """
    Create a connection to the SQLite database with improved handling
    for concurrent access
    """
    try:
        # Add timeout and enable automatic retrying of locked database
        conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
        conn.row_factory = sqlite3.Row
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        # Set journal mode to WAL for better concurrency
        conn.execute("PRAGMA journal_mode = WAL")
        return conn
    except sqlite3.Error as e:
        print(f"Database connection error: {e}")
        # Return None so callers can handle the case of a failed connection
        return None

def safe_close(conn):
    """Safely close a database connection if it's open"""
    if conn is not None:
        try:
            conn.close()
        except Exception as e:
            print(f"Error closing database connection: {e}")

def init_db():
    """Initialize the database with required tables"""
    conn = None
    try:
        conn = get_db_connection()
        if conn is None:
            print("Cannot initialize database: Unable to connect")
            return
            
        cursor = conn.cursor()
        
        # Create repositories table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS repositories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            repo_url TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            owner TEXT NOT NULL,
            description TEXT,
            stars INTEGER DEFAULT 0,
            forks INTEGER DEFAULT 0,
            language TEXT,
            last_updated TEXT,
            last_synced TEXT,
            metadata TEXT
        )
        ''')
        
        # Create technologies table for tech stack tracking
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS technologies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            count INTEGER DEFAULT 0
        )
        ''')
        
        conn.commit()
    except Exception as e:
        print(f"Error initializing database: {e}")
    finally:
        safe_close(conn)

def add_repository(repo_url: str, repo_data: Dict[str, Any]) -> bool:
    """
    Add a new repository to the database
    
    Args:
        repo_url: The GitHub repository URL
        repo_data: Dictionary containing repository information
        
    Returns:
        bool: True if repository was added successfully, False otherwise
    """
    max_retries = 5
    retry_delay = 1.0  # seconds
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            if conn is None:
                print(f"Cannot add repository {repo_url}: Unable to connect to database")
                return False
                
            cursor = conn.cursor()
            
            # Check if repository already exists
            cursor.execute("SELECT id FROM repositories WHERE repo_url = ?", (repo_url,))
            if cursor.fetchone():
                conn.close()
                return False  # Repository already exists
            
            # Convert repo_data to JSON string for storage
            metadata = json.dumps(repo_data.get("custom_metadata", {}))
            
            # Insert repository
            cursor.execute('''
            INSERT INTO repositories 
            (repo_url, name, owner, description, stars, forks, language, last_updated, last_synced, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                repo_url,
                repo_data["name"],
                repo_data["owner"]["login"],
                repo_data.get("description", ""),
                repo_data["stars"],
                repo_data["forks"],
                repo_data.get("language", ""),
                repo_data["updated_at"],
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                metadata
            ))
            
            conn.commit()
            
            # Update technology count - after committing main transaction
            # to reduce lock duration
            if repo_data.get("language"):
                update_technology(repo_data["language"])
            
            # Update technologies from metadata if available
            if repo_data.get("custom_metadata", {}).get("tech_stack"):
                for tech in repo_data["custom_metadata"]["tech_stack"]:
                    update_technology(tech)
                    
            conn.close()
            return True
            
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                print(f"Database locked, retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
                time.sleep(retry_delay)
                retry_delay *= 1.5  # Exponential backoff
                continue
            print(f"Error adding repository: {e}")
            return False
        except Exception as e:
            print(f"Error adding repository: {e}")
            return False
    
    return False  # If we reached here, all retries failed

def update_repository(repo_url: str, repo_data: Dict[str, Any]) -> bool:
    """
    Update an existing repository in the database
    
    Args:
        repo_url: The GitHub repository URL
        repo_data: Dictionary containing repository information
        
    Returns:
        bool: True if repository was updated successfully, False otherwise
    """
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if repository exists
        cursor.execute("SELECT id FROM repositories WHERE repo_url = ?", (repo_url,))
        if not cursor.fetchone():
            conn.close()
            return False  # Repository doesn't exist
        
        # Convert repo_data to JSON string for storage
        metadata = json.dumps(repo_data.get("custom_metadata", {}))
        
        # Update repository
        cursor.execute('''
        UPDATE repositories SET
        name = ?,
        owner = ?,
        description = ?,
        stars = ?,
        forks = ?,
        language = ?,
        last_updated = ?,
        last_synced = ?,
        metadata = ?
        WHERE repo_url = ?
        ''', (
            repo_data["name"],
            repo_data["owner"]["login"],
            repo_data.get("description", ""),
            repo_data["stars"],
            repo_data["forks"],
            repo_data.get("language", ""),
            repo_data["updated_at"],
            datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            metadata,
            repo_url
        ))
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error updating repository: {e}")
        return False

def get_all_repositories() -> List[Dict[str, Any]]:
    """Get all repositories from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM repositories ORDER BY last_synced DESC")
        
        repositories = []
        for row in cursor.fetchall():
            repo = dict(row)
            # Convert metadata JSON string back to dictionary
            try:
                repo["metadata"] = json.loads(repo["metadata"]) if repo["metadata"] else {}
            except:
                repo["metadata"] = {}
            repositories.append(repo)
            
        conn.close()
        return repositories
    except Exception as e:
        print(f"Error getting repositories: {e}")
        return []

def get_repository(repo_url: str) -> Optional[Dict[str, Any]]:
    """Get a specific repository by URL"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM repositories WHERE repo_url = ?", (repo_url,))
        
        row = cursor.fetchone()
        if not row:
            conn.close()
            return None
            
        repo = dict(row)
        # Convert metadata JSON string back to dictionary
        try:
            repo["metadata"] = json.loads(repo["metadata"]) if repo["metadata"] else {}
        except:
            repo["metadata"] = {}
            
        conn.close()
        return repo
    except Exception as e:
        print(f"Error getting repository: {e}")
        return None

def delete_repository(repo_url: str) -> bool:
    """Delete a repository from the database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if repository exists
        cursor.execute("SELECT language FROM repositories WHERE repo_url = ?", (repo_url,))
        repo = cursor.fetchone()
        if not repo:
            conn.close()
            return False
            
        # Update technology count if needed
        if repo["language"]:
            decrease_technology_count(repo["language"])
        
        # Delete repository
        cursor.execute("DELETE FROM repositories WHERE repo_url = ?", (repo_url,))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"Error deleting repository: {e}")
        return False

def update_technology(name: str):
    """
    Increment the count for a technology with retry mechanism
    to handle database locks
    """
    max_retries = 5
    retry_delay = 1.0  # seconds
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            if conn is None:
                print(f"Cannot update technology {name}: Unable to connect to database")
                return
                
            cursor = conn.cursor()
            
            # Check if technology exists
            cursor.execute("SELECT count FROM technologies WHERE name = ?", (name,))
            tech = cursor.fetchone()
            
            if tech:
                # Update count
                cursor.execute("UPDATE technologies SET count = count + 1 WHERE name = ?", (name,))
            else:
                # Insert new technology
                cursor.execute("INSERT INTO technologies (name, count) VALUES (?, 1)", (name,))
                
            conn.commit()
            conn.close()
            return  # Success!
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                # If this is not our last attempt, wait and retry
                if attempt < max_retries - 1:
                    print(f"Database locked, retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                    continue
            print(f"Error updating technology: {e}")
            return
        except Exception as e:
            print(f"Error updating technology: {e}")
            return

def decrease_technology_count(name: str):
    """
    Decrease the count for a technology with retry mechanism
    to handle database locks
    """
    max_retries = 5
    retry_delay = 1.0  # seconds
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            if conn is None:
                print(f"Cannot decrease count for {name}: Unable to connect to database")
                return
                
            cursor = conn.cursor()
            
            # Update count and remove if zero
            cursor.execute("UPDATE technologies SET count = count - 1 WHERE name = ?", (name,))
            cursor.execute("DELETE FROM technologies WHERE count <= 0")
                
            conn.commit()
            conn.close()
            return  # Success!
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                # If this is not our last attempt, wait and retry
                if attempt < max_retries - 1:
                    print(f"Database locked, retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                    continue
            print(f"Error decreasing technology count: {e}")
            return
        except Exception as e:
            print(f"Error decreasing technology count: {e}")
            return

def get_technology_stats() -> List[Dict[str, Any]]:
    """
    Get statistics for all technologies with retry mechanism
    to handle database locks
    """
    max_retries = 5
    retry_delay = 1.0  # seconds
    
    for attempt in range(max_retries):
        try:
            conn = get_db_connection()
            if conn is None:
                print("Cannot get technology stats: Unable to connect to database")
                return []
                
            cursor = conn.cursor()
            cursor.execute("SELECT name, count FROM technologies ORDER BY count DESC")
            
            stats = [dict(row) for row in cursor.fetchall()]
            conn.close()
            return stats
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e):
                # If this is not our last attempt, wait and retry
                if attempt < max_retries - 1:
                    print(f"Database locked, retrying in {retry_delay} seconds... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                    continue
            print(f"Error getting technology stats: {e}")
            return []
        except Exception as e:
            print(f"Error getting technology stats: {e}")
            return []

# Initialize database if it doesn't exist
if not os.path.exists(DB_PATH):
    init_db()
