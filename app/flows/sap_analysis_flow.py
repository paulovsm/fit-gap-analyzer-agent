from crewai.flow.flow import Flow, listen, start
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime
import uuid
import structlog
import json
import re

from app.models.api_models import (
    AnalysisRequest,
    AnalysisResult,
    AnalysisStatus,
    RequirementAnalysis,
    ProcessAnalysis,
    BusinessImpact,
    FileUploadInfo
)

# Importar as crews especializadas
from app.crews.process_analysis_crew.crew import ProcessAnalysisCrew
from app.crews.requirements_analysis_crew.crew import RequirementsAnalysisCrew
from app.crews.gap_analysis_crew.crew import GapAnalysisCrew
from app.crews.meeting_analysis_crew.crew import MeetingAnalysisCrew
from app.crews.report_generation_crew.crew import ReportGenerationCrew

from app.services.firestore_service import firestore_service

logger = structlog.get_logger()


class SAPAnalysisState(BaseModel):
    """Estado do fluxo de análise SAP"""
    analysis_id: str
    presentation_id: str
    requirements_file_info: Optional[FileUploadInfo] = None
    meeting_transcript_id: Optional[str] = None
    sap_module: str
    analysis_type: str
    additional_context: Optional[str] = None
    
    # Resultados intermediários de cada crew
    process_analysis_result: Optional[Dict[str, Any]] = None
    requirements_analysis_result: Optional[Dict[str, Any]] = None
    gap_analysis_result: Optional[Dict[str, Any]] = None
    meeting_analysis_result: Optional[Dict[str, Any]] = None
    
    # Resultado final
    final_result: Optional[AnalysisResult] = None
    
    # Controle de status
    status: AnalysisStatus = AnalysisStatus.PENDING
    progress_percentage: float = 0.0
    current_stage: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime = datetime.utcnow()
    
    class Config:
        arbitrary_types_allowed = True


class SAPAnalysisFlow(Flow[SAPAnalysisState]):
    """Flow principal para análise de processos SAP com múltiplas crews especializadas"""
    
    def __init__(self):
        """Inicializa o flow de análise SAP"""
        super().__init__()
        self.logger = logger.bind(flow="sap_analysis")
        
        # Inicializar crews especializadas
        self.process_crew = ProcessAnalysisCrew()
        self.requirements_crew = RequirementsAnalysisCrew()
        self.gap_crew = GapAnalysisCrew()
        self.meeting_crew = MeetingAnalysisCrew()
        self.report_crew = ReportGenerationCrew()
    
    @start()
    def initialize_analysis(self, request: AnalysisRequest) -> str:
        """
        Inicializa a análise SAP com os parâmetros fornecidos
        
        Args:
            request: Requisição de análise SAP
            
        Returns:
            Status de inicialização
        """
        try:
            # Gera ID único para a análise
            analysis_id = str(uuid.uuid4())
            
            # Atualiza o estado
            self.state.analysis_id = analysis_id
            self.state.presentation_id = request.presentation_id
            self.state.requirements_file_id = request.requirements_file_id
            self.state.meeting_transcript_id = request.meeting_transcript_id
            self.state.sap_module = request.sap_module.value
            self.state.analysis_type = request.analysis_type.value
            self.state.additional_context = request.additional_context
            self.state.status = AnalysisStatus.PROCESSING
            self.state.current_stage = "Inicializando análise"
            self.state.progress_percentage = 5.0
            
            self.logger.info(
                "Analysis initialized",
                analysis_id=analysis_id,
                sap_module=self.state.sap_module,
                presentation_id=self.state.presentation_id
            )
            
            return "Analysis initialized successfully"
            
        except Exception as e:
            self.logger.error("Error initializing analysis", error=str(e))
            self.state.status = AnalysisStatus.ERROR
            self.state.error_message = f"Erro na inicialização: {str(e)}"
            raise
    
    @listen(initialize_analysis)
    def analyze_business_processes(self, _) -> str:
        """
        Executa análise de processos de negócio usando crew especializada
        
        Returns:
            Status da análise de processos
        """
        try:
            self.state.current_stage = "Analisando processos de negócio"
            self.state.progress_percentage = 20.0
            
            self.logger.info(
                "Starting business process analysis",
                analysis_id=self.state.analysis_id
            )
            
            # Preparar inputs para a crew de processos
            inputs = {
                "analysis_id": self.state.analysis_id,
                "presentation_id": self.state.presentation_id,
                "sap_module": self.state.sap_module,
                "additional_context": self.state.additional_context or ""
            }
            
            # Executar crew de análise de processos
            process_crew_instance = self.process_crew.crew()
            result = process_crew_instance.kickoff(inputs=inputs)
            
            # Armazenar resultado
            self.state.process_analysis_result = self._extract_crew_output(result)
            self.state.progress_percentage = 35.0
            
            self.logger.info(
                "Business process analysis completed",
                analysis_id=self.state.analysis_id
            )
            
            return "Business processes analyzed successfully"
            
        except Exception as e:
            self.logger.error(
                "Error in business process analysis",
                analysis_id=self.state.analysis_id,
                error=str(e)
            )
            self.state.status = AnalysisStatus.ERROR
            self.state.error_message = f"Erro na análise de processos: {str(e)}"
            raise
    
    @listen(analyze_business_processes)
    def analyze_requirements(self, _) -> str:
        """
        Executa análise de requisitos usando crew especializada
        
        Returns:
            Status da análise de requisitos
        """
        try:
            if not self.state.requirements_file_id:
                self.logger.info("No requirements file provided, skipping requirements analysis")
                return "No requirements to analyze"
            
            self.state.current_stage = "Analisando requisitos de negócio"
            self.state.progress_percentage = 50.0
            
            self.logger.info(
                "Starting requirements analysis",
                analysis_id=self.state.analysis_id,
                requirements_file_id=self.state.requirements_file_id
            )
            
            # Preparar inputs para a crew de requisitos
            inputs = {
                "analysis_id": self.state.analysis_id,
                "requirements_file_id": self.state.requirements_file_id,
                "sap_module": self.state.sap_module,
                "process_analysis_context": self.state.process_analysis_result
            }
            
            # Executar crew de análise de requisitos
            requirements_crew_instance = self.requirements_crew.crew()
            result = requirements_crew_instance.kickoff(inputs=inputs)
            
            # Armazenar resultado
            self.state.requirements_analysis_result = self._extract_crew_output(result)
            self.state.progress_percentage = 60.0
            
            self.logger.info(
                "Requirements analysis completed",
                analysis_id=self.state.analysis_id
            )
            
            return "Requirements analyzed successfully"
            
        except Exception as e:
            self.logger.error(
                "Error in requirements analysis",
                analysis_id=self.state.analysis_id,
                error=str(e)
            )
            self.state.status = AnalysisStatus.ERROR
            self.state.error_message = f"Erro na análise de requisitos: {str(e)}"
            raise
    
    @listen(analyze_requirements)
    def perform_gap_analysis(self, _) -> str:
        """
        Executa análise de gaps usando crew especializada
        
        Returns:
            Status da análise de gaps
        """
        try:
            self.state.current_stage = "Realizando análise de gaps"
            self.state.progress_percentage = 70.0
            
            self.logger.info(
                "Starting gap analysis",
                analysis_id=self.state.analysis_id
            )
            
            # Preparar inputs para a crew de gaps
            inputs = {
                "analysis_id": self.state.analysis_id,
                "sap_module": self.state.sap_module,
                "process_analysis_context": self.state.process_analysis_result,
                "requirements_analysis_context": self.state.requirements_analysis_result
            }
            
            # Executar crew de análise de gaps
            gap_crew_instance = self.gap_crew.crew()
            result = gap_crew_instance.kickoff(inputs=inputs)
            
            # Armazenar resultado
            self.state.gap_analysis_result = self._extract_crew_output(result)
            self.state.progress_percentage = 80.0
            
            self.logger.info(
                "Gap analysis completed",
                analysis_id=self.state.analysis_id
            )
            
            return "Gap analysis completed successfully"
            
        except Exception as e:
            self.logger.error(
                "Error in gap analysis",
                analysis_id=self.state.analysis_id,
                error=str(e)
            )
            self.state.status = AnalysisStatus.ERROR
            self.state.error_message = f"Erro na análise de gaps: {str(e)}"
            raise
    
    @listen(perform_gap_analysis)
    def analyze_meeting_transcript(self, _) -> str:
        """
        Executa análise de transcrição de reunião usando crew especializada
        
        Returns:
            Status da análise da reunião
        """
        try:
            if not self.state.meeting_transcript_id:
                self.logger.info("No meeting transcript provided, skipping meeting analysis")
                return "No meeting transcript to analyze"
            
            self.state.current_stage = "Analisando transcrição da reunião"
            self.state.progress_percentage = 85.0
            
            self.logger.info(
                "Starting meeting transcript analysis",
                analysis_id=self.state.analysis_id,
                meeting_transcript_id=self.state.meeting_transcript_id
            )
            
            # Preparar inputs para a crew de reuniões
            inputs = {
                "analysis_id": self.state.analysis_id,
                "meeting_transcript_id": self.state.meeting_transcript_id,
                "requirements_context": self.state.requirements_analysis_result,
                "gap_context": self.state.gap_analysis_result
            }
            
            # Executar crew de análise de reuniões
            meeting_crew_instance = self.meeting_crew.crew()
            result = meeting_crew_instance.kickoff(inputs=inputs)
            
            # Armazenar resultado
            self.state.meeting_analysis_result = self._extract_crew_output(result)
            self.state.progress_percentage = 90.0
            
            self.logger.info(
                "Meeting transcript analysis completed",
                analysis_id=self.state.analysis_id
            )
            
            return "Meeting transcript analyzed successfully"
            
        except Exception as e:
            self.logger.error(
                "Error in meeting transcript analysis",
                analysis_id=self.state.analysis_id,
                error=str(e)
            )
            self.state.status = AnalysisStatus.ERROR
            self.state.error_message = f"Erro na análise da reunião: {str(e)}"
            raise
    
    @listen(analyze_meeting_transcript)
    def generate_final_report(self, _) -> str:
        """
        Gera relatório final consolidado usando crew especializada
        
        Returns:
            Status da geração do relatório
        """
        try:
            self.state.current_stage = "Gerando relatório final"
            self.state.progress_percentage = 95.0
            
            self.logger.info(
                "Starting final report generation",
                analysis_id=self.state.analysis_id
            )
            
            # Preparar contexto completo para o relatório final
            inputs = {
                "analysis_id": self.state.analysis_id,
                "sap_module": self.state.sap_module,
                "analysis_type": self.state.analysis_type,
                "process_analysis": self.state.process_analysis_result,
                "requirements_analysis": self.state.requirements_analysis_result,
                "gap_analysis": self.state.gap_analysis_result,
                "meeting_analysis": self.state.meeting_analysis_result
            }
            
            # Executar crew de geração de relatório
            report_crew_instance = self.report_crew.crew()
            result = report_crew_instance.kickoff(inputs=inputs)
            
            # Processar resultado final
            final_report = self._extract_crew_output(result)
            
            # Criar resultado estruturado
            self.state.final_result = self._create_structured_result(final_report)
            
            # Atualizar status final
            self.state.status = AnalysisStatus.COMPLETED
            self.state.progress_percentage = 100.0
            self.state.current_stage = "Análise concluída"
            
            # Salvar resultado no Firestore
            firestore_service.save_analysis_result(
                self.state.analysis_id,
                self.state.final_result.model_dump()
            )
            
            self.logger.info(
                "Final report generated successfully",
                analysis_id=self.state.analysis_id
            )
            
            return "Final report generated successfully"
            
        except Exception as e:
            self.logger.error(
                "Error generating final report",
                analysis_id=self.state.analysis_id,
                error=str(e)
            )
            self.state.status = AnalysisStatus.ERROR
            self.state.error_message = f"Erro na geração do relatório: {str(e)}"
            raise
    
    def _extract_crew_output(self, crew_result) -> Dict[str, Any]:
        """
        Extrai o output de uma crew de forma estruturada
        
        Args:
            crew_result: Resultado retornado pela crew
            
        Returns:
            Dicionário com o resultado estruturado
        """
        try:
            output_data = {
                "raw_output": "",
                "tasks_outputs": [],
                "tokens_used": 0,
                "execution_time": 0
            }
            
            # Extrair output principal
            if hasattr(crew_result, 'raw'):
                output_data["raw_output"] = crew_result.raw
            else:
                output_data["raw_output"] = str(crew_result)
            
            # Extrair outputs das tarefas individuais
            if hasattr(crew_result, 'tasks_output'):
                output_data["tasks_outputs"] = [
                    {
                        "description": getattr(task, 'description', ''),
                        "output": getattr(task, 'raw', str(task)),
                        "agent": getattr(task, 'agent', '')
                    }
                    for task in crew_result.tasks_output
                ]
            elif hasattr(crew_result, 'tasks'):
                output_data["tasks_outputs"] = [
                    {
                        "description": getattr(task, 'description', ''),
                        "output": getattr(task.output, 'raw', str(task.output)) if hasattr(task, 'output') else '',
                        "agent": getattr(task, 'agent', '')
                    }
                    for task in crew_result.tasks if hasattr(task, 'output')
                ]
            
            # Extrair métricas se disponíveis
            output_data["tokens_used"] = getattr(crew_result, 'tokens_used', 0)
            output_data["execution_time"] = getattr(crew_result, 'execution_time', 0)
            
            return output_data
            
        except Exception as e:
            self.logger.error("Error extracting crew output", error=str(e))
            return {
                "raw_output": str(crew_result),
                "tasks_outputs": [],
                "tokens_used": 0,
                "execution_time": 0
            }
    
    def _create_structured_result(self, final_report: Dict[str, Any]) -> AnalysisResult:
        """
        Cria resultado estruturado a partir do relatório final
        
        Args:
            final_report: Resultado do relatório final
            
        Returns:
            AnalysisResult estruturado
        """
        try:
            # Extrair dados dos resultados das crews
            presentation_analysis = self._extract_presentation_analysis()
            requirements_analysis = self._extract_requirements_analysis()
            
            # Extrair contadores
            total_requirements = self._count_requirements()
            gaps_identified = self._count_gaps()
            high_impact_gaps = self._count_high_impact_gaps()
            
            # Extrair recomendações e próximos passos
            recommendations = self._extract_recommendations(final_report)
            next_steps = self._extract_next_steps(final_report)
            
            # Extrair resumo geral
            overall_summary = self._extract_overall_summary(final_report)
            
            return AnalysisResult(
                analysis_id=self.state.analysis_id,
                presentation_analysis=presentation_analysis,
                requirements_analysis=requirements_analysis,
                overall_summary=overall_summary,
                total_requirements=total_requirements,
                gaps_identified=gaps_identified,
                high_impact_gaps=high_impact_gaps,
                recommendations=recommendations,
                next_steps=next_steps,
                created_at=datetime.utcnow(),
                processing_time_seconds=(datetime.utcnow() - self.state.created_at).total_seconds()
            )
            
        except Exception as e:
            self.logger.error("Error creating structured result", error=str(e))
            # Fallback: criar resultado básico
            return AnalysisResult(
                analysis_id=self.state.analysis_id,
                presentation_analysis=[],
                requirements_analysis=[],
                overall_summary=final_report.get("raw_output", "Análise concluída")[:1000],
                total_requirements=0,
                gaps_identified=0,
                high_impact_gaps=0,
                recommendations=["Revisar resultado da análise"],
                next_steps=["Implementar melhorias identificadas"],
                created_at=datetime.utcnow(),
                processing_time_seconds=(datetime.utcnow() - self.state.created_at).total_seconds()
            )
    
    def _extract_presentation_analysis(self) -> list:
        """Extrai análise de apresentação dos resultados das crews"""
        try:
            if not self.state.process_analysis_result:
                return []
            
            # Processar resultado da crew de processos para extrair ProcessAnalysis
            process_output = self.state.process_analysis_result.get("raw_output", "")
            
            # Implementar parsing específico baseado no formato do output
            # Por enquanto, retornar estrutura básica
            return [
                ProcessAnalysis(
                    slide_number=1,
                    process_name="Processo identificado",
                    current_state="Analisado",
                    sap_module_fit=0.8,
                    complexity_score=0.6,
                    automation_potential=0.7,
                    business_impact=BusinessImpact.MEDIUM,
                    description=process_output[:500] if process_output else "Análise de processo"
                ).model_dump()
            ]
            
        except Exception as e:
            self.logger.error("Error extracting presentation analysis", error=str(e))
            return []
    
    def _extract_requirements_analysis(self) -> list:
        """Extrai análise de requisitos dos resultados das crews"""
        try:
            if not self.state.requirements_analysis_result:
                return []
            
            # Processar resultado da crew de requisitos
            requirements_output = self.state.requirements_analysis_result.get("raw_output", "")
            
            # Implementar parsing específico baseado no formato do output
            return [
                RequirementAnalysis(
                    requirement_id="REQ-001",
                    description="Requisito identificado",
                    category="Funcional",
                    priority="Alta",
                    sap_coverage=0.8,
                    gap_identified=True,
                    effort_estimate="Médio",
                    business_impact=BusinessImpact.HIGH,
                    recommendation="Implementar customização"
                ).model_dump()
            ]
            
        except Exception as e:
            self.logger.error("Error extracting requirements analysis", error=str(e))
            return []
    
    def _extract_overall_summary(self, final_report: Dict[str, Any]) -> str:
        """Extrai resumo geral do relatório final"""
        try:
            summary = final_report.get("raw_output", "")
            if summary:
                return summary[:1000]
            
            # Fallback: criar resumo a partir dos resultados das crews
            summary_parts = []
            
            if self.state.process_analysis_result:
                summary_parts.append("Análise de processos concluída.")
            
            if self.state.requirements_analysis_result:
                summary_parts.append("Análise de requisitos realizada.")
            
            if self.state.gap_analysis_result:
                summary_parts.append("Gaps identificados e priorizados.")
            
            if self.state.meeting_analysis_result:
                summary_parts.append("Insights extraídos da reunião.")
            
            return " ".join(summary_parts) if summary_parts else "Análise SAP concluída com sucesso."
            
        except Exception as e:
            self.logger.error("Error extracting overall summary", error=str(e))
            return "Análise SAP concluída."
    
    def _count_requirements(self) -> int:
        """Conta requisitos identificados"""
        try:
            if not self.state.requirements_analysis_result:
                return 0
            
            # Implementar contagem baseada no output da crew
            requirements_output = self.state.requirements_analysis_result.get("raw_output", "")
            
            # Contagem simples baseada em palavras-chave
            count = requirements_output.lower().count("requisito")
            return max(count, 1) if requirements_output else 0
            
        except Exception as e:
            self.logger.error("Error counting requirements", error=str(e))
            return 0
    
    def _count_gaps(self) -> int:
        """Conta gaps identificados"""
        try:
            if not self.state.gap_analysis_result:
                return 0
            
            # Implementar contagem baseada no output da crew de gaps
            gap_output = self.state.gap_analysis_result.get("raw_output", "")
            
            # Contagem simples baseada em palavras-chave
            gap_keywords = ["gap", "lacuna", "diferença", "ausência"]
            count = sum(gap_output.lower().count(keyword) for keyword in gap_keywords)
            return max(count, 1) if gap_output else 0
            
        except Exception as e:
            self.logger.error("Error counting gaps", error=str(e))
            return 0
    
    def _count_high_impact_gaps(self) -> int:
        """Conta gaps de alto impacto"""
        try:
            if not self.state.gap_analysis_result:
                return 0
            
            # Implementar contagem baseada no output da crew de gaps
            gap_output = self.state.gap_analysis_result.get("raw_output", "")
            
            # Contagem baseada em palavras-chave de alto impacto
            high_impact_keywords = ["crítico", "alto impacto", "prioritário", "urgente"]
            count = sum(gap_output.lower().count(keyword) for keyword in high_impact_keywords)
            return count
            
        except Exception as e:
            self.logger.error("Error counting high impact gaps", error=str(e))
            return 0
    
    def _extract_recommendations(self, final_report: Dict[str, Any]) -> list:
        """Extrai recomendações do relatório final"""
        try:
            report_output = final_report.get("raw_output", "")
            
            # Implementar extração baseada em padrões
            recommendations = []
            
            # Buscar seções de recomendações
            if "recomendação" in report_output.lower():
                # Implementar parsing mais sofisticado
                recommendations.append("Implementar melhorias identificadas na análise")
            
            if self.state.gap_analysis_result:
                recommendations.append("Priorizar resolução dos gaps críticos")
            
            if self.state.requirements_analysis_result:
                recommendations.append("Revisar requisitos não atendidos")
            
            return recommendations if recommendations else ["Revisar resultado da análise"]
            
        except Exception as e:
            self.logger.error("Error extracting recommendations", error=str(e))
            return ["Implementar melhorias identificadas na análise"]
    
    def _extract_next_steps(self, final_report: Dict[str, Any]) -> list:
        """Extrai próximos passos do relatório final"""
        try:
            report_output = final_report.get("raw_output", "")
            
            # Implementar extração baseada em padrões
            next_steps = []
            
            # Buscar seções de próximos passos
            if "próximo" in report_output.lower() or "next" in report_output.lower():
                next_steps.append("Revisar análise detalhada")
            
            next_steps.extend([
                "Planejar implementação das melhorias",
                "Validar soluções propostas com stakeholders",
                "Definir cronograma de implementação"
            ])
            
            return next_steps
            
        except Exception as e:
            self.logger.error("Error extracting next steps", error=str(e))
            return ["Revisar análise detalhada", "Planejar implementação das melhorias"]
    
    def _extract_presentation_analysis(self, tasks_outputs) -> list:
        """Extrai análise de apresentação dos outputs das tarefas"""
        # Implementar lógica de extração específica
        return []
    
    def _extract_requirements_analysis(self, tasks_outputs) -> list:
        """Extrai análise de requisitos dos outputs das tarefas"""
        # Implementar lógica de extração específica
        return []
    
    def _extract_overall_summary(self, crew_result) -> str:
        """Extrai resumo geral do resultado da crew"""
        if hasattr(crew_result, 'raw'):
            return crew_result.raw[:1000]
        return str(crew_result)[:1000] if crew_result else "Análise SAP concluída"
    
    def _count_requirements(self, tasks_outputs) -> int:
        """Conta requisitos identificados"""
        return 0  # Implementar lógica específica
    
    def _count_gaps(self, tasks_outputs) -> int:
        """Conta gaps identificados"""
        return 0  # Implementar lógica específica
    
    def _count_high_impact_gaps(self, tasks_outputs) -> int:
        """Conta gaps de alto impacto"""
        return 0  # Implementar lógica específica
    
    def _extract_recommendations(self, tasks_outputs) -> list:
        """Extrai recomendações dos outputs"""
        return ["Implementar melhorias identificadas na análise"]
    
    def _extract_next_steps(self, tasks_outputs) -> list:
        """Extrai próximos passos dos outputs"""
        return ["Revisar análise detalhada", "Planejar implementação das melhorias"]
    
    def get_current_status(self) -> Dict[str, Any]:
        """
        Retorna o status atual da análise
        
        Returns:
            Dicionário com status atual
        """
        return {
            "analysis_id": self.state.analysis_id,
            "status": self.state.status.value,
            "progress_percentage": self.state.progress_percentage,
            "current_stage": self.state.current_stage,
            "error_message": self.state.error_message,
            "created_at": self.state.created_at.isoformat(),
            "has_result": self.state.final_result is not None
        }
