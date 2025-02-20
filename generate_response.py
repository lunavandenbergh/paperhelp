import streamlit as st


# Find the most relevant chunks of the pdf, compared to user question, in the existing embeddings
def find_relevant_chunks(question, model, collection, top_k=3):
    question_embedding = model.encode([question]).tolist()
    results = collection.query(
        query_embeddings=question_embedding,
        n_results=top_k
    )
    return results['documents'][0]  # Returns the top matching chunks

def generate_response(prompt, model, collection, client):
    relevant_chunks = find_relevant_chunks(prompt, model, collection)
    context = "\n\n".join(relevant_chunks)
    system_message = f"Use the following document excerpts to answer the question:\n\n{context}\n\nQuestion: {prompt}"

    stream = client.chat.completions.create(
            model="mistralai/Mixtral-8x7B-Instruct-v0.1",
            messages=[
                {"role": "system", "content": system_message},
                *st.session_state.messages,
            ],
				        )
    response = stream.choices[0].message.content
    return response


