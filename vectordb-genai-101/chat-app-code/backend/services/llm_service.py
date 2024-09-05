import logging
from .inference_service import es_chat_completion

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# TODO - this should not be hardcoded
index_source_fields = {
    "restaurant_reviews": [
        "semantic_body"
    ]
}


def init_conversation_history():
    # convo = [
    #     {
    #         "role": "user",
    #         "content": "Hi, I have questions about Notary regulations"
    #     },
    #     {
    #         "role": "assistant",
    #         "content": "Sure, I can help with that. What specific questions do you have?"
    #     },
    # ]
    convo = []

    return convo


def create_llm_prompt(question, results, conversation_history):
    """
    Create a prompt for the LLM based on the question, search results, and conversation history provided
    :param question:
    :param results:
    :param conversation_history:
    :return:
    """
    logging.info("Starting to create LLM prompt")
    context = ""
    logging.info(f"Results: {results}")
    for hit in results:
        inner_hit_path = f"{hit['_index']}.{index_source_fields.get(hit['_index'])[0]}"
        logging.info(f"hit: {hit}")

        ## For semantic_text matches, we need to extract the text from the inner_hits
        if 'inner_hits' in hit and inner_hit_path in hit['inner_hits']:
            logging.info('inner_hits found')
            for inner_hit in hit['inner_hits'][inner_hit_path]['hits']['hits']:
                context += f"{inner_hit['_source']['text']}\n---\n"
        else:
            source_field = index_source_fields.get(hit["_index"])[0]
            hit_context = hit["_source"][source_field]
            context += f"{hit_context}\n"

    prompt = f"""
  Instructions:

  - You are a helpful and knowledgeable assistant designed to assist users in querying information related to Search, Observability, and Security. Your primary goal is to provide clear, concise, and accurate responses based on semantically relevant documents retrieved using Elasticsearch.

Guidelines:

Audience:

Assume the user could be of any experience level but lean towards a technical slant in your explanations.
Avoid overly complex jargon unless it is common in the context of Elasticsearch, Search, Observability, or Security.
Response Structure:

Clarity: Responses should be clear and concise, avoiding unnecessary verbosity.
Conciseness: Provide information in the most direct way possible, using bullet points when appropriate.
Formatting: Use Markdown formatting for:
Bullet points to organize information
Code blocks for any code snippets, configurations, or commands
Relevance: Ensure the information provided is directly relevant to the user's query, prioritizing accuracy.
Content:

Technical Depth: Offer sufficient technical depth while remaining accessible. Tailor the complexity based on the user's apparent knowledge level inferred from their query.
Examples: Where appropriate, provide examples or scenarios to clarify concepts or illustrate use cases.
Documentation Links: When applicable, suggest additional resources or documentation from Elastic.co that can further assist the user.
Tone and Style:

Maintain a professional yet approachable tone.
Encourage curiosity by being supportive and patient with all user queries, regardless of their complexity.


  - Answer questions truthfully and factually using only the context presented.
  - If you don't know the answer, just say that you don't know, don't make up an answer.
  - You must always cite the document where the answer was extracted using inline academic citation style [], using the position.
  - Use markdown format for code examples.
  - You are correct, factual, precise, and reliable.

Conversation History:
{conversation_history}
 
Context:
{context}

The user has a question:
{question}

Answer this question using the context provided and the conversation history.
if the answer is not in the context, please say "I'm unable to answer because the answer is not in the context or previously discussed." DO NOT make up an answer.
  """

    logging.info(f"Done creating LLM prompt")
    logging.info(f"Full Prompt: {prompt}")
    return prompt


def build_conversation_history(history, user_message, ai_response):
    """
    Function to build converstation history for the LLM
    Keep 2 messages from the user and 2 messages from the AI
    When the count of messages from the user and AI each is greater than 2,
     keep the last 2 messages as is
     make a call to the LLM to summarize the conversation and keep the summary

    Summary is kept in the "system" role

    structure
    [
      {"role": "system", "content": "Conversation summary:  [summary here]"},
      {"role": "user", "content": "2 messages ago"},
      {"role": "assistant", "content": "2 responses ago"},
      {"role": "user", "content": "1 message ago"},
      {"role": "assistant", "content": "1 response ago"}
    ]
    """

    logging.info("Starting to build conversation history function")
    if len(history) < 4:
        logging.info("History is less than 4 messages. Adding new messages to history")
        history.extend([
            {
                "role": "user",
                "content": user_message
            },
            {
                "role": "assistant",
                "content": ai_response
            }
        ])
        new_history = history
    else:
        logging.info("History is greater than 4 messages. Summarizing conversation")
        summary_prompt = f"""
You are a conversation summarizer specializing in notary laws, regulations, and related topics in the USA. Your task is to create a concise summary of the conversation history, incorporating the new message provided. This summary will be used as context for future interactions, so focus on key points, questions, and any unresolved issues.

Rules:
1. Summarize the entire conversation, including the provided history and the new message.
2. Concentrate on notary-related information, legal concepts, and any specific questions or concerns raised.
3. Highlight any unresolved issues or areas that may require further clarification.
4. Use a compact format optimized for AI processing, not human readability.
5. Limit the summary to approximately 150 words.

Current conversation history:
{history}

New User message:
{user_message}

New Assistant response:
{ai_response}

Provide your summary in the following format:
SUMMARY: [Your concise summary here]
TOPICS: [List of key topics discussed]
UNRESOLVED: [Any open questions or issues]
        """

        # call the LLM to summarize the conversation
        # summary = query_aws_bedrock_nonstreaming(summary_prompt)
        summary = es_chat_completion(summary_prompt)
        logging.info(f"LLM Summary of history: {summary}")

        # Build new history
        new_history = [
            {
                "role": "system",
                "content": summary
            },
            history[-2],
            history[-1],
            {
                "role": "user",
                "content": user_message
            },
            {
                "role": "assistant",
                "content": ai_response
            }
        ]

    logging.info(f"New conversation history: {new_history}")

    return new_history