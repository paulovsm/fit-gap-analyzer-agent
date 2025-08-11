from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from typing import List
from app.config.settings import settings
from app.tools.sap_tools import SAPGapAnalysisTool


@CrewBase
class GapAnalysisCrew:
    """Crew especializada em análise de gaps SAP"""
    
    agents_config = "app/crews/gap_analysis_crew/config/agents.yaml"
    tasks_config = "app/crews/gap_analysis_crew/config/tasks.yaml"
    
    def __init__(self):
        """Inicializa a crew com configurações e ferramentas"""
        self.llm = LLM(
            model=settings.gemini_model,
            api_key=settings.google_api_key,
            temperature=0.1
        )
        
        # Ferramentas específicas para análise de gaps
        self.tools = [
            SAPGapAnalysisTool()
        ]
    
    @agent
    def gap_analyst(self) -> Agent:
        """Agente especialista em análise de gaps"""
        return Agent(
            config=self.agents_config['gap_analyst'],
            verbose=settings.crew_verbose,
            tools=self.tools,
            llm=self.llm,
            memory=settings.crew_memory
        )
    
    @agent
    def solution_architect(self) -> Agent:
        """Agente arquiteto de soluções SAP"""
        return Agent(
            config=self.agents_config['solution_architect'],
            verbose=settings.crew_verbose,
            tools=self.tools,
            llm=self.llm,
            memory=settings.crew_memory
        )
    
    @task
    def identify_gaps_task(self) -> Task:
        """Tarefa de identificação de gaps"""
        return Task(
            config=self.tasks_config['identify_gaps'],
            agent=self.gap_analyst()
        )
    
    @task
    def prioritize_solutions_task(self) -> Task:
        """Tarefa de priorização de soluções"""
        return Task(
            config=self.tasks_config['prioritize_solutions'],
            agent=self.solution_architect(),
            context=[self.identify_gaps_task()]
        )
    
    @crew
    def crew(self) -> Crew:
        """Cria a crew de análise de gaps"""
        return Crew(
            agents=[
                self.gap_analyst(),
                self.solution_architect()
            ],
            tasks=[
                self.identify_gaps_task(),
                self.prioritize_solutions_task()
            ],
            process=Process.sequential,
            verbose=settings.crew_verbose,
            memory=settings.crew_memory
        )
