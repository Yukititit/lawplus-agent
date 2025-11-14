from langchain.messages import ToolMessage
from agent.tools import tools_by_name
from typing import Any


async def case_tools(state: Any, runtime: Any) -> Any:
    """Performs the tool call"""

    result = []
    for tool_call in state.messages[-1].tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observation = tool.invoke(tool_call["args"] | {"runtime": state})
        result.append(ToolMessage(content=observation, tool_call_id=tool_call["id"]))

    return {"messages": result}
