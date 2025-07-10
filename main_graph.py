# this graph is a test version of the main_graph from sp0tOnV2AI
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode
from typing import Literal
import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Imports après le chargement du .env
from types_test import LLMParams, GraphWithMessagesState, LLMSingleton
from engine_test import get_llm_with_params

from slow_tool import slow_tool

tools = [slow_tool]


class MainAgent(LLMSingleton):
    """
    Singleton class for managing the main LLM instance.

    Usage:
        # Get the singleton instance
        llm_instance = MainAgentSingleton()

        # All subsequant calls return the same instance
        same_instance = MainAgentSingleton()
        assert_llm_instance is same_instance  # True
    """

    def __init__(self):
        if self.llm is None:
            agent = get_llm_with_params(
                LLMParams(
                    privacy_level="cloud_public_model",
                    use_case="simple_chat",
                )
            )
            # for the test, we don't bind any tools but keep the structure
            self.llm = agent.bind_tools(tools, tool_choice="auto") if tools else agent


def should_continue_node(state: GraphWithMessagesState) -> Literal["tools", "__end__"]:
    """
    Determine if the agent should continue or end the conversation.
    """
    print("should_continue_node", state.messages[-1].content, flush=True)
    return "tools" if (hasattr(state.messages[-1], 'tool_calls') and state.messages[-1].tool_calls) else "__end__"


async def stream_from_agent_node(state: GraphWithMessagesState):
    """
    Stream the answer to the given prompt.
    """
    agent = MainAgent()
    stream = agent.llm.astream(state.messages)
    async for chunk in stream:
        print("stream_from_agent_node", chunk.content, flush=True)
        yield {"messages": [chunk]}


# node that will automatically execute the tools for us
tool_node = ToolNode(tools=tools)

workflow = StateGraph(GraphWithMessagesState)

workflow.add_node("agent_node", stream_from_agent_node)
workflow.add_node("tools", tool_node)

workflow.set_entry_point("agent_node")

workflow.add_conditional_edges(
    "agent_node",
    should_continue_node,
    {
        "tools": "tools",
        "__end__": END,
    },
)

# after the tools are executed, route back to the agent node to respond to the user
workflow.add_edge("tools", "agent_node")

main_agent = workflow.compile()
