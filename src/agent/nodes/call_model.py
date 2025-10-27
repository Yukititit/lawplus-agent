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


async def call_model(state: any, runtime: any) -> any:
    """Process input and returns output.

    Can use runtime context to alter behavior.
    """

    messages = [
        SystemMessage(
            content="You are a helpful assistant that helps lawyer to process with a case."
        )
    ] + state.messages

    response = await model_with_tools.ainvoke(messages)
    return {"messages": response}
