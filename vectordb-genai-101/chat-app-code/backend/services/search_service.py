from elasticsearch import Elasticsearch
import logging
import os

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Initialize the Elasticsearch client
es_client = Elasticsearch(
    hosts=os.getenv('ES_URL', 'http://kubernetes-vm:9200'),
    # api_key=os.getenv('ES_API_KEY')
    basic_auth=(
        os.getenv('ES_USER', 'elastic'),
        os.getenv('ES_PASSWORD', 'changeme')
    )
)


def perform_es_search(query, index):
    """Performs the Elasticsearch query based on the context type."""
    logging.info(f"Starting Elasticsearch search for query: {query}")

## TODO USERS ENTER QUERY CODE HERE
    es_query = {

    }


    try:
        result = es_client.search(index="elastic-labs", body=es_query)

    except Exception as e:
        # If generated query fails fallback to backup query
        logging.error(f"Error in Elasticsearch search: {str(e)}")
        raise

    logging.info(f"elasticsearch results: {result}")
    return result["hits"]["hits"]




import os
from elasticsearch import Elasticsearch

client = Elasticsearch(
    hosts=["https://e42f683bda7c40a5965b829ba3058ece.es.us-east-1.aws.elastic.cloud:443"],
    api_key=os.getenv("ELASTIC_API_KEY"),
)

resp = client.search(
    index="elastic-labs",
    retriever={
        "standard": {
            "query": {
                "nested": {
                    "path": "semantic_body.inference.chunks",
                    "query": {
                        "sparse_vector": {
                            "inference_id": "my-elser-endpoint",
                            "field": "semantic_body.inference.chunks.embeddings",
                            "query": "How do I configure quantization for a dense vector?"
                        }
                    }
                }
            }
        }
    },
)
print(resp)

