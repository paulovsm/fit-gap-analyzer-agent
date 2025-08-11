from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from typing import List
from app.config.settings import settings
from app.tools.firestore_tools import GetMeetingTranscriptionTool


@CrewBase
class MeetingAnalysisCrew:
    """Crew especializada em análise de transcrições de reuniões"""
    
    agents_config = "app/crews/meeting_analysis_crew/config/agents.yaml"
    tasks_config = "app/crews/meeting_analysis_crew/config/tasks.yaml"
    
    def __init__(self):
        """Inicializa a crew com configurações e ferramentas"""
        self.llm = LLM(
            model=settings.gemini_model,
            api_key=settings.google_api_key,
            temperature=0.1
        )
        
        # Ferramentas específicas para análise de reuniões
        self.tools = [
            GetMeetingTranscriptionTool()
        ]
    
    @agent
    def meeting_analyst(self) -> Agent:
        """Agente especialista em análise de reuniões"""
        return Agent(
            config=self.agents_config['meeting_analyst'],
            verbose=settings.crew_verbose,
            tools=self.tools,
            llm=self.llm,
            memory=settings.crew_memory
        )
    
    @agent
    def insights_extractor(self) -> Agent:
        """Agente especialista em extração de insights"""
        return Agent(
            config=self.agents_config['insights_extractor'],
            verbose=settings.crew_verbose,
            tools=self.tools,
            llm=self.llm,
            memory=settings.crew_memory
        )
    
    @task
    def analyze_meeting_task(self) -> Task:
        """Tarefa de análise de transcrição"""
        return Task(
            config=self.tasks_config['analyze_meeting'],
            agent=self.meeting_analyst()
        )
    
    @task
    def extract_insights_task(self) -> Task:
        """Tarefa de extração de insights"""
        return Task(
            config=self.tasks_config['extract_insights'],
            agent=self.insights_extractor(),
            context=[self.analyze_meeting_task()]
        )
    
    @crew
    def crew(self) -> Crew:
        """Cria a crew de análise de reuniões"""
        return Crew(
            agents=[
                self.meeting_analyst(),
                self.insights_extractor()
            ],
            tasks=[
                self.analyze_meeting_task(),
                self.extract_insights_task()
            ],
            process=Process.sequential,
            verbose=settings.crew_verbose,
            memory=settings.crew_memory
        )
