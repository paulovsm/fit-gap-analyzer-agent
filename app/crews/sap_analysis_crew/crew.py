from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from typing import List
from app.config.settings import settings
from app.tools.firestore_tools import (
    GetPresentationTool,
    GetMeetingTranscriptionTool,
    GetBusinessRequirementsTool,
    SearchPresentationsByTopicTool
)
from app.tools.sap_tools import (
    SAPProcessAnalysisTool,
    SAPGapAnalysisTool,
    SAPProcessFlowAnalyzer
)


@CrewBase
class SAPAnalysisCrew:
    """Crew especializada em análise de processos SAP"""
    
    agents_config = "app/crews/sap_analysis_crew/config/agents.yaml"
    tasks_config = "app/crews/sap_analysis_crew/config/tasks.yaml"
    
    def __init__(self):
        """Inicializa a crew com configurações e ferramentas"""
        self.llm = LLM(
            model=settings.gemini_model,
            api_key=settings.google_api_key,
            temperature=0.1
        )
        
        # Ferramentas compartilhadas
        self.firestore_tools = [
            GetPresentationTool(),
            GetMeetingTranscriptionTool(),
            GetBusinessRequirementsTool(),
            SearchPresentationsByTopicTool()
        ]
        
        self.sap_tools = [
            SAPProcessAnalysisTool(),
            SAPGapAnalysisTool(),
            SAPProcessFlowAnalyzer()
        ]
    
    @agent
    def business_process_analyst(self) -> Agent:
        """Agente especialista em análise de processos de negócio SAP"""
        return Agent(
            config=self.agents_config['business_process_analyst'],
            verbose=settings.crew_verbose,
            tools=self.firestore_tools + self.sap_tools,
            llm=self.llm,
            memory=settings.crew_memory
        )
    
    @agent
    def requirements_analyst(self) -> Agent:
        """Agente analista de requisitos de negócio SAP"""
        return Agent(
            config=self.agents_config['requirements_analyst'],
            verbose=settings.crew_verbose,
            tools=self.firestore_tools + self.sap_tools,
            llm=self.llm,
            memory=settings.crew_memory
        )
    
    @agent
    def gap_analysis_specialist(self) -> Agent:
        """Agente especialista em análise de gaps SAP"""
        return Agent(
            config=self.agents_config['gap_analysis_specialist'],
            verbose=settings.crew_verbose,
            tools=self.sap_tools,
            llm=self.llm,
            memory=settings.crew_memory
        )
    
    @agent
    def meeting_transcript_analyzer(self) -> Agent:
        """Agente analisador de transcrições de reuniões SAP"""
        return Agent(
            config=self.agents_config['meeting_transcript_analyzer'],
            verbose=settings.crew_verbose,
            tools=self.firestore_tools,
            llm=self.llm,
            memory=settings.crew_memory
        )
    
    @agent
    def final_report_agent(self) -> Agent:
        """Agente especialista em relatórios de análise SAP"""
        return Agent(
            config=self.agents_config['final_report_agent'],
            verbose=settings.crew_verbose,
            tools=[],  # Apenas consolida informações
            llm=self.llm,
            memory=settings.crew_memory
        )
    
    @task
    def analyze_business_processes_task(self) -> Task:
        """Tarefa de análise de processos de negócio"""
        return Task(
            config=self.tasks_config['analyze_business_processes'],
            agent=self.business_process_analyst()
        )
    
    @task
    def analyze_business_requirements_task(self) -> Task:
        """Tarefa de análise de requisitos de negócio"""
        return Task(
            config=self.tasks_config['analyze_business_requirements'],
            agent=self.requirements_analyst()
        )
    
    @task
    def perform_gap_analysis_task(self) -> Task:
        """Tarefa de análise de gaps"""
        return Task(
            config=self.tasks_config['perform_gap_analysis'],
            agent=self.gap_analysis_specialist()
        )
    
    @task
    def analyze_meeting_transcript_task(self) -> Task:
        """Tarefa de análise de transcrição de reunião"""
        return Task(
            config=self.tasks_config['analyze_meeting_transcript'],
            agent=self.meeting_transcript_analyzer()
        )
    
    @task
    def generate_final_report_task(self) -> Task:
        """Tarefa de geração de relatório final"""
        return Task(
            config=self.tasks_config['generate_final_report'],
            agent=self.final_report_agent()
        )
    
    @crew
    def crew(self) -> Crew:
        """Cria a crew SAP com todos os agentes e tarefas"""
        return Crew(
            agents=[
                self.business_process_analyst(),
                self.requirements_analyst(),
                self.gap_analysis_specialist(),
                self.meeting_transcript_analyzer(),
                self.final_report_agent()
            ],
            tasks=[
                self.analyze_business_processes_task(),
                self.analyze_business_requirements_task(),
                self.perform_gap_analysis_task(),
                self.analyze_meeting_transcript_task(),
                self.generate_final_report_task()
            ],
            process=Process.sequential,
            verbose=settings.crew_verbose,
            memory=settings.crew_memory
        )
