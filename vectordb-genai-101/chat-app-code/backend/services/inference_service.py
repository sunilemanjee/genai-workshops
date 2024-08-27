import logging
from elasticsearch import Elasticsearch
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# TODO move this to central location so this and search_service don't create separate connections
es_client = Elasticsearch(
    hosts=os.getenv('ES_CLOUD_URL'),
    api_key=os.getenv('ES_API_KEY'),
    timeout=90
)


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



