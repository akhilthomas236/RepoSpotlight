# Local Testing with Firebase

This guide helps you test your RepoSpotlight application with Firebase storage locally before deploying to Streamlit Cloud.

## Step 1: Set up a Firebase Project

1. Go to [Firebase Console](https://console.firebase.google.com/)
2. Click "Add project" and follow the setup steps
3. Once your project is created, go to Project Settings > Service accounts
4. Click "Generate new private key" to download your Firebase credentials JSON file
5. Save this file in a secure location (don't commit it to version control)

## Step 2: Configure Local Environment

### Option 1: Using Environment Variables

Set the Firebase credentials as an environment variable:

```bash
# Mac/Linux
export FIREBASE_CREDENTIALS_PATH="/path/to/your/firebase-credentials.json"
export USE_CLOUD_DB="true"

# Windows (CMD)
set FIREBASE_CREDENTIALS_PATH=C:\path\to\your\firebase-credentials.json
set USE_CLOUD_DB=true

# Windows (PowerShell)
$env:FIREBASE_CREDENTIALS_PATH="C:\path\to\your\firebase-credentials.json"
$env:USE_CLOUD_DB="true"
```

### Option 2: Using Streamlit Secrets

Create a `.streamlit/secrets.toml` file (if you haven't already):

```toml
# Database Configuration
USE_CLOUD_DB = true

# Firebase Configuration - File Path Method
FIREBASE_CREDENTIALS_PATH = "/path/to/your/firebase-credentials.json"

# Alternatively, paste the entire JSON content as a string
# FIREBASE_CREDENTIALS = """
# {
#   "type": "service_account",
#   ... your credentials here ...
# }
# """
```

## Step 3: Run the Application Locally

1. Start your virtual environment:
   ```bash
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```

3. If you previously used SQLite and want to migrate your data:
   ```bash
   python migrate_to_firebase.py
   ```

## Troubleshooting

### Firebase Initialization Issues
- Make sure the credentials JSON file exists and is readable
- Check that the JSON is properly formatted
- Verify that you've enabled Firestore in your Firebase project

### Data Migration Issues
- Ensure both SQLite and Firebase databases are properly configured
- Check that your SQLite database file exists and has data
- Run the app with debug logging enabled:
  ```bash
  streamlit run app.py --log_level=debug
  ```

### Connection Issues
- Make sure your network allows connections to Firebase
- Verify that your Firebase project has billing enabled if you're using high volumes of data
