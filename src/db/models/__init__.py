"""This module defines the database models for the agent."""

from .task import Task
from .case import Case
from .case_nature import CaseNature
from .upload import Upload
from .document import Document
from .doc_event import DocEvent
from .doc_calendar_event import DocCalendarEvent
from .lawfirm import LawFirm
from .linked_account import LinkedAccount
from .template import Template
from .transcript import Transcript
from .token_usage import TokenUsage
from .document_analysis import DocumentAnalysis
from .document_info import DocumentInfo
from .document_party import DocumentParty
from .document_party_info import DocumentPartyInfo
from .research_profile import ResearchProfile
from .pleadings import Pleading
from .subsequent_pleadings import SubsequentPleading
from .stage import Stage
from .subsequent_stages import SubsequentStage
from .mail_analysis import MailAnalysis
from .docpleadingInfos import DocPleadingInfos
from .in_house_contract import InHouseContract
from .in_house_contract_clause import InHouseContractClause
from .in_house_contract_version_group import InHouseContractVersionGroup
from .in_house_document import InHouseDocument
from .in_house_document_analysis import InHouseDocumentAnalysis
from .in_house_contract_event import InHouseContractEvent

__all__ = [
    Task,
    Case,
    CaseNature,
    Upload,
    Document,
    DocEvent,
    DocCalendarEvent,
    LawFirm,
    LinkedAccount,
    MailAnalysis,
    Template,
    Transcript,
    TokenUsage,
    DocumentAnalysis,
    DocumentInfo,
    DocumentParty,
    ResearchProfile,
    DocumentPartyInfo,
    Pleading,
    SubsequentPleading,
    Stage,
    SubsequentStage,
    DocPleadingInfos,
    InHouseContract,
    InHouseContractClause,
    InHouseContractVersionGroup,
    InHouseDocument,
    InHouseDocumentAnalysis,
    InHouseContractEvent,
]
