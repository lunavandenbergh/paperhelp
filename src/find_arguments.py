import streamlit as st
import json


def generate_arguments():
    import google.genai
    text = st.session_state["text"]
    prompt = f"""Given the user's paper draft, identify each distinct argument and return them in structured JSON format.
                Your response has to be processed as a string that directly becomes a JSON object.
                The JSON object should contain one	field called "arguments", which is a list of the arguments.
                Each argument should be treated as a standalone unit and should include the following details:
                - context: The full argument. Please keep any mistakes or errors in the text as they are.
                - parts: Breakdown of the argument into:
                  - claim: The main assertion or statement being argued.
                  - evidence: Factual or logical support for the claim.
                - counterargument: Empty by default. This will be filled in later.
                - feedback: Analysis of the arguments weaknesses, such as logical fallacies, lack of clarity, or weak evidence.
                - actionable_feedback: Specific steps to improve the argument.
																
																The paper draft:	{text}"""

    client = google.genai.Client(api_key=str(st.secrets["GEMINI_API_KEY"]))
    response = client.models.generate_content(
         model="gemini-2.0-flash", 
         contents=prompt,
    )
    arguments = response.text
    
    # Clean up the response text
    if arguments.startswith("```json") and arguments.endswith("```"):
        arguments = arguments[7:-3].strip()
    try:
        st.session_state["arguments"] = json.loads(arguments)
        st.session_state["updated_arguments"] = [False] * len(st.session_state["arguments"]["arguments"])
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}. Retrying...")
        generate_arguments() 

    agent = st.session_state["agent"]
    query = f"Given the user's paper draft text, provide general feedback on it, no longer than 150 words. Don't cite anything."
    general_feedback = agent.run(query)
    st.session_state["general_feedback"] = general_feedback.content
        

def generate_papers(argument_nr : int):
    argument = st.session_state.arguments["arguments"][argument_nr]
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
    st.session_state["arguments"]["arguments"][argument_nr] = argument
    st.write(st.session_state["arguments"])
    
    # Update the session state to indicate that the argument has been updated
    update_status = st.session_state["updated_arguments"]
    update_status[argument_nr] = True
    st.session_state["updated_arguments"] = update_status
    st.rerun()