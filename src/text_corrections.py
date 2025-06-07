"""
text_corrections.py

Provides functions and models for extracting, highlighting, and displaying text corrections
(spelling, grammar, style, etc.) in the paper feedback applications. Uses LLMs (Google Gemini) to
identify errors and generate suggestions.

Features:
- Extracts corrections from paper drafts using LLMs
- Highlights arguments and corrections in the paper text
"""

import json
import re
import streamlit as st
import html
from pydantic import BaseModel

class Correction(BaseModel):
    """
    Data model for representing a correction in the text.

    Attributes:
        error (str): The exact error in the text.
        context (str): Few words before and after the error.
        suggestion (str): Suggested correction.
        offset (int): Starting position of the error in the text.
        length (int): Length of the error.
        type (str): Type of error (spelling, grammar, style, etc.).
    """
    error: str
    context: str
    suggestion: str
    offset: int
    length: int
    type: str

def get_corrections_llm():
    """
    Uses Google Gemini LLM to extract corrections from the user's paper draft.
    Stores the results in Streamlit session state as a list of corrections.
    """
    import google.genai
    text = st.session_state["text"]
    prompt = f"""You are a language correction system. Given a text, identify each error (spelling, grammar, style, ...).
                 Don't include errors that are part of the citation or references.
                 Ignore errors pertaining to symbols used like \\n, hyphens to split words between lines, ....
                 Each error should include the following details:
                 - error: The exact error in the text.
                 - context: Few words before and after the text containing the error.
                 - suggestion: The most likely suggestion	for the error.
                 - offset: The starting position of the error in the text, counted in characters from the start of the text.
                 - length: The length of the error in the text.
                 - type: The type of error (spelling, grammar, style, ...).
                 
                 Here's the text: {text}"""
 
    client = google.genai.Client(api_key=str(st.secrets["GEMINI_API_KEY"]))
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': list[Correction],
            }
        )
        corrections = response.text
    except:
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite", 
                contents=prompt,
                config={
                'response_mime_type': 'application/json',
                'response_schema': list[Correction],
            }
            )
            corrections = response.text
        except:
            try:
                response = client.models.generate_content(
                    model="gemini-1.5-flash", 
                    contents=prompt,
                    config={
                'response_mime_type': 'application/json',
                'response_schema': list[Correction],
            }
                )
                corrections = response.text
            except:
                print("Error generating content with all three models.")
                return
    if corrections.startswith("```json") and corrections.endswith("```"):
        corrections = corrections[7:-3].strip()
    try:
        st.session_state["corrections_llm"] = json.loads(corrections) 
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        get_corrections_llm()  # Retry if something fails 

def highlight_text_arguments(text, corrections):
    """
    Highlights argument sections in the text using HTML spans.

    Args:
        text (str): The original text.
        corrections (list): List of corrections (dicts) with offset and length.
    """
    highlighted_text = text
    for correction in sorted(corrections, key=lambda x: x["offset"], reverse=True):
        start = correction["offset"]
        end = start + correction["length"]
        error_text = text[start:end]
        # If there are double newlines, split and wrap each line separately
        if "\n\n" in error_text:
            lines = error_text.split("\n\n")
            updated_text = ""
            for line in lines:
                if lines.index(line) != len(lines) - 1:
                    updated_text += f'<span class="argumentintext">{line}</span>\n\n'
                else:
                    updated_text += f'<span class="argumentintext">{line}</span>'
            highlighted_text = (
                highlighted_text[:start] +
                updated_text +
                highlighted_text[end:]
            )
        else:
            highlighted_text = (
                highlighted_text[:start] +
                f'<span class="argumentintext">{error_text}</span>' +
                highlighted_text[end:]
            )
        
    return highlighted_text

def highlight_text_corrections(text, corrections):
    """
    Highlights corrections in the text using colored underlines for different error types.

    Args:
        text (str): The original text.
        corrections (list): List of corrections (dicts) with offset, length, type, and suggestion.

    Returns:
        str: The text with corrections highlighted.
    """
    highlighted_text = text
    normalized_text = highlighted_text.replace("\n", " ")
    normalized_text = normalized_text.replace("’", "'")
    
    for correction in sorted(corrections, key=lambda x: x["offset"], reverse=True):
        normalized_context = correction["context"].replace("\n", " ")

        error = correction["error"]
        if normalized_text.count(error) == 1:
            start = normalized_text.find(error)
            end = start + correction["length"]
        else:
            context_start = normalized_text.find(normalized_context)
            error_incontext = normalized_context.find(correction["error"])
        
            if context_start == -1 or error_incontext == -1:
                print(f"Failed to process correction: {correction}")
                continue
            else:
                calculated_offset = context_start + error_incontext
                start = calculated_offset
                end = start + correction["length"]
        
        if start < 0 or end > len(highlighted_text):
            print(f"Skipping invalid correction: {correction}")
            continue
        
        if correction["suggestion"] is not None:
            suggestion = html.escape(correction["suggestion"])
        else:
            suggestion = ""
            
        if "\n" in correction["error"]:
            continue
        
        # Highlight based on error type
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
