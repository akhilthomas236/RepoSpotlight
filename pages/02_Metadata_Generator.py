import streamlit as st
import json

def main():
    st.set_page_config(
        page_title="RepoSpotlight - Metadata Generator",
        page_icon="🛠️",
        layout="wide"
    )
    
    st.title("Metadata Generator")
    
    st.markdown("""
    Use this tool to generate custom metadata for your GitHub project. 
    This metadata will enhance how your project is displayed in the showcase.
    
    Fill out the form below and click "Generate JSON" to create your metadata file.
    """)
    
    col1, col2 = st.columns(2)
    
    with col1:
        project_name = st.text_input("Project Name", placeholder="My Awesome Project")
        tagline = st.text_input("Tagline", placeholder="A short catchy description")
        showcase_image = st.text_input("Showcase Image URL", placeholder="https://example.com/image.jpg")
        demo_url = st.text_input("Demo URL", placeholder="https://example.com/demo")
        documentation_url = st.text_input("Documentation URL", placeholder="https://example.com/docs")
        
        features = st.text_area(
            "Features (one per line)", 
            placeholder="Feature 1\nFeature 2\nFeature 3"
        )
        
        tech_stack = st.text_area(
            "Tech Stack (one per line)", 
            placeholder="Technology 1\nTechnology 2\nTechnology 3"
        )
    
    with col2:
        st.subheader("Contact Information")
        email = st.text_input("Email", placeholder="contact@example.com")
        twitter = st.text_input("Twitter Handle", placeholder="your_twitter")
        linkedin = st.text_input("LinkedIn Profile", placeholder="your_linkedin")
        
        st.subheader("Contributors")
        st.markdown("Add at least one contributor (yourself)")
        
        contributors = []
        
        for i in range(3):  # Allow up to 3 contributors in the form
            st.markdown(f"### Contributor {i+1}")
            name = st.text_input(f"Name {i+1}", key=f"name_{i}")
            github = st.text_input(f"GitHub Username {i+1}", key=f"github_{i}")
            role = st.text_input(f"Role {i+1}", key=f"role_{i}")
            
            if name and github and role:
                contributors.append({
                    "name": name,
                    "github": github,
                    "role": role
                })
    
    if st.button("Generate JSON"):
        # Parse features and tech stack from text areas
        features_list = [f.strip() for f in features.split("\n") if f.strip()]
        tech_stack_list = [t.strip() for t in tech_stack.split("\n") if t.strip()]
        
        # Create metadata object
        metadata = {
            "project_name": project_name,
            "tagline": tagline,
            "showcase_image": showcase_image,
            "demo_url": demo_url,
            "documentation_url": documentation_url,
            "features": features_list,
            "tech_stack": tech_stack_list,
            "contact": {
                "email": email,
                "twitter": twitter,
                "linkedin": linkedin
            },
            "contributors": contributors
        }
        
        # Display the generated JSON
        st.subheader("Generated Metadata")
        st.json(metadata)
        
        st.markdown("""
        ### How to Use This Metadata
        
        1. Copy the JSON above
        2. Create a file named `project_metadata.json` in the `.github` folder of your repository
        3. Paste the JSON into this file and commit to your repository
        
        Now when you view your repository in the GitHub Project Showcase app, it will use this enhanced metadata!
        """)

if __name__ == "__main__":
    main()
