from abc import ABC
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage
from pydantic import BaseModel, Field
from typing import Annotated, List, Literal, Optional

class GraphWithMessagesState(BaseModel):
    messages: Annotated[List[BaseMessage], add_messages]
    input_urls: List[str] = Field(default=[])
    generation_output_url: str | None = None
    output_generation_path: str | None = None
    sp0ton_users_api_url: str | None = None

class LLMParams(BaseModel):
    privacy_level: Literal["cloud_public_model"] = Field(default="cloud_public_model")
    use_case: Literal["simple_chat"] = Field(default="simple_chat")

class InputMessage(BaseModel):
    agent_params: LLMParams | None = None
    input_urls: Optional[List[str]] = Field(default=[])
    message: str

class UrlsPayload(BaseModel):
    input_urls: Optional[List[str]] = Field(
        default=[],
        description="The URLs of the files to process (optional, can be empty)"
    )

class LLMSingleton(ABC):
    """Abstract base class for singleton classes that contain an LLM instance."""

    # properties will be set by concrete implementations
    _instance = None
    llm = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LLMSingleton, cls).__new__(cls)
            cls._instance.__init__()
        return cls._instance

    def __init__(self):
        pass