import language_tool_python
import streamlit as st
import time

def get_corrections():
    tic = time.time()
    tool = language_tool_python.LanguageTool('en-US')
    toc	= time.time()
    print(f"Initializing the tool took {toc - tic:.2f} seconds")
    text = st.session_state["text"]
    matches = tool.check(text)
    corrections = []
    
    for match in matches:
        corrections.append({
            "error": match.context,
            "suggestion": match.replacements,
            "offset": match.offset,
            "length": match.errorLength,
            "type": match.ruleIssueType
        })
    
    return corrections

def highlight_text(text, corrections):
    highlighted_text = text
    for correction in sorted(corrections, key=lambda x: x["offset"], reverse=True):
        start = correction["offset"]
        end = start + correction["length"]
        error_text = text[start:end]
        suggestion = ", ".join(correction["suggestion"])
        if correction["type"] == "misspelling":
            highlighted_text = (
                highlighted_text[:start] +
                f'<span style="border: 3px solid pink;" title="{suggestion}">{error_text}</span>' +
                highlighted_text[end:]
            )
        elif correction["type"] == "grammar":
            highlighted_text = (
                highlighted_text[:start] +
                f'<span style="border: 3px solid powderblue;" title="{suggestion}">{error_text}</span>' +
                highlighted_text[end:]
            )
        else:
            highlighted_text = (
                highlighted_text[:start] +
                f'<span style="border: 3px solid lightgreen;" title="{suggestion}">{error_text}</span>' +
                highlighted_text[end:]
            )
    return highlighted_text