import streamlit as st
import language_tool_python
import re
from src.process_pdf import extract_text_from_pdf
from src.text_corrections import get_corrections, highlight_text

# TODO omdat ik de afgekapte woorden uit de tekst haal en er volledig insteek
# klopt de offset niet meer bij alle fouten
# --> moet nog gefixt worden e.g. offset aanpassen

st.set_page_config(
    page_title="Spelling and grammar checker", 
    page_icon="📄",
    initial_sidebar_state="expanded",
    layout="wide")

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

st.title("Spelling and grammar checker")
left_col, right_col = st.columns(spec=[2,1],border=True)

with left_col:
    st.header("Your text")
    ## ANNOTATIONS ##
    corrections = st.session_state["corrections"]
    st.markdown(highlight_text(st.session_state["text"], corrections), unsafe_allow_html=True)
    
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
                st.markdown(f"- <mark style='background-color: pink;'>{error_word}</mark> **Type**: spelling mistake **Suggestion**: {', '.join(correction['suggestion'])}", unsafe_allow_html=True)
            elif correction["type"] == "grammar":
                st.markdown(f"- <mark style='background-color: lightblue;'>{error_word}</mark> **Type**: grammar mistake **Suggestion**: {', '.join(correction['suggestion'])}", unsafe_allow_html=True)
    with tab3:
        for correction in corrections:
            if correction["type"] == "style":
                st.markdown(f"- **Type**: {correction['type']} **Error**: {correction['error']} **Suggestion**: {', '.join(correction['suggestion'])}")
