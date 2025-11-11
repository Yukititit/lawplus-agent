from __future__ import annotations
from typing import TypedDict, Annotated, List
from langchain_core.tools import tool
from dataclasses import dataclass, field
from typing import Any, Dict, Literal
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, START, END
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langgraph.checkpoint.postgres import PostgresSaver

from dotenv import load_dotenv

load_dotenv()

from agent.nodes import case_assistant, case_tools


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


def should_continue(state: State) -> Literal["case_tools", END]:
    """Decide if we should continue the loop or stop based upon whether the LLM made a tool call"""

    messages = state.messages
    last_message = messages[-1]

    # If the LLM makes a tool call, then perform an action
    if last_message.tool_calls:
        return "case_tools"

    # Otherwise, we stop (reply to the user)
    return END


graph = (
    StateGraph(State, context_schema=Context)
    .add_node(case_assistant)
    .add_node(case_tools)
    .add_edge("__start__", "case_assistant")
    .add_conditional_edges("case_assistant", should_continue, ["case_tools", END])
    .add_edge("case_tools", "case_assistant")
    .compile(name="Case Assistant")
)
