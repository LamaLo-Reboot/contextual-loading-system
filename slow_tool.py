from langchain_core.tools import tool
from typing import List, Optional
from slow_tool_graph import slow_tool_graph
from types_test import UrlsPayload

@tool("slow_tool", args_schema=UrlsPayload)
def slow_tool(input_urls: Optional[List[str]] = None) -> str:
    """Tool for test which simulates a slow operation (5 seconds)."""
    if input_urls is None:
        input_urls = []
    return slow_tool_func(input_urls)

def slow_tool_func(input_urls: Optional[List[str]] = None) -> str:
    res = slow_tool_graph.invoke({
        "input_urls": input_urls,
        "message": []
    })
    print("slow_tool", res["messages"][-1].content, flush=True)
    return res["messages"][-1].content