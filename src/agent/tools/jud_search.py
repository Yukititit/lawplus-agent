
from langchain.messages import SystemMessage
import json
import os
from elasticsearch import Elasticsearch, helpers
from openai import AzureOpenAI
from dotenv import load_dotenv
from time import sleep
import pandas as pd
from langchain_core.messages import AIMessage
import asyncio
from functools import partial

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
            judgement_keywords = retrieval.get('judgement_keywords', [])
            judgement_keywords_chinese = retrieval.get('judgement_keywords_chinese', [])

            summary_embedding = generate_embeddings(judgement_summary)
            index = "judgement_processed_v202511"

            def build_bool_query(primary_keyword: str, companion_keywords: list[str]) -> dict:
                primary_kw = primary_keyword.strip()
                must_clause = {
                    "match": {
                        "text": {
                            "query": primary_kw,
                            "operator": "and"
                        }
                    }
                }
                should_clauses = [
                    {
                        "match_phrase": {
                            "text": {
                                "query": primary_kw,
                                "boost": 8
                            }
                        }
                    },
                    {
                        "match": {
                            "text": {
                                "query": primary_kw,
                                "boost": 2
                            }
                        }
                    }
                ]
                for kw in companion_keywords:
                    kw = kw.strip()
                    if not kw:
                        continue
                    should_clauses.append({
                        "match_phrase": {
                            "text": {
                                "query": kw,
                                "boost": 4
                            }
                        }
                    })
                    should_clauses.append({
                        "match": {
                            "text": {
                                "query": kw
                            }
                        }
                    })
                return {
                    "bool": {
                        "must": [must_clause],
                        "should": should_clauses,
                        "minimum_should_match": 1
                    }
                }

            async def search_async(query_body: dict, size: int = 5):
                loop = asyncio.get_running_loop()
                func = partial(
                    es.search,
                    _source=["text"],
                    index=index,
                    query=query_body,
                    knn={
                        "field": "summary_vector",
                        "query_vector": summary_embedding,
                        "k": 10,
                        "num_candidates": 50,
                        "boost": 0.5
                    },
                    highlight={
                        "pre_tags": ["<em>"],
                        "post_tags": ["</em>"],
                        "fields": {
                            "text": {}
                        }
                    },
                    size=size
                )
                return await loop.run_in_executor(None, func)

            tasks = []
            for i, keyword in enumerate(judgement_keywords):
                others = judgement_keywords[:i] + judgement_keywords[i + 1 :]
                tasks.append(search_async(build_bool_query(keyword, others)))
            for i, keyword in enumerate(judgement_keywords_chinese):
                others = judgement_keywords_chinese[:i] + judgement_keywords_chinese[i + 1 :]
                tasks.append(search_async(build_bool_query(keyword, others)))

            results = await asyncio.gather(*tasks, return_exceptions=True) if tasks else []

            merged_hits = []
            new_history = history[:]
            seen_ids = set()

            if not results and not tasks:
                results = [
                    es.search(
                        _source=["text"],
                        index=index,
                        query={"match_all": {}},
                        knn={
                            "field": "summary_vector",
                            "query_vector": summary_embedding,
                            "k": 10,
                            "num_candidates": 50,
                            "boost": 0.5
                        },
                        size=5
                    )
                ]

            for resp in results:
                if isinstance(resp, Exception):
                    new_history.append([])
                    continue
                hits = resp.get('hits', {}).get('hits', [])
                new_history.append(hits)
                for h in hits[:2]:
                    doc_id = h.get('_id')
                    if doc_id not in seen_ids:
                        merged_hits.append(h)
                        seen_ids.add(doc_id)

            return {
                "jud_search_results": merged_hits,
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
