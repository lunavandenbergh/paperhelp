import shutil
import streamlit as st
import os
import time

st.set_page_config(page_title="Upload your PDF!", 
                   page_icon="📄")

with open( "src/style.css" ) as css:
    st.markdown( f'<style>{css.read()}</style>' , unsafe_allow_html= True)
    
st.title("Welcome!")
st.write("Upload a PDF to process it.")

def initialize_app():
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

uploaded_file = st.file_uploader("Upload your PDF here", type="pdf")

if uploaded_file is not None:
    save_path = os.path.join("uploads", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    import re
    import pymupdf4llm

    text = pymupdf4llm.to_markdown(save_path)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text) # Remove newlines within paragraphs
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text) # Join hyphenated words
    st.session_state["text"] = text
    st.session_state["pdf_path"] = uploaded_file.name  

    print(f"Going to the next page... It's now {time.localtime().tm_hour}:{time.localtime().tm_min}:{time.localtime().tm_sec}")
    st.switch_page("pages/Feedback.py")
    