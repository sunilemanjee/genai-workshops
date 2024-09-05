import logging
from elasticsearch import Elasticsearch
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# TODO move this to central location so this and search_service don't create separate connections
# Initialize the Elasticsearch client
es_client = Elasticsearch(
    hosts=os.getenv('ES_URL', 'http://kubernetes-vm:9200'),
    # api_key=os.getenv('ES_API_KEY'),
    basic_auth=(
        os.getenv('ES_USER', 'elastic'),
        os.getenv('ES_PASSWORD', 'changeme')
    ),
    timeout=90
)
logging.info(f"Elasticsearch client Info: {es_client.info()}")


def es_chat_completion(prompt, inference_id):
    logging.info(f"Starting Elasticsearch chat completion with Inference ID: {inference_id}")

    response = es_client.inference.inference(
        inference_id = inference_id,
        task_type = "completion",
        input = prompt,
        timeout="90s"
    )

    logging.info(f"Response from Elasticsearch chat completion: {response}")

    return response['completion'][0]['result']



