from openai import OpenAI
from sentence_transformers import SentenceTransformer
import streamlit as st
import time

# Find the most relevant chunks of the pdf, compared to user question, in the existing embeddings
def find_relevant_chunks(question, collection, top_k=3):
    tic = time.time()
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    question_embedding = model.encode([question]).tolist()
    results = collection.query(
        query_embeddings=question_embedding,
        n_results=top_k
    )
    toc = time.time()
    print(f"Finding relevant chunks took {toc - tic:.2f} seconds")
    return results['documents'][0]  # Returns the top matching chunks

def generate_response(prompt, collection, client):
    relevant_chunks = find_relevant_chunks(prompt, collection)
    context = "\n\n".join(relevant_chunks)
    system_message = f"Use the following document excerpts to answer the question:\n\n{context}\n\nQuestion: {prompt}."

    stream = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_message},
                *st.session_state.messages,
            ],
            )
    response = stream.choices[0].message.content
    return response


