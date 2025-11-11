from .draft_document import draft_document
from .get_case_info import get_case_info
from .list_documents import list_documents
from .read_document import read_docucment


tools = [draft_document, get_case_info, list_documents, read_docucment]
tools_by_name = {tool.name: tool for tool in tools}