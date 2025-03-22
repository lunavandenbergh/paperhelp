from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer	

# Split the PDF into chunks so we don't hit the token size limit during information retrieval
def split_text(text):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1500,
        chunk_overlap  = 100,
        length_function = len,
    )
    return text_splitter.split_text(text)

def create_embeddings(chunks, batch_size=32):
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return model.encode(chunks, batch_size=batch_size, show_progress_bar=True)

# Add embeddings and chunks to the collection
def store_embeddings(collection, chunks, embeddings, file_name):
				# Add new embeddings
    ids = [f"{file_name}_{i}" for i in range(len(chunks))]
    collection.add(
        embeddings=embeddings.tolist(),
        documents=chunks,
        ids=ids,
        metadatas=[{"source": file_name} for _ in chunks]
    )