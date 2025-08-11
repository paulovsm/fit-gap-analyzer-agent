from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from .base_models import AnalysisStatus, BusinessImpact, SAPModule, AnalysisType


class FileUploadInfo(BaseModel):
    """Informações do arquivo carregado"""
    filename: str
    file_size: int
    content_type: str
    file_path: str
    uploaded_at: datetime


class AnalysisRequest(BaseModel):
    """Requisição de análise SAP"""
    presentation_id: str = Field(..., description="ID da apresentação no Firestore")
    requirements_file_info: Optional[FileUploadInfo] = Field(None, description="Informações do arquivo de requisitos carregado")
    meeting_transcript_id: Optional[str] = Field(None, description="ID da transcrição da reunião")
    sap_module: SAPModule = Field(..., description="Módulo SAP a ser analisado")
    analysis_type: AnalysisType = Field(AnalysisType.FULL_ANALYSIS, description="Tipo de análise")
    additional_context: Optional[str] = Field(None, description="Contexto adicional para análise")


class RequirementAnalysis(BaseModel):
    """Análise de um requisito específico"""
    requirement_id: str
    requirement_description: str
    core_process_analysis: str
    core_process_page_numbers: List[int]
    core_process_explanation: str
    is_gap: bool
    gap_reason: Optional[str] = None
    gap_justification: Optional[str] = None
    transcript_reference: Optional[str] = None
    transcript_page_numbers: List[int] = []
    business_impact: BusinessImpact
    final_conclusion: str


class ProcessAnalysis(BaseModel):
    """Análise detalhada de processo"""
    process_name: str
    process_description: str
    page_number: int
    process_flow: str
    key_steps: List[str]
    business_rules: List[str]
    integration_points: List[str]
    potential_gaps: List[str]


class AnalysisResult(BaseModel):
    """Resultado completo da análise"""
    analysis_id: str
    presentation_analysis: List[ProcessAnalysis]
    requirements_analysis: List[RequirementAnalysis]
    overall_summary: str
    total_requirements: int
    gaps_identified: int
    high_impact_gaps: int
    recommendations: List[str]
    next_steps: List[str]
    created_at: datetime
    processing_time_seconds: float


class AnalysisResponse(BaseModel):
    """Resposta da API de análise"""
    analysis_id: str
    status: AnalysisStatus
    progress_percentage: float = 0.0
    current_stage: Optional[str] = None
    result: Optional[AnalysisResult] = None
    error_message: Optional[str] = None
    created_at: datetime
    estimated_completion_time: Optional[datetime] = None


class AnalysisStatusResponse(BaseModel):
    """Resposta de status da análise"""
    analysis_id: str
    status: AnalysisStatus
    progress_percentage: float
    current_stage: Optional[str] = None
    estimated_completion_time: Optional[datetime] = None
    created_at: datetime
    error_message: Optional[str] = None
