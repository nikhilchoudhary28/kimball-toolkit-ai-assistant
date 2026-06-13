import os
from pypdf import PdfReader
from tqdm import tqdm
from elasticsearch import Elasticsearch

def extract_text_from_pdf(pdf_path):
    print(f"Opening {pdf_path}...")
    reader = PdfReader(pdf_path)
    documents = []
    for page_num, page in enumerate(tqdm(reader.pages)):
        text = page.extract_text()
        if text and text.strip():
            documents.append({"page": page_num + 1, "text": text.strip()})
    return documents

def create_chunks(documents, chunk_size=1500, chunk_overlap=200):
    print(f"\nProcessing chunks (Size: {chunk_size}, Overlap: {chunk_overlap})...")
    chunks = []
    full_text = ""
    char_to_page = []
    
    for doc in documents:
        page_num = doc["page"]
        page_text = doc["text"] + " "
        full_text += page_text
        char_to_page.extend([page_num] * len(page_text))
        
    start = 0
    chunk_id = 0
    while start < len(full_text):
        end = start + chunk_size
        chunk_text = full_text[start:end]
        mid_point = start + (len(chunk_text) // 2)
        source_page = char_to_page[mid_point] if mid_point < len(char_to_page) else char_to_page[-1]
        
        chunks.append({
            "chunk_id": chunk_id,
            "source_page": source_page,
            "text": chunk_text.strip()
        })
        chunk_id += 1
        start += (chunk_size - chunk_overlap)
    return chunks

def index_to_elasticsearch(chunks, index_name="kimball_book"):
    # Force direct IPv4 connection parameters and skip SSL/TLS verification checks
    # Force connection parameters, skip validation, and enforce compatible API headers
    # Connect directly using the stable IPv4 endpoint
    es = Elasticsearch(
        "http://127.0.0.1:9200",
        request_timeout=30
    )
    
    
    
    # Try an explicit, hard ping check
    try:
        if not es.ping():
            raise Exception("Ping failed")
    except Exception:
        print("Error: Python client still cannot find Elasticsearch endpoint directly.")
        print("Bypassing validation gate and attempting force-stream instead...")

    # Safe index setup configuration
    index_settings = {
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
        "mappings": {
            "properties": {
                "chunk_id": {"type": "integer"},
                "source_page": {"type": "integer"},
                "text": {"type": "text"}
            }
        }
    }
    
    try:
        if es.indices.exists(index=index_name):
            es.indices.delete(index=index_name)
        es.indices.create(index=index_name, body=index_settings)
    except Exception as e:
        print(f"Index initialization warning: {e}. Attempting direct document upload instead...")
    
    print("\nUploading chunks directly to database...")
    for chunk in tqdm(chunks):
        try:
            es.index(index=index_name, id=str(chunk["chunk_id"]), body=chunk)
        except Exception as e:
            print(f"\nFailed to upload chunk {chunk['chunk_id']}: {e}")
            return
        
    print(f"\nSuccessfully indexed all {len(chunks)} blocks into Elasticsearch!")

if __name__ == "__main__":
    pdf_file = "data/book.pdf"
    if not os.path.exists(pdf_file):
        print(f"Error: Could not find the file at {pdf_file}.")
    else:
        raw_docs = extract_text_from_pdf(pdf_file)
        processed_chunks = create_chunks(raw_docs, chunk_size=1500, chunk_overlap=200)
        index_to_elasticsearch(processed_chunks)