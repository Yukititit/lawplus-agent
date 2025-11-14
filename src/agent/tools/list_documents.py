from typing import Any, Optional
from langchain.tools import tool

from src.db import Session
from src.db.models import Document


# Define tools
@tool
def list_documents(runtime: Optional[Any] = None) -> str:
    """List all documents in the case."""

    db = Session()
    documents = (
        db.query(Document)
        .filter(
            Document.case_id == runtime.case_id,
            Document.deleted == False,
            Document.processed == True,
        )
        .all()
    )

    docs = []
    for document in documents:
        analysis = document.upload.document_analysis

        docs.append(
            {
                "id": str(document.id),
                "uid": str(document.upload_id),
                "type": analysis.doc_type,
                "summary": analysis.summary,
                "dated": analysis.dated,
            }
        )

    db.close()
    return docs
