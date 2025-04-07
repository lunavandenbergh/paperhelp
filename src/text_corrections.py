import json
import language_tool_python
import streamlit as st

def get_corrections():
    #tool_public = language_tool_python.LanguageToolPublicAPI('en-US')
    tool = language_tool_python.LanguageTool('en-US')
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

def get_corrections_llm():
    import google.genai
    text = st.session_state["text"]
    prompt = f"""You are a language correction system. 
                Given a text, identify each error (spelling, grammar, style, ...) and return them in structured JSON format.
                Your response has to be processed as a string that directly becomes a JSON object.
                Each error should be treated as a standalone unit and should include the following details:
                - error: The exact error in the text.
                - suggestion: The most likely suggestion	for the error.
                - place: Breakdown of the location into:
                  - offset: The starting position of the error in the text.
																		- length: The length of the error in the text.
                - type: The type of error (spelling, grammar, style, ...).
                
                Here's the text: {text}"""

    client = google.genai.Client(api_key=str(st.secrets["GEMINI_API_KEY"]))
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents=prompt,
    )
    
    arguments = response.text
    # Clean up the response text if it starts with ```json and ends with ```
    if arguments.startswith("```json") and arguments.endswith("```"):
        arguments = arguments[7:-3].strip()
    try:
        st.session_state["corrections_llm"] = json.loads(arguments) 
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        st.session_state["corrections_llm"] = None 

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
                f'<span style="border-bottom: 3px solid red;" title="{suggestion}">{error_text}</span>' +
                highlighted_text[end:]
            )
        elif correction["type"] == "grammar":
            highlighted_text = (
                highlighted_text[:start] +
                f'<span style="border-bottom: 3px solid blue;" title="{suggestion}">{error_text}</span>' +
                highlighted_text[end:]
            )
        elif correction["type"] == "argument":
            highlighted_text = (
                highlighted_text[:start] +
                f'<span style="border-bottom: 3px solid orange;" title="{suggestion}">{error_text}</span>' +
                highlighted_text[end:]
            )
        else:
            highlighted_text = (
                highlighted_text[:start] +
                f'<span style="border-bottom: 3px solid lightgreen;" title="{suggestion}">{error_text}</span>' +
                highlighted_text[end:]
            )
    return highlighted_text