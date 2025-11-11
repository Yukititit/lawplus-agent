from langchain.tools import tool
from langgraph.config import get_stream_writer;
from langchain_openai import AzureChatOpenAI

@tool
async def draft_document(content: str) -> str:
    """Draft a document for the users
    """

    writer = get_stream_writer()

    llm = AzureChatOpenAI(
        model_name="gpt-4.1-mini",
        api_version="2024-12-01-preview",
    )


    response = ""
    async for chunk in llm.astream(content):  # Your LLM stream
        response += chunk
        writer({"type": "token", "content": chunk})

    return response