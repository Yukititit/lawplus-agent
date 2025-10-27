from __future__ import annotations
from typing import TypedDict, Annotated, List
from langchain_core.tools import tool
from dataclasses import dataclass
from typing import Any, Dict
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph
from langgraph.runtime import Runtime
from typing_extensions import TypedDict
import os 
from openai import AzureOpenAI
import operator
from elasticsearch import Elasticsearch
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
    # print('res',response)
    
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

    input_text: str = "Hello? tell me some interesting about Law"


async def call_model(state: State, runtime: Runtime[Context]) -> Dict[str, Any]:
    """Process input and returns LLM output."""
    input_text = state.input_text
    print("input_text:", input_text)
    
    prompt="""  
    You are a specialized Legal AI Assistant with expertise in extracting precise, relevant information from user queries related to law, regulations, cases, statutes, or legal concepts. Your role is to analyze the user's input query and distill the core elements into a structured list of keywords or key phrases. These will be used for downstream tasks: vector similarity search (to find semantically related legal documents) and keyword search (to match exact terms in legal databases).
        Follow these steps strictly:

        Read the user's input carefully, focusing on legal topics, entities (e.g., laws, cases, parties, jurisdictions), actions (e.g., violations, appeals), and context (e.g., civil vs. criminal, specific countries).
        Identify 3-8 key terms or phrases that capture the essence. Prioritize:

        Specific legal terms (e.g., "contract breach" over "problem").
        Entities like "GDPR", "Supreme Court", "Article 14".
        Actions or concepts like "injunction", "negligence liability".
        Avoid generic words; make them actionable for search.


        Output ONLY a JSON object in this exact format: {"keywords": ["term1", "term2", "term3", ...]}. No additional text, explanations, or wrappers.

        
    """
    
    # return {
    #     "input_text":input_text
    # }
    try:
        response =  client.chat.completions.create(  
            model="gpt-4.1-mini",  
            messages=[
                {"role": "system", "content": prompt},  
                {"role": "user", "content": input_text}
            ],
            max_tokens=200,  
            temperature=0.7,
        )
        output_text = response.choices[0].message.content
        print("output_text:", output_text)
        retrieval=get_law_info(output_text)
        
        print("retrieval:", retrieval)

    
    
    
    except Exception as e:
        output_text = f"Error: {str(e)}"  # 错误处理
        print(f"LLM Error: {e}")
    
 
    config_param = (runtime.context or {}).get("my_configurable_param", "default")
    
    return {
        "input_text": f"{ retrieval} (Config: {config_param})"  
    }



graph = (
    StateGraph(State, context_schema=Context)
    .add_node(call_model)
    .add_edge("__start__", "call_model")
    .compile(name="New Graph")
)
