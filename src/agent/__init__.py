"""New LangGraph Agent.

This module defines a custom graph.
"""

from agent.graphs.case_agent import graph as case_agent
from agent.graphs.research_agent import graph as research_agent

__all__ = ["case_agent", "research_agent"]
