import streamlit as st
import time
import json
from together.error import APIConnectionError

def split_text(text, max_length=2000):
    """Splits the text into chunks of max_length."""
    return [text[i:i + max_length] for i in range(0, len(text), max_length)]

def generate_arguments(precalculated, client):
    if precalculated:
        with open("arguments.json", "r") as file:
            data = json.load(file)
            return data
    system_message = '''You are an advanced argument analysis system. 
                         Given a text, identify each distinct argument and return them in structured JSON format. 
                         Please do not respond with anything other than the JSON format. 
                         Each argument should be treated as a standalone unit and should include the following details:
                         - context: The full argument
                         - parts: Breakdown of the argument into:
                             - claim: The main assertion or statement being argued.
                             - evidence: Factual or logical support for the claim.
                             - counterargument: Any opposing viewpoint presented.
                         - feedback: Analysis of the arguments weaknesses, such as logical fallacies, lack of clarity, or weak evidence.
                         - actionable_feedback: Specific steps to improve the argument.'''
    
    text_chunks = split_text(st.session_state["text"])
    retries = 3
    for attempt in range(retries):
        try:
            messages = [{"role": "system", "content": system_message}]
            for chunk in text_chunks:
                messages.append({"role": "user", "content": chunk})
            
            stream = client.chat.completions.create(
                model="mistralai/Mixtral-8x7B-Instruct-v0.1",
                messages=messages,
            )
            response = stream.choices[0].message.content
            
            # Validate JSON
            try:
                arguments_json = json.loads(response)
                return json.dumps(arguments_json)  # Return as a JSON string
            except json.JSONDecodeError as e:
                print(f"Invalid JSON response: {e}")
                continue  # Retry if JSON is invalid

        except APIConnectionError as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2)  # Wait for 2 seconds before retrying
            else:
                raise