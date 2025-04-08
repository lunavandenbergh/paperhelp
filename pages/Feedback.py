import time
from openai import OpenAI
import streamlit as st

tic_overall = time.time()
print(f"Starting the app... It's now {time.localtime().tm_hour}:{time.localtime().tm_min}:{time.localtime().tm_sec}")

st.set_page_config(
    page_title="Scientific Writing: Feedback Tool", 
    page_icon="📄",
    initial_sidebar_state="collapsed",
    layout="wide")

st.markdown('<style>' + open('assets/style.css').read() + '</style>', unsafe_allow_html=True)

st.title("Scientific Writing Feedback Tool")

from src.generate_response import generate_response
from src.display_text import display_citations, display_feedback, display_message, display_text
import chromadb

if "feedback_type" not in st.session_state:
    st.session_state["feedback_type"] = "General"

if "corrections_llm" not in st.session_state:
    tic = time.time()
    from src.text_corrections import get_corrections_llm
    get_corrections_llm()
    toc = time.time()
    print(f"Text correction (llm) took {toc - tic:.2f} seconds")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    st.session_state["openai_client"] = openai_client
    chroma_client = chromadb.PersistentClient()
    st.session_state["chroma_client"] = chroma_client

if "agent" not in st.session_state:
    tic = time.time()
    pdf_path = st.session_state["pdf_path"]
    client = OpenAI(api_key=st.secrets["PERPLEXITY_API_KEY"], 
                    base_url="https://api.perplexity.ai")
    st.session_state["agent"] = client
    toc = time.time()
    print(f"Initializing assistant took {toc - tic:.2f} seconds")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome! How can I help you? You can ask me anything about the paper you provided or anything else.", "citations": None}]

if "arguments" not in st.session_state or not isinstance(st.session_state["arguments"], dict):
    tic = time.time()
    from src.find_arguments import	generate_arguments
    generate_arguments()
    toc = time.time()
    print(f"Argument generation took {toc - tic:.2f} seconds")

if "processpdf" not in st.session_state or st.session_state["processpdf"] == False:
    tic = time.time()
    pdf_path = st.session_state.get("pdf_path", None)
    
    from src.process_pdf import create_embeddings, split_text, store_embeddings

    pdf_text = st.session_state["text"]
    chunks = split_text(pdf_text)

    embeddings = create_embeddings(chunks)

    st.session_state["processpdf"] = True

    pdf_name = pdf_path.replace(" ","")
    pdf_name	= pdf_name.replace("/","")
    cleaned = ''.join(filter(str.isalnum, pdf_path))[1:17]
    chroma_client = st.session_state["chroma_client"]
    collection = chroma_client.get_or_create_collection(name="paper")
    st.session_state["collection"] = collection
    store_embeddings(collection, chunks, embeddings, cleaned)

    toc = time.time()
    print(f"PDF processing + saving embeddings took {toc - tic:.2f} seconds")

if "ignored_corrections" not in st.session_state:
    st.session_state["ignored_corrections"] = []

left_col, right_col = st.columns(spec=[7,4],border=True)

with left_col:
    st.subheader("Your Paper")
    text_container = st.container(height=500,border=True, key="text_container")
    with text_container:
        display_text()
    
    chat_container = st.container(height=400, border=True, key="chat_container")
    with chat_container:
        chat = st.container(height=310, border=False)
        with chat:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.write(message["content"], unsafe_allow_html=True) 
                    if message["role"] == "assistant" and message["citations"] is not None:
                        display_citations(message["citations"])
        if prompt := st.chat_input("Ask me about your pdf!"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat:
                with st.chat_message("user"):
                    st.write(prompt)
                with st.chat_message("assistant"):
                    with st.spinner("Thinking of a response..."):
                        assistant = st.session_state["agent"]
                        output = generate_response(prompt, st.session_state["collection"], st.session_state["agent"])
                        #output = {
                        #    "response": "Example response [1]. Another sentence [3].",
                        #    "citations": ["Author1 et al. (2022). Paper title. Journal, 1(1), 1-10.", "Author2 et al. (2022). Another paper title. Journal, 1(1), 1-10.", "Author3 et al. (2022). Yet another paper title. Journal, 1(1), 1-10."]
                        #}
                        message = display_message(output["response"],output["citations"])
                        
                st.session_state.messages.append({"role": "assistant", "content": message, "citations": output["citations"]})
    
with right_col:
    st.subheader("Feedback")

    col_but1, col_but2, col_but3 = st.columns([1,1,1], vertical_alignment="center")
    with col_but1:
        if st.button("General", key="general", type="secondary"):
            st.session_state["feedback_type"] = "General"
            st.rerun()
    with col_but2:
        if st.button("Arguments", key="args", type="secondary"):
            st.session_state["feedback_type"] = "Arguments"
            st.rerun()
    with col_but3:
        if st.button("Corrections", key="correct", type="secondary"):
            st.session_state["feedback_type"] = "Corrections"
            st.rerun()
            
    display_feedback()

toc_overall = time.time()
print(f"Overall execution time: {toc_overall - tic_overall:.2f} seconds")
