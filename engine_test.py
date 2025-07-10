import json
import os
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.pregel import Pregel
from types_test import LLMParams, InputMessage
from loading_graph import loading_graph

import asyncio

async def get_agent_http_streamed_result(graph: Pregel, message: InputMessage):
    files_prompt_part = ""
    if message.input_urls:
        input_urls_str = "\n".join([f"- {url}" for url in message.input_urls])
        files_prompt_part += f"""

- I have provided the following input URLs, for files you may need to process:
{input_urls_str}
"""
    
    enhanced_human_message = HumanMessage(content=message.message + files_prompt_part)
    inputs = {"messages": [enhanced_human_message]}

    # Prompt system ultra-directif
    sys_prompt = f"""You are a helpful assistant equipped with tools. You MUST respond in French since this is a test.

**CRITICAL TOOL USAGE RULES:**
- You MUST ALWAYS use `test_slow_tool` when asked about simulation, slow processing, or test content.
- You MUST call `test_slow_tool` with empty arguments `{{}}` if no URLs are provided.
- NEVER ask for URLs - just use the tool with empty arguments.
- NEVER ask follow-up questions - execute the tool immediately.

**EXAMPLES:**
- "Simule un traitement" → Call test_slow_tool({{}})
- "Génère du contenu" → Call test_slow_tool({{}})
- "Test slow" → Call test_slow_tool({{}})

**MANDATORY BEHAVIOR:**
- If user mentions simulation, slow processing, or test content → Use test_slow_tool({{}})
- If user asks for any kind of test → Use test_slow_tool({{}})
- Always provide empty object {{}} as argument if no URLs given.

You ALWAYS respond in valid Markdown syntax."""

    messages_with_sys_prompt = {
        "messages": [
            SystemMessage(content=sys_prompt),
            *inputs["messages"],
        ]
    }

    async for result in get_agent_streamed_result(graph, messages_with_sys_prompt):
        if result["type"] == "chunk" and result["content"].strip() != "":
            yield f"data: {json.dumps({'type': 'chunk', 'content': result['content']})}\n\n"
        elif result["type"] == "end" and result["content"].strip() != "":
            yield f"data: {json.dumps({'type': 'end', 'content': result['content']})}\n\n"
        elif result["type"] == "loading":
            yield f"data: {json.dumps({'type': 'loading', 'content': result['content']})}\n\n"
    yield "data: [DONE]\n\n"

async def get_agent_streamed_result(graph: Pregel, inputs: dict[str, list[BaseMessage]]):
    first_loading_message_sent = False
    tool_executing = False
    current_tool_name = None

    async def stream_loading_messages_task(tool_name: str):
        """Task to stream loading messages"""
        loading_inputs = {
            "messages": [],
            "tool_name": tool_name,
            "message_count": 0
        }
        
        try:
            message_count = 0
            async for loading_event in loading_graph.astream(loading_inputs):
                if "loading_message" in loading_event:
                    loading_message_data = loading_event["loading_message"]
                    if "messages" in loading_message_data and loading_message_data["messages"]:
                        message_content = loading_message_data["messages"][-1].content
                        # print(f"--- Yielding loading message {message_count + 1}: {message_content}---", flush=True)
                        
                        # Yield the loading message
                        yield {
                            "content": message_content,
                            "type": "loading",
                        }
                        message_count += 1
                        
                        # Wait between messages
                        await asyncio.sleep(2)
                        
                        # Limit number of messages
                        if message_count >= 3:
                            break
                            
        except asyncio.CancelledError:
            # print("--- Loading messages task cancelled ---", flush=True)
            raise

    async for event in graph.astream_events(inputs):
        event_kind = event["event"]
        
        # Initial loading message
        if event_kind == "on_chain_start" and not first_loading_message_sent:
            first_loading_message_sent = True
            yield {
                "content": "loading...",
                "type": "loading",
            }
        
        # Tool execution start
        elif event_kind == "on_tool_start":
            tool_executing = True
            current_tool_name = event.get("name", "default")
            # print(f"--- Tool started: {current_tool_name}---", flush=True)
            
            # ✅ Streamer directement les messages d'attente dans le flux principal
            loading_inputs = {
                "messages": [],
                "tool_name": current_tool_name,
                "message_count": 0
            }
            
            message_count = 0
            async for loading_event in loading_graph.astream(loading_inputs):
                # Vérifier si l'outil est toujours en cours
                if not tool_executing:
                    # print("--- Tool no longer executing, stopping loading messages ---", flush=True)
                    break
                    
                if "loading_message" in loading_event:
                    loading_message_data = loading_event["loading_message"]
                    if "messages" in loading_message_data and loading_message_data["messages"]:
                        message_content = loading_message_data["messages"][-1].content
                        # print(f"--- Yielding loading message {message_count + 1}: {message_content}---", flush=True)
                        
                        # ✅ Yield directement dans le flux principal
                        yield {
                            "content": message_content,
                            "type": "loading",
                        }
                        message_count += 1
                        
                        # Attendre entre les messages
                        await asyncio.sleep(2)
                        
                        # Limiter le nombre de messages
                        if message_count >= 3:
                            break
            
        # Tool execution end
        elif event_kind == "on_tool_end":
            # print("--- Tool execution ended ---", flush=True)
            tool_executing = False
            current_tool_name = None
        
        # Chat model streaming (normal response)
        elif event_kind == "on_chat_model_stream":
            # ✅ Arrêter immédiatement les messages d'attente
            if tool_executing:
                # print("--- Stopping loading messages due to chat model stream ---", flush=True)
                tool_executing = False
                current_tool_name = None
            
            content = event["data"]["chunk"].content
            yield {
                "content": content,
                "type": "chunk",
            }
        
        # Chat model end
        elif event_kind == "on_chat_model_end":
            yield {
                "content": event["data"]["output"].content,
                "type": "end",
            }

def get_llm_with_params(agent_params: LLMParams):
    """Returns the appropriate LLM instance based on the given parameters."""
    if (
        agent_params.privacy_level == "cloud_public_model"
        and agent_params.use_case == "simple_chat"
    ):
        # ✅ Utiliser exclusivement GOOGLE_AI_STUDIO_API_KEY
        api_key = os.getenv("GOOGLE_AI_STUDIO_API_KEY")
        
        if not api_key:
            raise ValueError("GOOGLE_AI_STUDIO_API_KEY environment variable not set")
            
        return ChatGoogleGenerativeAI(
            google_api_key=api_key,
            model="gemini-2.5-flash-lite-preview-06-17",
            temperature=0.0,
        )