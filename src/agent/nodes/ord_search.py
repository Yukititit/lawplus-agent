
from langchain.messages import SystemMessage
import json
import os
from elasticsearch import Elasticsearch, helpers
from openai import AzureOpenAI
from dotenv import load_dotenv
from time import sleep
import pandas as pd


load_dotenv()
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")

def generate_embeddings(
    text, model="text-embedding-3-large"
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


async def ord_search(state: any, runtime: any) -> any:
    
    try:
        retrieval=state.messages[0].content
        retrieval = json.loads(retrieval)
        
        print('retrieval in ord_search:',type(retrieval),retrieval)
        
        use_ordinance_search=retrieval['use_ordinance_search']
        if use_ordinance_search:
            
            ordinance_summary=retrieval['ordinance_summary']
            ordinance_keywords=retrieval['ordinance_keywords']
            print('ordinance_keywords in ord_search:',ordinance_keywords)
            print('ordinance_summary in ord_search:',ordinance_summary)
            summary_embedding=generate_embeddings(ordinance_summary)
            index="ordinances_v202508"
            search_query = " ".join(ordinance_keywords)
            query = {
                "_source":["content"],
                "query": {
                    "match": {
                        "content": {
                            "query": search_query,
                            "operator": "and"
                        }
                    }
                },
                "knn": {
                    "field": "content embedding",
                    "query_vector": summary_embedding,
                    "k": 5,
                    "num_candidates": 10
                },
                "rank": {
                    "rff": {}
                },
                "size": 5
            }

            response=es.search(
                _source=["content"],
                index=index,
                query={
                    "bool": {
                        "should": [
                            {
                                "match": {
                                    "content": {
                                        "query": search_query,
                                        "operator": "and"
                                    }
                                }
                            }
                        ]
                    },
                },
                knn={
                    "field": "content embeddings",
                    "query_vector": summary_embedding,
                    "k": 5,
                    "num_candidates": 10
                },
                rank={
                    "rrf": {}
                },
                size=5
            )
            print('ord_search response:',response['hits']['hits'])

            return {
                "ord_search_results": response['hits']['hits'],
                "messages": []
            }
        else:
            return {
                "ord_search_results": [],
                "messages": []
            }
    except Exception as e:
            
            return {
                "ord_search_results": {"error": str(e), "hits": []},
                "messages": []
            }
