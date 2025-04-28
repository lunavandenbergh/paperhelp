import json
import re
import streamlit as st
import html

def get_corrections_llm():
    import google.genai
    text = st.session_state["text"]
    prompt = f"""You are a language correction system. 
                 Given a text, identify each error (spelling, grammar, style, ...) and return them in structured JSON format.
                 Your response has to be processed as a string that directly becomes a JSON object.
                 Each error should be treated as a standalone unit and should include the following details:
                 - error: The exact error in the text.
                 - context: The sentence	or containing the error.
                 - suggestion: The most likely suggestion	for the error.
                 - offset: The starting position of the error in the text, counted in characters from the start of the text.
                 - length: The length of the error in the text.
                 - type: The type of error (spelling, grammar, style, ...).
                 
                 Here's the text: {text}"""
 
    client = google.genai.Client(api_key=str(st.secrets["GEMINI_API_KEY"]))
    response = client.models.generate_content(
         model="gemini-2.0-flash", 
         contents=prompt,
    )
    corrections = response.text
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
        # als er \n in de tekst staat, span aflsuiten en volgende lijn in een nieuwe span zetten
        if "\n\n" in error_text:
            lines = error_text.split("\n\n")
            updated_text = ""
            for line in lines:
                if lines.index(line) != len(lines) - 1:
                    updated_text += f'<span style="border-bottom: 3px solid orange;">{line}</span>\n\n'
                else:
                    updated_text += f'<span style="border-bottom: 3px solid orange;">{line}</span>'
            highlighted_text = (
                highlighted_text[:start] +
                updated_text +
                highlighted_text[end:]
            )
        else:
            highlighted_text = (
                highlighted_text[:start] +
                f'<span style="border-bottom: 3px solid orange;">{error_text}</span>' +
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
                f'<span style="border-bottom: 3px solid red;" title="Suggestion: {suggestion}">{highlighted_text[start:end]}</span>' +
                highlighted_text[end:]
            )
        elif correction["type"] == "grammar":
            highlighted_text = (
                highlighted_text[:start] +
                f'<span style="border-bottom: 3px solid blue;" title="Suggestion: {suggestion}">{highlighted_text[start:end]}</span>' +
                highlighted_text[end:]
            )
        elif correction["type"] == "style":
            highlighted_text = (
                highlighted_text[:start] +
                f'<span style="border-bottom: 3px solid green;" title="Suggestion: {suggestion}">{highlighted_text[start:end]}</span>' +
                highlighted_text[end:]
            )
    return highlighted_text
