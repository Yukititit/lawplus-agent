from typing import Any, Optional
from langchain.tools import tool, ToolRuntime

from src.db import Session
from src.db.models import Case


@tool
def get_case_info(runtime: Optional[Any] = None) -> str:
    """Get Case Information"""

    db = Session()
    case = db.query(Case).filter(Case.id == runtime.case_id).first()

    case_profile = ""
    for session in case.profile_sessions:
        if not session.profiles:
            continue

        case_profile += f"**{session.key}**" + "\n"
        for profile in session.profiles:
            case_profile += profile.value + "\n"

    db.close()
    return case_profile
