import json
import logging
import boto3
from botocore.config import Config as BotoConfig
from botocore.exceptions import ClientError
import os

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


# from backend.config.config import Config

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


def get_bedrock_client():
    logging.info("Setting up AWS Bedrock client")
    try:
        session = boto3.Session(
            # aws_access_key_id=Config.AWS_ACCESS_KEY_ID,
            # aws_secret_access_key=Config.AWS_SECRET_ACCESS_KEY,
            # region_name=Config.AWS_DEFAULT_REGION
        )
        boto_config = BotoConfig(connect_timeout=15, read_timeout=45)
        return session.client("bedrock-runtime", config=boto_config)

        # return session.client("bedrock-runtime")
    except Exception as e:
        print(f"Error setting up AWS Bedrock client: {str(e)}")
        return None


def query_aws_bedrock(message):
    bedrock_client = get_bedrock_client()
    if not bedrock_client:
        return "Error: Bedrock client not configured properly."

    try:
        # Prepare the body with Claude-specific parameters
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": message
                            # "text": "How many ducks have more than 2 feet?"
                        }
                    ]
                }
            ]
        }
        logging.info(f"calling AWS Bedrock invoke_model_with_response_stream: {body} ")
        response = bedrock_client.invoke_model_with_response_stream(
            modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        # Process the streaming response
        full_response = ""
        # logging.info(f"Processing streaming response: {response}")
        stream = response.get('body')
        # logging.info(f"Stream: {stream}")
        for event in stream:
            logging.info(f'event: {event}')
            chunk = json.loads(event["chunk"]["bytes"])
            if 'text_delta' in chunk:
                full_response += chunk['text_delta']['text']

        return full_response  # Return the full response text
    except ClientError as e:
        logging.error(f"Error querying AWS Bedrock: {e}")
        return f"Sorry, I couldn't process your request at the moment due to: {str(e)}"


# async def query_aws_bedrock_stream(message):
#     bedrock_client = get_bedrock_client()
#     if not bedrock_client:
#         raise Exception("Error: Bedrock client not configured properly.")
#
#     try:
#         body = {
#             "anthropic_version": "bedrock-2023-05-31",
#             "max_tokens": 2000,
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": [{"type": "text", "text": message}]
#                 }
#             ]
#         }
#         logging.info(f"Calling AWS Bedrock invoke_model_with_response_stream: {body}")
#         response = bedrock_client.invoke_model_with_response_stream(
#             modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
#             body=json.dumps(body),
#             contentType="application/json",
#             accept="application/json",
#         )
#
#         stream = response.get('body')
#         logging.info(f"Stream: {stream}")
#         async for event in stream:
#             logging.info(f'event: {event}')
#             yield event
#
#     except ClientError as e:
#         logging.error(f"Error querying AWS Bedrock: {e}")
#         raise Exception(f"Sorry, I couldn't process your request at the moment due to: {str(e)}")

# def query_aws_bedrock(message):
#     bedrock_client = get_bedrock_client()
#     if not bedrock_client:
#         return "Error: Bedrock client not configured properly."
#
#     try:
#         # Prepare the body with Claude-specific parameters
#         body = {
#             "anthropic_version": "bedrock-2023-05-31",
#             "max_tokens": 2000,
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": [{"type": "text", "text": message}]
#                 }
#             ]
#         }
#         logging.info(f"calling AWS Bedrock invoke_model_with_response_stream: {body}")
#         response = bedrock_client.invoke_model_with_response_stream(
#             modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
#             body=json.dumps(body),
#             contentType="application/json",
#             accept="application/json",
#         )
#
#         # Process the streaming response
#         stream = response.get('body')
#         logging.info(f"Stream: {stream}")
#         async for event in stream:
#             logging.info(f'event: {event}')
#             if 'chunk' in event:
#                 # Decode bytes to string and then load as JSON
#                 decoded_chunk = event['chunk']['bytes'].decode('utf-8')
#                 json_chunk = json.loads(decoded_chunk)
#                 yield json_chunk  # Yield the JSON object instead of raw event
#     except ClientError as e:
#         logging.error(f"Error querying AWS Bedrock: {e}")
#         return f"Sorry, I couldn't process your request at the moment due to: {str(e)}"
#

# async def query_aws_bedrock_stream(message):
#     bedrock_client = get_bedrock_client()
#     if not bedrock_client:
#         raise Exception("Error: Bedrock client not configured properly.")
#
#     try:
#         body = {
#             "anthropic_version": "bedrock-2023-05-31",
#             "max_tokens": 2000,
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": [{"type": "text", "text": message}]
#                 }
#             ]
#         }
#         logging.info(f"Calling AWS Bedrock invoke_model_with_response_stream: {body}")
#         # This assumes you have an asynchronous method to invoke the model with response stream
#         response = await bedrock_client.invoke_model_with_response_stream(
#             modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
#             body=json.dumps(body),
#             contentType="application/json",
#             accept="application/json",
#         )
#
#         stream = response.get('body')
#         logging.info(f"Stream: {stream}")
#         async for event in stream:
#             logging.info(f'event: {event}')
#             yield event
#
#     except ClientError as e:
#         logging.error(f"Error querying AWS Bedrock: {e}")
#         raise Exception(f"Sorry, I couldn't process your request at the moment due to: {str(e)}")

import asyncio


async def async_event_stream_wrapper(sync_stream):
    """
    Asynchronously wraps a synchronous event stream to make it compatible with 'async for' loops.
    """
    try:
        for event in sync_stream:
            yield event  # Yield the event for asynchronous processing
            await asyncio.sleep(0)  # Release control to the event loop
    finally:
        sync_stream.close()  # Ensure the stream is properly closed after iteration


async def query_aws_bedrock_stream(message):
    bedrock_client = get_bedrock_client()
    if not bedrock_client:
        raise Exception("Error: Bedrock client not configured properly.")

    try:
        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": [{"type": "text", "text": message}]}]
        }
        logging.info(f"Calling AWS Bedrock invoke_model_with_response_stream: {body}")
        response = bedrock_client.invoke_model_with_response_stream(
            modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        stream = response.get('body')
        logging.info(f"Stream: {stream}")

        # Use the wrapper to handle the synchronous stream asynchronously
        async for event in async_event_stream_wrapper(stream):
            logging.info(f'Event: {event}')
            if 'chunk' in event:
                decoded_chunk = event['chunk']['bytes'].decode('utf-8')
                json_chunk = json.loads(decoded_chunk)
                yield json_chunk  # Yield the JSON object instead of raw event
    except ClientError as e:
        logging.error(f"Error querying AWS Bedrock: {e}")
        raise Exception(f"Sorry, I couldn't process your request at the moment due to: {str(e)}")


def query_aws_bedrock_nonstreaming(message):
    bedrock_client = get_bedrock_client()
    if not bedrock_client:
        raise Exception("Error: Bedrock client not configured properly.")

    try:

        body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": [{"type": "text", "text": message}]}]
        }
        response = bedrock_client.invoke_model(
            modelId="anthropic.claude-3-5-sonnet-20240620-v1:0",
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )

        # Decode the response body
        response_body = json.loads(response['body'].read().decode('utf-8'))
        logging.info(f"query_aws_bedrock_nonstreaming Response body: {response_body}")
        try:
            generated_retriever_info = json.loads(response_body['content'][0]['text'])
            logging.info(f"Generated Retriever Info: {generated_retriever_info}")
            logging.info(f"Generated Retriever Info type: {type(generated_retriever_info)}")
            return generated_retriever_info
        except json.decoder.JSONDecodeError as e:
            # todo make an argument to say if this call is for the retriever (dict with json decode needed) or summary (text)
            history_summary = response_body['content'][0]['text']
            logging.info(f"History Summary: {history_summary}")
            return history_summary

    except Exception as e:
        logging.error(f"Error querying AWS Bedrock: {e}")
        raise Exception(f"Sorry, I couldn't process your request at the moment due to: {str(e)}")


# function to build conversation history
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
        summary = query_aws_bedrock_nonstreaming(summary_prompt)
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


# Example usage
if __name__ == "__main__":
    result = query_aws_bedrock("What is the legal age for drinking in California?",
                               [{"role": "USER", "message": "Tell me about US state laws"}])
    print(result)
