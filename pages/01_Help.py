import streamlit as st
import json

def main():
    st.set_page_config(
        page_title="RepoSpotlight - Help",
        page_icon="❓",
        layout="wide"
    )
    
    st.title("RepoSpotlight - Help")
    
    st.header("How to Use This App")
    
    st.markdown("""
    ### Basic Usage
    
    1. Enter a GitHub repository URL in the sidebar
    2. The app will fetch the repository details and README
    3. Review the project information displayed in the main panel
    
    ### GitHub Token (Optional)
    
    You can provide a GitHub personal access token to:
    - Increase API rate limits
    - Access private repositories
    - Enable more API features
    
    To create a token:
    1. Go to [GitHub Settings > Developer settings > Personal access tokens](https://github.com/settings/tokens)
    2. Click "Generate new token"
    3. Select the "repo" scope for repository access
    4. Copy the generated token and paste it in the app's sidebar
    
    ### Custom Metadata
    
    To enhance your project showcase, you can add custom metadata:
    
    1. Create a `.github` folder in your repository
    2. Add a file named `project_metadata.json` with your custom data
    3. The app will automatically detect and use this metadata
    
    ## Metadata Structure
    """)
    
    with st.expander("View Example Metadata"):
        with open("example_metadata.json", "r") as f:
            metadata = json.load(f)
        st.json(metadata)
    
    st.header("Troubleshooting")
    
    st.markdown("""
    ### Common Issues
    
    **"Invalid GitHub repository URL" error**
    - Ensure the URL follows the format: `https://github.com/username/repository`
    - Check for typos in the username or repository name
    
    **"Rate limit exceeded" error**
    - Provide a GitHub token to increase your API rate limit
    - Wait a few minutes before trying again
    
    **Repository not loading**
    - Check if the repository exists and is accessible
    - For private repositories, ensure you've provided a token with appropriate permissions
    
    ### Need More Help?
    
    If you encounter issues not covered here, please check the GitHub repository for this app or open an issue.
    """)

if __name__ == "__main__":
    main()
