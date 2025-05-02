import streamlit as st
import json
from pydantic import BaseModel

class Argument(BaseModel):
    context: str
    claim: str
    evidence: str
    counterargument: str
    feedback: str
    actionable_feedback: str

def generate_arguments():
    import google.genai
    text = st.session_state["text"]
    prompt = f"""Given the user's paper draft, identify each argument that could be improved.
                 Keep the length of the arguments to a maximum of a few sentences, within one paragraph.
                Each argument should be treated as a standalone unit and should include the following details:
                - context: The full argument. Please keep any mistakes or errors in the text as they are. Please keep the text as it is, within a single paragraph.
                - parts: Breakdown of the argument into:
                  - claim: The main assertion or statement being argued.
                  - evidence: Factual or logical support for the claim.
                - counterargument: Empty by default. This will be filled in later.
                - feedback: Analysis of the arguments weaknesses, such as logical fallacies, lack of clarity, or weak evidence.
                - actionable_feedback: Specific steps to improve the argument.
                
                The paper draft:	{text}"""

    client = google.genai.Client(api_key=str(st.secrets["GEMINI_API_KEY"]))
    try:
        print("Trying gemini-2.0-flash...")
        response = client.models.generate_content(
            model="gemini-2.0-flash", 
            contents=prompt,
            config={
                'response_mime_type': 'application/json',
                'response_schema': list[Argument],
            }
        )
        print("Response from gemini-2.0-flash: ", response)
        arguments = response.text
    except:
        print("Error generating content with gemini-2.0-flash. Trying gemini-2.0-flash-lite...")
        try:
            response = client.models.generate_content(
                model="gemini-2.0-flash-lite", 
                contents=prompt,
                config={
                'response_mime_type': 'application/json',
                'response_schema': list[Argument],
            }
            )
            arguments = response.text
        except:
            print("Error generating content with gemini-2.0-flash-lite. Trying gemini-1.5-flash...")
            try:
                response = client.models.generate_content(
                    model="gemini-1.5-flash", 
                    contents=prompt,
                    config={
                'response_mime_type': 'application/json',
                'response_schema': list[Argument],
            }
                )
                arguments = response.text
            except:
                print("Error generating content with all three models.")
                return
    print(f"Response: {arguments}")
    # Clean up the response text
    if arguments.startswith("```json") and arguments.endswith("```"):
        arguments = arguments[7:-3].strip()
    try:
        st.session_state["arguments"] = json.loads(arguments)
        st.session_state["updated_arguments"] = [False] * len(st.session_state["arguments"])
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}. Retrying...")
        generate_arguments() 
        

def generate_papers(argument_nr : int):
    argument = st.session_state["arguments"][argument_nr]
    agent = st.session_state["agent"]

    # Actually generate the papers
    prompt = f"""
            Given the following argument that is part of the user's paper draft, 
            provide a list of at most three relevant scientific papers that can be used to improve or counter the argument.
            The argument is: {argument['context']}

            Format your response as a JSON object with the following fields:
            - papers: A list of papers that can be used to improve or counter the argument, existing of:
                - title: The title of the paper.
                - authors: The authors of the paper.
                - year: The year of publication.
                - url: A link to the paper.
                - abstract: A short summary of the paper.
            - general: How the provided papers can improve the argument.
        """
    response = agent.run(prompt)

    response_text = response.content
    # Remove extra characters from the response
    start_json = response_text.find("{")
    end_json = response_text.rfind("}")
    response_text = response_text[start_json:end_json + 1]
    try:
        response_json = json.loads(response_text) 
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        generate_papers(argument_nr)  # Retry if there's an error

    argument["counterargument"] = response_json
    st.session_state["arguments"][argument_nr] = argument
    st.write(st.session_state["arguments"])
    
    # Update the session state to indicate that the argument has been updated
    update_status = st.session_state["updated_arguments"]
    update_status[argument_nr] = True
    st.session_state["updated_arguments"] = update_status
    st.rerun()
