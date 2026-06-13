import os
from elasticsearch import Elasticsearch
from google import genai
from google.genai import types

def retrieve_context(query_text, index_name="kimball_book", top_n=3):
    """Searches Elasticsearch to extract the most relevant book chunks."""
    es = Elasticsearch("http://127.0.0.1:9200")
    
    search_query = {
        "query": {
            "match": {
                "text": query_text
            }
        }
    }
    
    response = es.search(index=index_name, body=search_query, size=top_n)
    
    context_chunks = []
    for hit in response['hits']['hits']:
        source = hit['_source']
        context_chunks.append(f"[Source: Page {source['source_page']}]\n{source['text']}")
        
    return "\n\n---\n\n".join(context_chunks)

def generate_answer(user_question, context):
    """Sends the context block and the user question to Gemini for a grounded answer."""
    # The client automatically reads the GEMINI_API_KEY environment variable
    client = genai.Client()
    
    # Craft a strict system prompt to completely block hallucinations
    system_instruction = (
        "You are an expert Data Engineering Assistant specializing in Kimball Dimensional Modeling.\n"
        "Answer the user's question using ONLY the provided textbook context snippets below.\n"
        "If the context does not contain the answer, say 'I cannot find that specific detail in the text.'\n"
        "Always cite the Source Page numbers provided in the context when making assertions.\n"
    )
    
    user_prompt = f"CONTEXT:\n{context}\n\nQUESTION:\n{user_question}"
    
    print("\n🤖 Consulting the Gemini brain based on retrieved pages...")
    
    # Using gemini-2.5-flash: blazing fast, cheap, and perfect for structured context processing
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=user_prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.2, # Low temperature ensures factual answers
        ),
    )
    
    return response.text

def ask_assistant(question):
    print(f"\n💬 User Question: '{question}'")
    
    # Step 1: Query the local database engine
    context = retrieve_context(question)
    
    # Step 2: Feed text context to Gemini
    answer = generate_answer(question, context)
    
    print("\n✨ GEMINI ANSWER:")
    print("======================================================================")
    print(answer)
    print("======================================================================")

if __name__ == "__main__":
    query = "Explain why conformed dimensions are essential for drill across reports"
    ask_assistant(query)