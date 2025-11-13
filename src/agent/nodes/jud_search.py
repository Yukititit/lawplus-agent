
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
def clean_keywords(keywords: list[str]) -> list[str]:

    # 常见的英文停用词集合（简化版，可扩展）
    stopwords = {
        'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
        'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
        'to', 'was', 'will', 'with', 'you'
    }
    if not keywords:
        return keywords
    cleaned = []
    for kw in keywords:
        kw_lower = kw.strip().lower()  # 去除空格，转小写
        if kw_lower and kw_lower not in stopwords:  # 跳过空字符串和停用词
            cleaned.append(kw)  # 保留原词（不转小写，以保持原格式）
    return cleaned

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
            judgement_keywords = clean_keywords(judgement_keywords)
            judgement_keywords_chinese = clean_keywords(judgement_keywords_chinese)
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
                                'slop': 10,
                                "boost": 8
                            }
                        }
                    },
                    {
                        "match": {
                            "text": {
                                "query": primary_kw,
                                "boost": 1
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
            def build_bool_query_chinese(primary_keyword: str, companion_keywords: list[str]) -> dict:
                primary_kw = primary_keyword.strip()
                must_clause = {
                    "match_phrase": {
                        "text": {
                            "query": primary_kw,
                            'slop': 10,
                            "operator": "and"
                        }
                    }
                }
                should_clauses = [
                    {
                        "match_phrase": {
                            "text": {
                                "query": primary_kw,
                                "boost": 8,
                                'slop': 10,
                            }
                        }
                    },
                    {
                        "match_phrase": {
                            "text": {
                                "query": primary_kw,
                                "boost": 1,
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
                            "text": {
                                "query": kw,
                                "boost": 5,
                                'slop': 10,
                            }
                        }
                    })
                    should_clauses.append({
                        "match_phrase": {
                            "text": {
                                "query": kw,
                                'slop': 10,
                                "boost": 0.5,
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

            async def search_async(query_body: dict, size: int = 3):
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
                tasks.append(search_async(build_bool_query_chinese(keyword, others)))

            results = await asyncio.gather(*tasks, return_exceptions=True) if tasks else []

            merged_hits = []
            new_history = history[:]  # 拷贝原历史（稍后会 flatten 和去重处理）

            # 先检查历史中的 seen_ids，并 flatten new_history 以确保平坦
            seen_ids = set()
            flattened_history = []
            for item in new_history:
                if isinstance(item, list):
                    for h in item:  # 如果嵌套，展开
                        doc_id = h.get('_id')
                        if doc_id and doc_id not in seen_ids:  # 去重历史本身（可选，但安全）
                            flattened_history.append(h)
                            seen_ids.add(doc_id)
                else:  # 已平坦
                    doc_id = item.get('_id')
                    if doc_id and doc_id not in seen_ids:
                        flattened_history.append(item)
                        seen_ids.add(doc_id)
            new_history = flattened_history  # 更新为平坦、去重历史

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
                    continue
                hits = resp.get('hits', {}).get('hits', [])
                
                
                # 合并到 new_history：全 hits，逐个检查 seen_ids（先检查，后 append/合并）
                for h in hits:
                    doc_id = h.get('_id')
                    if doc_id and doc_id not in seen_ids:
                        new_history.append(h)  # 平坦 append，确保 [{}, {}] 格式
                        seen_ids.add(doc_id)
                

            return {
                "jud_search_history": new_history,  # 现在是平坦 [{}, {}]
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
