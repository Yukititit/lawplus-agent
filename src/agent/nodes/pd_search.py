
from langchain.messages import SystemMessage
import json
import os
from elasticsearch import Elasticsearch, helpers
from openai import AzureOpenAI
from dotenv import load_dotenv
from time import sleep
import pandas as pd
from langchain_core.messages import AIMessage


load_dotenv()
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")

def generate_embeddings(
    text, model="text-embedding-3-small"
):
    client = AzureOpenAI(
        api_key=AZURE_OPENAI_API_KEY,
        api_version="2024-02-01",
        azure_endpoint=AZURE_OPENAI_ENDPOINT,
    )
    # return ""
    return client.embeddings.create(input=[text], model=model,dimensions=1536).data[0].embedding


es_endpoint = os.environ.get("ES_ENDPOINT")
es_api_key = os.environ.get("ES_API_KEY")
es = Elasticsearch(es_endpoint, api_key=es_api_key)


async def pd_search(state: any, runtime: any) -> any:
    
    try:
        ai_message = next((m for m in reversed(state.messages) if isinstance(m, AIMessage)), None)
        if ai_message is None:
            raise Exception('No AIMessage。')
        retrieval = ai_message.content
        retrieval = json.loads(retrieval)
        
        
        use_practice_direction_search=retrieval['use_practice_direction_search']
        history = state.pd_search_history if hasattr(state, 'pd_search_history') else []
        
        
        if use_practice_direction_search:
            
            practice_direction_summary=retrieval['practice_direction_summary']
            practice_direction_keywords=retrieval['practice_direction_keywords']

            summary_embedding=generate_embeddings(practice_direction_summary)
            index="practice_direction_v202508"
            print('practice_direction_keywords11',practice_direction_keywords)
            should_matches = [{"match": {"content": k}} for k in practice_direction_keywords]
            es_query = {
                "bool": {
                    "should": should_matches,
                    "minimum_should_match": 1,
                    "boost": 2.0,
                 
                }
            }
            
            
            response=es.search(
                _source=["content"],
                index=index,
                query=es_query,
                # knn={
                #     "field": "content embeddings",
                #     "query_vector": summary_embedding,
                #     "k": 5,
                #     "num_candidates": 10,
                #     "boost": 0.5
                # },
                # rank={
                #     "rrf": {}
                # },
                highlight={
                    "pre_tags": ["<em>"],
                    "post_tags": ["</em>"],
                    "fields": {
                        "content": {}
                    }
                },
                size=5
            )
            new_history = history + [response['hits']['hits']]
            
    
            return {
                # "pd_search_results": response['hits']['hits'],
                "pd_search_history": new_history,
                "messages": []
            }
        else:
            return {
                # "pd_search_results": [],
                "pd_search_history": history,
                "messages": []
            }
    except Exception as e:
            
            history = state.pd_search_history if hasattr(state, 'pd_search_history') else []
            return {
                # "pd_search_results": {"error": str(e), "hits": []},
                "pd_search_history": history,
                "messages": []
            }
