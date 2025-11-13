from typing import Any, Optional
from langchain.tools import tool, ToolRuntime

from src.db import Session
from src.db.models import Case


@tool
def get_case_info(runtime: Optional[Any] = None) -> str:
    """Get Case Information"""

    db = Session()
    case = db.query(Case).filter(Case.id == runtime.case_id).first()

    case_profile = f"""
 {'\n'.join(
    [f"**{session.key}**\n{'\n'.join([profile.value for profile in session.profiles])}" 
    for session in case.profile_sessions if session.profiles
 ])}
"""
    db.close()
    return case_profile
