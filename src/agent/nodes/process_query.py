from agent.tools import get_case_info
from langchain_openai import AzureChatOpenAI
from langchain.messages import SystemMessage


model = AzureChatOpenAI(
    model_name="gpt-4.1-mini",
    api_version="2024-12-01-preview",
)


# Augment the LLM with tools

tools = [get_case_info]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)


async def process_query(state: any, runtime: any) -> any:
    """Process input and returns output.

    Can use runtime context to alter behavior.
    """

    prompt = """
        As a professional legal AI assistant, your task is to analyze user queries related to laws, regulations, cases, ordinances, practice directions, or legal concepts. Your responsibilities include understanding user input queries in the context of the entire conversation, identifying if the query requires new searches or can be answered from previous responses, extracting relevant keywords for precise searches only when necessary, and generating concise summaries for similarity searches based on embedded ordinances, judgments, or practice directions.

        Please carefully follow these steps:

        1. Review the entire conversation history to understand the context. Identify if the current user query is a follow-up asking for details, explanations, or expansions on specific items mentioned in previous assistant responses. 

        2. Determine the search criteria based on the context:

        - First, check if the query can be fully answered using information from the conversation history alone. If yes, set ALL use flags (use_ordinance_search, use_judgement_search, use_practice_direction_search) to false, and set all keywords lists and summaries to empty. In this case, no new searches are needed.

        - If the query cannot be fully answered from history (i.e., it requires new information), you MUST trigger at least one search: set at least one use flag to true. Prioritize based on query type:
          - If the query describes a specific case scenario, court proceeding, or factual dispute involving judicial decisions, rulings, or discovery processes, prioritize and set use_judgement_search to true.
          - If the query is a new, standalone request for general legal information not covered in history, set the corresponding search flags to true (e.g., use_ordinance_search for statutory queries). Only if the query explicitly specifies focusing solely on certain types of information, set the others to false.
          - If the query covers multiple areas and requires new info, use both or all applicable to ensure at least one is true. For general queries without explicit specification, prioritize using both for fuller context.
        3. For each enabled search (only if truly new info needed):

        - Extract keywords from the current query, prioritizing specific legal terms, entities, and actions/concepts that are closely related special vocabulary with high overlap to the query wording. 
        Keywords must be directly tied to the query's core elements; do not include synonymous word groups or redundant variations. Extract English keywords into the English list and Chinese keywords into the separate Chinese list. Do not include the name of the index. When the query involves amounts or numerical values, extract them independently as separate keywords in both lists (e.g., English: ["70 million HKD"], Chinese: ["7000萬港元"]), preserving the original format and complete units (HKD, years, sq ft etc.) for precise matching. 

        *** STRICT UNIVERSAL VOCABULARY RULES - VIOLATION WILL CAUSE WRONG RETRIEVAL ***
        - ONLY extract keywords that are HIGHLY SPECIFIC to this particular legal issue and can uniquely distinguish this case from thousands of others.
        - A keyword is valid ONLY if it satisfies **ALL THREE** conditions simultaneously:
            1. 1. It is a proper noun (person/company/case name), 
            2. or a dedicated legal term (e.g. "constructive dismissal", "adverse possession", "無效婚姻"), 
            3. or a key factual element (specific act/object like "share option backdating", "roof seepage", "ICAC investigation").
        - MUST EXCLUDE all generic/legal universal words. Here is the **blacklist** (including but not limited): 
          English: law, legal, case, judgment, ordinance, court, issue, problem, consult, dispute, claim, breach, violation, rights, liability, evidence, appeal, section, article, act
          Chinese: 法律, 法例, 條例, 判決, 案例, 案件, 問題, 咨詢, 爭議, 違反, 權利, 責任, 證據, 上訴, 第, 條, 法
        - If a word is in the blacklist or its synonym/variation, **immediately discard it**.
        - For short queries (≤15 words), max 2 keywords; for longer, max 4 keywords total.
        - Sort by **uniqueness importance**: most critical first (the one that, if removed, would make retrieval fail).
        
        **Example**:
        Query: "我老公隱瞞有精神病同我結咗婚，可唔可以告無效婚姻？"
        → Valid: 
        English: ["annulment", "mental disorder"]  
        Chinese: ["無效婚姻", "精神病"]  
        → Invalid & discarded: 結婚, 隱瞞, 告, 法律 etc.

        - Create a hypothetical answer summary (no more than 100 words) using the HyDE (Hypothetical Document Embeddings) RAG technique: First, generate a concise, self-contained response as if directly answering the user's query based on your knowledge of legal concepts. This hypothetical document should cover key facts, explanations, relevant principles, and implications in a natural, informative style, but tailored to mimic the style of the target dataset for better semantic matching:
          - For ordinance_summary: Use formal statutory language, structured like legal ordinances with sections, articles, definitions, and prescriptive clauses.
          - For judgement_summary: Adopt a judicial style for a concise summary of a court judgment, including case background, legal issues, reasoning, and rulings.
          - For practice_direction_summary: Employ procedural and guideline-oriented language, focusing on practical instructions, steps, and directives for legal practitioners.
        The goal is to produce text that, when embedded, retrieves semantically similar real documents from the specific dataset (e.g., ordinances, judgments, or practice directions) for enhanced retrieval accuracy. Ensure it is clear, structured, and focused on the query's core elements without introducing unrelated details.

        - Output only a JSON object in the specified format, ensuring JSON is valid and parseable.

        { 
        "use_ordinance_search": true/false,
        "ordinance_keywords": ["English term", ...] if true else [],
        "ordinance_keywords_chinese": ["Chinese term", ...] if true else [],
        "ordinance_summary": "summary string" if true else "",
        "use_judgement_search": true/false,
        "judgement_keywords": ["English term", ...] if true else [],
        "judgement_keywords_chinese": ["Chinese term", ...] if true else [],
        "judgement_summary": "summary string" if true else "",
        "use_practice_direction_search": true/false,
        "practice_direction_keywords": ["English term", ...] if true else [],
        "practice_direction_keywords_chinese": ["Chinese term", ...] if true else [],
        "practice_direction_summary": "summary string" if true else ""
        }

        No additional text, descriptions, or wrappers are needed. Ensure JSON is valid and parseable.
        
    """
    
    
    
    
    messages = [
        SystemMessage(
            content=prompt
        )
    ] + state.messages

    # response = await model_with_tools.ainvoke(messages)
    response = await model.ainvoke(messages)
    
    return {"messages": [response]}
