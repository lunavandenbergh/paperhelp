import streamlit as st
import language_tool_python
import re
from src.process_pdf import extract_text_from_pdf
from src.text_corrections import get_corrections, highlight_text
from sentence_transformers import SentenceTransformer	
from together import Together
import chromadb
# TODO add license(s)
from src.generate_response import generate_response
from src.process_pdf import create_embeddings, extract_text_from_pdf, split_text, store_embeddings

st.set_page_config(
    page_title="Spelling and grammar checker", 
    page_icon="📄",
    initial_sidebar_state="expanded",
    layout="wide")

client = Together(api_key=st.secrets["TOGETHER_API_KEY"])
chroma_client = chromadb.PersistentClient()

if "feedback_type" not in st.session_state:
    st.session_state["feedback_type"] = "Arguments"

if "text" not in st.session_state:
    pdf_path = st.session_state.get("pdf_path", None)
    text = extract_text_from_pdf("files/test_abstract.pdf")
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text)
    st.session_state["text"] = text

if "corrections" not in st.session_state:
    tool = language_tool_python.LanguageTool('en-US')
    # Join hyphenated words (otherwise they will be treated as separate words and probably incorrect)
    st.session_state["corrections"] = get_corrections(tool, st.session_state["text"])

# Set a default model
if "togetherai_model" not in st.session_state:
    st.session_state["togetherai_model"] = "mistralai/Mixtral-8x7B-Instruct-v0.1"

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Welcome! How can I help you? You can ask me anything about the paper you provided or anything else."})

st.title("Scientific Writing Feedback Tool")

# Input pdf field
pdf_path = st.session_state.get("pdf_path", None)
pdf_text = extract_text_from_pdf(pdf_path)
chunks = split_text(pdf_text)

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
embeddings = []
embeddings = create_embeddings(chunks)

# Chromadb: get/create a collection and store embeddings in it
pdf_name = pdf_path.replace(" ","")
cleaned = ''.join(filter(str.isalnum, pdf_path))
cleaned = cleaned[7:17]
collection = chroma_client.get_or_create_collection(name=cleaned)
store_embeddings(collection, chunks, embeddings, cleaned)

left_col, right_col = st.columns(spec=[2,1],border=True)
with left_col:
    text_container = st.container(height=400)
    with text_container:
        ## ANNOTATIONS ##
        corrections = st.session_state["corrections"]
        st.markdown(highlight_text(st.session_state["text"], corrections), unsafe_allow_html=True)
    
    chat = st.container(height=300)
    with chat:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    # Accept user input
    if prompt := st.chat_input("Ask me about your pdf!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat:
            with st.chat_message("user"):
                st.write(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking of a response..."):
                    response = generate_response(prompt,model,collection, client)
                st.write(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
    
with right_col:
    st.header("Feedback")
    tab1, tab2, tab3 = st.tabs(["Arguments","Corrections","Style suggestions"])
    corrections = st.session_state["corrections"]
    feedback_type = st.session_state["feedback_type"]
    with tab1:
        for correction in corrections:
            if correction["type"] == "Arguments":
            # TODO Display argument feedback
                continue
    with tab2:
        for correction in corrections:
            start = correction["offset"]
            end = start + correction["length"]
            error_word = st.session_state["text"][start:end]
            if correction["type"] == "misspelling":
                st.markdown(f"<mark style='background-color: pink;'>{error_word}</mark> - **Spelling mistake**", unsafe_allow_html=True)
            elif correction["type"] == "grammar":
                st.markdown(f"<mark style='background-color: lightblue;'>{error_word}</mark> - **Grammar mistake**", unsafe_allow_html=True)
    with tab3:
        for correction in corrections:
            start = correction["offset"]
            end = start + correction["length"]
            error_word = st.session_state["text"][start:end]
            if correction["type"] == "style":
                st.markdown(f"<mark style='background-color: lightgreen;'>{error_word}</mark> **Error**: {correction['error']} **Suggestion**: {', '.join(correction['suggestion'])}", unsafe_allow_html=True)
