from crewai_tools import BaseTool
from typing import Type, Optional, List, Dict, Any
from pydantic import BaseModel, Field
import asyncio
from app.services.firestore_service import firestore_service
from app.models.firestore_models import (
    PresentationTranscriptionResponse,
    MeetingTranscriptionResponse,
    BusinessRequirement
)


class PresentationInput(BaseModel):
    """Input para buscar apresentação"""
    presentation_id: str = Field(..., description="ID da apresentação no Firestore")


class MeetingInput(BaseModel):
    """Input para buscar reunião"""
    meeting_id: str = Field(..., description="ID da reunião no Firestore")


class RequirementsInput(BaseModel):
    """Input para buscar requisitos"""
    requirements_file_id: str = Field(..., description="ID do arquivo de requisitos")


class PresentationTopicInput(BaseModel):
    """Input para buscar apresentações por tópico"""
    topic: str = Field(..., description="Tópico a ser buscado")
    limit: int = Field(10, description="Limite de resultados")


class GetPresentationTool(BaseTool):
    """Ferramenta para buscar transcrição de apresentação no Firestore"""
    
    name: str = "get_presentation_transcription"
    description: str = (
        "Busca a transcrição completa de uma apresentação no Firestore. "
        "Retorna todos os slides com suas transcrições, análises semânticas e metadados."
    )
    args_schema: Type[BaseModel] = PresentationInput
    
    def _run(self, presentation_id: str) -> str:
        """Executa a busca da apresentação"""
        try:
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                firestore_service.get_presentation_transcription(presentation_id)
            )
            loop.close()
            
            if result:
                return f"""
APRESENTAÇÃO ENCONTRADA:
ID: {result.id}
Arquivo: {result.file_name}
Status: {result.status}
Número de slides: {result.slides_count}
Data de criação: {result.created_at}

TRANSCRIÇÃO:
{result.transcription.model_dump_json(indent=2) if result.transcription else 'Transcrição não disponível'}
"""
            else:
                return f"Apresentação com ID {presentation_id} não encontrada."
                
        except Exception as e:
            return f"Erro ao buscar apresentação: {str(e)}"


class GetMeetingTranscriptionTool(BaseTool):
    """Ferramenta para buscar transcrição de reunião no Firestore"""
    
    name: str = "get_meeting_transcription"
    description: str = (
        "Busca a transcrição completa de uma reunião no Firestore. "
        "Retorna o texto completo, segmentos com speaker diarization e metadados."
    )
    args_schema: Type[BaseModel] = MeetingInput
    
    def _run(self, meeting_id: str) -> str:
        """Executa a busca da reunião"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                firestore_service.get_meeting_transcription(meeting_id)
            )
            loop.close()
            
            if result:
                segments_info = ""
                if result.segments:
                    segments_info = f"\nSegmentos de speaker diarization: {len(result.segments)} segmentos"
                
                return f"""
REUNIÃO ENCONTRADA:
ID: {result.id}
Arquivo: {result.file_name}
Status: {result.status}
Duração: {result.duration_seconds} segundos
Data de criação: {result.created_at}
{segments_info}

TEXTO COMPLETO DA REUNIÃO:
{result.full_text if result.full_text else 'Texto não disponível'}

METADADOS DA REUNIÃO:
{result.metadata.model_dump_json(indent=2) if result.metadata else 'Metadados não disponíveis'}

RESUMO:
{result.summary if result.summary else 'Resumo não disponível'}
"""
            else:
                return f"Reunião com ID {meeting_id} não encontrada."
                
        except Exception as e:
            return f"Erro ao buscar reunião: {str(e)}"


class GetBusinessRequirementsTool(BaseTool):
    """Ferramenta para buscar requisitos de negócio no Firestore"""
    
    name: str = "get_business_requirements"
    description: str = (
        "Busca todos os requisitos de negócio de um arquivo específico no Firestore. "
        "Retorna a lista completa de requisitos com suas descrições."
    )
    args_schema: Type[BaseModel] = RequirementsInput
    
    def _run(self, requirements_file_id: str) -> str:
        """Executa a busca dos requisitos"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                firestore_service.get_business_requirements(requirements_file_id)
            )
            loop.close()
            
            if result:
                requirements_text = f"REQUISITOS DE NEGÓCIO ENCONTRADOS ({len(result)} requisitos):\n\n"
                
                for i, req in enumerate(result, 1):
                    requirements_text += f"""
{i}. REQUISITO ID: {req.requirement_id}
   DESCRIÇÃO: {req.description}
   PRIORIDADE: {req.priority if req.priority else 'Não especificada'}
   CATEGORIA: {req.category if req.category else 'Não especificada'}
   STAKEHOLDER: {req.stakeholder if req.stakeholder else 'Não especificado'}
   CRITÉRIOS DE ACEITAÇÃO: {req.acceptance_criteria if req.acceptance_criteria else 'Não especificados'}
   ---
"""
                
                return requirements_text
            else:
                return f"Nenhum requisito encontrado para o arquivo {requirements_file_id}."
                
        except Exception as e:
            return f"Erro ao buscar requisitos: {str(e)}"


class SearchPresentationsByTopicTool(BaseTool):
    """Ferramenta para buscar apresentações por tópico"""
    
    name: str = "search_presentations_by_topic"
    description: str = (
        "Busca apresentações relacionadas a um tópico específico nos conceitos-chave. "
        "Útil para encontrar apresentações relacionadas a um processo SAP específico."
    )
    args_schema: Type[BaseModel] = PresentationTopicInput
    
    def _run(self, topic: str, limit: int = 10) -> str:
        """Executa a busca por tópico"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(
                firestore_service.search_presentations_by_topic(topic, limit)
            )
            loop.close()
            
            if result:
                search_results = f"APRESENTAÇÕES ENCONTRADAS PARA O TÓPICO '{topic}' ({len(result)} resultados):\n\n"
                
                for i, presentation in enumerate(result, 1):
                    key_concepts = ", ".join(presentation.transcription.key_concepts) if presentation.transcription else "N/A"
                    search_results += f"""
{i}. ID: {presentation.id}
   ARQUIVO: {presentation.file_name}
   SLIDES: {presentation.slides_count}
   CONCEITOS-CHAVE: {key_concepts}
   RESUMO: {presentation.transcription.overall_summary[:200] + '...' if presentation.transcription and presentation.transcription.overall_summary else 'N/A'}
   ---
"""
                
                return search_results
            else:
                return f"Nenhuma apresentação encontrada para o tópico '{topic}'."
                
        except Exception as e:
            return f"Erro ao buscar apresentações: {str(e)}"
