
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


async def ord_search(state: any, runtime: any) -> any:
    
    try:
        ai_message = next((m for m in reversed(state.messages) if isinstance(m, AIMessage)), None)
        if ai_message is None:
            raise Exception('No AIMessage。')
        retrieval = ai_message.content
        retrieval = json.loads(retrieval)


        use_ordinance_search=retrieval['use_ordinance_search']
        history = state.ord_search_history if hasattr(state, 'ord_search_history') else []

        if use_ordinance_search:
            
            ordinance_summary=retrieval['ordinance_summary']
            ordinance_keywords=retrieval['ordinance_keywords']
            ordinance_keywords_chinese=retrieval['ordinance_keywords_chinese']
            summary_embedding=generate_embeddings(ordinance_summary)
            index="ordinances_v202508"
            search_query = " ".join(ordinance_keywords)

            def build_bool_query(primary_keyword: str, companion_keywords: list[str]) -> dict:
                primary_kw = primary_keyword.strip()
                must_clause = {
                    "match": {
                        "content": {
                            "query": primary_kw,
                            "operator": "and"
                        }
                    }
                }
                should_clauses = [
                    {
                        "match_phrase": {
                            "content": {
                                "query": primary_kw,
                                "boost": 8
                            }
                        }
                    },
                    {
                        "match": {
                            "content": {
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
                            "content": {
                                "query": kw,
                                "boost": 4
                            }
                        }
                    })
                    should_clauses.append({
                        "match": {
                            "content": {
                                "query": kw
                            }
                        }
                    })
                bool_query = {
                    "bool": {
                        "must": [must_clause],
                        "should": should_clauses,
                        "minimum_should_match": 1
                    }
                }
                return bool_query
            def build_bool_query_chinese(primary_keyword: str, companion_keywords: list[str]) -> dict:
                primary_kw = primary_keyword.strip()
                must_clause = {
                    "match_phrase": {
                        "content": {
                            "query": primary_kw,
                            'slop': 10,
                            "operator": "and"
                        }
                    }
                }
                should_clauses = [
                    {
                        "match_phrase": {
                            "content": {
                                "query": primary_kw,
                                "boost": 8,
                                'slop': 10,
                            }
                        }
                    },
                    {
                        "match_phrase": {
                            "content": {
                                "query": primary_kw,
                                "boost": 2,
                                'slop': 10,
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
                            "content": {
                                "query": kw,
                                "boost": 4,
                                'slop': 10,
                            }
                        }
                    })
                    should_clauses.append({
                        "match_phrase": {
                            "content": {
                                "query": kw,
                                'slop': 10,
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

            async def search_async(query_body: dict, size: int = 4):
                loop = asyncio.get_running_loop()
                func = partial(
                    es.search,
                    _source=["content"],
                    index=index,
                    query=query_body,
                    knn={
                        "field": "content embeddings",
                        "query_vector": summary_embedding,
                        "k": 5,
                        "num_candidates": 10,
                        "boost": 0.5
                    },
                    highlight={
                        "pre_tags": ["<em>"],
                        "post_tags": ["</em>"],
                        "fields": {
                            "content": {}
                        }
                    },
                    size=size
                )
                return await loop.run_in_executor(None, func)

            tasks = []
            for i, k in enumerate(ordinance_keywords):
                others = ordinance_keywords[:i] + ordinance_keywords[i+1:]
                tasks.append(search_async(build_bool_query(k, others)))
            for i, k in enumerate(ordinance_keywords_chinese):
                others = ordinance_keywords_chinese[:i] + ordinance_keywords_chinese[i+1:]
                tasks.append(search_async(build_bool_query_chinese(k, others)))

            results = await asyncio.gather(*tasks, return_exceptions=True) if len(tasks) > 0 else []

            merged_hits = []
            new_history = history[:]
            seen_ids = set()

            for resp in results:
                if isinstance(resp, Exception):
                    continue

                hits = resp.get('hits', {}).get('hits', [])
                for h in hits:
                    doc_id = h.get('_id')
                    if doc_id not in seen_ids:
                        merged_hits.append(h)
                        new_history.append(h)
                        seen_ids.add(doc_id)

            return {
                "ord_search_results": merged_hits,
                "ord_search_history": new_history,
                "messages": []
            }
        else:
            return {
                "ord_search_results": [],
                "ord_search_history": history,
                "messages": []
            }
    except Exception as e:
            history = state.ord_search_history if hasattr(state, 'ord_search_history') else []
            return {
                "ord_search_results": {"error": str(e), "hits": []},
                "ord_search_history": history,
                "messages": []
            }
