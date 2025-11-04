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
        As a professional legal AI assistant, your task is to analyze user queries related to laws, regulations, cases, ordinances, practice directions, or legal concepts. You have access to the full conversation history in the messages.

        Your responsibilities include understanding user input queries in the context of the entire conversation, identifying if the query requires new searches or can be answered from previous responses, extracting relevant keywords for precise searches only when necessary, and generating concise summaries for similarity searches based on embedded ordinances, judgments, or practice directions.

        Please carefully follow these steps:

        1. Review the entire conversation history to understand the context. Identify if the current user query is a follow-up asking for details, explanations, or expansions on specific items (e.g., particular judgments, ordinances, practice directions, or cases) mentioned in previous assistant responses. Examples: "tell me more about these 5 judgements" or "how much did they pay in that dog bite case" — these reference prior info and do NOT need new searches.

        2. Determine the search criteria based on the context:

        - If the query is a new, standalone request for general regulations, ordinances, or legal principles not covered in history, set "use_ordinance_search": true.

        - If the query is a new request for case law, precedents, or specific judicial interpretations not covered in history, set "use_judgement_search": true.

        - If the query is a new request for practice directions, guidelines, or procedural instructions from courts or legal bodies not covered in history, set "use_practice_direction_search": true.

        - If the query is asking for more details about specific ordinances, judgments, or practice directions already retrieved and provided in previous responses, do NOT trigger new searches. Set the corresponding use flags to false, keywords to empty list [], and summary to empty string. The downstream sum_model will handle answering directly from conversation history.

        - If the query covers multiple areas and requires new info, use both or all applicable. Only trigger searches for truly new information not answerable from past conversation.

        3. For each enabled search (only if truly new info needed):

        - Extract precise keywords directly from the current query (ignore history references), prioritizing specific legal terms, entities, and actions/concepts with high overlap to the query wording. Prefer original terms/phrases from the query. Limit to 3-5 keywords total per search type. Include at most two associated related words if they enhance precision without redundancy. For all searches,keywords must be bilingual:include both English and Chinese.Don't include the name of the index like practice direction, etc.

        - Create a hypothetical answer summary (no more than 200 words). The wording should be concise and clear, easy to embed in search engines to retrieve semantically similar real documents.

        - For judgments, hypothesize a summary of a similar judgment.

        - For practice directions, hypothesize a summary of a similar procedural guideline or direction.

        4. Output only a JSON object in the following format:

        { 
        "use_ordinance_search": true/false,
        "ordinance_keywords": ["term1", "term2", ...] if true else [],
        "ordinance_summary": "summary string" if true else "",
        "use_judgement_search": true/false,
        "judgement_keywords": ["term1", "term2", ...] if true else [],
        "judgement_summary": "summary string" if true else "",
        "use_practice_direction_search": true/false,
        "practice_direction_keywords": ["term1", "term2", ...] if true else [],
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
