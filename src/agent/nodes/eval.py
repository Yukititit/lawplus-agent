from langchain_openai import AzureChatOpenAI
from langchain.messages import SystemMessage
from langchain_core.messages import AIMessage, HumanMessage
import json
import os
from dotenv import load_dotenv
from datetime import datetime
os.environ['DEEPEVAL_TELEMETRY_OPT_OUT'] = "1"
from deepeval.metrics import AnswerRelevancyMetric
from deepeval.test_case import LLMTestCase
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

load_dotenv()
from deepeval.metrics import FaithfulnessMetric
#GEval
from deepeval.metrics import GEval
from deepeval.test_case import LLMTestCaseParams
from deepeval import evaluate

from deepeval.dataset import EvaluationDataset
from deepeval.metrics.g_eval import Rubric
from deepeval.models import AzureOpenAIModel

import pandas as pd
import csv
from collections import defaultdict


AZURE_OPENAI_API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")


model = AzureOpenAIModel(


    # model_name="gpt-4.1-mini",
    # deployment_name="gpt-4.1-mini",

    model_name="gpt-5-mini",
    deployment_name="gpt-5-mini",
    azure_openai_api_key=AZURE_OPENAI_API_KEY,

    openai_api_version="2024-12-01-preview",  # 替换为实际支持的版本
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    temperature=1,
    
)

THRESHOLD = 0.8
MAX_REVISIONS = 1
RECENT_ROUNDS = 1


def _extract_retrieval_context(state: any) -> str:
    def safe_join(items):
        return "\n\n".join([s for s in items if isinstance(s, str) and s.strip()])

    ord_hist = getattr(state, 'ord_search_history', []) or []
    jud_hist = getattr(state, 'jud_search_history', []) or []
    pd_hist = getattr(state, 'pd_search_history', []) or []

    if RECENT_ROUNDS > 0:
        ord_hist = ord_hist[-RECENT_ROUNDS:] if len(ord_hist) > 0 else ord_hist
        jud_hist = jud_hist[-RECENT_ROUNDS:] if len(jud_hist) > 0 else jud_hist
        pd_hist = pd_hist[-RECENT_ROUNDS:] if len(pd_hist) > 0 else pd_hist


    ord_chunks = []
    for round_hits in ord_hist:
        for hit in (round_hits or []):
            src = (hit.get('_source') or {}) if isinstance(hit, dict) else {}
            content = src.get('content')
            if not content:
                hl = (hit.get('highlight') or {}) if isinstance(hit, dict) else {}
                hls = hl.get('content')
                if isinstance(hls, list) and hls:
                    content = hls[0]
            if content:
                ord_chunks.append(str(content))

    jud_chunks = []
    for round_hits in jud_hist:
        for hit in (round_hits or []):
            src = (hit.get('_source') or {}) if isinstance(hit, dict) else {}
            summary = src.get('summary') or src.get('content')
            id=hit.get('_id')
            if not summary:
                hl = (hit.get('highlight') or {}) if isinstance(hit, dict) else {}
                hls = hl.get('summary') or hl.get('content')
                if isinstance(hls, list) and hls:
                    summary = hls[0]
            if summary:
                jud_chunks.append(f"[JudgementID] {id} {str(summary)}")

    pd_chunks = []
    for round_hits in pd_hist:
        for hit in (round_hits or []):
            src = (hit.get('_source') or {}) if isinstance(hit, dict) else {}
            content = src.get('content')
            if not content:
                hl = (hit.get('highlight') or {}) if isinstance(hit, dict) else {}
                hls = hl.get('content')
                if isinstance(hls, list) and hls:
                    content = hls[0]
            if content:
                pd_chunks.append(str(content))

    parts = []
    if ord_chunks:
        parts.append("[Ordinances]\n" + safe_join(ord_chunks[:5]))
    if jud_chunks:
        parts.append("[Judgements]\n" + safe_join(jud_chunks[:5]))
    if pd_chunks:
        parts.append("[Practice Directions]\n" + safe_join(pd_chunks[:5]))
    print("parts", parts)
    return safe_join(parts) if parts else "No retrieval context"


async def eval(state: any, runtime: any) -> any:
    """使用 deepeval 评估最近一次回答，必要时触发重写。"""

    ai_message = next((m for m in reversed(state.messages) if isinstance(m, AIMessage)), None)
    if ai_message is None:
        return {"messages": []}


    human_message = next((m for m in reversed(state.messages) if isinstance(m, HumanMessage)), None)
    query_text = human_message.content if human_message else ""

    retrieval_context = _extract_retrieval_context(state)


    result = chatbot_eval(query_text, ai_message.content, retrieval_context)
    case_score = result.get("case_number", {}).get("score")
    legal_score = result.get("legal_relevance", {}).get("score") or result.get("legal", {}).get("score")
    case_reason = result.get("case_number", {}).get("explain")
    legal_reason = result.get("legal_relevance", {}).get("explain") or result.get("legal", {}).get("explain")

    scores = [s for s in [case_score, legal_score] if isinstance(s, (int, float))]
    score = sum(scores) / len(scores) if scores else 0.0
    explain_parts = []
    if case_reason:
        explain_parts.append(f"Factual Faithfulness: {case_reason}")
    if legal_reason:
        explain_parts.append(f"Legal Relevance: {legal_reason}")
    explain = "\n".join(explain_parts) if explain_parts else "No evaluator reasons provided."

    needs_revision = score < THRESHOLD and getattr(state, "revision_count", 0) < MAX_REVISIONS

    updates = {
        "eval_score": float(score),
        "eval_explain": explain,
    }

    if needs_revision:
        revision_count = getattr(state, "revision_count", 0) + 1
        updates["revision_count"] = revision_count
        updates["need_revision"] = True

        feedback = (
            "Please revise your previous answer to meet all requirements.\n\n"
            f"Evaluator feedback: {explain}\n\n"
            "Must strictly: (1) Use ONLY provided documents; (2) Be accurate and concise; "
            "(3) Clearly cite sources in a Markdown 'Sources Used' section with bullets using formats: "
            "judgement {id}, ordinance [index], knowledge [index]; (4) If unanswerable from provided materials, say so."
        )

        return {
            **updates,
            "messages": [HumanMessage(content=feedback)],
        }

    updates["need_revision"] = False
    return {**updates, "messages": []}





import sys
import logging
# def chatbot_eval(query, output, retrieval_context):
#     """
#     Evaluate a single chatbot response using Factual Faithfulness and Legal Faithfulness metrics.
    
#     Args:
#         query (str): The input query.
#         output (str): The actual output from the chatbot.
#         retrieval_context (str): The retrieval context.
    
#     Returns:
#         dict: A dictionary containing the evaluation results.
#     """
#     query = str(query).encode('utf-8', errors='replace').decode('utf-8')
#     output = str(output).encode('utf-8', errors='replace').decode('utf-8')
#     retrieval_context = str(retrieval_context).encode('utf-8', errors='replace').decode('utf-8')

#     try:
#         test_case = LLMTestCase(
#             input=query,
#             actual_output=output,
#             retrieval_context=[retrieval_context]
#         )
    
        

#         # Factual Faithfulness Metric (formerly Case Number Metric)
#     #     case_number_metric_strict = GEval(
#     #      model=model,
#     # name="Factual Faithfulness",
#     # criteria="""Evaluate the factual faithfulness of the actual output against the retrieval context and input with extreme strictness. 
#     # Facts in the output must be verified against either the retrieval context (primary source) or the input (user-provided facts that can be reused without retrieval). 
#     # Focus on key factual elements including: case numbers, regulation/cap names and codes, dates (e.g., years, specific dates), monetary amounts (e.g., damages in HK$), and other numerical values (e.g., regulation numbers like 'Regulation 39'). 
#     # Require exact matching without any deviations, fabrications, or partial matches. 
#     # If no factual elements appear in the actual output, assign full faithfulness score (10.0). 
#     # When factual elements are present, any single mismatch in any component (e.g., year/code/sequence for case numbers; full name/code for regulations; exact value/unit for amounts and numbers) results in a significantly low score.""",
#     # evaluation_steps=[
#     #     "If no factual elements (case numbers, regulation/cap names/codes, dates, amounts, or other numbers) appear in the 'actual output', assign full score (10.0) - no verification needed",
#     #     "If factual elements appear in 'actual output', extract all mentioned instances categorized by type:",
#     #     "  - Case numbers: Extract full format (year, court code, sequence number, e.g., [2019] HKCFI 471)",
#     #     "  - Regulation/Cap names and codes: Extract full names and codes (e.g., 'Construction Sites (Safety) Regulations (Cap. 59I)')",
#     #     "  - Dates: Extract all dates or years (e.g., 2023, 2024-05-15)",
#     #     "  - Monetary amounts: Extract values with units (e.g., HK$1.3 million, over HK$4 million)",
#     #     "  - Other numbers: Extract regulation/section numbers or similar (e.g., Regulation 39, Section 10T)",
#     #     "For each extracted factual element, check for exact match in the retrieval context first; if not found, then check the input",
#     #     "Verify exact matching for each type against retrieval context or input:",
#     #     "  - Case numbers: All components (year, court code, sequence) must match exactly in either source",
#     #     "  - Regulation/Cap: Full name and code must match without abbreviations or alterations in either source",
#     #     "  - Dates: Exact match in format and value (no approximations like 'around 2023') in either source",
#     #     "  - Amounts: Exact numerical value, unit, and qualifiers (e.g., 'over' or 'nearly') must match in either source",
#     #     "  - Other numbers: Exact match in value and context (e.g., regulation number) in either source",
#     #     "Assign a significantly low score (0-2) for any single mismatch, fabrication (not in retrieval or input), or partial matching across any element",
#     #     "Assign a low score (3-4) for any addition of facts not present in either the retrieval context or input",
#     #     "Only outputs with exact, complete matches across all factual elements to the retrieval context or input receive a full score (10.0)"
#     # ],
#     # evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.RETRIEVAL_CONTEXT],
#     # rubric=[
#     #     Rubric(score_range=(0, 2), expected_outcome="Any factual error, including single or multiple mismatches, fabrications (facts not in retrieval context or input), or partial matches in case numbers, regulation/cap names/codes, dates, monetary amounts, or other numerical values."),
#     #     Rubric(score_range=(3, 4), expected_outcome="Any addition of facts not present in the retrieval context or input, or partial matching across any element."),
#     #     Rubric(score_range=(10, 10), expected_outcome="100% factually accurate with no errors—all factual elements exactly match the retrieval context or input.")
#     #     ]
#     # )
        
        
#         case_number_metric = GEval(
#             model=model,
#             name="Factual Faithfulness",
#             criteria="""Evaluate the factual faithfulness of the actual output against the retrieval context and input with moderate strictness. 
#             Facts in the output must be verified against either the retrieval context (primary source) or the input (user-provided facts that can be reused without retrieval). 
#             Focus on key factual elements including: case numbers, regulation/cap names and codes, dates (e.g., years, specific dates), monetary amounts (e.g., damages in HK$), and other numerical values (e.g., regulation numbers like 'Regulation 39'). 
#             Require semantic matching where the meaning is equivalent (e.g., different formats or phrasings that convey the same fact), without fabrications or significant deviations. 
#             If no factual elements appear in the actual output, assign full faithfulness score (10.0). 
#             When factual elements are present, minor format variations (e.g., date styles) are acceptable if the core meaning matches; only substantive mismatches result in a low score.""",
#             evaluation_steps=[
#                 "If no factual elements (case numbers, regulation/cap names/codes, dates, amounts, or other numbers) appear in the 'actual output', assign full score (10.0) - no verification needed",
#                 "If factual elements appear in 'actual output', extract all mentioned instances categorized by type:",
#                 "  - Case numbers: Extract full format (year, court code, sequence number, e.g., [2019] HKCFI 471)",
#                 "  - Regulation/Cap names and codes: Extract full names and codes (e.g., 'Construction Sites (Safety) Regulations (Cap. 59I)')",
#                 "  - Dates: Extract all dates or years (e.g., 2023, 2024-05-15, '16 January 1996')",
#                 "  - Monetary amounts: Extract values with units (e.g., HK$1.3 million, over HK$4 million)",
#                 "  - Other numbers: Extract regulation/section numbers or similar (e.g., Regulation 39, Section 10T)",
#                 "For each extracted factual element, check for semantic match in the retrieval context first; if not found, then check the input",
#                 "Verify semantic matching for each type against retrieval context or input (meaning equivalent, allowing format/phrasing variations):",
#                 "  - Case numbers: Core components (year, court code, sequence) must convey the same case in either source",
#                 "  - Regulation/Cap: Core name and code must refer to the same regulation without substantive changes in either source",
#                 "  - Dates: Values must be semantically equivalent (same day/year, ignoring format variations like 'January 16, 1996' vs. '1996-01-16T...' or minor rephrasing) in either source—no approximations like 'around 2023'",
#                 "  - Amounts: Numerical value, unit, and qualifiers (e.g., 'over' or 'nearly') must convey the same amount in either source",
#                 "  - Other numbers: Value and context (e.g., regulation number) must refer to the same element in either source",
#                 "Assign a significantly low score (0-2) only for substantive mismatches, fabrications (not in retrieval or input), or clear partial matching across any element",
#                 "Assign a low score (3-4) for minor additions of facts not present in either the retrieval context or input",
#                 "Outputs with semantically equivalent matches across all factual elements to the retrieval context or input receive a full score (10.0)"
#             ],
#             evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.RETRIEVAL_CONTEXT],
#             rubric=[
#                 Rubric(score_range=(0, 2), expected_outcome="Substantive factual errors, including mismatches, fabrications (facts not in retrieval context or input), or partial matches in case numbers, regulation/cap names/codes, dates, monetary amounts, or other numerical values (beyond semantic equivalence)."),
#                 Rubric(score_range=(3, 4), expected_outcome="Minor additions of facts not present in the retrieval context or input."),
#                 Rubric(score_range=(10, 10), expected_outcome="100% factually accurate with no substantive errors—all factual elements semantically match the retrieval context or input (format variations acceptable).")
#             ]
#         )
        
        
        
        
        
#         # Legal Faithfulness Metric
#         legal_relevance = GEval(
#             model=model,
#             name="Legal Relevance",
#             evaluation_steps=[
#                     "Extract key legal elements from the input query, including facts, legal issues, specific statutes, case types, or required precedents.",
#                     "Assess the retrieved contextual information (e.g., statutes, judgments) for coverage of these elements, focusing on semantic relevance and applicability.",
#                     "Identify gaps, irrelevant details, or mismatches (e.g., unrelated case law or outdated statutes) that fail to satisfy the query's legal needs.",
#                     "Heavily penalize low coverage or hallucinations in retrieval (e.g., irrelevant documents that could mislead legal analysis).",
#                     "Provide reasons for the relevance score, highlighting how well the retrieval supports accurate legal response and potential risks of poor matches."
#                 ],
#             evaluation_params=[LLMTestCaseParams.INPUT,  LLMTestCaseParams.RETRIEVAL_CONTEXT],
#             threshold=0.5
#         )
        
#         # 执行评估
#         case_number_metric.measure(test_case)
#         if retrieval_context == "No retrieval context":
#             legal_relevance.score = 1
#             legal_relevance.reason = "No retrieval context"

#             total_cost = case_number_metric.evaluation_cost
#         else:
#             legal_relevance.measure(test_case)

#             total_cost = case_number_metric.evaluation_cost + legal_relevance.evaluation_cost
        
#         # 存储结果
#         result_row = {
#             'test_id': 1,  # Single evaluation, so fixed ID
#             'case_number_score': case_number_metric.score,
#             'case_number_reason': str(case_number_metric.reason),
#             'case_number_cost': case_number_metric.evaluation_cost,
#             'legal_score': legal_relevance.score,
#             'legal_reason': str(legal_relevance.reason),
#             'legal_cost': legal_relevance.evaluation_cost,
#             'total_cost': total_cost,
#             'input': query,
#             'actual_output': output,
#             'retrieval_context': retrieval_context
#         }
#         result={
#             "case_number": {"score": case_number_metric.score, "explain": str(case_number_metric.reason)},
#             "legal_relevance": {"score": legal_relevance.score, "explain": str(legal_relevance.reason)}
#         }
# # 保存到 Excel 文件
#         dir_path = r'D:\data\eval_recording'
#         os.makedirs(dir_path, exist_ok=True)
#         today = datetime.now().strftime('%Y-%m-%d')
#         excel_file = os.path.join(dir_path, f'eval_results_{today}.xlsx')
        
#         df_new = pd.DataFrame([result_row])
#         if os.path.exists(excel_file):
#             df_existing = pd.read_excel(excel_file)
#             df = pd.concat([df_existing, df_new], ignore_index=True)
#         else:
#             df = df_new
#         df.to_excel(excel_file, index=False)
        
#         return result
#     except Exception as e:
#         logging.error(f"Error during evaluation: {e}")
#         return {
#             "case_number": {"score": None, "explain": f"Error: {e}"},
#             "legal": {"score": None, "explain": f"Error: {e}"}
#         }

#pull dataset for local testing

# def dataset_eval(dataset_path: str = "test_rag"):
#     dataset = EvaluationDataset()
#     dataset.pull(alias=dataset_path)

#     results = []
#     i=0
#     output_file = "testing_results-gpt-5.1-mini.xlsx"
#     with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        
#         for golden in (dataset.goldens):
#             i += 1

#             # 使用函数评估单个案例
#             result = chatbot_eval(golden.input, golden.actual_output, golden.retrieval_context)
#             result['test_id'] = i  # 更新ID为当前循环索引
#             results.append(result)

#         # 创建主结果DataFrame
#         df_results = pd.DataFrame(results)
        
#         # 保存到Excel的不同工作表
#         # 1. 主要结果汇总表
#         main_columns = ['test_id', 'case_number_score', 'legal_score', 'total_cost', 
#                     'case_number_reason', 'legal_reason']
#         df_results[main_columns].to_excel(writer, sheet_name='Summary_Results', index=False)
        
#         # 2. 完整数据表（包含input/output/retrieval）
#         full_columns = ['test_id', 'input', 'actual_output', 'retrieval_context', 
#                     'case_number_score', 'legal_score', 'case_number_cost', 'legal_cost','case_number_reason', 'legal_reason']
#         df_results[full_columns].to_excel(writer, sheet_name='Full_Data', index=False)
        
#         # 3. 成本分析表
#         cost_data = pd.DataFrame({
#             'Metric': ['Case Number Total Cost', 'Legal Total Cost', 'Overall Total Cost'],
#             'Value': [
#                 df_results['case_number_cost'].sum(),
#                 df_results['legal_cost'].sum(),
#                 df_results['total_cost'].sum()
#             ]
#         })
#         cost_data.to_excel(writer, sheet_name='Cost_Analysis', index=False)
        
#         # 4. 评分统计表
#         score_stats = pd.DataFrame({
#             'Metric': ['Case Number Avg Score', 'Case Number Pass Rate', 
#                     'Legal Avg Score', 'Legal Pass Rate', 'Overall Pass Rate'],
#             'Value': [
#                 f"{df_results['case_number_score'].mean():.3f}",
#                 f"{(df_results['case_number_score'] >= 0.5).mean()*100:.1f}%",
#                 f"{df_results['legal_score'].mean():.3f}",
#                 f"{(df_results['legal_score'] >= 0.5).mean()*100:.1f}%",
#                 f"{((df_results['case_number_score'] >= 0.5) & (df_results['legal_score'] >= 0.5)).mean()*100:.1f}%"
#             ]
#         })
#         score_stats.to_excel(writer, sheet_name='Score_Stats', index=False)
        
#         print(f"\n✅ 评估完成！结果已保存到: {output_file}")
#         print(f"📊 总共评估了 {len(results)} 个测试用例")
#         print(f"💰 总成本: {df_results['total_cost'].sum():.2f}")
#         print(f"📈 平均Case Number得分: {df_results['case_number_score'].mean():.3f}")
#         print(f"📈 平均Legal得分: {df_results['legal_score'].mean():.3f}")
        
    
    
    