"""
Cloud database module for RepoSpotlight using Firebase Firestore
Used as a persistent data storage solution for Streamlit Cloud
"""
import json
from typing import List, Dict, Any, Optional
import datetime
import os
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import uuid

# Firebase initialization status
_firebase_initialized = False

# Get the Firebase credentials from environment or secrets
def get_firebase_creds():
    """Retrieve Firebase credentials from environment or Streamlit secrets"""
    # Check for JSON in environment variable
    firebase_json = os.environ.get("FIREBASE_CREDENTIALS")
    
    # If not in environment, check Streamlit secrets
    if not firebase_json and hasattr(st, "secrets") and "FIREBASE_CREDENTIALS" in st.secrets:
        firebase_json = st.secrets["FIREBASE_CREDENTIALS"]
    
    if firebase_json:
        return firebase_json
    
    # If the credentials are stored as a file path
    creds_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
    if not creds_path and hasattr(st, "secrets") and "FIREBASE_CREDENTIALS_PATH" in st.secrets:
        creds_path = st.secrets["FIREBASE_CREDENTIALS_PATH"]
    
    if creds_path and os.path.exists(creds_path):
        with open(creds_path, 'r') as f:
            return f.read()
    
    return None

# Initialize Firebase connection
def init_firebase():
    """Initialize Firebase connection"""
    global _firebase_initialized
    
    if _firebase_initialized:
        return True
    
    try:
        # Get Firebase credentials
        firebase_creds = get_firebase_creds()
        if not firebase_creds:
            raise ValueError("Firebase credentials not found. Please set FIREBASE_CREDENTIALS in environment or secrets.")
        
        # Create temporary credentials file (Firebase requires a file path)
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
            temp_file.write(firebase_creds)
            temp_file_path = temp_file.name
        
        # Initialize Firebase with the credentials
        cred = credentials.Certificate(temp_file_path)
        firebase_admin.initialize_app(cred)
        
        # Clean up the temporary file
        os.unlink(temp_file_path)
        
        _firebase_initialized = True
        return True
    except Exception as e:
        print(f"Error initializing Firebase: {e}")
        return False

# Get Firestore database client
def get_db():
    """Get the Firestore database client"""
    if not init_firebase():
        raise ValueError("Failed to initialize Firebase")
    return firestore.client()

# Initialize database collections
def init_db():
    """Initialize database - no action needed for Firestore as collections are created on first use"""
    try:
        # Attempt to get the database client to check connection
        get_db()
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

# Dummy function to maintain compatibility with SQLite version
def get_db_connection():
    """Dummy function to maintain API compatibility with SQLite version"""
    return None

# Dummy function to maintain compatibility with SQLite version
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
        db = get_db()
        
        # Check if repository already exists
        repo_ref = db.collection('repositories').where('repo_url', '==', repo_url).limit(1)
        existing_repos = list(repo_ref.stream())
        if existing_repos:
            return False  # Repository already exists
        
        # Convert repo_data to JSON string for storage
        metadata = json.dumps(repo_data.get("custom_metadata", {}))
        
        # Generate a unique ID
        repo_id = str(uuid.uuid4())
        
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
            "metadata": metadata,
            "id": repo_id  # Store ID for compatibility with SQLite version
        }
        
        # Add to database
        db.collection('repositories').document(repo_id).set(repo_data_to_store)
        
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
        db = get_db()
        
        # Check if repository exists
        repo_ref = db.collection('repositories').where('repo_url', '==', repo_url).limit(1)
        existing_repos = list(repo_ref.stream())
        if not existing_repos:
            return False  # Repository doesn't exist
        
        # Get the document ID
        doc_id = existing_repos[0].id
        existing_data = existing_repos[0].to_dict()
        
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
            "metadata": metadata,
            "id": existing_data.get("id", doc_id)  # Preserve ID
        }
        
        # Update in database
        db.collection('repositories').document(doc_id).update(repo_data_to_store)
        
        return True
        
    except Exception as e:
        print(f"Error updating repository: {e}")
        return False

def get_all_repositories() -> List[Dict[str, Any]]:
    """Get all repositories from the database"""
    try:
        db = get_db()
        
        # Fetch all repositories
        repos_ref = db.collection('repositories').stream()
        
        # Process items
        repositories = []
        for doc in repos_ref:
            repo = doc.to_dict()
            
            # Convert metadata JSON string back to dictionary
            try:
                repo["metadata"] = json.loads(repo["metadata"]) if repo["metadata"] else {}
            except:
                repo["metadata"] = {}
            
            # Ensure ID field exists
            if "id" not in repo:
                repo["id"] = doc.id
                
            # Add to list
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
        db = get_db()
        
        # Fetch repository
        repo_ref = db.collection('repositories').where('repo_url', '==', repo_url).limit(1)
        docs = list(repo_ref.stream())
        
        if not docs:
            return None
            
        doc = docs[0]
        repo = doc.to_dict()
        
        # Convert metadata JSON string back to dictionary
        try:
            repo["metadata"] = json.loads(repo["metadata"]) if repo["metadata"] else {}
        except:
            repo["metadata"] = {}
            
        # Ensure ID field exists
        if "id" not in repo:
            repo["id"] = doc.id
            
        return repo
    except Exception as e:
        print(f"Error getting repository: {e}")
        return None

def delete_repository(repo_url: str) -> bool:
    """Delete a repository from the database"""
    try:
        db = get_db()
        
        # Check if repository exists
        repo_ref = db.collection('repositories').where('repo_url', '==', repo_url).limit(1)
        docs = list(repo_ref.stream())
        
        if not docs:
            return False
            
        doc = docs[0]
        repo = doc.to_dict()
            
        # Update technology count if needed
        if repo.get("language"):
            decrease_technology_count(repo["language"])
        
        # Delete repository
        db.collection('repositories').document(doc.id).delete()
        
        return True
    except Exception as e:
        print(f"Error deleting repository: {e}")
        return False

def update_technology(name: str):
    """Increment the count for a technology"""
    try:
        db = get_db()
        
        # Check if technology exists
        tech_ref = db.collection('technologies').where('name', '==', name).limit(1)
        docs = list(tech_ref.stream())
        
        if docs:
            # Update count
            doc = docs[0]
            tech = doc.to_dict()
            db.collection('technologies').document(doc.id).update({
                'count': tech.get('count', 0) + 1
            })
        else:
            # Insert new technology
            db.collection('technologies').add({
                'name': name, 
                'count': 1
            })
            
    except Exception as e:
        print(f"Error updating technology: {e}")

def decrease_technology_count(name: str):
    """Decrease the count for a technology"""
    try:
        db = get_db()
        
        # Check if technology exists
        tech_ref = db.collection('technologies').where('name', '==', name).limit(1)
        docs = list(tech_ref.stream())
        
        if docs:
            doc = docs[0]
            tech = doc.to_dict()
            current_count = tech.get('count', 0)
            
            if current_count <= 1:
                # Remove if count will be zero
                db.collection('technologies').document(doc.id).delete()
            else:
                # Decrease count
                db.collection('technologies').document(doc.id).update({
                    'count': current_count - 1
                })
            
    except Exception as e:
        print(f"Error decreasing technology count: {e}")

def get_technology_stats() -> List[Dict[str, Any]]:
    """Get statistics for all technologies"""
    try:
        db = get_db()
        
        # Fetch all technologies
        tech_ref = db.collection('technologies').stream()
        
        # Convert to list of dictionaries
        stats = []
        for doc in tech_ref:
            tech = doc.to_dict()
            stats.append({
                'name': tech.get('name', ''),
                'count': tech.get('count', 0)
            })
            
        # Sort by count in descending order
        stats.sort(key=lambda x: x['count'], reverse=True)
        
        return stats
    except Exception as e:
        print(f"Error getting technology stats: {e}")
        return []

# Initialize database
init_db()
