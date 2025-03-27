import streamlit as st
import asyncio
import json

def split_text(text, max_length=2000):
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

# TODO think about how to handle counterarguments
def generate_arguments():
    import google.genai
    try:
        asyncio.get_event_loop()
    except RuntimeError:
        asyncio.set_event_loop(asyncio.new_event_loop())
    text = st.session_state["text"]
    prompt = f"""You are an advanced argument analysis system. 
                Given a text, identify each distinct argument and return them in structured JSON format.
                Your response has to be processed as a string that directly becomes a JSON object.
                Each argument should be treated as a standalone unit and should include the following details:
                - context: The full argument. Please keep any mistakes or errors in the text as they are.
                - parts: Breakdown of the argument into:
                  - claim: The main assertion or statement being argued.
                  - evidence: Factual or logical support for the claim.
                  - counterargument: Any opposing viewpoint presented.
                - feedback: Analysis of the arguments weaknesses, such as logical fallacies, lack of clarity, or weak evidence.
                - actionable_feedback: Specific steps to improve the argument.
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
        st.session_state["arguments"] = json.loads(arguments) 
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        st.session_state["arguments"] = None 
        
    general_feedback = client.models.generate_content(
                                   model="gemini-2.0-flash",
                                   contents=f"Given the following text, provide short, general feedback on the paper draft: {text}",
    )
    st.session_state["general_feedback"] = general_feedback.text
