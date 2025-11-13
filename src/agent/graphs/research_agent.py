from __future__ import annotations
from typing import TypedDict, Annotated, List
from langchain_core.tools import tool
from dataclasses import dataclass, field
from typing import Any, Dict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from typing_extensions import TypedDict
import os 
from openai import AzureOpenAI
import operator
from elasticsearch import Elasticsearch
from langgraph.graph.message import add_messages  

from dotenv import load_dotenv
load_dotenv()
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    api_version="2024-02-01",
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
)

es_endpoint = os.environ.get("ES_ENDPOINT")
es_api_key = os.environ.get("ES_API_KEY")
es = Elasticsearch(es_endpoint, api_key=es_api_key)



from agent.nodes import ord_search, jud_search, process_query, sum_model, pd_search, eval

#tool
def get_law_info(input_list: list) -> dict:
    """Get law information"""
    index="ordinances_v202508"
    search_query = " ".join(input_list)
    query = {
        "_source":["content"],
        "query": {
            "match": {
                "content": {
                    "query": search_query,
                    "operator": "and"
                }
            }
        }
    }
    response=es.search(index=index,body=query)

    
    return response



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
    
    ord_search_history: List[Dict[str, Any]] = field(default_factory=list)
    
    jud_search_history: List[Dict[str, Any]] = field(default_factory=list)
    pd_search_history:  List[Dict[str, Any]] = field(default_factory=list)
    case_score: float = 0.0
    legal_score: float = 0.0
    eval_explain: str = ""
    revision_count: float = 0
    need_revision: bool = False
    legal_revision: bool = False
    messages: Annotated[List[BaseMessage], add_messages] = field(default_factory=list)
    


graph = (
    StateGraph(State, context_schema=Context)
    .add_node(process_query)
    .add_node(ord_search)
    .add_node(jud_search)
    .add_node(pd_search)
    .add_node(sum_model)
    .add_node(eval)
    
    .add_edge("__start__", "process_query")
    .add_edge("process_query", "ord_search")
    .add_edge("process_query", "jud_search")
    .add_edge("process_query", "pd_search")
    .add_edge("ord_search", "sum_model")
    .add_edge("jud_search", "sum_model")    
    .add_edge("pd_search", "sum_model")  
    .add_edge("sum_model", "eval")
    .add_conditional_edges(
        "eval",
        lambda state: "revise_legal" if getattr(state, "legal_revision", False) else ("revise" if getattr(state, "need_revision", False) else "end"),
        {
            "revise_legal": "process_query",
            "revise": "sum_model",
            "end": "__end__",
        },
    )
    
    .compile(name="Research Agent")
)
