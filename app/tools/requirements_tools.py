from crewai_tools import BaseTool
from typing import Type, Dict, Any
from pydantic import BaseModel, Field
import structlog
from app.services.requirements_processor import requirements_processor

logger = structlog.get_logger()


class RequirementsFileProcessorToolInput(BaseModel):
    """Input para a ferramenta de processamento de arquivos de requisitos"""
    file_path: str = Field(description="Caminho para o arquivo de requisitos (XLSX ou CSV)")


class RequirementsFileProcessorTool(BaseTool):
    """Ferramenta para processar arquivos de requisitos XLSX/CSV"""
    
    name: str = "requirements_file_processor"
    description: str = (
        "Processa arquivos de requisitos em formato XLSX ou CSV, extraindo "
        "informações estruturadas como ID, descrição, categoria, prioridade, "
        "status, processo de negócio e critérios de aceitação."
    )
    args_schema: Type[BaseModel] = RequirementsFileProcessorToolInput
    
    def _run(self, file_path: str) -> str:
        """
        Executa o processamento do arquivo de requisitos
        
        Args:
            file_path: Caminho para o arquivo
            
        Returns:
            String JSON com os requisitos processados
        """
        try:
            # Processar arquivo
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                result = loop.run_until_complete(
                    requirements_processor.process_requirements_file(file_path)
                )
            finally:
                loop.close()
            
            # Converter para formato JSON para o LLM
            import json
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error("Error in RequirementsFileProcessorTool", error=str(e))
            return f"Erro ao processar arquivo de requisitos: {str(e)}"


class RequirementsDataAnalyzerToolInput(BaseModel):
    """Input para análise de dados de requisitos"""
    requirements_json: str = Field(description="JSON com os dados dos requisitos processados")
    analysis_focus: str = Field(description="Foco da análise (ex: gaps, coverage, complexity)")


class RequirementsDataAnalyzerTool(BaseTool):
    """Ferramenta para analisar dados estruturados de requisitos"""
    
    name: str = "requirements_data_analyzer"
    description: str = (
        "Analisa dados estruturados de requisitos para identificar padrões, "
        "categorizar por complexidade, identificar gaps potenciais e avaliar "
        "cobertura funcional."
    )
    args_schema: Type[BaseModel] = RequirementsDataAnalyzerToolInput
    
    def _run(self, requirements_json: str, analysis_focus: str) -> str:
        """
        Analisa os dados de requisitos
        
        Args:
            requirements_json: JSON com dados dos requisitos
            analysis_focus: Foco da análise
            
        Returns:
            Análise estruturada dos requisitos
        """
        try:
            import json
            
            # Parse dos dados
            data = json.loads(requirements_json)
            requirements = data.get('requirements', [])
            metadata = data.get('metadata', {})
            
            # Análise baseada no foco
            analysis_result = {
                "total_requirements": len(requirements),
                "metadata": metadata,
                "analysis_focus": analysis_focus
            }
            
            if analysis_focus.lower() in ['gaps', 'gap']:
                analysis_result["gap_analysis"] = self._analyze_gaps(requirements)
            elif analysis_focus.lower() in ['coverage', 'cobertura']:
                analysis_result["coverage_analysis"] = self._analyze_coverage(requirements)
            elif analysis_focus.lower() in ['complexity', 'complexidade']:
                analysis_result["complexity_analysis"] = self._analyze_complexity(requirements)
            else:
                # Análise completa
                analysis_result["gap_analysis"] = self._analyze_gaps(requirements)
                analysis_result["coverage_analysis"] = self._analyze_coverage(requirements)
                analysis_result["complexity_analysis"] = self._analyze_complexity(requirements)
            
            return json.dumps(analysis_result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error("Error in RequirementsDataAnalyzerTool", error=str(e))
            return f"Erro na análise de requisitos: {str(e)}"
    
    def _analyze_gaps(self, requirements: list) -> Dict[str, Any]:
        """Analisa potenciais gaps nos requisitos"""
        gaps = {
            "incomplete_requirements": [],
            "missing_acceptance_criteria": [],
            "unclear_descriptions": [],
            "unspecified_priorities": []
        }
        
        for req in requirements:
            # Requisitos incompletos
            if not req.get('description') or len(req.get('description', '').strip()) < 10:
                gaps["incomplete_requirements"].append(req.get('id', 'Unknown'))
            
            # Sem critérios de aceitação
            if not req.get('acceptance_criteria'):
                gaps["missing_acceptance_criteria"].append(req.get('id', 'Unknown'))
            
            # Descrições pouco claras
            desc = req.get('description', '')
            if desc and len(desc.split()) < 5:
                gaps["unclear_descriptions"].append(req.get('id', 'Unknown'))
            
            # Prioridades não especificadas
            priority = req.get('priority', '').lower()
            if priority not in ['high', 'medium', 'low', 'alta', 'média', 'baixa']:
                gaps["unspecified_priorities"].append(req.get('id', 'Unknown'))
        
        return gaps
    
    def _analyze_coverage(self, requirements: list) -> Dict[str, Any]:
        """Analisa cobertura funcional dos requisitos"""
        coverage = {
            "by_category": {},
            "by_priority": {},
            "by_business_process": {},
            "functional_vs_non_functional": {"functional": 0, "non_functional": 0}
        }
        
        for req in requirements:
            # Por categoria
            category = req.get('category', 'Unknown')
            coverage["by_category"][category] = coverage["by_category"].get(category, 0) + 1
            
            # Por prioridade
            priority = req.get('priority', 'Unknown')
            coverage["by_priority"][priority] = coverage["by_priority"].get(priority, 0) + 1
            
            # Por processo de negócio
            process = req.get('business_process', 'Unspecified')
            coverage["by_business_process"][process] = coverage["by_business_process"].get(process, 0) + 1
            
            # Funcional vs Não-funcional
            if category.lower() in ['functional', 'funcional']:
                coverage["functional_vs_non_functional"]["functional"] += 1
            else:
                coverage["functional_vs_non_functional"]["non_functional"] += 1
        
        return coverage
    
    def _analyze_complexity(self, requirements: list) -> Dict[str, Any]:
        """Analisa complexidade dos requisitos"""
        complexity = {
            "by_complexity_level": {},
            "high_complexity_requirements": [],
            "average_description_length": 0,
            "requirements_with_dependencies": []
        }
        
        desc_lengths = []
        
        for req in requirements:
            # Complexidade explícita
            complexity_level = req.get('complexity', '')
            if complexity_level:
                complexity["by_complexity_level"][complexity_level] = \
                    complexity["by_complexity_level"].get(complexity_level, 0) + 1
            
            # Análise de complexidade implícita
            desc = req.get('description', '')
            desc_length = len(desc.split())
            desc_lengths.append(desc_length)
            
            # Requisitos complexos (descrição longa ou critérios múltiplos)
            if desc_length > 50 or len(req.get('acceptance_criteria', '').split()) > 30:
                complexity["high_complexity_requirements"].append({
                    "id": req.get('id'),
                    "description_length": desc_length,
                    "reason": "Long description or complex acceptance criteria"
                })
            
            # Dependências (palavras-chave que indicam dependência)
            dependency_keywords = ['depend', 'require', 'after', 'before', 'integration', 'interface']
            if any(keyword in desc.lower() for keyword in dependency_keywords):
                complexity["requirements_with_dependencies"].append(req.get('id'))
        
        # Média do comprimento das descrições
        if desc_lengths:
            complexity["average_description_length"] = sum(desc_lengths) / len(desc_lengths)
        
        return complexity
