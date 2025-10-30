from langchain_openai import AzureChatOpenAI
from langchain.messages import SystemMessage

model = AzureChatOpenAI(
    model_name="gpt-4.1-mini",
    api_version="2024-12-01-preview",
)

from agent.tools import get_case_info

# Augment the LLM with tools
tools = [get_case_info]
tools_by_name = {tool.name: tool for tool in tools}
model_with_tools = model.bind_tools(tools)


async def sum_model(state: any, runtime: any) -> any:
    """Process input and returns output.

    Can use runtime context to alter behavior.
    """

    ord_hist = getattr(state, 'ord_search_history', None)
    jud_hist = getattr(state, 'jud_search_history', None)
    if ord_hist is not None and len(ord_hist) > 0:
        ord_search_results_all = ord_hist
    else:
        ord_search_results_all = [getattr(state, 'ord_search_results', [])]
    if jud_hist is not None and len(jud_hist) > 0:
        jud_search_results_all = jud_hist
    else:
        jud_search_results_all = [getattr(state, 'jud_search_results', [])]
    prompt=f"""  
    As a specialized Legal AI Assistant, your task is to provide accurate, concise, and evidence-based responses to user queries on legal matters using only the information provided in the attached documents. You must strictly limit your responses to the content within the attached documents, including ordinances, judgments, statutes, case law excerpts, and any other referenced materials. Do not introduce, speculate on, or reference any external knowledge, facts, laws, or interpretations beyond what is explicitly contained in these documents. If a query cannot be fully or partially addressed using only the provided materials, you should clearly state this and explain why, without adding unsubstantiated details.

    When a query requires a comprehensive response, such as combining results from multiple tools (e.g., case details and related ordinances), you should do so while clearly citing all references in the specified formats (`judgement {id}`, `ordinance: [index]`, `knowledge: [index]`). In every response, you **must** clearly indicate which ordinances and/or judgments were used to support the answer. List them explicitly at the end of your response in a **Markdown-formatted section** titled **"Sources Used"**, using bullet points for each item (e.g., - Ordinance [index]: Brief description of relevance; - Judgement {id}: Brief summary of key ruling applied). If no specific sources were used (e.g., query unanswerable), note this in the section.

    Please ensure that you utilize the related ordinances and judgments provided in the specified formats to support your responses.

    Ensure that your responses are well-structured, accurately reflect the information in the documents, and adhere to the guidelines provided.

    Here are some supporting informations.
    related ordinances (all history rounds):{ord_search_results_all}
    related judgements (all history rounds):{jud_search_results_all}
    If search results are empty, answer based solely on conversation history, extracting details from prior responses.
    """
    messages = [
        SystemMessage(
            content=prompt
        )
    ] + state.messages

    response = await model.ainvoke(messages)
    return {"messages": [response]}
