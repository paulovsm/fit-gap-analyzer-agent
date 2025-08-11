from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from typing import List
from app.config.settings import settings
from app.tools.firestore_tools import (
    GetPresentationTool,
    SearchPresentationsByTopicTool
)
from app.tools.sap_tools import SAPProcessAnalysisTool


@CrewBase
class ProcessAnalysisCrew:
    """Crew especializada em análise de processos de negócio SAP"""
    
    agents_config = "app/crews/process_analysis_crew/config/agents.yaml"
    tasks_config = "app/crews/process_analysis_crew/config/tasks.yaml"
    
    def __init__(self):
        """Inicializa a crew com configurações e ferramentas"""
        self.llm = LLM(
            model=settings.gemini_model,
            api_key=settings.google_api_key,
            temperature=0.1
        )
        
        # Ferramentas específicas para análise de processos
        self.tools = [
            GetPresentationTool(),
            SearchPresentationsByTopicTool(),
            SAPProcessAnalysisTool()
        ]
    
    @agent
    def process_analyst(self) -> Agent:
        """Agente especialista em análise de processos SAP"""
        return Agent(
            config=self.agents_config['process_analyst'],
            verbose=settings.crew_verbose,
            tools=self.tools,
            llm=self.llm,
            memory=settings.crew_memory
        )
    
    @agent
    def business_expert(self) -> Agent:
        """Agente especialista em processos de negócio"""
        return Agent(
            config=self.agents_config['business_expert'],
            verbose=settings.crew_verbose,
            tools=self.tools,
            llm=self.llm,
            memory=settings.crew_memory
        )
    
    @task
    def analyze_processes_task(self) -> Task:
        """Tarefa de análise detalhada de processos"""
        return Task(
            config=self.tasks_config['analyze_processes'],
            agent=self.process_analyst()
        )
    
    @task
    def validate_business_logic_task(self) -> Task:
        """Tarefa de validação da lógica de negócio"""
        return Task(
            config=self.tasks_config['validate_business_logic'],
            agent=self.business_expert(),
            context=[self.analyze_processes_task()]
        )
    
    @crew
    def crew(self) -> Crew:
        """Cria a crew de análise de processos"""
        return Crew(
            agents=[
                self.process_analyst(),
                self.business_expert()
            ],
            tasks=[
                self.analyze_processes_task(),
                self.validate_business_logic_task()
            ],
            process=Process.sequential,
            verbose=settings.crew_verbose,
            memory=settings.crew_memory
        )
