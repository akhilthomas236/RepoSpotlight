import streamlit as st
import requests
import json
import os
import base64
from github import Github
import markdown
import re
from pathlib import Path
import datetime

# Import the database module
import database as db

# Initialize database if needed
def ensure_db_initialized():
    """Make sure the database is initialized properly"""
    try:
        # Check if technologies table exists
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='technologies'")
        if not cursor.fetchone():
            cursor.execute('''
            CREATE TABLE IF NOT EXISTS technologies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                count INTEGER DEFAULT 0
            )
            ''')
            conn.commit()
            st.success("Database schema updated")
        conn.close()
    except Exception as e:
        st.error(f"Database initialization error: {str(e)}")

# Function to get repository information
def get_repo_info(repo_url):
    """
    Extract and return information from a GitHub repository
    """
    # Normalize the URL to handle various formats
    # Remove trailing slash, .git extension, and any query parameters
    repo_url = repo_url.strip().rstrip('/')
    if repo_url.endswith('.git'):
        repo_url = repo_url[:-4]
    
    # Extract owner and repo name from URL
    # Supports formats:
    # - https://github.com/username/repo
    # - http://github.com/username/repo
    # - github.com/username/repo
    # - git@github.com:username/repo.git
    pattern = r"(?:https?:\/\/)?(?:www\.)?github\.com[\/:]([^\/]+)\/([^\/\s\?#]+)"
    match = re.search(pattern, repo_url)
    
    if not match:
        st.error("Invalid GitHub repository URL")
        st.info("URL should be in format: github.com/username/repository")
        return None
    
    owner = match.group(1)
    repo_name = match.group(2)
    
    # GitHub access token (optional)
    access_token = st.session_state.get("github_token", "")
    
    try:
        if access_token:
            g = Github(access_token)
        else:
            g = Github()
        
        try:    
            repo = g.get_repo(f"{owner}/{repo_name}")
        except Exception as e:
            if "404" in str(e):
                st.error(f"Repository not found: {owner}/{repo_name}")
                st.info("Make sure the repository exists and is spelled correctly.")
                return None
            elif "403" in str(e):
                st.error("API rate limit exceeded")
                st.info("Consider adding a GitHub token to increase your rate limit.")
                return None
            else:
                st.error(f"Error accessing repository: {str(e)}")
                return None
        
        # Get README content
        try:
            readme_content = repo.get_readme().decoded_content.decode("utf-8")
        except Exception as e:
            readme_content = "No README found"
        
        # Check for project metadata in possible locations
        metadata = {}
        metadata_paths = [
            ".github/project_metadata.json",
            "project_metadata.json",
            "docs/project_metadata.json",
            ".metadata/project.json"
        ]
        
        for path in metadata_paths:
            try:
                metadata_content = repo.get_contents(path)
                metadata = json.loads(metadata_content.decoded_content.decode("utf-8"))
                st.success(f"Found metadata at {path}")
                break
            except:
                # Try next location
                continue
        
        # Get recent commits
        recent_commits = get_recent_commits(repo)
        
        # Get repository data
        repo_data = {
            "name": repo.name,
            "full_name": repo.full_name,
            "description": repo.description,
            "stars": repo.stargazers_count,
            "forks": repo.forks_count,
            "watchers": repo.watchers_count,
            "language": repo.language,
            "issues": repo.open_issues_count,
            "created_at": repo.created_at.strftime("%Y-%m-%d"),
            "updated_at": repo.updated_at.strftime("%Y-%m-%d"),
            "readme": readme_content,
            "owner": {
                "login": repo.owner.login,
                "avatar_url": repo.owner.avatar_url,
                "html_url": repo.owner.html_url
            },
            "html_url": repo.html_url,
            "topics": repo.get_topics(),
            "custom_metadata": metadata,
            "recent_commits": recent_commits,
            "default_branch": repo.default_branch
        }
        
        return repo_data
    except Exception as e:
        st.error(f"Error fetching repository: {str(e)}")
        return None

# Function to convert markdown to HTML
def md_to_html(md_text):
    """Convert markdown text to HTML"""
    return markdown.markdown(md_text, extensions=['tables', 'fenced_code'])

# Function to generate project metadata template
def generate_metadata_template():
    """Generate a template for project metadata"""
    template = {
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
    return json.dumps(template, indent=2)

# Function to get recent commits
def get_recent_commits(repo, limit=5):
    """Fetch recent commits from the repository"""
    try:
        commits = repo.get_commits()
        recent_commits = []
        
        # Get first 'limit' commits
        for commit in commits[:limit]:
            commit_data = {
                "sha": commit.sha[:7],  # First 7 chars of commit hash
                "message": commit.commit.message.split("\n")[0],  # First line of commit message
                "author": commit.commit.author.name,
                "date": commit.commit.author.date.strftime("%Y-%m-%d"),
                "url": commit.html_url
            }
            recent_commits.append(commit_data)
            
        return recent_commits
    except Exception as e:
        st.warning(f"Could not fetch commits: {str(e)}")
        return []

def show_repository_detail(repo_url):
    """Show detailed view of a repository"""
    # Back button
    if st.button("← Back to Repository List", key="back_button"):
        st.session_state["view_mode"] = "tiles"
        st.session_state["selected_repo"] = None
        st.rerun()
    
    if repo_url:
        # Get repository from database
        db_repo = db.get_repository(repo_url)
        
        if db_repo:
            # Show the last synced date
            st.caption(f"Last synced: {db_repo['last_synced']}")
            
            # Refresh button
            if st.button("🔄 Refresh Repository Data", key="refresh_detail"):
                with st.spinner("Refreshing repository data..."):
                    repo_data = get_repo_info(db_repo["repo_url"])
                    if repo_data:
                        if db.update_repository(db_repo["repo_url"], repo_data):
                            st.success(f"Refreshed: {db_repo['name']}")
                            st.rerun()
        
            # Try to get fresh data from GitHub
            with st.spinner("Loading repository data..."):
                repo_data = get_repo_info(db_repo["repo_url"])
            
            if repo_data:
                # Layout with columns
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    # Display owner avatar
                    st.image(repo_data["owner"]["avatar_url"], width=100)
                    # Repository details
                    st.subheader(repo_data["name"])
                    st.write(f"by [{repo_data['owner']['login']}]({repo_data['owner']['html_url']})")
                    st.write(repo_data["description"] if repo_data["description"] else "No description")
                    
                    # Repository stats
                    st.write(f"⭐ Stars: {repo_data['stars']}")
                    st.write(f"🍴 Forks: {repo_data['forks']}")
                    st.write(f"👀 Watchers: {repo_data['watchers']}")
                    st.write(f"🔤 Language: {repo_data['language']}")
                    st.write(f"⚠️ Open Issues: {repo_data['issues']}")
                    st.write(f"📅 Created: {repo_data['created_at']}")
                    st.write(f"🔄 Updated: {repo_data['updated_at']}")
                    
                    # Topics
                    if repo_data["topics"]:
                        st.write("🏷️ Topics:")
                        st.write(", ".join(repo_data["topics"]))
                    
                    # Link to repository
                    st.markdown(f"[View on GitHub]({repo_data['html_url']})")
                    
                    # Recent activity section
                    if repo_data.get("recent_commits"):
                        st.subheader("Recent Activity")
                        for commit in repo_data["recent_commits"]:
                            st.markdown(f"""
                            📝 [{commit['sha']}]({commit['url']}) - {commit['message']}
                            <small>by {commit['author']} on {commit['date']}</small>
                            """, unsafe_allow_html=True)
                
                with col2:
                    # Custom metadata if available
                    if repo_data["custom_metadata"]:
                        metadata = repo_data["custom_metadata"]
                        
                        # Project name from metadata if available
                        if "project_name" in metadata:
                            st.header(metadata["project_name"])
                        
                        # Tagline if available
                        if "tagline" in metadata:
                            st.subheader(metadata["tagline"])
                        
                        # Showcase image if available
                        if "showcase_image" in metadata:
                            st.image(metadata["showcase_image"])
                        
                        # Demo and documentation links
                        cols = st.columns(2)
                        if "demo_url" in metadata:
                            cols[0].markdown(f"[Live Demo]({metadata['demo_url']})")
                        if "documentation_url" in metadata:
                            cols[1].markdown(f"[Documentation]({metadata['documentation_url']})")
                        
                        # Features
                        if "features" in metadata and metadata["features"]:
                            st.subheader("Features")
                            for feature in metadata["features"]:
                                st.markdown(f"- {feature}")
                        
                        # Tech stack
                        if "tech_stack" in metadata and metadata["tech_stack"]:
                            st.subheader("Tech Stack")
                            st.write(", ".join(metadata["tech_stack"]))
                        
                        # Contributors
                        if "contributors" in metadata and metadata["contributors"]:
                            st.subheader("Contributors")
                            for contributor in metadata["contributors"]:
                                st.write(f"- {contributor['name']} ({contributor['role']})")
                    
                    # README content
                    st.header("README")
                    st.markdown(repo_data["readme"])
            else:
                st.error("Failed to load repository data from GitHub")
        else:
            st.error(f"Repository not found in database: {repo_url}")
    else:
        st.error("No repository selected")

def display_tile_view(repositories):
    """Display repositories in tile view"""
    if repositories:
        # Create rows with 3 repositories per row
        for i in range(0, len(repositories), 3):
            row_repos = repositories[i:i+3]
            cols = st.columns(3)
            
            for j, repo in enumerate(row_repos):
                with cols[j]:
                    with st.container(border=True):
                        # Repository card
                        st.subheader(repo["name"])
                        st.caption(f"by {repo['owner']}")
                        
                        # Add description with character limit
                        description = repo["description"]
                        if description and len(description) > 100:
                            description = description[:97] + "..."
                        st.write(description or "No description")
                        
                        # Stats row
                        stats_col1, stats_col2, stats_col3 = st.columns(3)
                        stats_col1.metric("Stars", repo["stars"])
                        stats_col2.metric("Forks", repo["forks"])
                        stats_col3.metric("Language", repo["language"] or "N/A")
                        
                        # Action buttons
                        col1, col2, col3 = st.columns(3)
                        
                        # View button
                        view_key = f"view_{repo['id']}"
                        if col1.button("📖 View", key=view_key):
                            # Debug message
                            st.info(f"Setting selected repo: {repo['repo_url']}")
                            st.session_state["selected_repo"] = repo["repo_url"]
                            st.session_state["view_mode"] = "detail"
                            st.rerun()
                        
                        # Refresh button
                        refresh_key = f"refresh_{repo['id']}"
                        if col2.button("🔄 Refresh", key=refresh_key):
                            with st.spinner("Refreshing..."):
                                repo_data = get_repo_info(repo["repo_url"])
                                if repo_data:
                                    if db.update_repository(repo["repo_url"], repo_data):
                                        st.success(f"Refreshed: {repo['name']}")
                                        st.rerun()
                        
                        # Delete button
                        delete_key = f"delete_{repo['id']}"
                        if col3.button("🗑️ Delete", key=delete_key):
                            if db.delete_repository(repo["repo_url"]):
                                st.success(f"Deleted: {repo['name']}")
                                st.rerun()
    else:
        st.info("No repositories added yet. Add a GitHub repository URL in the sidebar.")
        
        # Example showcase
        st.header("Example Project Showcase")
        st.markdown("""
        This app allows you to showcase GitHub projects by:
        
        1. Displaying repository details and stats
        2. Showing the README content
        3. Utilizing custom metadata for enhanced presentation
        
        ### Features
        - 🔍 Add any public GitHub repository URL
        - 🔄 Refresh repository data to keep it up to date
        - 🔑 Optional GitHub token for private repositories
        - 📊 View repository statistics
        - 📝 Read project READMEs
        - 🎨 Custom metadata support for enhanced showcase
        """)

def display_list_view(repositories):
    """Display repositories in list view"""
    if repositories:
        for repo in repositories:
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.subheader(repo["name"])
                    st.caption(f"by {repo['owner']}")
                    st.write(repo["description"] or "No description")
                    
                    # Tech info
                    st.write(f"Language: {repo['language'] or 'N/A'} | ⭐ {repo['stars']} | 🍴 {repo['forks']}")
                
                with col2:
                    # Action buttons
                    view_key = f"list_view_{repo['id']}"
                    refresh_key = f"list_refresh_{repo['id']}"
                    delete_key = f"list_delete_{repo['id']}"
                    
                    if st.button("📖 View", key=view_key):
                        st.session_state["selected_repo"] = repo["repo_url"]
                        st.session_state["view_mode"] = "detail"
                        st.rerun()
                    
                    if st.button("🔄 Refresh", key=refresh_key):
                        with st.spinner("Refreshing..."):
                            repo_data = get_repo_info(repo["repo_url"])
                            if repo_data:
                                if db.update_repository(repo["repo_url"], repo_data):
                                    st.success(f"Refreshed: {repo['name']}")
                                    st.rerun()
                    
                    if st.button("🗑️ Delete", key=delete_key):
                        if db.delete_repository(repo["repo_url"]):
                            st.success(f"Deleted: {repo['name']}")
                            st.rerun()
    else:
        st.info("No repositories added yet. Add a GitHub repository URL in the sidebar.")

def main():
    # Call initialization
    ensure_db_initialized()
    
    # Initialize session state for repository management
    if "selected_repo" not in st.session_state:
        st.session_state["selected_repo"] = None
    
    if "view_mode" not in st.session_state:
        st.session_state["view_mode"] = "tiles"  # Options: tiles, list, detail
    
    # Set page config
    st.set_page_config(
        page_title="GitHub Project Showcase",
        page_icon="🚀",
        layout="wide"
    )
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("Configuration")
        
        # GitHub personal access token (optional)
        github_token = st.text_input(
            "GitHub Token (optional)",
            type="password",
            help="Personal access token for increased API rate limits and private repos"
        )
        
        # Save token in session state
        if github_token:
            st.session_state["github_token"] = github_token
        
        # Add new repository section
        st.header("Add Repository")
        
        # GitHub repository URL
        new_repo_url = st.text_input(
            "GitHub Repository URL",
            placeholder="https://github.com/username/repository"
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            add_button = st.button("Add Repository")
        
        with col2:
            refresh_all = st.button("Refresh All")
        
        # Show metadata template
        if st.checkbox("Show metadata template"):
            st.code(generate_metadata_template(), language="json")
            
            st.markdown("""
            ### How to use metadata
            1. Create a `.github` folder in your repository
            2. Add a file named `project_metadata.json` with your custom metadata
            3. This app will automatically use that metadata for enhanced showcase
            """)
            
        # Technology stats
        st.header("Technology Stats")
        try:
            tech_stats = db.get_technology_stats()
            if tech_stats:
                for tech in tech_stats:
                    st.write(f"• {tech['name']}: {tech['count']} projects")
            else:
                st.info("No technology statistics available yet")
        except Exception as e:
            st.warning(f"Could not load technology stats: {str(e)}")
    
    # Main content
    st.title("GitHub Project Showcase")
    
    # Add new repository
    if add_button and new_repo_url:
        with st.spinner("Fetching repository information..."):
            repo_data = get_repo_info(new_repo_url)
            
            if repo_data:
                if db.add_repository(new_repo_url, repo_data):
                    st.success(f"Added repository: {repo_data['name']}")
                    # Force a rerun to update the list
                    st.rerun()
                else:
                    st.warning("Repository already exists in the database")
    
    # Refresh all repositories
    if refresh_all:
        repos = db.get_all_repositories()
        with st.spinner("Refreshing all repositories..."):
            for repo in repos:
                repo_data = get_repo_info(repo["repo_url"])
                if repo_data:
                    db.update_repository(repo["repo_url"], repo_data)
            st.success("All repositories refreshed")
            # Force a rerun to update all data
            st.rerun()
    
    # Check if we're in detail view 
    if st.session_state["view_mode"] == "detail" and st.session_state["selected_repo"]:
        # Show detail view of selected repository
        show_repository_detail(st.session_state["selected_repo"])
    else:
        # Get repositories from database
        repositories = db.get_all_repositories()
        
        # Display repository count and overview
        col1, col2 = st.columns(2)
        with col1:
            st.subheader(f"📚 {len(repositories)} Repositories")
        
        with col2:
            if st.session_state["view_mode"] in ["tiles", "list"]:
                view_options = ["Tile View", "List View"]
                selected_view = st.radio("View Mode", view_options, horizontal=True, 
                                      label_visibility="collapsed",
                                      index=0 if st.session_state["view_mode"] == "tiles" else 1)
                current_view = "tiles" if selected_view == "Tile View" else "list"
                
                # Only update if the view changed
                if current_view != st.session_state["view_mode"]:
                    st.session_state["view_mode"] = current_view
                    st.rerun()
        
        # Display repositories in tiles or list view
        if st.session_state["view_mode"] == "tiles":
            display_tile_view(repositories)
        elif st.session_state["view_mode"] == "list":
            display_list_view(repositories)

# Run the app
if __name__ == "__main__":
    main()
