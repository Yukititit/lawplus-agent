from __future__ import annotations
from typing import TypedDict, Annotated, List
from langchain_core.tools import tool
from dataclasses import dataclass, field
from typing import Any, Dict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages 
from dotenv import load_dotenv
load_dotenv()

from agent.nodes import case_assistant

class Context(TypedDict):
    """Context parameters for the agent.
    Set these when creating assistants OR when invoking the graph.
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """
    my_configurable_param: str


@dataclass
class State:
    """Input state for the agent.

    Defines the initial structure of incoming data.
    See: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
    """
    
    messages: Annotated[List[BaseMessage], add_messages] = field(default_factory=list)
    # output_text: str = ""


graph = (
    StateGraph(State, context_schema=Context)
    .add_node(case_assistant)
    .add_edge("__start__", "case_assistant")
    
    .compile(name="Case Assistant")
)
