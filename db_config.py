"""
Database configuration manager for RepoSpotlight
Automatically selects the appropriate database backend based on the environment
"""
import os
import streamlit as st

# Check if we're running on Streamlit Cloud
def is_cloud_environment():
    """
    Check if the app is running on Streamlit Cloud
    
    This checks for common environment variables that would be present in a cloud environment
    or a specific flag set in secrets.toml
    
    Returns:
        bool: True if running on cloud, False if running locally
    """
    # Streamlit Cloud sets this environment variable
    if os.environ.get("STREAMLIT_SHARING") or os.environ.get("STREAMLIT_CLOUD"):
        return True
        
    # Check for a user-defined flag in secrets
    if hasattr(st, "secrets") and "USE_CLOUD_DB" in st.secrets:
        return st.secrets["USE_CLOUD_DB"] == True
    
    # Check for environment variable
    if os.environ.get("USE_CLOUD_DB") == "true":
        return True
    
    # Default to local
    return False

# Import the appropriate database module
if is_cloud_environment():
    try:
        import firebase_database as db
        print("Using cloud database backend (Firebase)")
    except ImportError:
        print("Error importing cloud database module. Falling back to SQLite.")
        import database as db
else:
    import database as db
    print("Using local SQLite database backend")
