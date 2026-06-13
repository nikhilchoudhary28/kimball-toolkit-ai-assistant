from elasticsearch import Elasticsearch

def search_book(query_text, top_n=3):
    # Connect to your synchronized local database
    es = Elasticsearch("http://127.0.0.1:9200")
    
    # Structure a standard Elasticsearch match query
    search_query = {
        "query": {
            "match": {
                "text": query_text
            }
        }
    }
    
    # Execute search against your custom index
    response = es.search(index="kimball_book", body=search_query, size=top_n)
    
    print(f"\n🔍 Searching for: '{query_text}'")
    print(f"=========================================")
    
    # Loop over and print out the top matching fragments
    for i, hit in enumerate(response['hits']['hits']):
        score = hit['_score']
        source = hit['_source']
        print(f"\n▶ Match #{i+1} | Relevance Score: {score:.2f} | Source Page: {source['source_page']}")
        print(f"----------------------------------------------------------------------")
        print(source['text'][:400] + "...")

if __name__ == "__main__":
    # Test your engine with a foundational Kimball concept!
    search_book("What is a conformed dimension and drill across report")