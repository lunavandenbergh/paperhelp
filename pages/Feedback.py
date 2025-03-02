from concurrent.futures import ThreadPoolExecutor
import json
import time
from openai import OpenAI
import pymupdf4llm
import streamlit as st
import language_tool_python
import re
from src.find_arguments import	generate_arguments
from src.process_pdf import extract_text_from_pdf
from src.text_corrections import get_corrections, highlight_text
import chromadb
from src.generate_response import generate_response
from src.process_pdf import create_embeddings, extract_text_from_pdf, split_text, store_embeddings

st.set_page_config(
    page_title="Scientific Writing: Feedback Tool", 
    page_icon="📄",
    initial_sidebar_state="collapsed",
    layout="wide")

tic_overall = time.time()

with open( "src/style.css" ) as css:
    st.markdown( f'<style>{css.read()}</style>' , unsafe_allow_html= True)

if "feedback_type" not in st.session_state:
    st.session_state["feedback_type"] = "Arguments"

if "text" not in st.session_state:
    tic = time.time()
    pdf_path = st.session_state.get("pdf_path", None)
    pdf_path = pdf_path.split('uploads\\', 1)[-1]
    new_pdf_path = f"files/{pdf_path}"
    text = pymupdf4llm.to_markdown(new_pdf_path)
    text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text) # Remove newlines within paragraphs
    text = re.sub(r'(\w+)-\s+(\w+)', r'\1\2', text) # Join hyphenated words
    st.session_state["text"] = text
    toc = time.time()
    print(f"Text extraction took {toc - tic:.2f} seconds")

if "corrections" not in st.session_state:
    tic = time.time()
    if "language_tool" not in st.session_state:
        st.session_state["language_tool"] = language_tool_python.LanguageTool('en-US')
    tool = st.session_state["language_tool"]
    st.session_state["corrections"] = get_corrections(tool, st.session_state["text"])
    toc = time.time()
    print(f"Text correction took {toc - tic:.2f} seconds")

if "openai_model" not in st.session_state:
    st.session_state["openai_model"] = "gpt-4o-mini"
    openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    st.session_state["openai_client"] = openai_client
    chroma_client = chromadb.PersistentClient()
    st.session_state["chroma_client"] = chroma_client

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome! How can I help you? You can ask me anything about the paper you provided or anything else."}]

if "arguments" not in st.session_state:
    tic = time.time()
    arguments = generate_arguments(False, st.session_state["openai_client"])
    st.session_state["arguments"] = eval(arguments)
    toc = time.time()
    print(f"Argument generation took {toc - tic:.2f} seconds")

if "processpdf" not in st.session_state or st.session_state["processpdf"] == False:
    tic = time.time()
    pdf_path = st.session_state.get("pdf_path", None)
    pdf_text = extract_text_from_pdf(pdf_path)
    chunks = split_text(pdf_text)

    with ThreadPoolExecutor() as executor:
        embeddings_future = executor.submit(create_embeddings, chunks)
        embeddings = embeddings_future.result()

    st.session_state["processpdf"] = True

    pdf_name = pdf_path.replace(" ","")
    cleaned = ''.join(filter(str.isalnum, pdf_path))[7:17]
    chroma_client = st.session_state["chroma_client"]
    collection = chroma_client.get_or_create_collection(name=cleaned)
    st.session_state["collection"] = collection
    store_embeddings(collection, chunks, embeddings, cleaned)

    toc = time.time()
    print(f"PDF processing + saving embeddings took {toc - tic:.2f} seconds")

st.title("Scientific Writing Feedback Tool")

left_col, right_col = st.columns(spec=[2,1],border=True)
with left_col:
    text_container = st.container(height=400)
    with text_container:
        corrections = st.session_state["corrections"]
        highlighted_text = highlight_text(st.session_state["text"], corrections)
        st.markdown(highlighted_text, unsafe_allow_html=True)
    
    chat = st.container(height=300)
    with chat:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.write(message["content"])
    if prompt := st.chat_input("Ask me about your pdf!"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with chat:
            with st.chat_message("user"):
                st.write(prompt)
            with st.chat_message("assistant"):
                with st.spinner("Thinking of a response..."):
                    response = generate_response(prompt, st.session_state["collection"], st.session_state["openai_client"])
                    
                    def stream_response():
                        for word in response.split(" "):
                            yield word + " "
                            time.sleep(0.03)         
                st.write_stream(stream_response())
            st.session_state.messages.append({"role": "assistant", "content": response})
    
with right_col:
    st.header("Feedback")
    tab1, tab2, tab3 = st.tabs(["Arguments","Corrections","Style suggestions"])
    corrections = st.session_state["corrections"]
    feedback_type = st.session_state["feedback_type"]
    with tab1:
        arguments = st.session_state["arguments"]
        for argument in arguments["arguments"]:
            st.write(f"**{argument['context']}**")
            st.markdown(f"- **Claim**: {argument['parts']['claim']}")
            st.markdown(f"- **Evidence**: {argument['parts']['evidence']}")
            st.markdown(f"- **Counterargument**: {argument['parts']['counterargument']}")
            st.markdown(f"- **Feedback**: {argument['feedback']}")
            st.markdown(f"- **Actionable feedback**: {argument['actionable_feedback']}")
            st.divider()
    with tab2:
        for correction in corrections:
            start = correction["offset"]
            end = start + correction["length"]
            error_word = st.session_state["text"][start:end]
            suggestion = ", ".join(correction["suggestion"])
            if correction["type"] == "misspelling":
                st.markdown(f"<span style='border: 3px solid pink;' title='{suggestion}'>{error_word}</span> - **Spelling mistake**", unsafe_allow_html=True)
            elif correction["type"] == "grammar":
                st.markdown(f"<span style='border: 3px solid lightblue;' title='{suggestion}'>{error_word}</span> - **Grammar mistake**", unsafe_allow_html=True)
    with tab3:
        for correction in corrections:
            start = correction["offset"]
            end = start + correction["length"]
            error_word = st.session_state["text"][start:end]
            if correction["type"] == "style":
                st.markdown(f"<span style='border: 3px solid lightgreen;'>{error_word}</span> **Error**: {correction['error']} **Suggestion**: {', '.join(correction['suggestion'])}", unsafe_allow_html=True)

toc_overall = time.time()
print(f"Overall execution time: {toc_overall - tic_overall:.2f} seconds")
