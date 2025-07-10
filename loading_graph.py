import asyncio
import time
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage
from types_test import GraphWithMessagesState
from typing import Dict, List, Optional


class LoadingGraphState(GraphWithMessagesState):
    """
    State for the loading graph with additional context about the operation.
    """
    tool_name: Optional[str] = None
    message_count: int = 0

def get_loading_message(tool_name: str, message_count: int) -> str:
    """
    Generate a contextual message based on the tool being used and message sequence.
    
    Architecture Decision: Using markdown formatting for consistency with other graphs
    in the Sp0tonV2-AI project. Each tool has contextual progress messages with
    appropriate emoji and markdown formatting.
    
    Implementation Detail: Messages progress from initial processing to completion,
    providing clear user feedback during long-running operations.
    """
    messages_map = {
        "generate_image": [
            "🎨 **Image Generation** - Creating optimized prompt...",
            "🎨 **Image Generation** - Processing your request... Almost done!",
            "🎨 **Image Generation** - Finalizing your image... *Last adjustments in progress*"
        ],
        "text2video": [
            "🎬 **Video Generation** - Analyzing video prompt...",
            "🎬 **Video Generation** - Creating your video... *Processing frames*",
            "🎬 **Video Generation** - Finalizing your video... *Last renders in progress*"
        ],
        "transcribe_audio": [
            "🎵 **Audio Transcription** - Analyzing audio file...",
            "🎵 **Audio Transcription** - Processing transcription... *Voice recognition in progress*",
            "🎵 **Audio Transcription** - Finalizing transcription... *Last quality checks*"
        ],
        "test_slow_tool": [ 
            "⏳ **Simulation d'outil** - Initialisation en cours...",
            "⏳ **Simulation d'outil** - Traitement des données... *Analyse en cours*",
            "⏳ **Simulation d'outil** - Finalisation du résultat... *Dernières vérifications*"
        ],
        "default": [
            "⏳ **Processing** - Analyzing your request...",
            "⏳ **Processing** - We're almost there... *Data processing*",
            "⏳ **Processing** - Last step... *Finalizing the result*"
        ]
    }
    messages = messages_map.get(tool_name, messages_map["default"])
    return messages[min(message_count, len(messages) - 1)]

async def loading_message_node(state: LoadingGraphState):
    """
    Generate and send formatted loading messages with markdown support.
    
    Implementation Detail: Uses markdown formatting for consistency with other
    graphs in the project. Includes 2-second delays to provide natural pacing
    for user feedback during long operations.
    """
    
    message = get_loading_message(
        state.tool_name or "default",
        state.message_count  
    )

    print(f"🔍 LOADING_GRAPH: Generated message: {message}", flush=True)

    # 2 second delay before first message
    await asyncio.sleep(2)

    return {
        "messages": [AIMessage(content=message)],
        "message_count": state.message_count + 1,
    }

async def should_continue_loading(state: LoadingGraphState) -> str:
    """
    Determine if the loading should continue based on message count.
    
    Best Practice: Limits to 3 messages maximum to avoid overwhelming the user
    while providing sufficient progress feedback.
    """    
    if state.message_count >= 3:
        return "end"
    
    return "continue"


def create_loading_graph():
    """
    Create the loading graph with markdown-formatted messages.
    
    Architecture Decision: Single-node graph with conditional looping provides
    clean separation of concerns while maintaining simplicity. Messages are
    formatted with markdown for consistency with other project graphs.
    """
    workflow = StateGraph(LoadingGraphState)
    
    workflow.add_node("loading_message", loading_message_node)
    
    workflow.set_entry_point("loading_message")
    
    workflow.add_conditional_edges(
        "loading_message",
        should_continue_loading,
        {
            "continue": "loading_message",
            "end": END
        }
    )
    
    return workflow.compile()

loading_graph = create_loading_graph()