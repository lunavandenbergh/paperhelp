import html
import streamlit	as st
import re
from src.text_corrections import highlight_text_arguments, highlight_text_corrections

def ignore_correction(start, end):
    st.session_state["ignored_corrections"].append((start, end))

def display_feedback():
    
    feedback_type = st.session_state["feedback_type"]

    if feedback_type == "General":
        st.write(f"<div class='item-general'>{st.session_state['general_feedback']}</div>", unsafe_allow_html=True)

    if feedback_type == "Arguments":
        arguments_container = st.container(height=868, border=False, key="arguments_container")
        arguments = st.session_state["arguments"]
        for argument in arguments["arguments"]:
            long_argument = argument['context']
            arguments_container.write(
                f"""
                <div class='item-argumentation'>
                    <div class='expandable-text'>Full argument: <b>{long_argument}</b></div>
                    <div class='arg-part'><i>Claim:</i> {argument['parts']['claim']}<br><br>
                    <i>Evidence:</i> {argument['parts']['evidence']}</div> 
                    <div class='arg-part'><i>Counterargument:</i> {argument['parts']['counterargument']}</div> 
                    <div class='arg-part'><i>Feedback:</i> {argument['feedback']}<br><br>
                    <i>Actionable feedback:</i> {argument['actionable_feedback']}</div>
                </div>
                """, unsafe_allow_html=True)

    if feedback_type == "Corrections":
        corrections_llm = st.session_state["corrections_llm"]
        corrections_container = st.container(height=868, border=False)
        with corrections_container:
            for correction in corrections_llm:
                if correction["type"] == "spelling":
                    st.write(f"<div class='item-spelling' title='{html.escape(correction['suggestion'])}'>{correction['error']} → <span style='color: red'><b>{correction['suggestion']}</b></span><br><small>Spelling mistake</small></div>",	unsafe_allow_html=True)
                    continue
                if correction["type"] == "grammar":
                    st.write(f"<div class='item-grammar' title='{html.escape(correction['suggestion'])}'>{correction['error']} → <span style='color: blue'><b>{correction['suggestion']}</b></span><br><small>Grammar mistake</small></div>",	unsafe_allow_html=True)
                    continue
                if correction["type"] == "style":
                    st.write(f"<div class='item-style' title='{html.escape(correction['suggestion'])}'>{correction['error']} → <span style='color: green'><b>{correction['suggestion']}</b></span><br><small>Style suggestion</small></div>",	unsafe_allow_html=True)
                    continue
                else:
                    st.write(f"<div class='item-other' title='{html.escape(correction['suggestion'])}'>{correction['error']} → <span style='color: purple'><b>{correction['suggestion']}</b></span><br><small>Other</small></div>",	unsafe_allow_html=True)
            
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
        normalized_text = text.replace("\n", " ")
        for arg in all_arguments:
            start = normalized_text.find(arg)
            if start != -1:
                corrections.append({
                    "error": arg,
                    "suggestion": ["Correction"],
                    "offset": start,
                    "length": len(arg),
                    "type": "argument"
                })
        highlighted_text = highlight_text_arguments(st.session_state["text"], corrections)
        st.markdown(highlighted_text, unsafe_allow_html=True)
    elif feedback_type == "Corrections":
        corrections = st.session_state["corrections_llm"]
        highlighted_text = highlight_text_corrections(st.session_state["text"], corrections)
        st.markdown(highlighted_text, unsafe_allow_html=True)
    else:
        st.markdown(st.session_state["text"], unsafe_allow_html=True)
        
def display_message(text,citations):
    updated_text = text
    if bool(re.search(r"\[\d+\]", text)):
        citations_in_text = re.findall(r"\[\d+\]", text)
        for citation in citations_in_text:
            number = citation[1]
            citation_from_list = citations.urls[int(number)-1].url
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
        for citation_url in citations.urls:
            st.write(f"[{i}] {citation_url.url}")
            i += 1