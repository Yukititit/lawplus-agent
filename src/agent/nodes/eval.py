from langchain_openai import AzureChatOpenAI
from langchain_core.messages import AIMessage, HumanMessage,SystemMessage
import os
from dotenv import load_dotenv
from datetime import datetime
os.environ['DEEPEVAL_TELEMETRY_OPT_OUT'] = "1"
from deepeval.test_case import LLMTestCase
import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
from pprint import pprint
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

from langchain_openai import AzureChatOpenAI
from langchain.messages import SystemMessage

model2 = AzureChatOpenAI(
    model_name="gpt-4.1-mini",
    api_version="2024-12-01-preview",
)
model = AzureOpenAIModel(


    # model_name="gpt-4.1-mini",
    # deployment_name="gpt-4.1-mini",

    model_name="gpt-5-mini",
    deployment_name="gpt-5-mini",
    azure_openai_api_key=AZURE_OPENAI_API_KEY,

    openai_api_version="2024-12-01-preview",  
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
            hit = round_hits or []
            src = (hit.get('_source') or {}) if isinstance(hit, dict) else {}
            summary = src.get('text')
            id=hit.get('_id')

            # if not summary:
            #     hl = (hit.get('highlight') or {}) if isinstance(hit, dict) else {}
            #     hls = hl.get('summary') or hl.get('text')
            #     if isinstance(hls, list) and hls:
            #         summary = hls[0]
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
        parts.append("[Ordinances]\n" + safe_join(ord_chunks))
    if jud_chunks:
        parts.append("[Judgements]\n" + safe_join(jud_chunks))
    if pd_chunks:
        parts.append("[Practice Directions]\n" + safe_join(pd_chunks))

    return safe_join(parts) if parts else "No retrieval context"


async def eval(state: any, runtime: any) -> any:
    """use deepeval to evaluate the latest answer, and trigger revision if necessary."""
    ai_message = next((m for m in reversed(state.messages) if isinstance(m, AIMessage)), None)
    if ai_message is None:
        return {"messages": []}


    human_message = next((m for m in reversed(state.messages) if isinstance(m, HumanMessage)), None)
    query_text = human_message.content if human_message else ""

    retrieval_context = _extract_retrieval_context(state)


    result = chatbot_eval(query_text, ai_message.content, retrieval_context)
    case_score = result.get("case_number", {}).get("score")
    legal_score = result.get("legal_relevance", {}).get("score") 
    case_reason = result.get("case_number", {}).get("explain")
    legal_reason = result.get("legal_relevance", {}).get("explain") 

 
    print(f"csea_score: {case_score}, legal_score: {legal_score}")
    explain_parts = []
    if case_reason:
        explain_parts.append(f"Factual Faithfulness: {case_reason}")
    if legal_reason:
        explain_parts.append(f"Legal Relevance: {legal_reason}")
    explain = "\n".join(explain_parts) if explain_parts else "No evaluator reasons provided."

    def _safe_float(value):
        if value is None:
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            logging.warning(f" {value!r} can't be float, return None")
            return None

    updates = {
        "case_score": _safe_float(case_score),
        "legal_score": _safe_float(legal_score),
        "eval_explain": explain,
    }


    revision_count_current = getattr(state, "revision_count", 0)
    legal_low = isinstance(legal_score, (int, float)) and legal_score < 0.6
    case_low = isinstance(case_score, (int, float)) and case_score < 0.7

    if legal_low and revision_count_current < MAX_REVISIONS:
        revision_count = revision_count_current + 1
        updates["revision_count"] = revision_count
        updates["legal_revision"] = True
        updates["need_revision"] = False

        feedback_for_query = (
            "The original query received a low legal relevance score during evaluation. "
            "Your task is to refine it into a single, improved query that enhances search intent for legal retrieval.\n\n"
            f"Original user query: {query_text}\n\n"
            f"Evaluator feedback (legal): {legal_reason}\n\n"
            "Instructions:\n"
            "- Analyze the feedback to identify gaps in legal precision, coverage, or intent.\n"
            "- Enrich the query by abstracting key legal concepts (e.g., incorporate related statutes, doctrines, or jurisdictions if relevant) while keeping it broad yet targeted.\n"
            "- Make it concise, natural, and optimized for retrieval (e.g., use synonyms, negate ambiguities, or add specificity without over-narrowing).\n"
            "- Output ONLY the new query as a single string. Do not include explanations or additional text."
        )

        # feedback_message = HumanMessage(
        #     content=feedback_for_query,
        #     additional_kwargs={"from_eval": "legal_revision_feedback"},
        # )
        messages = [
            SystemMessage(
                content=feedback_for_query
            )
        ] + state.messages

        response = await model2.ainvoke(messages)
        return {**updates, "messages": [response]}


    # secondary determination: when the factual faithfulness is low, go back to the summary model to rewrite the answer (continue to use the current logic)
    if case_low and revision_count_current < MAX_REVISIONS:
        revision_count = revision_count_current + 1
        updates["revision_count"] = revision_count
        updates["need_revision"] = True
        updates["legal_revision"] = False

        feedback = (
            "Please revise your previous answer to meet all requirements.\n\n"
            f"Evaluator feedback: {case_reason}\n\n"
            "Must strictly: (1) Use ONLY provided documents; (2) Be accurate and concise; "
            "(3) Clearly cite sources in a Markdown 'Sources Used' section with bullets using formats: "
            "judgement {id}, ordinance [index], knowledge [index]; (4) If unanswerable from provided materials, say so."
        )


        feedback_message = HumanMessage(
            content=feedback,
            additional_kwargs={"from_eval": "case_revision_feedback"},
        )

        return {**updates, "messages": [feedback_message]}




    updates["need_revision"] = False
    updates["legal_revision"] = False
    updates["revision_count"] = 0
    return {**updates, "messages": []}





import sys
import logging
def chatbot_eval(query, output, retrieval_context):
    """
    Evaluate a single chatbot response using Factual Faithfulness and Legal Faithfulness metrics.
    
    Args:
        query (str): The input query.
        output (str): The actual output from the chatbot.
        retrieval_context (str): The retrieval context.
    
    Returns:
        dict: A dictionary containing the evaluation results.
    """
    query = str(query).encode('utf-8', errors='replace').decode('utf-8')
    output = str(output).encode('utf-8', errors='replace').decode('utf-8')
    retrieval_context = str(retrieval_context).encode('utf-8', errors='replace').decode('utf-8')

    try:
        test_case = LLMTestCase(
            input=query,
            actual_output=output,
            retrieval_context=[retrieval_context]
        )
    
        

        # Factual Faithfulness Metric (formerly Case Number Metric)
    #     case_number_metric_strict = GEval(
    #      model=model,
    # name="Factual Faithfulness",
    # criteria="""Evaluate the factual faithfulness of the actual output against the retrieval context and input with extreme strictness. 
    # Facts in the output must be verified against either the retrieval context (primary source) or the input (user-provided facts that can be reused without retrieval). 
    # Focus on key factual elements including: case numbers, regulation/cap names and codes, dates (e.g., years, specific dates), monetary amounts (e.g., damages in HK$), and other numerical values (e.g., regulation numbers like 'Regulation 39'). 
    # Require exact matching without any deviations, fabrications, or partial matches. 
    # If no factual elements appear in the actual output, assign full faithfulness score (10.0). 
    # When factual elements are present, any single mismatch in any component (e.g., year/code/sequence for case numbers; full name/code for regulations; exact value/unit for amounts and numbers) results in a significantly low score.""",
    # evaluation_steps=[
    #     "If no factual elements (case numbers, regulation/cap names/codes, dates, amounts, or other numbers) appear in the 'actual output', assign full score (10.0) - no verification needed",
    #     "If factual elements appear in 'actual output', extract all mentioned instances categorized by type:",
    #     "  - Case numbers: Extract full format (year, court code, sequence number, e.g., [2019] HKCFI 471)",
    #     "  - Regulation/Cap names and codes: Extract full names and codes (e.g., 'Construction Sites (Safety) Regulations (Cap. 59I)')",
    #     "  - Dates: Extract all dates or years (e.g., 2023, 2024-05-15)",
    #     "  - Monetary amounts: Extract values with units (e.g., HK$1.3 million, over HK$4 million)",
    #     "  - Other numbers: Extract regulation/section numbers or similar (e.g., Regulation 39, Section 10T)",
    #     "For each extracted factual element, check for exact match in the retrieval context first; if not found, then check the input",
    #     "Verify exact matching for each type against retrieval context or input:",
    #     "  - Case numbers: All components (year, court code, sequence) must match exactly in either source",
    #     "  - Regulation/Cap: Full name and code must match without abbreviations or alterations in either source",
    #     "  - Dates: Exact match in format and value (no approximations like 'around 2023') in either source",
    #     "  - Amounts: Exact numerical value, unit, and qualifiers (e.g., 'over' or 'nearly') must match in either source",
    #     "  - Other numbers: Exact match in value and context (e.g., regulation number) in either source",
    #     "Assign a significantly low score (0-2) for any single mismatch, fabrication (not in retrieval or input), or partial matching across any element",
    #     "Assign a low score (3-4) for any addition of facts not present in either the retrieval context or input",
    #     "Only outputs with exact, complete matches across all factual elements to the retrieval context or input receive a full score (10.0)"
    # ],
    # evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.RETRIEVAL_CONTEXT],
    # rubric=[
    #     Rubric(score_range=(0, 2), expected_outcome="Any factual error, including single or multiple mismatches, fabrications (facts not in retrieval context or input), or partial matches in case numbers, regulation/cap names/codes, dates, monetary amounts, or other numerical values."),
    #     Rubric(score_range=(3, 4), expected_outcome="Any addition of facts not present in the retrieval context or input, or partial matching across any element."),
    #     Rubric(score_range=(10, 10), expected_outcome="100% factually accurate with no errors—all factual elements exactly match the retrieval context or input.")
    #     ]
    # )
        
        
        case_number_metric = GEval(
            model=model,
            name="Factual Faithfulness",
            criteria="""Evaluate the factual faithfulness of the actual output against the retrieval context and input with moderate strictness. 
            Facts in the output must be verified against either the retrieval context (primary source) or the input (user-provided facts that can be reused without retrieval). 
            Focus on key factual elements including: case numbers, regulation/cap names and codes, dates (e.g., years, specific dates), monetary amounts (e.g., damages in HK$), and other numerical values (e.g., regulation numbers like 'Regulation 39'). 
            Require semantic matching where the meaning is equivalent (e.g., different formats or phrasings that convey the same fact), without fabrications or significant deviations. 
            If no factual elements appear in the actual output, assign full faithfulness score (10.0). 
            When factual elements are present, minor format variations (e.g., date styles) are acceptable if the core meaning matches; only substantive mismatches result in a low score.""",
            evaluation_steps=[
                "If no factual elements (case numbers, regulation/cap names/codes, dates, amounts, or other numbers) appear in the 'actual output', assign full score (10.0) - no verification needed",
                "If factual elements appear in 'actual output', extract all mentioned instances categorized by type:",
                "  - Case numbers: Extract full format (year, court code, sequence number, e.g., [2019] HKCFI 471)",
                "  - Regulation/Cap names and codes: Extract full names and codes (e.g., 'Construction Sites (Safety) Regulations (Cap. 59I)')",
                "  - Dates: Extract all dates or years (e.g., 2023, 2024-05-15, '16 January 1996')",
                "  - Monetary amounts: Extract values with units (e.g., HK$1.3 million, over HK$4 million)",
                "  - Other numbers: Extract regulation/section numbers or similar (e.g., Regulation 39, Section 10T)",
                "For each extracted factual element, check for semantic match in the retrieval context first; if not found, then check the input",
                "Verify semantic matching for each type against retrieval context or input (meaning equivalent, allowing format/phrasing variations):",
                "  - Case numbers: Core components (year, court code, sequence) must convey the same case in either source",
                "  - Regulation/Cap: Core name and code must refer to the same regulation without substantive changes in either source",
                "  - Dates: Values must be semantically equivalent (same day/year, ignoring format variations like 'January 16, 1996' vs. '1996-01-16T...' or minor rephrasing) in either source—no approximations like 'around 2023'",
                "  - Amounts: Numerical value, unit, and qualifiers (e.g., 'over' or 'nearly') must convey the same amount in either source",
                "  - Other numbers: Value and context (e.g., regulation number) must refer to the same element in either source",
                "Assign a significantly low score (0-2) only for substantive mismatches, fabrications (not in retrieval or input), or clear partial matching across any element",
                "Assign a low score (3-4) for minor additions of facts not present in either the retrieval context or input",
                "Outputs with semantically equivalent matches across all factual elements to the retrieval context or input receive a full score (10.0)"
            ],
            evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT, LLMTestCaseParams.RETRIEVAL_CONTEXT],
            rubric=[
                Rubric(score_range=(0, 2), expected_outcome="Substantive factual errors, including mismatches, fabrications (facts not in retrieval context or input), or partial matches in case numbers, regulation/cap names/codes, dates, monetary amounts, or other numerical values (beyond semantic equivalence)."),
                Rubric(score_range=(3, 4), expected_outcome="Minor additions of facts not present in the retrieval context or input."),
                Rubric(score_range=(10, 10), expected_outcome="100% factually accurate with no substantive errors—all factual elements semantically match the retrieval context or input (format variations acceptable).")
            ]
        )
        
        
        
        
        # # Legal Faithfulness Metric
        # legal_relevance = GEval(
        #     model=model,
        #     name="Legal Relevance",
        #     evaluation_steps=[
        #             "Extract key legal elements from the input query, including facts, legal issues, specific statutes, case types, or required precedents.",
        #             "Assess the retrieved contextual information (e.g., statutes, judgments) for coverage of these elements, focusing on semantic relevance and applicability.",
        #             "Identify gaps, irrelevant details, or mismatches (e.g., unrelated case law or outdated statutes) that fail to satisfy the query's legal needs.",
        #             "Heavily penalize low coverage or hallucinations in retrieval (e.g., irrelevant documents that could mislead legal analysis).",
        #             "Provide reasons for the relevance score, highlighting how well the retrieval supports accurate legal response and potential risks of poor matches."
        #         ],
        #     evaluation_params=[LLMTestCaseParams.INPUT,  LLMTestCaseParams.RETRIEVAL_CONTEXT],
        #     threshold=0.5
        # )        
        # Legal Faithfulness Metric
        legal_relevance = GEval(
            model=model,
            name="Legal Relevance",
            evaluation_steps=[
                    "Extract key legal elements from the input query, including facts, legal issues, specific statutes, case types, or required precedents.",
                    "Assess the retrieved contextual information (e.g., statutes, judgments) for coverage of these elements, focusing on semantic relevance and applicability.",
                    "Identify gaps, irrelevant details, or mismatches (e.g., unrelated case law or outdated statutes) that fail to satisfy the query's legal needs.",
                    "Provide reasons for the relevance score, highlighting how well the retrieval supports accurate legal response and potential risks of poor matches."
                ],
            evaluation_params=[LLMTestCaseParams.INPUT,  LLMTestCaseParams.RETRIEVAL_CONTEXT],
            threshold=0.5
        )
        
        # 执行评估
        
        if retrieval_context == "No retrieval context":
            legal_relevance.score = 1
            legal_relevance.reason = "No retrieval context"
            case_number_metric.score = 1
            case_number_metric.reason = "No retrieval context"
            total_cost = case_number_metric.evaluation_cost
        else:
            case_number_metric.measure(test_case)
            legal_relevance.measure(test_case)

            total_cost = case_number_metric.evaluation_cost + legal_relevance.evaluation_cost
        
        # 存储结果
        result_row = {
            'test_id': 1,  # Single evaluation, so fixed ID
            'case_number_score': case_number_metric.score,
            'case_number_reason': str(case_number_metric.reason),
            'case_number_cost': case_number_metric.evaluation_cost,
            'legal_score': legal_relevance.score,
            'legal_reason': str(legal_relevance.reason),
            'legal_cost': legal_relevance.evaluation_cost,
            'total_cost': total_cost,
            'input': query,
            'actual_output': output,
            'retrieval_context': retrieval_context
        }
        result={
            "case_number": {"score": case_number_metric.score, "explain": str(case_number_metric.reason)},
            "legal_relevance": {"score": legal_relevance.score, "explain": str(legal_relevance.reason)}
        }

# 保存到 Excel 文件
        dir_path = r'D:\data\eval_recording'
        os.makedirs(dir_path, exist_ok=True)
        today = datetime.now().strftime('%Y-%m-%d')
        excel_file = os.path.join(dir_path, f'eval_results_{today}.xlsx')
        
        df_new = pd.DataFrame([result_row])
        if os.path.exists(excel_file):
            df_existing = pd.read_excel(excel_file)
            df = pd.concat([df_existing, df_new], ignore_index=True)
        else:
            df = df_new
        df.to_excel(excel_file, index=False)
        
        return result
    except Exception as e:
        logging.error(f"Error during evaluation: {e}")
        return {
            "case_number": {"score": None, "explain": f"Error: {e}"},
            "legal": {"score": None, "explain": f"Error: {e}"}
        }
