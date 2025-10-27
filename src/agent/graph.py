"""LangGraph single-node graph template.

Returns a predefined response. Replace logic and configuration as needed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict

from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from typing_extensions import TypedDict



from langchain.messages import AnyMessage
from typing_extensions import TypedDict, Annotated
import operator


@dataclass
class State:
    """Input state for the agent.

    Defines the initial structure of incoming data.
    See: https://langchain-ai.github.io/langgraph/concepts/low_level/#state
    """

    messages: Annotated[list[AnyMessage], operator.add]


class Context(TypedDict):
    """Context parameters for the agent.

    Set these when creating assistants OR when invoking the graph.
    See: https://langchain-ai.github.io/langgraph/cloud/how-tos/configuration_cloud/
    """

    my_configurable_param: str

from agent.nodes import call_model

# Define the graph
graph = (
    StateGraph(State, context_schema=Context)
    .add_node('call_model', call_model)
    .add_edge("__start__", "call_model")
    .compile(name="New Graph")
)   