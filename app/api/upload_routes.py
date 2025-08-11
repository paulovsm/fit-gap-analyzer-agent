from fastapi import APIRouter, File, UploadFile, Form, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import Optional
import structlog
from datetime import datetime
from pathlib import Path

from app.config.settings import settings
from app.models.api_models import FileUploadInfo, AnalysisRequest
from app.services.requirements_processor import requirements_processor
from app.flows.sap_analysis_flow import SAPAnalysisFlow
from app.models.base_models import SAPModule, AnalysisType

logger = structlog.get_logger()
router = APIRouter(prefix="/upload", tags=["File Upload"])


@router.post("/requirements", response_model=FileUploadInfo)
async def upload_requirements_file(
    file: UploadFile = File(..., description="Arquivo de requisitos (XLSX ou CSV)")
):
    """
    Upload de arquivo de requisitos
    
    Aceita arquivos nos formatos:
    - XLSX (Excel)
    - XLS (Excel legado)
    - CSV (Comma Separated Values)
    """
    try:
        # Validar tipo de arquivo
        file_extension = Path(file.filename).suffix.lower()
        if file_extension not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de arquivo não suportado. Tipos aceitos: {settings.allowed_file_types}"
            )
        
        # Validar tamanho do arquivo
        file_content = await file.read()
        if len(file_content) > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo muito grande. Tamanho máximo: {settings.max_file_size // (1024*1024)}MB"
            )
        
        # Salvar arquivo
        file_path = await requirements_processor.save_uploaded_file(
            file_content, file.filename
        )
        
        # Criar informações do arquivo
        file_info = FileUploadInfo(
            filename=file.filename,
            file_size=len(file_content),
            content_type=file.content_type,
            file_path=file_path,
            uploaded_at=datetime.utcnow()
        )
        
        logger.info(
            "Requirements file uploaded successfully",
            filename=file.filename,
            size=len(file_content),
            path=file_path
        )
        
        return file_info
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error uploading requirements file", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno no upload do arquivo")


@router.post("/analyze-with-file")
async def analyze_with_uploaded_file(
    presentation_id: str = Form(..., description="ID da apresentação no Firestore"),
    sap_module: SAPModule = Form(..., description="Módulo SAP"),
    analysis_type: AnalysisType = Form(AnalysisType.FULL_ANALYSIS, description="Tipo de análise"),
    meeting_transcript_id: Optional[str] = Form(None, description="ID da transcrição da reunião"),
    additional_context: Optional[str] = Form(None, description="Contexto adicional"),
    requirements_file: UploadFile = File(..., description="Arquivo de requisitos")
):
    """
    Inicia análise SAP com upload de arquivo de requisitos
    
    Esta rota combina upload de arquivo e início de análise em uma operação
    """
    try:
        # 1. Upload do arquivo
        file_extension = Path(requirements_file.filename).suffix.lower()
        if file_extension not in settings.allowed_file_types:
            raise HTTPException(
                status_code=400,
                detail=f"Tipo de arquivo não suportado. Tipos aceitos: {settings.allowed_file_types}"
            )
        
        file_content = await requirements_file.read()
        if len(file_content) > settings.max_file_size:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo muito grande. Tamanho máximo: {settings.max_file_size // (1024*1024)}MB"
            )
        
        # Salvar arquivo
        file_path = await requirements_processor.save_uploaded_file(
            file_content, requirements_file.filename
        )
        
        # Criar FileUploadInfo
        file_info = FileUploadInfo(
            filename=requirements_file.filename,
            file_size=len(file_content),
            content_type=requirements_file.content_type,
            file_path=file_path,
            uploaded_at=datetime.utcnow()
        )
        
        # 2. Criar requisição de análise
        analysis_request = AnalysisRequest(
            presentation_id=presentation_id,
            requirements_file_info=file_info,
            meeting_transcript_id=meeting_transcript_id,
            sap_module=sap_module,
            analysis_type=analysis_type,
            additional_context=additional_context
        )
        
        # 3. Iniciar análise
        flow = SAPAnalysisFlow()
        result_message = flow.kickoff(analysis_request)
        
        # 4. Retornar informações
        return {
            "message": "Análise iniciada com sucesso",
            "analysis_id": flow.state.analysis_id,
            "file_info": file_info.model_dump(),
            "status": flow.state.status.value,
            "progress_percentage": flow.state.progress_percentage
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error in analyze_with_uploaded_file", error=str(e))
        raise HTTPException(status_code=500, detail="Erro interno na análise")


@router.get("/preview/{file_path:path}")
async def preview_requirements_file(file_path: str):
    """
    Preview do arquivo de requisitos processado
    
    Retorna uma prévia dos dados estruturados extraídos do arquivo
    """
    try:
        # Verificar se arquivo existe
        full_path = Path(settings.uploads_dir) / file_path
        if not full_path.exists():
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        # Processar arquivo
        requirements_data = await requirements_processor.process_requirements_file(str(full_path))
        
        # Retornar preview (primeiros 10 requisitos)
        preview_data = {
            "metadata": requirements_data["metadata"],
            "sample_requirements": requirements_data["requirements"][:10],
            "total_requirements": len(requirements_data["requirements"]),
            "columns": requirements_data["raw_columns"]
        }
        
        return preview_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error previewing requirements file", error=str(e))
        raise HTTPException(status_code=500, detail="Erro ao processar preview do arquivo")
