from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class TranscriptionStatus(str, Enum):
    """Status da transcrição"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class AnalysisStatus(str, Enum):
    """Status da análise"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"


class BusinessImpact(str, Enum):
    """Nível de impacto no negócio"""
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class SAPModule(str, Enum):
    """Módulos SAP suportados"""
    FI = "FI"  # Financial Accounting
    FI_AA = "FI-AA"  # Asset Accounting
    CO = "CO"  # Controlling
    MM = "MM"  # Materials Management
    SD = "SD"  # Sales and Distribution
    PP = "PP"  # Production Planning
    HR = "HR"  # Human Resources
    QM = "QM"  # Quality Management


class AnalysisType(str, Enum):
    """Tipos de análise disponíveis"""
    GAP_ANALYSIS = "gap_analysis"
    PROCESS_REVIEW = "process_review"
    REQUIREMENT_VALIDATION = "requirement_validation"
    FULL_ANALYSIS = "full_analysis"


class BaseAnalysisModel(BaseModel):
    """Modelo base para análises"""
    id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    status: AnalysisStatus = AnalysisStatus.PENDING
    error_message: Optional[str] = None
