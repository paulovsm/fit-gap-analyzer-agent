from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from typing import List
from app.config.settings import settings
from app.tools.firestore_tools import (
    GetBusinessRequirementsTool,
    GetPresentationTool
)
from app.tools.requirements_tools import (
    RequirementsFileProcessorTool,
    RequirementsDataAnalyzerTool
)
from app.tools.sap_tools import SAPProcessAnalysisTool


@CrewBase
class RequirementsAnalysisCrew:
    """Crew especializada em análise de requisitos de negócio SAP"""
    
    agents_config = "app/crews/requirements_analysis_crew/config/agents.yaml"
    tasks_config = "app/crews/requirements_analysis_crew/config/tasks.yaml"
    
    def __init__(self):
        """Inicializa a crew com configurações e ferramentas"""
        self.llm = LLM(
            model=settings.gemini_model,
            api_key=settings.google_api_key,
            temperature=0.1
        )
        
        # Ferramentas específicas para análise de requisitos
        self.tools = [
            GetBusinessRequirementsTool(),
            GetPresentationTool(),
            RequirementsFileProcessorTool(),
            RequirementsDataAnalyzerTool(),
            SAPProcessAnalysisTool()
        ]
    
    @agent
    def requirements_analyst(self) -> Agent:
        """Agente especialista em análise de requisitos"""
        return Agent(
            config=self.agents_config['requirements_analyst'],
            verbose=settings.crew_verbose,
            tools=self.tools,
            llm=self.llm,
            memory=settings.crew_memory
        )
    
    @agent
    def functional_expert(self) -> Agent:
        """Agente especialista em requisitos funcionais SAP"""
        return Agent(
            config=self.agents_config['functional_expert'],
            verbose=settings.crew_verbose,
            tools=self.tools,
            llm=self.llm,
            memory=settings.crew_memory
        )
    
    @task
    def analyze_requirements_task(self) -> Task:
        """Tarefa de análise de requisitos"""
        return Task(
            config=self.tasks_config['analyze_requirements'],
            agent=self.requirements_analyst()
        )
    
    @task
    def validate_functional_fit_task(self) -> Task:
        """Tarefa de validação de aderência funcional"""
        return Task(
            config=self.tasks_config['validate_functional_fit'],
            agent=self.functional_expert(),
            context=[self.analyze_requirements_task()]
        )
    
    @crew
    def crew(self) -> Crew:
        """Cria a crew de análise de requisitos"""
        return Crew(
            agents=[
                self.requirements_analyst(),
                self.functional_expert()
            ],
            tasks=[
                self.analyze_requirements_task(),
                self.validate_functional_fit_task()
            ],
            process=Process.sequential,
            verbose=settings.crew_verbose,
            memory=settings.crew_memory
        )
