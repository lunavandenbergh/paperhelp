import html
import re
import streamlit	as st
from src.text_corrections import highlight_text_arguments, highlight_text_corrections
from src.find_arguments import generate_papers

def ignore_correction(start, end):
    st.session_state["ignored_corrections"].append((start, end))

def display_feedback():
    
    feedback_type = st.session_state["feedback_type"]

    if feedback_type == "General":
        st.markdown(f"<div class='item-general'>{st.session_state['general_feedback']}</div>", unsafe_allow_html=True)

    if feedback_type == "Arguments":
        arguments_container = st.container(height=868, border=False, key="arguments_container")
        arguments = st.session_state["arguments"]
        i = 0
        for argument in arguments["arguments"]:
            long_argument = argument['context']
            if st.session_state["updated_arguments"][i] == False:
                with arguments_container:
                    argument_container = st.container(border=True)
                    with argument_container:
                        st.markdown(f"Full argument: **{long_argument}**")
                        parts_argument_container = st.container(border=True)
                        with parts_argument_container:
                            st.markdown(f"Claim: {argument['parts']['claim']}")
                            st.markdown(f"Evidence: {argument['parts']['evidence']}")
                        improvements_container = st.container(border=True)
                        with improvements_container:
                            st.markdown(f"What is wrong with this argument? {argument['feedback']}")
                            st.markdown(f"How to improve this argument? {argument['actionable_feedback']}")
                        relevant_literature_container = st.container(border=True)
                        with relevant_literature_container:
                            st.markdown(f"Relevant literature: **... Loading ...**")
                            button_key = f"literature_button_{i}"
                            literature_button = st.button("Load relevant literature", key=button_key, help="Load relevant literature for this argument. Might take a while.")
                            if literature_button:
                                generate_papers(i)
            elif st.session_state["updated_arguments"][i] == True:
                with arguments_container:
                    argument_container = st.container(border=True, key=f"argument_container_{i}")
                    with argument_container:
                        st.markdown(f"Full argument: **{long_argument}**")
                        parts_argument_container = st.container(border=True)
                        with parts_argument_container:
                            st.markdown(f"Claim: {argument['parts']['claim']}")
                            st.markdown(f"Evidence: {argument['parts']['evidence']}")
                        improvements_container = st.container(border=True)
                        with improvements_container:
                            st.markdown(f"What is wrong with this argument? {argument['feedback']}")
                            st.markdown(f"How to improve this argument? {argument['actionable_feedback']}")
                        relevant_literature_container = st.container(border=True)
                        with relevant_literature_container:
                            st.markdown(f"Relevant literature")
                            st.markdown(f"{argument['counterargument']['general']}")
                            for paper in argument['counterargument']['papers']:
                                st.markdown(f"[{paper['title']}]({paper['url']}) by {paper['authors']} ({paper['year']})")
                                st.markdown(f"- URL: {paper['url']}")
                                st.markdown(f"- Abstract: {paper['abstract']}")
            i = i + 1

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
            citation_from_list = citations["urls"][int(number)-1]["url"]
            updated_text = updated_text.replace(citation, 
            # TODO link ipv span title
                f"<span title='{citation_from_list}' style='border-bottom: 1px dashed blue;'>{citation}</span>")
        st.write(updated_text, unsafe_allow_html=True)
    else:
        st.write(text)
    display_citations(citations)
    return updated_text
    
def display_citations(citations):
    with st.expander("Sources used for this answer"):
        i = 1
        for citation_url in citations.urls:
            st.write(f"[{i}] {citation_url.url}") # TODO title of paper/website as link
            i += 1