import asyncio
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv
import os

load_dotenv()

# ✅ Vérifier seulement GOOGLE_AI_STUDIO_API_KEY
if not os.getenv("GOOGLE_AI_STUDIO_API_KEY"):
    raise ValueError("GOOGLE_AI_STUDIO_API_KEY environment variable not set")

from main_graph import main_agent
from engine_test import get_agent_streamed_result, get_agent_http_streamed_result
from types_test import InputMessage

async def test_loading_tool():
    """Test loading tool with proper prompt to trigger test_slow_tool."""
    print("=== TEST 1: Loading tool ===")

    # ✅ Prompt plus direct
    test_message = HumanMessage(content="Simule un traitement lent en utilisant test_slow_tool avec l'URL https://www.example.com")
    inputs = {"messages": [test_message]}

    print("Input:", test_message.content)
    print("--- Start streaming ---")

    # ✅ CORRECTION: Utiliser la même logique que les autres tests
    async for result in get_agent_streamed_result(main_agent, inputs):
        print(f"Result: {result}")
    
    print("--- End streaming ---\n")


# async def test_basic_streaming():
#     """Test basic streaming with the compiled graph."""
#     print("=== TEST 1: Basic graph streaming ===")
    
#     test_message = HumanMessage(content="Hello, can you tell me about streaming in Python in 2 sentences?")
#     inputs = {"messages": [test_message]}
    
#     print("Input:", test_message.content)
#     print("--- Start streaming ---")
    
#     async for chunk in main_agent.astream(inputs):
#         print(f"Chunk: {chunk}")
    
#     print("--- End streaming ---\n")


# async def test_with_engine_logic():
#     """Test with get_agent_streamed_result logic (events)."""
#     print("=== TEST 2: Streaming with engine.py logic ===")
    
#     test_message = HumanMessage(content="Explain LangGraph to me in French.")
#     inputs = {"messages": [test_message]}
    
#     print("Input:", test_message.content)
#     print("--- Streaming with get_agent_streamed_result ---")
    
#     async for result in get_agent_streamed_result(main_agent, inputs):
#         print(f"Stream result: {result}")
    
#     print("--- End streaming ---\n")


# async def test_http_streaming():
#     """Test HTTP streaming with SSE format."""
#     print("=== TEST 3: HTTP Streaming (SSE) ===")
    
#     message = InputMessage(
#         message="What is asynchronous streaming? Answer in French.",
#         input_urls=[]
#     )
    
#     print("Input:", message.message)
#     print("--- HTTP streaming ---")
    
#     async for sse_chunk in get_agent_http_streamed_result(main_agent, message):
#         print(f"SSE: {sse_chunk.strip()}")
    
#     print("--- End HTTP streaming ---\n")


# async def test_conversation_flow():
#     """Test conversation flow to verify state management."""
#     print("=== TEST 4: Conversation flow ===")
    
#     # First interaction
#     first_message = HumanMessage(content="Hello! My name is Alice.")
#     inputs = {"messages": [first_message]}
    
#     print("Message 1:", first_message.content)
#     print("--- First response ---")
    
#     # Get complete response
#     final_state = None
#     async for chunk in main_agent.astream(inputs):
#         print(f"Chunk 1: {chunk}")
#         final_state = chunk
    
#     # Second interaction with history
#     if final_state and "messages" in final_state:
#         second_message = HumanMessage(content="What is my name?")
#         inputs_with_history = {
#             "messages": final_state["messages"] + [second_message]
#         }
        
#         print("\nMessage 2:", second_message.content)
#         print("--- Response with history ---")
        
#         async for chunk in main_agent.astream(inputs_with_history):
#             print(f"Chunk 2: {chunk}")
    
#     print("--- End conversation ---\n")


# async def test_pregel_events():
#     """
#     Test to understand Pregel events.
    
#     This function demonstrates how astream_events() captures
#     all graph events during execution.
#     """
#     print("=== TEST 5: Pregel Events ===")
    
#     test_message = HumanMessage(content="Say hello to me.")
#     inputs = {"messages": [test_message]}
    
#     print("Input:", test_message.content)
#     print("--- Pregel events ---")
    
#     async for event in main_agent.astream_events(inputs):
#         event_kind = event["event"]
#         print(f"Event: {event_kind}")
        
#         if event_kind == "on_chat_model_stream":
#             content = event["data"]["chunk"].content
#             if content:
#                 print(f"  → Chunk: '{content}'")
                
#         elif event_kind == "on_chat_model_end":
#             content = event["data"]["output"].content
#             print(f"  → End: '{content[:50]}...'")
            
#         elif event_kind == "on_chain_start":
#             print(f"  → Chain start: {event['name']}")
            
#         elif event_kind == "on_chain_end":
#             print(f"  → Chain end: {event['name']}")
    
#     print("--- End Pregel events ---\n")


async def test_loading_system():
    """Test the complete loading system with events."""
    print("=== TEST 2: Complete loading system ===")

    test_message = HumanMessage(content="Simule un traitement lent avec l'outil test_slow_tool et l'URL https://www.example.com et génère du contenu de test")
    inputs = {"messages": [test_message]}

    print("Input:", test_message.content)
    print("--- Start streaming with events ---")

    async for result in get_agent_streamed_result(main_agent, inputs):
        print(f"Result: {result}")
    
    print("--- End streaming ---\n")

async def test_http_loading():
    """Test HTTP streaming with loading messages."""
    print("=== TEST 3: HTTP streaming with loading ===")

    message = InputMessage(
        message="Simule un traitement lent avec l'outil test_slow_tool et l'URL https://www.example.com et génère du contenu de test",
        input_urls=[]
    )

    print("Input:", message.message)
    print("--- HTTP streaming with loading ---")

    async for sse_chunk in get_agent_http_streamed_result(main_agent, message):
        print(f"SSE: {sse_chunk.strip()}")
    
    print("--- End HTTP streaming ---\n")

async def run_all_tests():
    """Execute all tests in logical order."""
    print("🚀 STARTING LOADING SYSTEM TESTS")
    print("=" * 50)
    
    try:
        await test_loading_tool()
        await test_loading_system()
        await test_http_loading()
        
        print("✅ ALL TESTS COMPLETED SUCCESSFULLY")
        
    except Exception as e:
        print(f"❌ ERROR DURING TESTS: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    """Entry point to run tests from console."""
    asyncio.run(run_all_tests())