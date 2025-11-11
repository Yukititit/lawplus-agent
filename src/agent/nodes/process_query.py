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

        - If the query is a new, standalone request for general legal information not covered in history, set the corresponding search flags to true. Only if the query explicitly specifies focusing solely on certain types of information, set the others to false.

        - If the query is asking for more details about specific legal items already provided in previous responses, do NOT trigger new searches. Set the corresponding use flags to false, keywords to an empty list, and summary to an empty string.

        - If the query covers multiple areas and requires new info, use both or all applicable. Only trigger searches for truly new information not answerable from past conversation. For general queries without explicit specification, prioritize using both for fuller context.

        3. For each enabled search (only if truly new info needed):

        - Extract keywords from the current query, prioritizing specific legal terms, entities, and actions/concepts that are closely related special vocabulary with high overlap to the query wording. 
        Keywords must be directly tied to the query's core elements; do not include synonymous word groups or redundant variations. Extract English keywords into the English list and Chinese keywords into the separate Chinese list. Do not include the name of the index. When the query involves amounts or numerical values, extract them independently as separate keywords in both lists (e.g., English: ["70 million"], Chinese: ["7000萬"]), preserving the original format for precise matching in subsequent Elasticsearch processes. 
        Handle numbers as completely as possible, including units and scales, to maximize retrieval accuracy. Sort keywords in each list by importance, with the most important ones first. 
        For a specific query, there can be no more than 5 keywords; for a short query, there can be a maximum of 3.
        Avoid including keywords that have repeated or redundant meanings.

        - Create a hypothetical answer summary (no more than 200 words) using the HyDE (Hypothetical Document Embeddings) RAG technique: First, generate a concise, self-contained response as if directly answering the user's query based on your knowledge of legal concepts. This hypothetical document should cover key facts, explanations, relevant principles, and implications in a natural, informative style, but tailored to mimic the style of the target dataset for better semantic matching:
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
