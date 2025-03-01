import shutil
import streamlit as st
import os

st.set_page_config(page_title="Upload your PDF!", page_icon="📄")

hide_sidebar = """
    <style>
        section[data-testid="stSidebar"] {display: none !important;}
    </style>
"""
st.markdown(hide_sidebar, unsafe_allow_html=True)

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

initialize_app()

uploaded_file = st.file_uploader("Upload your PDF here", type="pdf")

if uploaded_file:
    save_path = os.path.join("uploads", uploaded_file.name)
    with open(save_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.session_state["pdf_path"] = save_path

    st.switch_page("pages/Feedback.py")
