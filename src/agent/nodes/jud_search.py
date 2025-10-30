
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
        ai_message = next((m for m in reversed(state.messages) if isinstance(m, AIMessage)), None)
        if ai_message is None:
            raise Exception('No AIMessage。')
        retrieval = ai_message.content
        retrieval = json.loads(retrieval)
        use_judgement_search = retrieval['use_judgement_search']
        history = state.jud_search_history if hasattr(state, 'jud_search_history') else []
        if use_judgement_search:
            judgement_summary = retrieval['judgement_summary']
            judgement_keywords = retrieval['judgement_keywords']
            summary_embedding = generate_embeddings(judgement_summary)
            index = "judgement_processed_v202511"
            should_matches = [{"match": {"content": k}} for k in judgement_keywords]
            es_query = {
                "bool": {
                    "should": should_matches,
                }
            }
            response = es.search(
                _source=["summary"],
                index=index,
                query=es_query,
                knn={
                    "field": "summary_vector",
                    "query_vector": summary_embedding,
                    "k": 5,
                    "num_candidates": 10,
                    "boost": 0.5
                },
                rank={
                    "rrf": {}
                },
                size=5
            )
            new_history = history + [response['hits']['hits']]
            return {
                "jud_search_results": response['hits']['hits'],
                "jud_search_history": new_history,
                "messages": []
            }
        else:
            return {
                "jud_search_results": [],
                "jud_search_history": history,
                "messages": []
            }
    except Exception as e:
        history = state.jud_search_history if hasattr(state, 'jud_search_history') else []
        return {
            "jud_search_results": {"error": str(e), "hits": []},
            "jud_search_history": history,
            "messages": []
        }
