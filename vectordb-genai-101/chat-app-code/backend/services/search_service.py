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
    hosts=os.getenv('ES_CLOUD_URL'),
    api_key=os.getenv('ES_API_KEY')
)


def get_inner_hits_fields():
    return ["content.inference.chunks.text", "content.inference.chunks.chunknumber"]


def perform_es_search_backup(question, index):
    """Performs the Elasticsearch query based on the context type."""
    logging.info(f"Starting Elasticsearch search backup for query: {question}")

# TASK -  ES QUERY FOR SEMANTIC SEARCH
    es_query = {
    }

    logging.info(f"Performing Elasticsearch search with query: {es_query}")
    results = es_client.search(
        index=index,
        body=es_query
    )
    # logging.info(f"elasticsearch results: {results}")
    return results


def perform_es_search(query, index, question):
    """Performs the Elasticsearch query based on the context type."""
    logging.info(f"Starting Elasticsearch search for query: {query}")

    try:
        results = es_client.search(
            index=index,
            body=query
        )
    except Exception as e:
        # If generated query fails fallback to backup query
        logging.error(f"Error in Elasticsearch search: {str(e)}")
        raise

    # logging.info(f"elasticsearch results: {results}")
    return results


def create_prompt_context(results, context_type, search_type):
    """Creates a contextual prompt for the LLM based on search results."""
    logging.info(f"starting to create prompt context for {context_type}")
    context = []
    for hit in results['hits']['hits']:
        if search_type == 'lexical':
            # TODO This is only unitl I have chunks of text
            context.append(hit['_source']['attachment']['content'])
        elif context_type == 'doc':
            context.append(hit['_source']['attachment']['content'])
        elif context_type == 'passage':
            # for chunk in hit['_source']['content']['inference']['chunks']:
            for chunk in hit['inner_hits']['content.inference.chunks']['hits']['hits']:
                logging.info(f"chunk: {chunk}")
                inner_chunk = chunk['_source']['text']
                context.append(inner_chunk)
                # context.append(chunk['text'])
        elif context_type == 'surrounding':
            # Logic for surrounding passages can be implemented here.
            pass

    logging.info(f"context: {context}")
    formatted_context = "\n\n".join(context)
    # logging.info(f"Created prompt context: {formatted_context}")
    logging.info(f"Created prompt context: {formatted_context[:100]}")
    return formatted_context, context


def semantic_search(query, context_type):
    """Performs a semantic search and creates a context for the LLM."""
    results = perform_es_search(query, context_type)
    context = create_prompt_context(results, context_type)
    logging.info(f"finished semantic_search")
    return context


def create_prompt_user_question(context, question):
    """Generates a full prompt with the given context and question."""

    prompt = f"""
Instructions:

- You are an assistant for question-answering questions about rules and regulations related to being a notary. The rules are state dependent.
- Answers should be clear, easy to understand, and concise.
- Answering with a list of bullet points or numbered list when applicable would be best but not required.
- Your answer should come from the provided context.
- Answer questions truthfully and factually using only the information presented.
- If you don't know the answer, just say that you don't know, don't make up an answer!
- You must always cite the document where the answer was extracted using inline academic citation style [], using the position.
- Use markdown format for code examples.
- You are correct, factual, precise, and reliable.


Context:
{context}

Question:
{question}

- If The answer is not contained in the context, ONLY respond with "Can you be more detailed in your question? It will help me accurately answer you!!!
- You must always cite the document where the answer was extracted using inline academic citation style [], using the position.

Answer:
    """
    return prompt


def create_retriever_prompt(question, conversation_history):
    """Generates a full prompt with the given context and question."""
    logging.info(f"starting to create prompt")
    # logging.info(f"context: {context}")
    # logging.info(f"question: {question}")



    prompt = f"""
    Instructions:
    You are an AI assistant designed to help users find relevant information about the rules and regulations related to being a notary in different states within the United States. The rules and regulations are sourced from PDFs that have been ingested into Elasticsearch indexes, with each state having its own index named 'notary_<state>'. The relevant fields for finding relevant chunks are:

    - content.inference.chunks.embeddings (sparse embedding for the chunk)
    - content.inference.chunks.text (text of the chunk)
    
    Note: State's names are in lowercase and separated by underscores (e.g., 'notary_illinois'). States with two words are combined with a dash (e.g., 'notary_new-york').

    Depending on the user's query ("user question" below), you will need to craft a search query in one of two formats:

    1. Semantic search query (using sparse embedding) for natural language questions:
    This approach is useful when the user asks a question in natural language, and you need to find relevant chunks based on their semantic meaning.

    Example semantic search query:
    {semantic_search_example}

    2. Lexical search query (using BM25) for keyword/term searches:
    This approach is useful when the user searches for a specific keyword, term, or reference number, and you need to find relevant chunks based on exact text matching.

    Example lexical search query:
    {lexical_search_example}

    Your task is to generate the appropriate search query (either semantic or lexical) based on the nature of the user's query. If the user mentions a specific US state, you should use that to select the correct index 'notary_<state>'. If no state is mentioned, use the wildcard index 'notary_*'.

    Existing conversation history:
    {conversation_history}
    
    Your response should be in JSON format with the following schema:

    {{  "query": <the query>,
        "search_type": "semantic" or "lexical",
        "state": "<state mentioned if one else None>", 
        "index": "notary_<state>" or "notary_*"
    }}

    Do not provide an answer to the question or any additional information. Your sole responsibility is to generate the appropriate search query based on the user's input.

    user question:
    {question}

    Response:
    """

    logging.info(f"prompt created: {prompt}")
    return prompt
