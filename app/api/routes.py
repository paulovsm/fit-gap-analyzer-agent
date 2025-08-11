from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from typing import Dict, Any, Optional, List
from datetime import datetime
import structlog
from app.models.api_models import (
    AnalysisRequest,
    AnalysisResponse,
    AnalysisStatusResponse,
    AnalysisResult,
    AnalysisStatus
)
from app.services.analysis_service import analysis_service

logger = structlog.get_logger()

# Router para endpoints de análise
analysis_router = APIRouter(prefix="/analysis", tags=["analysis"])


@analysis_router.post("/start", response_model=AnalysisResponse)
async def start_analysis(request: AnalysisRequest) -> AnalysisResponse:
    """
    Inicia uma nova análise SAP
    
    Args:
        request: Dados da requisição de análise
        
    Returns:
        Resposta com ID da análise e status inicial
        
    Raises:
        HTTPException: Se houver erro na validação ou processamento
    """
    try:
        logger.info(
            "Received analysis request",
            sap_module=request.sap_module,
            presentation_id=request.presentation_id,
            analysis_type=request.analysis_type
        )
        
        # Validar dados obrigatórios
        if not request.presentation_id:
            raise HTTPException(
                status_code=400,
                detail="presentation_id é obrigatório"
            )
        
        # Iniciar análise
        response = await analysis_service.start_analysis(request)
        
        logger.info(
            "Analysis started successfully",
            analysis_id=response.analysis_id
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error starting analysis", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@analysis_router.get("/{analysis_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(analysis_id: str) -> AnalysisStatusResponse:
    """
    Obtém o status atual de uma análise
    
    Args:
        analysis_id: ID da análise
        
    Returns:
        Status atual da análise
        
    Raises:
        HTTPException: Se a análise não for encontrada
    """
    try:
        status_data = await analysis_service.get_analysis_status(analysis_id)
        
        if not status_data:
            raise HTTPException(
                status_code=404,
                detail=f"Análise {analysis_id} não encontrada"
            )
        
        return AnalysisStatusResponse(
            analysis_id=analysis_id,
            status=AnalysisStatus(status_data["status"]),
            progress_percentage=status_data.get("progress_percentage", 0.0),
            current_stage=status_data.get("current_stage"),
            estimated_completion_time=None,  # Pode ser calculado baseado no progresso
            created_at=datetime.fromisoformat(status_data["created_at"]),
            error_message=status_data.get("error_message")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting analysis status",
            analysis_id=analysis_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@analysis_router.get("/{analysis_id}/result")
async def get_analysis_result(analysis_id: str) -> Dict[str, Any]:
    """
    Obtém o resultado completo de uma análise
    
    Args:
        analysis_id: ID da análise
        
    Returns:
        Resultado completo da análise
        
    Raises:
        HTTPException: Se a análise não for encontrada ou não estiver concluída
    """
    try:
        # Verificar status primeiro
        status_data = await analysis_service.get_analysis_status(analysis_id)
        
        if not status_data:
            raise HTTPException(
                status_code=404,
                detail=f"Análise {analysis_id} não encontrada"
            )
        
        if status_data["status"] != AnalysisStatus.COMPLETED.value:
            raise HTTPException(
                status_code=400,
                detail=f"Análise ainda não concluída. Status atual: {status_data['status']}"
            )
        
        # Obter resultado
        result = await analysis_service.get_analysis_result(analysis_id)
        
        if not result:
            # Se não tem resultado no Firestore, mas status diz que tem, usar do store
            if "result" in status_data:
                result = status_data["result"]
            else:
                raise HTTPException(
                    status_code=404,
                    detail="Resultado da análise não encontrado"
                )
        
        logger.info(
            "Analysis result retrieved",
            analysis_id=analysis_id
        )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error getting analysis result",
            analysis_id=analysis_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@analysis_router.get("/active")
async def list_active_analyses() -> List[Dict[str, Any]]:
    """
    Lista todas as análises ativas (em andamento)
    
    Returns:
        Lista de análises ativas
    """
    try:
        active_analyses = await analysis_service.list_active_analyses()
        
        logger.info(
            "Active analyses listed",
            count=len(active_analyses)
        )
        
        return active_analyses
        
    except Exception as e:
        logger.error("Error listing active analyses", error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


@analysis_router.delete("/{analysis_id}")
async def cancel_analysis(analysis_id: str) -> Dict[str, str]:
    """
    Cancela uma análise em andamento
    
    Args:
        analysis_id: ID da análise
        
    Returns:
        Confirmação de cancelamento
        
    Raises:
        HTTPException: Se a análise não for encontrada ou não puder ser cancelada
    """
    try:
        # Verificar se a análise existe
        status_data = await analysis_service.get_analysis_status(analysis_id)
        
        if not status_data:
            raise HTTPException(
                status_code=404,
                detail=f"Análise {analysis_id} não encontrada"
            )
        
        current_status = status_data["status"]
        
        if current_status in [AnalysisStatus.COMPLETED.value, AnalysisStatus.ERROR.value]:
            raise HTTPException(
                status_code=400,
                detail=f"Não é possível cancelar análise com status: {current_status}"
            )
        
        # TODO: Implementar cancelamento da tarefa Celery
        # celery_app.control.revoke(task_id, terminate=True)
        
        logger.info(
            "Analysis cancelled",
            analysis_id=analysis_id
        )
        
        return {"message": f"Análise {analysis_id} cancelada com sucesso"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            "Error cancelling analysis",
            analysis_id=analysis_id,
            error=str(e)
        )
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno: {str(e)}"
        )


# Health check endpoint
@analysis_router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Endpoint de health check
    
    Returns:
        Status de saúde da API
    """
    return {
        "status": "healthy",
        "service": "sap-analysis-api",
        "timestamp": datetime.utcnow().isoformat()
    }
