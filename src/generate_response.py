from sentence_transformers import SentenceTransformer
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
    system_message = f"Use the following document excerpts if the paper draft is necesssary to answer the question :\n\n{context}\n\nDon't use the context if the user asks something that's not related to their paper. Question: {prompt}."

    messages = [
    {
        "role": "system",
        "content": (
            '''You are an academic assistant that provides feedback on research papers. 
               The user has uploaded a draft, which is stored in your knowledge base.

               You also can be asked to generate new text or provide scientific papers on a certain topic. 
                       
               ⚠️ Always search your knowledge base before answering questions. 
               If relevant information exists, include it in your response. 
               If no relevant data is found, politely ask the user for clarification.
                       
               Always cite your sources. Preferably, these sources are scientific papers or books.'''
        ),
    },
    {   
        "role": "user",
        "content": (
            f"{system_message}"
        ),
    },
]

    # Call the OpenAI API
    stream = client.chat.completions.create(
        model="sonar",
        messages=messages,
    )
    print(stream)
    response = stream.choices[0].message.content
    citations = stream.citations
    return {
        "response": response,
        "citations": citations,
    }
