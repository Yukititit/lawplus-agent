
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


async def jud_search(state: any, runtime: any) -> any:
    
    try:
        retrieval=state.messages[0].content
        retrieval = json.loads(retrieval)
        
        print('retrieval in jud_search:',type(retrieval),retrieval)
        
        use_judgement_search=retrieval['use_judgement_search']
        print('use_judgement_search in jud_search:',use_judgement_search)
        if use_judgement_search:
            
            judgement_summary=retrieval['judgement_summary']
            judgement_keywords=retrieval['judgement_keywords']
            print('judgement_keywords in ord_search:',judgement_keywords)
            print('judgement_summary in ord_search:',judgement_summary)
            summary_embedding=generate_embeddings(judgement_summary)
            index="judgement_processed_v202511"
            search_query = " ".join(judgement_keywords)

            response=es.search(
                _source=["summary"],
                index=index,
                query={
                    "bool": {
                        "should": [
                            {
                                "match": {
                                    "summary": {
                                        "query": search_query,
                                        "operator": "and"
                                    }
                                }
                            }
                        ]
                    },
                },
                knn={
                    "field": "summary_vector",
                    "query_vector": summary_embedding,
                    "k": 5,
                    "num_candidates": 10
                },
                rank={
                    "rrf": {}
                },
                size=5
            )
            print('jud_search response:',response['hits']['hits'])

            return {
                "jud_search_results": response['hits']['hits'],
                "messages": []
            }
        else:
            return {
                "jud_search_results": [],
                "messages": []
            }
    except Exception as e:
            
            return {
                "jud_search_results": {"error": str(e), "hits": []},
                "messages": []
            }
