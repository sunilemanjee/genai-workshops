import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from backend.services import search_service, bedrock_service
from fastapi import WebSocket, APIRouter
from elasticsearch import NotFoundError

router = APIRouter()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


class SearchQuery(BaseModel):
    query: str
    context_type: str


@router.post("/search")
async def perform_search(search_query: SearchQuery):
    logging.info(f"Received query: {search_query.query}")
    try:
        prompt_context = search_service.semantic_search(search_query.query, search_query.context_type)
        llm_response = bedrock_service.query_aws_bedrock(prompt_context)
        return {"prompt": prompt_context, "llm_response": llm_response}
    except Exception as e:
        logging.error(f"Error in processing search: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


class ChatMessage(BaseModel):
    message: str


@router.websocket_route("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    convo_history = bedrock_service.init_conversation_history()

    try:
        while True:
            # Receive the message from the client (user's question)
            data = await websocket.receive_text()
            logging.debug(f"Raw data received: {data}")

            # Parse the user's question
            chat_message = ChatMessage.parse_raw(data)
            logging.info(f"Received message: {chat_message.message}")

            # create Prompt to generate retriever
            retriever_generate_prompt = search_service.create_retriever_prompt(chat_message.message, convo_history)
            await websocket.send_json({
                "type": "verbose_info",
                "text": f"Prompt to Generate Semantic or Lexical retriever\n\n{retriever_generate_prompt}"
            })
            logging.info(f"Prompt to generate retriever: {retriever_generate_prompt}")

            # Call LLM to generate retriever query
            retriever_info = bedrock_service.query_aws_bedrock_nonstreaming(retriever_generate_prompt)
            logging.info(f"Retriever info: {retriever_info}")
            logging.info(f"retriever_info type: {type(retriever_info)}")

            # query Elasticsearch using generated retriever query
            try:
                retriever_query = retriever_info['query']
                retriever_index = retriever_info['index']
                retriever_type = retriever_info['search_type']

                await websocket.send_json({
                    "type": "verbose_info",
                    "text": f"Generated Retriever of type {retriever_type}\n\n{retriever_query}"
                })

                context_unparsed = search_service.perform_es_search(
                    retriever_query,
                    retriever_index,
                    chat_message.message
                )
            except NotFoundError as e:
                state = retriever_index.split('_')[1]  # Assuming the index is in the format 'notary_statename'
                error_message = f"I'm sorry but I don't seem to have Notary info for {state}."
                await websocket.send_json({
                    "type": "error_message",
                    "text": error_message
                })
                logging.error(f"Index not found for {retriever_index}: {str(e)}")
                continue  # or use 'break' if you want to stop the loop entirely
            except Exception as e:
                logging.error(f"Error in Elasticsearch search: {str(e)}")
                try:
                    retriever_info['query']
                except Exception as e:
                    logging.error(f"Error in retriever_query: {str(e)}")
                try:
                    retriever_info['index']
                except Exception as e:
                    logging.error(f"Error in retriever_index: {str(e)}")
                finally:
                    logging.error(f"retriever_info keys: {retriever_info.keys()}")
                logging.info("Falling back to backup query")
                context_unparsed = search_service.perform_es_search_backup(
                    chat_message.message,
                    "notary_*"
                )
            # logging.info(f"Context unparsed: {context_unparsed}")

            # Parse the results from Elasticsearch into context
            prompt_context, context = search_service.create_prompt_context(context_unparsed,
                                                                           "passage",  # TODO hardcoded for now
                                                                           retriever_type
                                                                           )

            # Send the contextual data back to the UI before making LLM calls
            logging.debug(f"Sending context back to UI: {context}")
            tmp_context = ('\n---------------------------------------------------------\n\n'
                           '---------------------------------------------------------\n\n\n').join(context)
            await websocket.send_json({
                "type": "verbose_info",
                "text": f"Context gathered from "
                        f"Elasticsearch\n\n---------------------------------------------------------\n\n"
                        f"---------------------------------------------------------\n\n{tmp_context}"
            })

            # Construct the full prompt for the LLM
            logging.info("Creating prompt for LLM")
            full_prompt = search_service.create_prompt_user_question(prompt_context,
                                                                     chat_message.message
                                                                     )
            logging.debug(f"Full prompt for LLM: {full_prompt}")

            # Query the LLM and stream results back to the client
            # build a response from the stream to add to the conversation history
            response = ''
            async for chunk in bedrock_service.query_aws_bedrock_stream(full_prompt):
                logging.debug(f"Chunk received from LLM: {chunk}")

                if isinstance(chunk, dict):
                    if chunk['type'] == 'content_block_delta':
                        response += chunk['delta']['text']
                    # elif chunk['type'] == 'message_stop':
                    #     #{'type': 'message_stop', 'amazon-bedrock-invocationMetrics': {'inputTokenCount': 2614, 'outputTokenCount': 247, 'invocationLatency': 7209, 'firstByteLatency': 886}}
                    #
                    #     pass
                    logging.debug(f"Sending chunk to client: {chunk}")
                    await websocket.send_json(chunk)

                else:
                    logging.error(f"Received non-dict chunk from LLM stream: {chunk}")

            # add filtering info to the response
            if retriever_index.split('_')[1] == "*":
                state_searched = "All States"
            else:
                state_searched = retriever_index.split('_')[1]
            state_response = f"Response gathered from {state_searched}"
            await websocket.send_json({
                "type": "verbose_info",
                "text": state_response
            })

            # Add the user's question and the LLM response to the conversation history
            logging.info("Building conversation history")
            convo_history = bedrock_service.build_conversation_history(history=convo_history,
                                                                       user_message=chat_message.message,
                                                                       ai_response=response
                                                                       )
            logging.debug(f"Conversation history: {convo_history}")
            tmp_convo_hist = '\n---------------------------------------------------------\n\n'.join(
                [str(h) for h in convo_history])
            await websocket.send_json({
                "type": "verbose_info",
                "text": f"Conversation history updated:\n\n{tmp_convo_hist}"
            })

    except Exception as e:
        logging.error("WebSocket encountered an error:", exc_info=True)
        await websocket.close(code=1001)
