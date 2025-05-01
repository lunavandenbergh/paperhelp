import time
import streamlit as st
from agno.agent import Agent
from textwrap import dedent
from agno.models.perplexity import Perplexity
from src.display_text import display_citations, display_feedback, display_message, display_text
from src.find_arguments import	generate_arguments

tic_overall = time.time()
print(f"Starting the app... It's now {time.localtime().tm_hour}:{time.localtime().tm_min}:{time.localtime().tm_sec}")

st.set_page_config(
    page_title="Paper Feedback Tool", 
    page_icon="📄",
    initial_sidebar_state="auto",
    layout="wide")

st.markdown('<style>' + open('assets/style.css').read() + '</style>', unsafe_allow_html=True)

st.title("Paper Feedback Tool")

@st.dialog("Your paper feedback is ready!")
def instructions():
				st.write("")
				st.write("On the left, you can see your paper draft, and on the right, you can choose between three types of feedback:")
				st.write("1. **General**: General feedback on your paper draft.")
				st.write("2. **Arguments**: Feedback on the different arguments in your paper draft. You will find a list of arguments present in your paper draft, and for each argument, you will receive feedback seperately.")
				st.write("3. **Corrections**: Corrections for spelling, grammar, and style in your paper draft.")
				st.write("A **feedback assistant** is available in the sidebar. You can ask it anything about your paper draft or relevant literature.")

if st.session_state["dry_run"] == True:
				st.session_state["feedback_type"] = "General"
				st.session_state["arguments"] = {"arguments": [{"context" : "This is context.",
                                                    "parts" : {"claim" : "This is claim.", "evidence" : "This is evidence."},
																																																				"counterargument" : "This is counterargument.",
																																																				"feedback" : "This is feedback.",
																																																				"actionable_feedback" : "This is actionable feedback."}]}
				st.session_state["general_feedback"] = "This is general feedback."
				st.session_state["corrections_llm"] = []

if "feedback_type" not in st.session_state:
    st.session_state["feedback_type"] = "General"

if st.session_state["feedback_type"] == "General":
    st.markdown('''<style>
        .st-key-general button {
	       color: grey;
        border: 1px solid grey;
        }</style>''', unsafe_allow_html=True)
if st.session_state["feedback_type"] == "Arguments":
				st.markdown('''<style>
        .st-key-args button {
	       color: grey;
        border: 1px solid grey;
        }</style>''', unsafe_allow_html=True)
if st.session_state["feedback_type"] == "Corrections":
				st.markdown('''<style>
        .st-key-correct button {
	       color: grey;
        border: 1px solid grey;
        }</style>''', unsafe_allow_html=True)

if "agent"	not in st.session_state:
    tic = time.time()

    researcher = Agent(
        model=Perplexity(id="sonar-pro",api_key=st.secrets["PERPLEXITY_API_KEY"]),
        debug_mode=True,
        description=dedent(f"""\
            You are an academic assistant that provides feedback on research paper drafts. 
            The user has uploaded a draft, which is at the end of this description.
												This can be a scientific paper, a thesis, or any other type of research-related document.
												It is important to note that it can also be part of a larger document. 
												Please keep this in mind when providing feedback.
            You can be asked by the system to provide feedback on the paper,
												but you can also be asked anything else by the user.

            You also can be asked to generate new text or provide scientific papers on a certain topic. 
                       
            Always search your knowledge base before answering questions. 
            You may reference uploaded documents directly even if they don't include formal citations.
            If relevant information exists, include it in your response. 
            If no relevant data is found, politely ask the user for clarification.
                       
            Always cite your sources in a scientific style. Preferably, these sources are scientific papers.
            In your text, use square brackets to indicate the citations, e.g. [1].
                           
            What follows is the user's uploaded paper draft:
            {st.session_state["text"]}\
            """),
        instructions=[
            "When asked a question about the user's paper, first search your memory.",
            "When asked about existing literature, provide scientific papers from reliable sources.",
            "Always provide scientific citations.",
												"Make sure not to go over 1024 tokens in your response.",],
        markdown=True,
    )
    
    st.session_state["agent"] = researcher
    toc = time.time()
    print(f"Initializing agent took {toc - tic:.2f} seconds")

if "general_feedback" not in st.session_state:
    agent = st.session_state["agent"]
    query = f"Given the user's paper draft text, provide general feedback on it, no longer than 150 words. Don't cite anything."
    general_feedback = agent.run(query)
    st.session_state["general_feedback"] = general_feedback.content

if "corrections_llm" not in st.session_state:
    tic = time.time()
    from src.text_corrections import get_corrections_llm
    get_corrections_llm()
    toc = time.time()
    print(f"Text correction (llm) took {toc - tic:.2f} seconds")

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome! How can I help you? You can ask me anything about the paper you provided or relevant literature.", "citations": None}]

if "arguments" not in st.session_state:
    tic = time.time()
    generate_arguments()
    toc = time.time()
    print(f"Argument generation took {toc - tic:.2f} seconds")

left_col, right_col = st.columns(spec=[8,5],border=True)

with left_col:
    st.subheader("Your Paper")
    text_container = st.container(height=655,border=False, key="text_container")
    with text_container:
        display_text()

with st.sidebar:
    st.header("Feedback Assistant")
    chat_container = st.container(height=610, border=False, key="chat_container")
    with chat_container:
        chat = st.container(height=520, border=False)
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
                        agent = st.session_state["agent"]
                        response = agent.run(prompt)
                        st.session_state["test_citations"] = response.citations
                        message = display_message(response.content, response.citations)
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

if "instructions_done" not in st.session_state:
    instructions()
    st.session_state["instructions_done"] = True

toc_overall = time.time()
print(f"Overall execution time: {toc_overall - tic_overall:.2f} seconds")
    