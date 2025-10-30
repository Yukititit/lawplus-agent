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


async def process_query(state: any, runtime: any) -> any:
    """Process input and returns output.

    Can use runtime context to alter behavior.
    """
    
    prompt="""  
        As a professional legal AI assistant, your task is to analyze user queries related to laws, regulations, cases, statutes, or legal concepts. Your responsibility includes understanding the user's input query, identifying the need to search for statutes or judgements, extracting relevant keywords for precise searches, and generating a concise summary for similarity searches based on the embedded statutes or judgements.

        Please carefully follow these steps:

        1. Read the user's input to identify the legal subject, entity, action, or concept, as well as the context.

        2. Determine the search criteria:
        - For queries involving statutes, regulations, or general legal principles, use "ordinance_search."
        - For queries involving case law, precedents, or specific judicial interpretations, use "judgement_search."
        - If the query covers both areas or doesn't specify, use both queries.
        

        3. For each enabled search:
        - Extract precise keywords from the query, prioritizing specific legal terms, entities, and actions/concepts. Avoid using generics and ensure that the keywords are searchable.For each keyword, include both its English and Chinese equivalents in the list.
        - Create a hypothetical answer.
            - For a judgement, hypothesize a summary of a similar judgement.
            example:"The facts of the case involve a dispute between a mother (Plaintiff) and her daughter (Defendant) over the beneficial ownership and possession of a property in Taikoo Shing, Hong Kong. The Plaintiff, as the registered owner, sought recovery of vacant possession from the Defendant, who claimed beneficial ownership based on an alleged 1989 oral agreement and oral representations. Ultimately, the court rendered a decision refusing the Defendant's application for leave to appeal against the judgement that ordered the Defendant to deliver vacant possession and pay mesne profits and expenses, stating that the Defendant's grounds for appeal lacked reasonable prospects of success and that no apparent bias or procedural unfairness was found."
            - For an ordinance, hypothesize the content of the legal provision.
            example:"2. Who are Mediators?\nMediators would not provide legal advice and would not take sides. They would not impose any decisions on the parties. Unlike Court proceedings or arbitrations, mediators are not there to determine the disputes or issues between the parties but merely to facilitate settlement.\n \nThere are a number of organizations in Hong Kong which provide lists of mediators. The major providers are: the Hong Kong Bar Association, the Law Society of Hong Kong and the Hong Kong International Arbitration Centre.\n"
        (No more than 500 words) Keep the wording concise and easy to embed in a search to retrieve real documents with similar semantics.

        4. Output only a JSON object of the following format:

        {
        "use_ordinance_search": true/false,
        "ordinance_keywords": ["term1", "term2", ...] 
        "ordinance_summary": "Summary string" (If false, returns an empty string)
        "use_judgement_search": true/false,
        "judgement_keywords": ["term1", "term2", ...] 
        "judgement_summary": "Summary string" 
        }

        No additional text, instructions, or wrappers are required.

    """
    messages = [
        SystemMessage(
            content=prompt
        )
    ] + state.messages


    # response = await model_with_tools.ainvoke(messages)
    response = await model.ainvoke(messages)
    print("messages:", messages)
    print("response", response)

    return {"messages": [response]}
