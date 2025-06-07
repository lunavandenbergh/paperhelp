"""
App.py

Main entry point for the paper feedback application.
Allows users to upload a PDF of their scientific paper draft,
extracts the text, and prepares it for AI-generated feedback.

Features:
- PDF upload and text extraction
- Session state management
- File cleanup on startup
"""

import shutil
import streamlit as st
import os
import time

st.set_page_config(page_title="Upload your PDF!", 
                   page_icon="📄",
                   initial_sidebar_state="collapsed",
                   layout="centered"
                   )

with open( "assets/style.css" ) as css:
    st.markdown( f'<style>{css.read()}</style>' , unsafe_allow_html= True)

st.title("Paper Feedback Tool")
explanation = st.container(key="explanation")
with explanation:
    st.markdown("**Welcome!** This tool provides **AI-generated feedback** on your **scientific paper draft**, helping you refine your writing with a focus on **argument feedback**.")
    st.divider()
    st.markdown("**Upload your PDF file** below to begin. Your document will be processed, and you'll receive feedback in just a few moments. *Note:* The tool is optimized for short drafts. Generating your feedback might take longer for larger documents.")
    st.markdown("**Need help?** You can chat with the **feedback assistant** at any time for clarification or further research suggestions.")

    uploaded_file = st.file_uploader("Upload your paper in PDF format here:", type="pdf", key="file_uploader_text")

def initialize_app():
    """
    Cleans up the 'uploads' directory by removing all files and subdirectories.
    This ensures a fresh state each time the app is started.
    """
    for filename in os.listdir("uploads"):
        file_path = os.path.join("uploads", filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print(f'Failed to delete {file_path}. Reason: {e}')

if "files_initialized" not in st.session_state:
    initialize_app()                        
    st.session_state["files_initialized"] = True

if uploaded_file is not None:
    # Save uploaded PDF to 'uploads' directory
    save_path = os.path.join("uploads", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    import pymupdf  # Used for PDF text extraction

    # Extract text from PDF and save to output.txt
    doc = pymupdf.open(save_path)
    out = open("output.txt", "wb")
    for page in doc:
        text = page.get_text().encode("utf8")
        out.write(text)
    out.close()
    file_path = 'output.txt'
    with open(file_path, 'r', encoding="utf8") as file:
        lines = file.readlines()
        file_content = '\n'.join(lines)
    
    # Store extracted text and file info in session state
    st.session_state["text"] = file_content
    st.session_state["pdf_path"] = uploaded_file.name
    st.session_state["dry_run"] = False
    
    # Switch to feedback page after processing
    print(f"Going to the next page... It's now {time.localtime().tm_hour}:{time.localtime().tm_min}:{time.localtime().tm_sec}")
    st.switch_page("pages/Feedback.py")
