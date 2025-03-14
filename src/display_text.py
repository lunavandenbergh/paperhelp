import html
import streamlit	as st

from src.text_corrections import highlight_text


def ignore_correction(start, end):
    st.session_state["ignored_corrections"].append((start, end))

def display_feedback():
    
    feedback_type = st.session_state["feedback_type"]

    if feedback_type == "General":
        st.write("General feedback")

    if feedback_type == "Arguments":
        arguments_container = st.container(height=600, border=False)
        arguments = st.session_state["arguments"]
        for argument in arguments["arguments"]:
            arguments_container.write(f"**{argument['context']}**")
            arguments_container.markdown(f"- **Claim**: {argument['parts']['claim']}")
            arguments_container.markdown(f"- **Evidence**: {argument['parts']['evidence']}")
            arguments_container.markdown(f"- **Counterargument**: {argument['parts']['counterargument']}")
            arguments_container.markdown(f"- **Feedback**: {argument['feedback']}")
            arguments_container.markdown(f"- **Actionable feedback**: {argument['actionable_feedback']}")
            arguments_container.divider()

    if feedback_type == "Corrections":
        corrections = st.session_state["corrections"]
        corrections_container = st.container(height=600, border=False)
        with corrections_container:
            for correction in corrections:
                start = correction["offset"]
                end = start + correction["length"]
                if (start, end) in st.session_state["ignored_corrections"]:
                    continue
                error_word = st.session_state["text"][start:end]
                suggestion = ", ".join(correction["suggestion"])
                if correction["type"] == "misspelling":
                    col1, col2 = st.columns([4, 1], vertical_alignment="center")
                    col1.markdown(f"<span style='border: 3px solid red;' title='{html.escape(suggestion)}'>{error_word}</span> - **Spelling mistake**", unsafe_allow_html=True)
                    if col2.button("X", key=f"ignore_{start}_{end}",type="tertiary"):
                        ignore_correction(start, end)
                        st.rerun()
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