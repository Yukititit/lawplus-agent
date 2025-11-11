from langchain_openai import AzureChatOpenAI
from langchain.messages import SystemMessage


model = AzureChatOpenAI(
    model_name="gpt-4.1-mini",
    api_version="2024-12-01-preview",
)

from agent.tools import tools


async def case_assistant(state: any, runtime: any) -> any:
    """Process input and returns output.

    Can use runtime context to alter behavior.
    """

    prompt = """  
    You are a specialized Legal AI Assistant 
    answer user queries.
    """
    messages = [SystemMessage(content=prompt)] + state.messages

    # Augment the LLM with tools
    model_with_tools = model.bind_tools(tools)

    response = await model_with_tools.ainvoke(messages)

    return {"messages": [response]}
