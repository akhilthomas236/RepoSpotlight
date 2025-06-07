<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# GitHub Project Showcase App

This is a Streamlit application that showcases GitHub projects. It reads README files and custom metadata from repositories to build a comprehensive project showcase page.

## Code Structure

- `app.py`: Main Streamlit application that handles the UI and GitHub API interactions
- `example_metadata.json`: Example metadata file showing the expected format for custom repository metadata

## Development Guidelines

- When extending the app, maintain the clean separation between UI components and data processing functions
- Use type hints for function parameters and return values
- Follow the existing error handling patterns
- Add appropriate docstrings for new functions
- Test with both public and private GitHub repositories
- Ensure the UI is responsive and works well on different screen sizes
