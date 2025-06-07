"""
Cloud database module for RepoSpotlight
Uses Deta Space as the storage backend for persistent data on Streamlit Cloud
"""
import json
from typing import List, Dict, Any, Optional
import datetime
import os
from deta import Deta
import streamlit as st

# Get the Deta project key from environment or secrets
def get_deta_key():
    """Retrieve Deta project key from environment or Streamlit secrets"""
    # Check for key in environment variable
    deta_key = os.environ.get("DETA_PROJECT_KEY")
    
    # If not in environment, check Streamlit secrets
    if not deta_key and hasattr(st, "secrets") and "DETA_PROJECT_KEY" in st.secrets:
        deta_key = st.secrets["DETA_PROJECT_KEY"]
    
    return deta_key

# Initialize Deta with the project key
def init_deta():
    """Initialize Deta client with project key"""
    deta_key = get_deta_key()
    if not deta_key:
        raise ValueError("Deta project key not found. Set the DETA_PROJECT_KEY environment variable or in Streamlit secrets.")
    return Deta(deta_key)

# Create/get database collections
def get_repositories_db():
    """Get the repositories database collection"""
    deta = init_deta()
    return deta.Base("repositories")

def get_technologies_db():
    """Get the technologies database collection"""
    deta = init_deta()
    return deta.Base("technologies")

# Initialize required collections
def init_db():
    """Initialize required database collections"""
    try:
        # Just accessing the collections initializes them if they don't exist
        get_repositories_db()
        get_technologies_db()
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

# Dummy function to maintain compatibility
def get_db_connection():
    """Dummy function to maintain API compatibility with SQLite version"""
    return None

# Dummy function to maintain compatibility
def safe_close(conn):
    """Dummy function to maintain API compatibility with SQLite version"""
    pass

def add_repository(repo_url: str, repo_data: Dict[str, Any]) -> bool:
    """
    Add a new repository to the database
    
    Args:
        repo_url: The GitHub repository URL
        repo_data: Dictionary containing repository information
        
    Returns:
        bool: True if repository was added successfully, False otherwise
    """
    try:
        repo_db = get_repositories_db()
        
        # Check if repository already exists
        existing = repo_db.fetch({"repo_url": repo_url}).items
        if existing:
            return False  # Repository already exists
        
        # Convert repo_data to JSON string for storage
        metadata = repo_data.get("custom_metadata", {})
        
        # Prepare repository data
        repo_data_to_store = {
            "repo_url": repo_url,
            "name": repo_data["name"],
            "owner": repo_data["owner"]["login"],
            "description": repo_data.get("description", ""),
            "stars": repo_data["stars"],
            "forks": repo_data["forks"],
            "language": repo_data.get("language", ""),
            "last_updated": repo_data["updated_at"],
            "last_synced": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metadata": json.dumps(metadata)
        }
        
        # Add to database
        repo_db.put(repo_data_to_store)
        
        # Update technology count
        if repo_data.get("language"):
            update_technology(repo_data["language"])
        
        # Update technologies from metadata if available
        if repo_data.get("custom_metadata", {}).get("tech_stack"):
            for tech in repo_data["custom_metadata"]["tech_stack"]:
                update_technology(tech)
                
        return True
        
    except Exception as e:
        print(f"Error adding repository: {e}")
        return False

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
        repo_db = get_repositories_db()
        
        # Check if repository exists
        existing = repo_db.fetch({"repo_url": repo_url}).items
        if not existing:
            return False  # Repository doesn't exist
        
        # Convert repo_data to JSON string for storage
        metadata = json.dumps(repo_data.get("custom_metadata", {}))
        
        # Prepare repository data
        repo_data_to_store = {
            "repo_url": repo_url,
            "name": repo_data["name"],
            "owner": repo_data["owner"]["login"],
            "description": repo_data.get("description", ""),
            "stars": repo_data["stars"],
            "forks": repo_data["forks"],
            "language": repo_data.get("language", ""),
            "last_updated": repo_data["updated_at"],
            "last_synced": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metadata": metadata
        }
        
        # Update in database - Deta automatically creates a new one if it doesn't exist
        repo_db.put(repo_data_to_store, existing[0]["key"])
        
        return True
        
    except Exception as e:
        print(f"Error updating repository: {e}")
        return False

def get_all_repositories() -> List[Dict[str, Any]]:
    """Get all repositories from the database"""
    try:
        repo_db = get_repositories_db()
        
        # Fetch all repositories
        results = repo_db.fetch().items
        
        # Process items
        repositories = []
        for repo in results:
            # Convert metadata JSON string back to dictionary
            try:
                repo["metadata"] = json.loads(repo["metadata"]) if repo["metadata"] else {}
            except:
                repo["metadata"] = {}
            
            # Add to list
            repo["id"] = repo["key"]  # Map key to id for compatibility
            repositories.append(repo)
            
        # Sort by last_synced in descending order
        repositories.sort(key=lambda x: x.get("last_synced", ""), reverse=True)
        
        return repositories
    except Exception as e:
        print(f"Error getting repositories: {e}")
        return []

def get_repository(repo_url: str) -> Optional[Dict[str, Any]]:
    """Get a specific repository by URL"""
    try:
        repo_db = get_repositories_db()
        
        # Fetch repository
        results = repo_db.fetch({"repo_url": repo_url}).items
        
        if not results:
            return None
            
        repo = results[0]
        
        # Convert metadata JSON string back to dictionary
        try:
            repo["metadata"] = json.loads(repo["metadata"]) if repo["metadata"] else {}
        except:
            repo["metadata"] = {}
            
        # Map key to id for compatibility
        repo["id"] = repo["key"]
        
        return repo
    except Exception as e:
        print(f"Error getting repository: {e}")
        return None

def delete_repository(repo_url: str) -> bool:
    """Delete a repository from the database"""
    try:
        repo_db = get_repositories_db()
        
        # Check if repository exists
        results = repo_db.fetch({"repo_url": repo_url}).items
        if not results:
            return False
            
        repo = results[0]
            
        # Update technology count if needed
        if repo.get("language"):
            decrease_technology_count(repo["language"])
        
        # Delete repository
        repo_db.delete(repo["key"])
        
        return True
    except Exception as e:
        print(f"Error deleting repository: {e}")
        return False

def update_technology(name: str):
    """Increment the count for a technology"""
    try:
        tech_db = get_technologies_db()
        
        # Check if technology exists
        results = tech_db.fetch({"name": name}).items
        
        if results:
            # Update count
            tech = results[0]
            tech_db.update({"count": tech["count"] + 1}, tech["key"])
        else:
            # Insert new technology
            tech_db.put({"name": name, "count": 1})
            
    except Exception as e:
        print(f"Error updating technology: {e}")

def decrease_technology_count(name: str):
    """Decrease the count for a technology"""
    try:
        tech_db = get_technologies_db()
        
        # Check if technology exists
        results = tech_db.fetch({"name": name}).items
        
        if results:
            tech = results[0]
            if tech["count"] <= 1:
                # Remove if count will be zero
                tech_db.delete(tech["key"])
            else:
                # Decrease count
                tech_db.update({"count": tech["count"] - 1}, tech["key"])
            
    except Exception as e:
        print(f"Error decreasing technology count: {e}")

def get_technology_stats() -> List[Dict[str, Any]]:
    """Get statistics for all technologies"""
    try:
        tech_db = get_technologies_db()
        
        # Fetch all technologies
        results = tech_db.fetch().items
        
        # Convert to list of dictionaries
        stats = []
        for tech in results:
            stats.append({
                "name": tech["name"],
                "count": tech["count"]
            })
            
        # Sort by count in descending order
        stats.sort(key=lambda x: x["count"], reverse=True)
        
        return stats
    except Exception as e:
        print(f"Error getting technology stats: {e}")
        return []

# Initialize database
init_db()
