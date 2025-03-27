import html
import streamlit	as st
import re
from src.text_corrections import highlight_text

def ignore_correction(start, end):
    st.session_state["ignored_corrections"].append((start, end))

def display_feedback():
    
    feedback_type = st.session_state["feedback_type"]

    if feedback_type == "General":
        st.write(st.session_state["general_feedback"])

    if feedback_type == "Arguments":
        arguments_container = st.container(height=750, border=False)
        arguments = st.session_state["arguments"]
        for argument in arguments["arguments"]:
            arguments_container.write(f"Argument: **{argument['context']}**")
            arguments_container.markdown(f"- **Claim**: {argument['parts']['claim']}")
            arguments_container.markdown(f"- **Evidence**: {argument['parts']['evidence']}")
            arguments_container.markdown(f"- **Counterargument**: {argument['parts']['counterargument']}")
            arguments_container.markdown(f"- **Feedback**: {argument['feedback']}")
            arguments_container.markdown(f"- **Actionable feedback**: {argument['actionable_feedback']}")
            arguments_container.divider()

    if feedback_type == "Corrections":
        corrections = st.session_state["corrections"]
        corrections_container = st.container(height=750, border=False)
        with corrections_container:
            for correction in corrections:
                start = correction["offset"]
                end = start + correction["length"]
                error_word = st.session_state["text"][start:end]
                suggestion = ", ".join(correction["suggestion"])
                if correction["type"] == "misspelling":
                    col1, col2 = st.columns([4, 1], vertical_alignment="center")
                    col1.markdown(f"<span style='border: 3px solid red;' title='{html.escape(suggestion)}'>{error_word}</span> - **Spelling mistake**", unsafe_allow_html=True)
                elif correction["type"] == "grammar":
                    st.markdown(f"<span style='border: 3px solid blue;' title='{html.escape(suggestion)}'>{error_word}</span> - **Grammar mistake**", unsafe_allow_html=True)
    
    if feedback_type == "Style":
        corrections = st.session_state["corrections"]
        for correction in corrections:
            start = correction["offset"]
            end = start + correction["length"]
            error_word = st.session_state["text"][start:end]
            if correction["type"] == "style":
                st.markdown(f"<span style='border: 3px solid green;'>{error_word}</span> **Error**: {correction['error']} **Suggestion**: {', '.join(correction['suggestion'])}", unsafe_allow_html=True)


def display_text():
    
    feedback_type = st.session_state["feedback_type"]

    if feedback_type == "General":
        st.markdown(st.session_state["text"], unsafe_allow_html=True)
    elif feedback_type == "Arguments":
        arguments = st.session_state["arguments"]
        text = st.session_state["text"]
        all_arguments = []
        for argument in arguments["arguments"]:
            all_arguments.append(argument['context'])
        corrections = []
        for arg in all_arguments:
            start = text.find(arg)
            if start != -1:
                corrections.append({
                    "error": arg,
                    "suggestion": ["Correction"],
                    "offset": start,
                    "length": len(arg),
                    "type": "argument"
                })
        highlighted_text = highlight_text(text, corrections)
        st.markdown(highlighted_text, unsafe_allow_html=True)
    elif feedback_type == "Corrections":
        corrections = st.session_state["corrections"]
        highlighted_text = highlight_text(st.session_state["text"], corrections)
        st.markdown(highlighted_text, unsafe_allow_html=True)
    else:
        st.markdown(st.session_state["text"], unsafe_allow_html=True)
        
def display_message(text,citations):
    updated_text = text
    if bool(re.search(r"\[\d+\]", text)):
        citations_in_text = re.findall(r"\[\d+\]", text)
        for citation in citations_in_text:
            number = citation[1]
            citation_from_list = citations[int(number)-1]
            updated_text = updated_text.replace(citation, 
            # TODO link ipv span title
                f"<span title='{citation_from_list}' style='border-bottom: 1px dashed blue;'>{citation}</span>")
        st.write(updated_text, unsafe_allow_html=True)
    else:
        st.write(text)
    display_citations(citations)
    return updated_text
    
def display_citations(citations):
    with st.expander("See citations"): #of popover
        i = 1
        for citation in citations:
            st.write(f"[{i}] {citation}")
            i += 1