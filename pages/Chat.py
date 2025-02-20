import streamlit as st
from sentence_transformers import SentenceTransformer	
from together import Together
import chromadb
# TODO add license(s)
from streamlit_pdf_viewer import pdf_viewer
from generate_response import generate_response
from process_pdf import create_embeddings, extract_text_from_pdf, split_text, store_embeddings

st.set_page_config(
    page_title="Chat with your PDF!", 
    page_icon="📄",
    initial_sidebar_state="expanded",
    layout="wide")

st.title("Chat with your PDF!")

client = Together(api_key=st.secrets["TOGETHER_API_KEY"])
chroma_client = chromadb.PersistentClient()

# Input pdf field
pdf_path = st.session_state.get("pdf_path", None)
pdf_text = extract_text_from_pdf(pdf_path)
chunks = split_text(pdf_text)

with st.sidebar:
    st.title("Take a look at your PDF here:")
    pdf_viewer(pdf_path)

model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
embeddings = []
embeddings = create_embeddings(chunks)

# Chromadb: get/create a collection and store embeddings in it
pdf_name = pdf_path.replace(" ","")
cleaned = ''.join(filter(str.isalnum, pdf_path))
cleaned = cleaned[7:17]
collection = chroma_client.get_or_create_collection(name=cleaned)
store_embeddings(collection, chunks, embeddings, cleaned)

# Set a default model
if "togetherai_model" not in st.session_state:
    st.session_state["togetherai_model"] = "mistralai/Mixtral-8x7B-Instruct-v0.1"

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = []
    st.session_state.messages.append({"role": "assistant", "content": "Welcome! How can I help you? You can ask me anything about the PDF you provided or anything else."})

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        
# Accept user input
if prompt := st.chat_input("Ask me about your pdf!"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.write(prompt)

    
    with st.chat_message("assistant"):
        with st.spinner("Thinking of a response..."):
            response = generate_response(prompt,model,collection, client)
        
        st.write(response)
    st.session_state.messages.append({"role": "assistant", "content": response})
