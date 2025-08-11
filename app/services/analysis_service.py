from celery import Celery
from typing import Dict, Any, Optional, List
import asyncio
import structlog
from app.config.settings import settings
from app.flows.sap_analysis_flow import SAPAnalysisFlow
from app.models.api_models import AnalysisRequest, AnalysisResponse, AnalysisStatus
from app.services.firestore_service import firestore_service
from datetime import datetime
import uuid

logger = structlog.get_logger()

# Configurar Celery para processamento assíncrono
celery_app = Celery(
    'sap_analysis_service',
    broker=settings.redis_url,
    backend=settings.redis_url
)

# Armazenamento em memória para status das análises (em produção, usar Redis)
analysis_status_store: Dict[str, Dict[str, Any]] = {}


class AnalysisService:
    """Serviço principal para análise SAP com suporte a processamento paralelo"""
    
    def __init__(self):
        """Inicializa o serviço de análise"""
        self.logger = logger.bind(service="analysis")
    
    async def start_analysis(self, request: AnalysisRequest) -> AnalysisResponse:
        """
        Inicia uma nova análise SAP de forma assíncrona
        
        Args:
            request: Requisição de análise
            
        Returns:
            Resposta com ID da análise e status inicial
        """
        try:
            # Gerar ID único para a análise
            analysis_id = str(uuid.uuid4())
            
            # Criar resposta inicial
            response = AnalysisResponse(
                analysis_id=analysis_id,
                status=AnalysisStatus.PENDING,
                progress_percentage=0.0,
                current_stage="Aguardando início do processamento",
                created_at=datetime.utcnow(),
                estimated_completion_time=None
            )
            
            # Armazenar status inicial
            analysis_status_store[analysis_id] = {
                "status": AnalysisStatus.PENDING.value,
                "progress_percentage": 0.0,
                "current_stage": "Aguardando início do processamento",
                "created_at": datetime.utcnow().isoformat(),
                "request": request.model_dump()
            }
            
            # Iniciar processamento em background
            process_analysis_task.delay(analysis_id, request.model_dump())
            
            self.logger.info(
                "Analysis started",
                analysis_id=analysis_id,
                sap_module=request.sap_module,
                presentation_id=request.presentation_id
            )
            
            return response
            
        except Exception as e:
            self.logger.error("Error starting analysis", error=str(e))
            raise
    
    async def get_analysis_status(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém o status atual de uma análise
        
        Args:
            analysis_id: ID da análise
            
        Returns:
            Status da análise ou None se não encontrada
        """
        try:
            # Verificar no store em memória primeiro
            if analysis_id in analysis_status_store:
                return analysis_status_store[analysis_id]
            
            # Se não encontrado em memória, verificar no Firestore
            result = await firestore_service.get_analysis_result(analysis_id)
            if result:
                return {
                    "status": AnalysisStatus.COMPLETED.value,
                    "progress_percentage": 100.0,
                    "current_stage": "Análise concluída",
                    "has_result": True,
                    "result": result
                }
            
            return None
            
        except Exception as e:
            self.logger.error(
                "Error getting analysis status",
                analysis_id=analysis_id,
                error=str(e)
            )
            raise
    
    async def get_analysis_result(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtém o resultado completo de uma análise
        
        Args:
            analysis_id: ID da análise
            
        Returns:
            Resultado da análise ou None se não encontrada
        """
        try:
            result = await firestore_service.get_analysis_result(analysis_id)
            return result
            
        except Exception as e:
            self.logger.error(
                "Error getting analysis result",
                analysis_id=analysis_id,
                error=str(e)
            )
            raise
    
    async def list_active_analyses(self) -> List[Dict[str, Any]]:
        """
        Lista todas as análises ativas (em andamento)
        
        Returns:
            Lista de análises ativas
        """
        try:
            active_analyses = []
            for analysis_id, status_data in analysis_status_store.items():
                if status_data["status"] in [AnalysisStatus.PENDING.value, AnalysisStatus.PROCESSING.value]:
                    active_analyses.append({
                        "analysis_id": analysis_id,
                        **status_data
                    })
            
            return active_analyses
            
        except Exception as e:
            self.logger.error("Error listing active analyses", error=str(e))
            raise


@celery_app.task(bind=True)
def process_analysis_task(self, analysis_id: str, request_data: Dict[str, Any]):
    """
    Tarefa Celery para processar análise SAP em background
    
    Args:
        analysis_id: ID da análise
        request_data: Dados da requisição
    """
    logger_task = logger.bind(task="process_analysis", analysis_id=analysis_id)
    
    try:
        logger_task.info("Starting analysis processing")
        
        # Atualizar status para processando
        analysis_status_store[analysis_id] = {
            **analysis_status_store.get(analysis_id, {}),
            "status": AnalysisStatus.PROCESSING.value,
            "current_stage": "Inicializando processamento",
            "progress_percentage": 5.0
        }
        
        # Criar request object
        request = AnalysisRequest(**request_data)
        
        # Inicializar e executar flow
        flow = SAPAnalysisFlow()
        
        # Callback para atualizar progresso
        def update_progress(stage: str, percentage: float):
            analysis_status_store[analysis_id].update({
                "current_stage": stage,
                "progress_percentage": percentage,
                "status": AnalysisStatus.PROCESSING.value
            })
        
        # Executar flow com callback de progresso
        try:
            # Simular execução do flow (já que não temos o CrewAI instalado)
            # Em produção, seria: result = flow.kickoff(inputs=request.model_dump())
            
            update_progress("Analisando processos de negócio", 25.0)
            # Simular tempo de processamento
            import time
            time.sleep(2)
            
            update_progress("Analisando requisitos", 50.0)
            time.sleep(2)
            
            update_progress("Realizando análise de gaps", 75.0)
            time.sleep(2)
            
            update_progress("Gerando relatório final", 95.0)
            time.sleep(1)
            
            # Simular resultado
            mock_result = {
                "analysis_id": analysis_id,
                "presentation_analysis": [],
                "requirements_analysis": [],
                "overall_summary": f"Análise concluída para módulo {request.sap_module}",
                "total_requirements": 5,
                "gaps_identified": 2,
                "high_impact_gaps": 1,
                "recommendations": [
                    "Implementar processo de aprovação automática",
                    "Configurar validações adicionais"
                ],
                "next_steps": [
                    "Revisar gaps de alta prioridade",
                    "Planejar implementação das melhorias"
                ],
                "created_at": datetime.utcnow().isoformat(),
                "processing_time_seconds": 7.0
            }
            
            # Salvar resultado no Firestore (simulado)
            # await firestore_service.save_analysis_result(analysis_id, mock_result)
            
            # Atualizar status final
            analysis_status_store[analysis_id] = {
                **analysis_status_store[analysis_id],
                "status": AnalysisStatus.COMPLETED.value,
                "current_stage": "Análise concluída",
                "progress_percentage": 100.0,
                "completed_at": datetime.utcnow().isoformat(),
                "result": mock_result
            }
            
            logger_task.info("Analysis completed successfully")
            
        except Exception as flow_error:
            logger_task.error("Error in flow execution", error=str(flow_error))
            analysis_status_store[analysis_id] = {
                **analysis_status_store[analysis_id],
                "status": AnalysisStatus.ERROR.value,
                "error_message": f"Erro na execução do flow: {str(flow_error)}",
                "failed_at": datetime.utcnow().isoformat()
            }
            raise
        
    except Exception as e:
        logger_task.error("Error processing analysis", error=str(e))
        
        # Atualizar status de erro
        analysis_status_store[analysis_id] = {
            **analysis_status_store.get(analysis_id, {}),
            "status": AnalysisStatus.ERROR.value,
            "error_message": str(e),
            "failed_at": datetime.utcnow().isoformat()
        }
        
        # Re-raise para que o Celery marque a tarefa como falha
        raise


# Singleton instance
analysis_service = AnalysisService()
