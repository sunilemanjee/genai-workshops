import logging
from .inference_service import es_chat_completion

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


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
    #logging.info(f"Results: {results}")

    # Check the structure of the first item in the list to see what it contains
    if results and isinstance(results, list):
        first_item = results[0]  # Access the first item to inspect its structure

        # Print the structure of the first item if it exists
        if isinstance(first_item, dict):
            structure = {key: type(value).__name__ for key, value in first_item.items()}
            print("Structure of the first item in results:", structure)
            # logging.info(f"Structure of the first item in results: {structure}")
        else:
            print("The first item in results is not a dictionary. Type:", type(first_item).__name__)
            # logging.info(f"The first item in results is not a dictionary. Type: {type(first_item).__name__}")
    else:
        print("Results is either empty or not a list.")
        # logging.info("Results is either empty or not a list.")

    for hit in results:
        # Check the structure of _source if needed
        source_structure = {key: type(value).__name__ for key, value in hit['_source'].items()}
        print("Structure of _source:", source_structure)
        # logging.info(f"Structure of _source: {source_structure}")

        # Extract data using the known fields
        hotel_name = hit['_source'].get('HotelName', 'N/A')
        hotel_rating = hit['_source'].get('HotelRating', 'N/A')
        address = hit['_source'].get('Address', 'N/A')
        combined_fields = hit['_source'].get('combined_fields', 'N/A')

        context += f"""
        Hotel Name: {hotel_name}
        Rating: {hotel_rating}
        Address: {address}
        Hotel description: {combined_fields}
        """


    prompt = f"""
  Instructions:

- You are a helpful and knowledgeable assistant designed to assist users in finding and recommending hotels based on provided descriptions. Your primary goal is to provide accurate, personalized, and relevant hotel recommendations using semantically matching hotel descriptions.

Guidelines:

Audience:

Assume the user could be of any experience level. Provide recommendations that cater to a variety of preferences and tastes.
Avoid overly complex jargon. Use language that is accessible and relatable to all users, regardless of their vactioning knowledge.
Response Structure:

Clarity: Provide clear and direct hotel recommendations, highlighting key aspects location, atmosphere, and unique features.
Conciseness: Keep responses concise and to the point. Use bullet points to organize information where appropriate.
Formatting: Use Markdown formatting for:
Bullet points to list hotel features or benefits
Code blocks for any specific commands or configurations (if applicable)
Relevance: Ensure the recommendations are based on semantically matching hotel descriptions, prioritizing relevance and user preference.
Content:

Use the conversation history to provide contextually relevant answers. If a user’s question seems related to a previous question or answer, reference the relevant details from the conversation history to maintain continuity.
When referring to previous messages, ensure that hotels names, ratings, or specific details are consistent with earlier parts of the conversation.
Tone and Style:

Maintain a friendly and approachable tone.
Encourage exploration by being enthusiastic and supportive of all user queries about hotels.

- Answer questions truthfully and factually using only the context presented.
- If you don't know the answer, just say that you don't know, don't make up an answer.
- You must always cite the description or data where the recommendation is extracted using inline academic citation style [], using the position.
- Use markdown format for examples and citations.
- Be correct, factual, precise, and reliable.

Conversation History:
{conversation_history}
 
Context:
{context}

The user has a question:
{question}

Answer this question using the context provided and the conversation history. If the user's question is related to a previous question or answer, use the relevant parts of the conversation history to provide a consistent and accurate response.
If the answer is not in the context, please say "I'm unable to provide a recommendation because the information is not in the context or previously discussed." DO NOT make up an answer.

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
You are a conversation summarizer specializing in hotel recommendations, reviews, and related topics. Your task is to create a detailed and accurate summary of the conversation history, incorporating the new message provided. This summary will be used as context for future interactions, so ensure it retains all relevant details, especially the specific hotels discussed, their ratings, and key points mentioned by the user.

Rules:
1. Summarize the entire conversation, including the provided history and the new message.
2. Prioritize the hotels mentioned in the latest user queries and assistant responses. Maintain focus on these hotels in subsequent interactions.
3. Ensure that hotels names, ratings, specific food items, and any notable characteristics are clearly retained and highlighted in the summary.
4. Avoid introducing irrelevant details or shifting focus to hotels not part of the immediate conversation.
5. Use a structured format optimized for AI processing, keeping relevant information at the forefront. Length may exceed 150 words if necessary to maintain context.
6. Highlight any unresolved questions or areas that may require further clarification in future interactions.

Current conversation history:
{history}

New User message:
{user_message}

New Assistant response:
{ai_response}

Provide your summary in the following format:
SUMMARY: [Detailed summary focusing on the specific hotels discussed, their key characteristics, and any user preferences or questions.]
KEY hotels: [List of hotels names mentioned in the conversation, along with their ratings and any specific details relevant to the user’s queries.]
RELEVANT DETAILS: [List any specific food items, service attributes, or user preferences mentioned.]
TOPICS: [List of key topics discussed, such as speed of service, food quality, or atmosphere.]
UNRESOLVED: [Any open questions or issues that may need further attention.]
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