import firebase_admin
from firebase_admin import credentials, firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from typing import Optional, Dict, Any, List
import structlog
from app.config.settings import settings
from app.models.firestore_models import (
    PresentationTranscriptionResponse,
    MeetingTranscriptionResponse,
    BusinessRequirement
)

logger = structlog.get_logger()


class FirestoreService:
    """Serviço para interação com o Firestore"""
    
    def __init__(self):
        """Inicializa o serviço do Firestore"""
        if not firebase_admin._apps:
            if settings.google_application_credentials:
                cred = credentials.Certificate(settings.google_application_credentials)
            else:
                # Use default credentials
                cred = credentials.ApplicationDefault()
            
            firebase_admin.initialize_app(cred, {
                'projectId': settings.firebase_project_id,
            })
        
        self.db = firestore.client()
        self.logger = logger.bind(service="firestore")
    
    async def get_presentation_transcription(self, presentation_id: str) -> Optional[PresentationTranscriptionResponse]:
        """
        Busca a transcrição de uma apresentação pelo ID
        
        Args:
            presentation_id: ID da apresentação
            
        Returns:
            PresentationTranscriptionResponse ou None se não encontrado
        """
        try:
            doc_ref = self.db.collection(settings.presentation_collection).document(presentation_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return PresentationTranscriptionResponse(**data)
            else:
                self.logger.warning("Presentation not found", presentation_id=presentation_id)
                return None
                
        except Exception as e:
            self.logger.error("Error fetching presentation", 
                            presentation_id=presentation_id, 
                            error=str(e))
            raise
    
    async def get_meeting_transcription(self, meeting_id: str) -> Optional[MeetingTranscriptionResponse]:
        """
        Busca a transcrição de uma reunião pelo ID
        
        Args:
            meeting_id: ID da reunião
            
        Returns:
            MeetingTranscriptionResponse ou None se não encontrado
        """
        try:
            doc_ref = self.db.collection(settings.meeting_collection).document(meeting_id)
            doc = doc_ref.get()
            
            if doc.exists:
                data = doc.to_dict()
                return MeetingTranscriptionResponse(**data)
            else:
                self.logger.warning("Meeting transcript not found", meeting_id=meeting_id)
                return None
                
        except Exception as e:
            self.logger.error("Error fetching meeting transcript", 
                            meeting_id=meeting_id, 
                            error=str(e))
            raise
    
    async def get_business_requirements(self, requirements_file_id: str) -> List[BusinessRequirement]:
        """
        Busca os requisitos de negócio por arquivo
        
        Args:
            requirements_file_id: ID do arquivo de requisitos
            
        Returns:
            Lista de BusinessRequirement
        """
        try:
            # Busca todos os requisitos relacionados ao arquivo
            query = self.db.collection(settings.requirements_collection).where(
                filter=FieldFilter("file_id", "==", requirements_file_id)
            )
            
            docs = query.stream()
            requirements = []
            
            for doc in docs:
                data = doc.to_dict()
                requirements.append(BusinessRequirement(**data))
            
            self.logger.info("Requirements fetched", 
                           file_id=requirements_file_id, 
                           count=len(requirements))
            return requirements
            
        except Exception as e:
            self.logger.error("Error fetching requirements", 
                            file_id=requirements_file_id, 
                            error=str(e))
            raise
    
    async def search_presentations_by_topic(self, topic: str, limit: int = 10) -> List[PresentationTranscriptionResponse]:
        """
        Busca apresentações por tópico
        
        Args:
            topic: Tópico a ser buscado
            limit: Limite de resultados
            
        Returns:
            Lista de PresentationTranscriptionResponse
        """
        try:
            # Busca nas apresentações que contenham o tópico nos key_concepts
            query = self.db.collection(settings.presentation_collection).where(
                filter=FieldFilter("transcription.key_concepts", "array_contains", topic)
            ).limit(limit)
            
            docs = query.stream()
            presentations = []
            
            for doc in docs:
                data = doc.to_dict()
                presentations.append(PresentationTranscriptionResponse(**data))
            
            return presentations
            
        except Exception as e:
            self.logger.error("Error searching presentations", 
                            topic=topic, 
                            error=str(e))
            raise
    
    async def save_analysis_result(self, analysis_id: str, result: Dict[str, Any]) -> bool:
        """
        Salva o resultado de uma análise no Firestore
        
        Args:
            analysis_id: ID da análise
            result: Resultado da análise
            
        Returns:
            True se salvo com sucesso
        """
        try:
            doc_ref = self.db.collection("analysis_results").document(analysis_id)
            doc_ref.set(result)
            
            self.logger.info("Analysis result saved", analysis_id=analysis_id)
            return True
            
        except Exception as e:
            self.logger.error("Error saving analysis result", 
                            analysis_id=analysis_id, 
                            error=str(e))
            raise
    
    async def get_analysis_result(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """
        Busca o resultado de uma análise
        
        Args:
            analysis_id: ID da análise
            
        Returns:
            Resultado da análise ou None se não encontrado
        """
        try:
            doc_ref = self.db.collection("analysis_results").document(analysis_id)
            doc = doc_ref.get()
            
            if doc.exists:
                return doc.to_dict()
            else:
                return None
                
        except Exception as e:
            self.logger.error("Error fetching analysis result", 
                            analysis_id=analysis_id, 
                            error=str(e))
            raise


# Singleton instance
firestore_service = FirestoreService()
