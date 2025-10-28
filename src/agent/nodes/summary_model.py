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
    prompt="""  
    You are a specialized Legal AI Assistant 
    answer user queries by supporting information from ordinances and judgments.
    """
    
    
    messages = [
        SystemMessage(
            content=prompt
        )
    ] + state.messages
    
    # response = await model_with_tools.ainvoke(messages)
    response = await model.ainvoke(messages)
    return {"messages": [response]}
