"""
Test script to verify Firebase credentials are properly configured
"""
import streamlit as st
import firebase_admin
from firebase_admin import credentials, firestore
import os
import json

def test_firebase_connection():
    """
    Test if Firebase credentials are properly configured and can
    establish a connection to Firestore
    """
    print("Checking Firebase credentials configuration...")
    
    # Check for credentials in environment variables
    firebase_creds_env = os.environ.get("FIREBASE_CREDENTIALS")
    firebase_path_env = os.environ.get("FIREBASE_CREDENTIALS_PATH")
    
    # Check for credentials in Streamlit secrets
    firebase_creds_secret = st.secrets.get("FIREBASE_CREDENTIALS") if hasattr(st, "secrets") else None
    firebase_path_secret = st.secrets.get("FIREBASE_CREDENTIALS_PATH") if hasattr(st, "secrets") else None
    
    print("\nCredential Sources:")
    print(f"- Environment FIREBASE_CREDENTIALS: {'Found' if firebase_creds_env else 'Not found'}")
    print(f"- Environment FIREBASE_CREDENTIALS_PATH: {'Found' if firebase_path_env else 'Not found'}")
    print(f"- Streamlit Secrets FIREBASE_CREDENTIALS: {'Found' if firebase_creds_secret else 'Not found'}")
    print(f"- Streamlit Secrets FIREBASE_CREDENTIALS_PATH: {'Found' if firebase_path_secret else 'Not found'}")
    
    # Try to initialize Firebase
    try:
        # Get credentials from environment or secrets
        creds_json = firebase_creds_env or firebase_creds_secret
        creds_path = firebase_path_env or firebase_path_secret
        
        if not creds_json and not creds_path:
            print("\n❌ No Firebase credentials found in environment or secrets.")
            return False
            
        if creds_json:
            print("\nUsing Firebase credentials from environment/secrets JSON...")
            # Create temporary file for the credentials
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, mode='w') as temp_file:
                if isinstance(creds_json, str):
                    temp_file.write(creds_json)
                else:
                    json.dump(creds_json, temp_file)
                temp_file_path = temp_file.name
                
            # Initialize Firebase with the temp file
            cred = credentials.Certificate(temp_file_path)
            
            # Delete the temporary file
            os.unlink(temp_file_path)
        else:
            print(f"\nUsing Firebase credentials from file path: {creds_path}")
            cred = credentials.Certificate(creds_path)
        
        # Initialize Firebase app if not already initialized
        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(cred)
        
        # Test Firestore connection
        db = firestore.client()
        collections = [col.id for col in db.collections()]
        
        print("\n✅ Successfully connected to Firebase Firestore!")
        print(f"Available collections: {collections if collections else 'No collections found'}")
        return True
        
    except Exception as e:
        print(f"\n❌ Firebase initialization failed: {str(e)}")
        return False

if __name__ == "__main__":
    test_firebase_connection()
