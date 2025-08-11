from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from .base_models import TranscriptionStatus, BaseAnalysisModel


class SlideElement(BaseModel):
    """Representa um elemento individual de um slide"""
    element_id: str
    element_type: str  # diagram, chart, text_block, image, etc.
    raw_content: Optional[str] = None  # Texto extraído ou caminho para imagem
    semantic_analysis: Dict[str, Any]
    relationships_to_other_elements: Optional[List[Dict[str, Any]]] = None


class SlideData(BaseModel):
    """Dados completos de um slide"""
    slide_number: int
    slide_title: Optional[str] = None
    slide_summary: str
    elements: List[SlideElement]


class PresentationMetadata(BaseModel):
    """Metadados da apresentação"""
    presentation_title: str
    presentation_date: datetime
    participants: List[str]
    presentation_type: str
    topics: List[str]
    language: Optional[str] = "pt-BR"


class PresentationTranscription(BaseModel):
    """Estrutura principal de transcrição de apresentação"""
    presentation_metadata: PresentationMetadata
    overall_summary: str
    key_concepts: List[str]
    narrative_flow_analysis: str
    slides: List[SlideData]


class TranscriptionRequest(BaseModel):
    """Requisição de transcrição de apresentação"""
    file_name: str
    presentation_title: Optional[str] = None
    presentation_date: Optional[datetime] = None
    author: Optional[str] = None
    presentation_type: Optional[str] = None
    language_code: str = "pt-BR"
    detailed_analysis: bool = True


class PresentationTranscriptionResponse(BaseModel):
    """Resposta da transcrição de apresentação"""
    id: str
    status: TranscriptionStatus
    file_name: str
    slides_count: Optional[int] = None
    transcription: Optional[PresentationTranscription] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    processing_time_seconds: Optional[float] = None


class TranscriptionSegment(BaseModel):
    """Segmento de transcrição com speaker diarization"""
    start_time: float
    end_time: float
    text: str
    confidence: float
    speaker_tag: Optional[str] = None


class MeetingMetadata(BaseModel):
    """Metadados da reunião"""
    meeting_title: str
    meeting_date: datetime
    participants: List[str]
    meeting_type: str
    topics: List[str]
    action_items: List[str]
    decisions: List[str]
    key_points: List[str]
    sentiment: Optional[str] = None
    urgency_level: Optional[str] = None
    follow_up_required: bool = False


class MeetingTranscriptionRequest(BaseModel):
    """Requisição de transcrição de reunião"""
    file_name: str
    meeting_title: Optional[str] = None
    meeting_date: Optional[datetime] = None
    participants: Optional[List[str]] = None
    meeting_type: Optional[str] = None
    language_code: str = "pt-BR"
    enhance_transcription: bool = True


class MeetingTranscriptionResponse(BaseModel):
    """Resposta da transcrição de reunião"""
    id: str
    status: TranscriptionStatus
    file_name: str
    duration_seconds: Optional[float] = None
    segments: Optional[List[TranscriptionSegment]] = None
    full_text: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Optional[MeetingMetadata] = None
    summary: Optional[str] = None
    meeting_minutes: Optional[str] = None


class BusinessRequirement(BaseModel):
    """Requisito de negócio"""
    requirement_id: str = Field(alias="Key")
    description: str = Field(alias="Description")
    priority: Optional[str] = None
    category: Optional[str] = None
    source: Optional[str] = None
    stakeholder: Optional[str] = None
    acceptance_criteria: Optional[str] = None
