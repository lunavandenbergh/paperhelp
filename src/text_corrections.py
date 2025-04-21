import json
import streamlit as st
import html

def get_corrections_llm():
    agent = st.session_state["agent"]
    prompt = f"""Given the user's paper draft text, identify each error (spelling, grammar, style, ...) and return them in structured JSON format.
                You can ignore errors specific to citations, references, or bibliography.
                Your response has to be processed as a string that directly becomes a JSON object.
                Each error should be treated as a standalone unit and should include the following details:
                - error: The exact error in the text.
                - context: The sentence	or containing the error.
                - suggestion: The most likely suggestion	for the error.
                - offset: The starting position of the error in the text, counted in characters from the start of the text.
                - length: The length of the error in the text.
                - type: The type of error (spelling, grammar, style, ...)."""

    response = agent.run(prompt)
    corrections = response.content
    # Clean up the response text if it starts with ```json and ends with ```
    if corrections.startswith("```json") and corrections.endswith("```"):
        corrections = corrections[7:-3].strip()
    try:
        st.session_state["corrections_llm"] = json.loads(corrections) 
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        get_corrections_llm()  # Retry if JSON decoding fails 


def highlight_text_arguments(text, corrections):
    highlighted_text = text
    for correction in sorted(corrections, key=lambda x: x["offset"], reverse=True):
        start = correction["offset"]
        end = start + correction["length"]
        error_text = text[start:end]
        suggestion = correction["suggestion"]
        highlighted_text = (
            highlighted_text[:start] +
            f'<span style="border-bottom: 3px solid orange;" title="{suggestion}">{error_text}</span>' +
            highlighted_text[end:]
        )
    return highlighted_text


def highlight_text_corrections(text, corrections):
    highlighted_text = text
    normalized_text = highlighted_text.replace("\n", " ")
    
    for correction in sorted(corrections, key=lambda x: x["offset"], reverse=True):
        normalized_context = correction["context"].replace("\n", " ")
        context_start = normalized_text.find(normalized_context)
        error_incontext = normalized_context.find(correction["error"])
        
        if context_start == -1 or error_incontext == -1:
            print(f"Failed to process correction: {correction}")
            continue
        
        calculated_offset = context_start + error_incontext
        start = calculated_offset
        end = start + correction["length"]
        
        if start < 0 or end > len(highlighted_text):
            print(f"Skipping invalid correction: {correction}")
            continue
        
        suggestion = html.escape(correction["suggestion"])
        
        if correction["type"] == "spelling":
            highlighted_text = (
                highlighted_text[:start] +
                f'<span style="border-bottom: 3px solid red;" title="{suggestion}">{highlighted_text[start:end]}</span>' +
                highlighted_text[end:]
            )
        elif correction["type"] == "grammar":
            highlighted_text = (
                highlighted_text[:start] +
                f'<span style="border-bottom: 3px solid blue;" title="{suggestion}">{highlighted_text[start:end]}</span>' +
                highlighted_text[end:]
            )
        elif correction["type"] == "style":
            highlighted_text = (
                highlighted_text[:start] +
                f'<span style="border-bottom: 3px solid green;" title="{suggestion}">{highlighted_text[start:end]}</span>' +
                highlighted_text[end:]
            )
        else:
            highlighted_text = (
                highlighted_text[:start] +
                f'<span style="border-bottom: 3px solid purple;" title="{suggestion}">{highlighted_text[start:end]}</span>' +
                highlighted_text[end:]
            )
    return highlighted_text
