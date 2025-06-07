# 🚀 RepoSpotlight

A Streamlit application that showcases GitHub projects with configurable repository locations. The app reads README files and project metadata to build a comprehensive project showcase page. It displays projects in an attractive tile layout and can be deployed to Streamlit Community Cloud with persistent data storage.

## Features

- ✨ Spotlight your best work in a beautiful interface
- 🔍 Add any public or private GitHub repository URL
- 🔄 Keep repository data fresh with one-click updates
- 🔑 GitHub token support for private repositories
- 📊 View comprehensive repository statistics
- 📝 Display formatted README files
- 🎨 Enhanced display with custom metadata
- ☁️ Support for both local and cloud-based storage
- 🌐 Ready for deployment to Streamlit Community Cloud

## Installation

1. Clone this repository
2. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```
2. Add GitHub repositories:
   - Enter a GitHub repository URL in the sidebar
   - Click "Add Repository"
3. Explore repositories:
   - Switch between tile view and list view
   - Click "View" to see repository details
   - Use "Refresh" to update repository data
4. Optionally provide a GitHub personal access token for increased API rate limits or access to private repositories

## Deployment to Streamlit Cloud

RepoSpotlight can be deployed to [Streamlit Community Cloud](https://streamlit.io/cloud) with persistent data storage. Follow these steps:

### 1. Set Up Firebase

1. Create a free Firebase account at [Firebase Console](https://console.firebase.google.com/)
2. Create a new Firebase project
3. Set up Firestore Database in your project
   - Go to Firestore Database in the Firebase console
   - Click "Create database"
   - Start in production mode
   - Choose a location close to your users
4. Generate a service account key:
   - Go to Project Settings > Service accounts
   - Click "Generate new private key"
   - Save the JSON file securely

### 2. Set Up Streamlit Cloud

1. Push your code to a GitHub repository
2. Log in to [Streamlit Community Cloud](https://share.streamlit.io/)
3. Click "New app" and select your GitHub repository
4. Configure your app settings:
   - Main file path: `app.py`
   - Python version: 3.9 or higher

### 3. Configure Secrets

In the Streamlit Cloud dashboard:

1. Go to your app settings
2. Find the "Secrets" section
3. Add the following configuration:

```toml
# Database Configuration
USE_CLOUD_DB = true

# Firebase Configuration
# Paste your Firebase service account JSON here as a string
FIREBASE_CREDENTIALS = """
{
  "type": "service_account",
  "project_id": "your-project-id",
  "private_key_id": "your-private-key-id",
  "private_key": "your-private-key",
  "client_email": "your-client-email",
  "client_id": "your-client-id",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "your-cert-url"
}
"""

# GitHub API Configuration (optional)
GITHUB_TOKEN = ""  # Optional
```

### 4. Migrate Existing Data (Optional)

If you have existing data in the local SQLite database and want to transfer it to Firebase:

1. Configure Firebase credentials in `.streamlit/secrets.toml`
2. Run the migration script:
   ```bash
   python migrate_to_firebase.py
   ```
3. Verify your data has been successfully migrated by checking the Firebase console

### 5. Deploy Your App

1. Click "Deploy" in the Streamlit Cloud dashboard
2. Wait for the build to complete
3. Your app will be available at the provided URL

## Custom Metadata

To enhance the project showcase, you can add a custom metadata file to your GitHub repository:

1. Create a `.github` folder in your repository (if it doesn't exist)
2. Add a file named `project_metadata.json` with the following structure:

```json
{
  "project_name": "Your Project Name",
  "tagline": "A short catchy description",
  "showcase_image": "URL to main project image",
  "demo_url": "URL to live demo if available",
  "documentation_url": "URL to project documentation",
  "features": [
    "Key feature 1",
    "Key feature 2",
    "Key feature 3"
  ],
  "tech_stack": [
    "Technology 1",
    "Technology 2",
    "Technology 3"
  ],
  "contact": {
    "email": "contact@example.com",
    "twitter": "your_twitter_handle",
    "linkedin": "your_linkedin_profile"
  },
  "contributors": [
    {
      "name": "Contributor Name",
      "github": "github_username",
      "role": "Role in project"
    }
  ]
}
```

## Requirements

- Python 3.7+
- Streamlit
- PyGithub
- requests
- markdown
- sqlite-utils

## License

MIT
