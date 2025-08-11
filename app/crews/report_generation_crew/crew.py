from crewai import Agent, Crew, Process, Task, LLM
from crewai.project import CrewBase, agent, crew, task
from typing import List
from app.config.settings import settings


@CrewBase
class ReportGenerationCrew:
    """Crew especializada em geração de relatórios finais"""
    
    agents_config = "app/crews/report_generation_crew/config/agents.yaml"
    tasks_config = "app/crews/report_generation_crew/config/tasks.yaml"
    
    def __init__(self):
        """Inicializa a crew com configurações e ferramentas"""
        self.llm = LLM(
            model=settings.gemini_model,
            api_key=settings.google_api_key,
            temperature=0.1
        )
    
    @agent
    def report_writer(self) -> Agent:
        """Agente especialista em redação de relatórios"""
        return Agent(
            config=self.agents_config['report_writer'],
            verbose=settings.crew_verbose,
            tools=[],  # Apenas consolida informações
            llm=self.llm,
            memory=settings.crew_memory
        )
    
    @agent
    def quality_reviewer(self) -> Agent:
        """Agente revisor de qualidade"""
        return Agent(
            config=self.agents_config['quality_reviewer'],
            verbose=settings.crew_verbose,
            tools=[],  # Apenas revisa conteúdo
            llm=self.llm,
            memory=settings.crew_memory
        )
    
    @task
    def generate_report_task(self) -> Task:
        """Tarefa de geração do relatório"""
        return Task(
            config=self.tasks_config['generate_report'],
            agent=self.report_writer()
        )
    
    @task
    def review_report_task(self) -> Task:
        """Tarefa de revisão do relatório"""
        return Task(
            config=self.tasks_config['review_report'],
            agent=self.quality_reviewer(),
            context=[self.generate_report_task()]
        )
    
    @crew
    def crew(self) -> Crew:
        """Cria a crew de geração de relatórios"""
        return Crew(
            agents=[
                self.report_writer(),
                self.quality_reviewer()
            ],
            tasks=[
                self.generate_report_task(),
                self.review_report_task()
            ],
            process=Process.sequential,
            verbose=settings.crew_verbose,
            memory=settings.crew_memory
        )
