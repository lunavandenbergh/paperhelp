import time
from openai import OpenAI
import streamlit as st
from agno.models.perplexity import Perplexity
from agno.tools.arxiv import ArxivTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.agent import Agent
from textwrap import dedent
from agno.knowledge.pdf import PDFKnowledgeBase, PDFReader
from agno.models.openai import OpenAIChat
from agno.team.team import Team

tic_overall = time.time()
print(f"Starting the app... It's now {time.localtime().tm_hour}:{time.localtime().tm_min}:{time.localtime().tm_sec}")

st.set_page_config(
    page_title="Scientific Writing: Feedback Tool", 
    page_icon="📄",
    initial_sidebar_state="collapsed",
    layout="wide")

st.markdown('<style>' + open('assets/style.css').read() + '</style>', unsafe_allow_html=True)

st.title("Scientific Writing Feedback Tool")

from src.display_text import display_citations, display_feedback, display_message, display_text
from agno.vectordb.lancedb import LanceDb
from agno.vectordb.search import SearchType

if "feedback_type" not in st.session_state:
    st.session_state["feedback_type"] = "General"

if "corrections_llm" not in st.session_state:
    tic = time.time()
    from src.text_corrections import get_corrections_llm
    get_corrections_llm()
    toc = time.time()
    print(f"Text correction (llm) took {toc - tic:.2f} seconds")

if "agent_openai"	not in st.session_state:
    tic = time.time()

    knowledge_base = PDFKnowledgeBase(
        path = f"./uploads/{st.session_state['pdf_path']}",
        vector_db=LanceDb(
        table_name="pdfs",
        uri="/tmp/lancedb",
        search_type=SearchType.keyword,
        ),
    )
    knowledge_base.load()
    researcher = Agent(
        model=OpenAIChat(id="gpt-4o",api_key=st.secrets["OPENAI_API_KEY"]),
        tools=[DuckDuckGoTools(), ArxivTools()],
        user_id="user",
        knowledge=knowledge_base,
        show_tool_calls=True,
        debug_mode=True,
        description=dedent("""\
            You are an academic assistant that provides feedback on research papers. 
            The user has uploaded a draft, which is stored in your knowledge base.

            You also can be asked to generate new text or provide scientific papers on a certain topic. 
                       
            Always search your knowledge base before answering questions. 
            You may reference uploaded documents directly even if they don't include formal citations.
            If relevant information exists, include it in your response. 
            If no relevant data is found, politely ask the user for clarification.
                       
            Always cite your sources. Preferably, these sources are scientific papers or books.
            Add citations at the end of your response.\
            """),
        instructions=[
            "Given a question, first check if the knowledge base (with the paper draft) contains relevant information.",
            "If it does, use that information to answer the question.",
            "Use the tools to search for information concerning literature."
            "Always provide scientific citations.",],
        markdown=True,
    )
    researcher.knowledge.load()  # Ensure data is properly loaded
    
    st.session_state["agent_openai"] = researcher
    

    toc = time.time()
    print(f"Initializing agent took {toc - tic:.2f} seconds")

if "agent_perplexity" not in st.session_state:
    tic = time.time()
    pdf_path = st.session_state["pdf_path"]
    client = Agent(
        model=Perplexity(id="sonar",api_key=st.secrets["PERPLEXITY_API_KEY"]),
        user_id="user",
        show_tool_calls=True,
        debug_mode=True,
        description=dedent("""\
            You are an academic assistant that provides feedback on research papers. 
            You will receive a user prompt an another assistant's response.
            It is your task to enhance the response by:
            - Providing citations for the response.
            - Adding relevant information if needed.
            Make sure that your ouput is as if you're the original assistant.
            Always cite your sources. Preferably, these sources are scientific papers or books.\
            """),
        markdown=True,
    )
    st.session_state["agent_perplexity"] = client
    toc = time.time()
    print(f"Initializing assistant took {toc - tic:.2f} seconds")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome! How can I help you? You can ask me anything about the paper you provided or relevant literature.", "citations": None}]

if "arguments" not in st.session_state or not isinstance(st.session_state["arguments"], dict):
    tic = time.time()
    from src.find_arguments import	generate_arguments
    generate_arguments()
    toc = time.time()
    print(f"Argument generation took {toc - tic:.2f} seconds")

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
                        agent = st.session_state["agent_openai"]
                        response = agent.run(prompt)
                        client_ppx = st.session_state["agent_perplexity"]
                        improved_response = client_ppx.run(f"User query: {prompt}\n\nAssistant response: {response.content}")
                        message = display_message(improved_response.content, improved_response.citations)
                        
                st.session_state.messages.append({"role": "assistant", "content": message, "citations": response.citations})
    
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
