import time
from langgraph.graph import StateGraph, END
from langchain_core.messages import AIMessage, HumanMessage
from types_test import GraphWithMessagesState

def simulate_slow_tool_node(state: GraphWithMessagesState):
    """
    Simulate a slow tool which takes 5 seconds to return a result.
    """
    print("--- Node: Simulate slow tool ---", flush=True)

    try:

        time.sleep(5)

        result_content = "Ceci est un test de contenu"
        print(f"--- Tool simulation completed: {result_content} ---", flush=True)

        return {
            "messages": [AIMessage(content=result_content)]
        }
    except Exception as e:
        error_message = f"Error in simulate_slow_tool_node: {e}"
        print(error_message, flush=True)
        return {
            "messages": [
                AIMessage(content="I encountered an error during the simulation. Please try again.")
            ]
        }

def create_slow_tool_graph():
    """Create a test tool graph."""
    workflow = StateGraph(GraphWithMessagesState)
    workflow.add_node("simulate_slow_tool", simulate_slow_tool_node)
    workflow.set_entry_point("simulate_slow_tool")
    workflow.add_edge("simulate_slow_tool", END)
    return workflow.compile()

slow_tool_graph = create_slow_tool_graph()
    