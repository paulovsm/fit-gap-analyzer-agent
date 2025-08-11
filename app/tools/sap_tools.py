from crewai_tools import BaseTool
from typing import Type, List, Dict, Any
from pydantic import BaseModel, Field
import re
import google.generativeai as genai
from app.config.settings import settings
import json
import asyncio


class LLMBasedTool(BaseTool):
    """Classe base para ferramentas que usam LLM"""
    
    def __init__(self):
        super().__init__()
        # Configure Gemini
        genai.configure(api_key=settings.google_api_key)
        self.model = genai.GenerativeModel(settings.gemini_model)
    
    def _call_llm(self, prompt: str, system_instruction: str = None) -> str:
        """Chama o LLM com o prompt fornecido"""
        try:
            if system_instruction:
                full_prompt = f"{system_instruction}\n\n{prompt}"
            else:
                full_prompt = prompt
            
            response = self.model.generate_content(full_prompt)
            return response.text
        except Exception as e:
            return f"Erro ao chamar LLM: {str(e)}"
    
    def _call_llm_with_structured_output(self, prompt: str, system_instruction: str = None) -> Dict[str, Any]:
        """Chama o LLM esperando uma resposta em JSON estruturado"""
        try:
            json_instruction = "\n\nRETORNE APENAS UM JSON VÁLIDO COM A ESTRUTURA SOLICITADA. NÃO INCLUA TEXTO ADICIONAL ANTES OU DEPOIS DO JSON."
            
            if system_instruction:
                full_prompt = f"{system_instruction}{json_instruction}\n\n{prompt}"
            else:
                full_prompt = f"{prompt}{json_instruction}"
            
            response = self.model.generate_content(full_prompt)
            
            # Tenta extrair JSON da resposta
            response_text = response.text.strip()
            
            # Remove markdown se presente
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            # Parse JSON
            return json.loads(response_text.strip())
            
        except json.JSONDecodeError as e:
            return {"error": f"Erro ao parsear JSON: {str(e)}", "raw_response": response.text}
        except Exception as e:
            return {"error": f"Erro ao chamar LLM: {str(e)}"}


class ProcessAnalysisInput(BaseModel):
    """Input para análise de processo SAP"""
    process_text: str = Field(..., description="Texto do processo a ser analisado")
    process_type: str = Field(..., description="Tipo de processo SAP (FI, FI-AA, CO, etc.)")


class GapAnalysisInput(BaseModel):
    """Input para análise de gap"""
    core_process_text: str = Field(..., description="Texto do processo core")
    requirement_text: str = Field(..., description="Texto do requisito")
    process_module: str = Field(..., description="Módulo SAP do processo")


class ProcessFlowAnalysisInput(BaseModel):
    """Input para análise de fluxo de processo"""
    slide_content: str = Field(..., description="Conteúdo do slide a ser analisado")
    slide_number: int = Field(..., description="Número do slide")


class SAPProcessAnalysisTool(LLMBasedTool):
    """Ferramenta para análise de processos SAP usando LLM"""
    
    name: str = "analyze_sap_process"
    description: str = (
        "Analisa um processo SAP usando inteligência artificial para extrair "
        "informações estruturadas como passos principais, regras de negócio, "
        "pontos de integração e possíveis gaps de forma inteligente."
    )
    args_schema: Type[BaseModel] = ProcessAnalysisInput
    
    def _run(self, process_text: str, process_type: str) -> str:
        """Executa a análise do processo SAP usando LLM"""
        try:
            system_instruction = f"""
Você é um especialista em SAP com profundo conhecimento do módulo {process_type}.
Analise o texto do processo fornecido e extraia informações estruturadas seguindo o formato JSON solicitado.
Seja preciso, detalhado e foque em aspectos técnicos e de negócio relevantes para SAP {process_type}.
"""

            prompt = f"""
Analise o seguinte processo SAP do módulo {process_type} e retorne um JSON com a seguinte estrutura:

{{
    "process_name": "Nome do processo identificado",
    "main_steps": [
        "Lista dos passos principais do processo",
        "Seja específico e técnico"
    ],
    "business_rules": [
        "Regras de negócio identificadas",
        "Validações e controles necessários"
    ],
    "integration_points": [
        "Pontos de integração com outros módulos SAP",
        "Interfaces e dependências identificadas"
    ],
    "sap_transactions": [
        "Códigos de transação SAP mencionados ou implícitos",
        "Ex: FB01, AS01, etc."
    ],
    "data_objects": [
        "Objetos de dados SAP relevantes",
        "Tabelas, campos, documentos"
    ],
    "potential_gaps": [
        "Possíveis lacunas ou pontos de atenção identificados",
        "Aspectos que podem precisar de customização"
    ],
    "complexity_assessment": {{
        "level": "BAIXA|MÉDIA|ALTA",
        "reasoning": "Justificativa para o nível de complexidade"
    }},
    "technical_recommendations": [
        "Recomendações técnicas específicas",
        "Melhores práticas para implementação"
    ]
}}

TEXTO DO PROCESSO:
{process_text}
"""
            
            result = self._call_llm_with_structured_output(prompt, system_instruction)
            
            if "error" in result:
                return f"Erro na análise: {result['error']}"
            
            # Formata a resposta de forma legível
            return self._format_analysis_result(result, process_type)
            
        except Exception as e:
            return f"Erro na análise do processo: {str(e)}"
    
    def _format_analysis_result(self, analysis: Dict[str, Any], process_type: str) -> str:
        """Formata o resultado da análise de forma legível"""
        
        main_steps = analysis.get('main_steps', [])
        business_rules = analysis.get('business_rules', [])
        integration_points = analysis.get('integration_points', [])
        sap_transactions = analysis.get('sap_transactions', [])
        data_objects = analysis.get('data_objects', [])
        potential_gaps = analysis.get('potential_gaps', [])
        complexity = analysis.get('complexity_assessment', {})
        recommendations = analysis.get('technical_recommendations', [])
        
        return f"""
ANÁLISE INTELIGENTE DO PROCESSO SAP ({process_type}):

PROCESSO IDENTIFICADO: {analysis.get('process_name', 'Não identificado')}

PASSOS PRINCIPAIS DO PROCESSO:
{chr(10).join([f"• {step}" for step in main_steps]) if main_steps else "• Nenhum passo identificado"}

REGRAS DE NEGÓCIO:
{chr(10).join([f"• {rule}" for rule in business_rules]) if business_rules else "• Nenhuma regra identificada"}

PONTOS DE INTEGRAÇÃO:
{chr(10).join([f"• {point}" for point in integration_points]) if integration_points else "• Nenhuma integração identificada"}

TRANSAÇÕES SAP RELACIONADAS:
{chr(10).join([f"• {trans}" for trans in sap_transactions]) if sap_transactions else "• Nenhuma transação identificada"}

OBJETOS DE DADOS SAP:
{chr(10).join([f"• {obj}" for obj in data_objects]) if data_objects else "• Nenhum objeto identificado"}

POSSÍVEIS GAPS/PONTOS DE ATENÇÃO:
{chr(10).join([f"• {gap}" for gap in potential_gaps]) if potential_gaps else "• Nenhum gap identificado"}

AVALIAÇÃO DE COMPLEXIDADE:
• Nível: {complexity.get('level', 'Não avaliado')}
• Justificativa: {complexity.get('reasoning', 'Não fornecida')}

RECOMENDAÇÕES TÉCNICAS:
{chr(10).join([f"• {rec}" for rec in recommendations]) if recommendations else "• Nenhuma recomendação específica"}

RESUMO EXECUTIVO:
Este processo {process_type} contém {len(main_steps)} passos principais, 
{len(business_rules)} regras de negócio, {len(integration_points)} pontos de integração,
{len(sap_transactions)} transações SAP identificadas e {len(potential_gaps)} possíveis gaps.
Complexidade avaliada como {complexity.get('level', 'não definida')}.
"""


class SAPGapAnalysisTool(LLMBasedTool):
    """Ferramenta para análise de gaps entre processo core e requisitos usando LLM"""
    
    name: str = "analyze_sap_gap"
    description: str = (
        "Compara um processo core SAP com um requisito de negócio usando IA para "
        "identificar gaps, fornecendo análise detalhada e justificativa inteligente."
    )
    args_schema: Type[BaseModel] = GapAnalysisInput
    
    def _run(self, core_process_text: str, requirement_text: str, process_module: str) -> str:
        """Executa a análise de gap usando LLM"""
        try:
            system_instruction = f"""
Você é um consultor SAP sênior especialista no módulo {process_module}.
Sua tarefa é analisar se um processo core SAP atende completamente a um requisito de negócio.
Seja analítico, técnico e preciso em sua avaliação. Considere:
- Funcionalidades padrão do SAP {process_module}
- Necessidades de configuração vs customização
- Impacto no negócio e riscos
- Viabilidade técnica e esforço
"""

            prompt = f"""
Compare o PROCESSO CORE SAP com o REQUISITO DE NEGÓCIO e retorne um JSON com a seguinte estrutura:

{{
    "gap_analysis": {{
        "has_gap": true/false,
        "gap_severity": "CRITICO|ALTO|MEDIO|BAIXO|NENHUM",
        "coverage_percentage": 0-100,
        "gap_type": "FUNCIONAL|TECNICO|CONFIGURACAO|CUSTOMIZACAO|INTEGRACAO"
    }},
    "detailed_analysis": {{
        "covered_aspects": [
            "Aspectos do requisito que são atendidos pelo processo core"
        ],
        "gap_aspects": [
            "Aspectos do requisito que NÃO são atendidos pelo processo core"
        ],
        "technical_requirements": [
            "Necessidades técnicas para fechar o gap (se houver)"
        ]
    }},
    "business_impact": {{
        "impact_level": "MUITO_ALTO|ALTO|MEDIO|BAIXO|MUITO_BAIXO",
        "affected_processes": [
            "Processos de negócio que serão impactados"
        ],
        "risks": [
            "Riscos associados ao gap (se houver)"
        ],
        "benefits_if_resolved": [
            "Benefícios de resolver o gap"
        ]
    }},
    "implementation_analysis": {{
        "effort_estimate": "BAIXO|MEDIO|ALTO|MUITO_ALTO",
        "approach_recommendations": [
            "Recomendações de abordagem para implementação"
        ],
        "alternative_solutions": [
            "Soluções alternativas ou workarounds"
        ],
        "prerequisites": [
            "Pré-requisitos técnicos ou de negócio"
        ]
    }},
    "expert_conclusion": {{
        "summary": "Resumo executivo da análise",
        "recommendation": "IMPLEMENTAR|CUSTOMIZAR|CONFIGURAR|WORKAROUND|REJEITAR",
        "priority": "CRITICA|ALTA|MEDIA|BAIXA",
        "timeline_estimate": "Estimativa de prazo para resolução"
    }}
}}

PROCESSO CORE SAP ({process_module}):
{core_process_text}

REQUISITO DE NEGÓCIO:
{requirement_text}
"""
            
            result = self._call_llm_with_structured_output(prompt, system_instruction)
            
            if "error" in result:
                return f"Erro na análise: {result['error']}"
            
            # Formata a resposta de forma legível
            return self._format_gap_analysis_result(result, process_module)
            
        except Exception as e:
            return f"Erro na análise de gap: {str(e)}"
    
    def _format_gap_analysis_result(self, analysis: Dict[str, Any], process_module: str) -> str:
        """Formata o resultado da análise de gap de forma legível"""
        
        gap_analysis = analysis.get('gap_analysis', {})
        detailed_analysis = analysis.get('detailed_analysis', {})
        business_impact = analysis.get('business_impact', {})
        implementation = analysis.get('implementation_analysis', {})
        conclusion = analysis.get('expert_conclusion', {})
        
        has_gap = gap_analysis.get('has_gap', False)
        gap_status = "SIM" if has_gap else "NÃO"
        
        return f"""
ANÁLISE INTELIGENTE DE GAP - MÓDULO {process_module}:

═══════════════════════════════════════════════════════════════
RESULTADO DA ANÁLISE DE GAP
═══════════════════════════════════════════════════════════════

GAP IDENTIFICADO: {gap_status}
Severidade: {gap_analysis.get('gap_severity', 'Não avaliada')}
Cobertura do Requisito: {gap_analysis.get('coverage_percentage', 0)}%
Tipo de Gap: {gap_analysis.get('gap_type', 'Não classificado')}

═══════════════════════════════════════════════════════════════
ANÁLISE DETALHADA
═══════════════════════════════════════════════════════════════

✅ ASPECTOS COBERTOS PELO PROCESSO CORE:
{chr(10).join([f"• {aspect}" for aspect in detailed_analysis.get('covered_aspects', [])]) or "• Nenhum aspecto identificado como coberto"}

❌ ASPECTOS NÃO COBERTOS (GAPS):
{chr(10).join([f"• {aspect}" for aspect in detailed_analysis.get('gap_aspects', [])]) or "• Nenhum gap identificado"}

🔧 NECESSIDADES TÉCNICAS:
{chr(10).join([f"• {req}" for req in detailed_analysis.get('technical_requirements', [])]) or "• Nenhuma necessidade técnica específica"}

═══════════════════════════════════════════════════════════════
IMPACTO NO NEGÓCIO
═══════════════════════════════════════════════════════════════

Nível de Impacto: {business_impact.get('impact_level', 'Não avaliado')}

🔄 PROCESSOS AFETADOS:
{chr(10).join([f"• {process}" for process in business_impact.get('affected_processes', [])]) or "• Nenhum processo específico identificado"}

⚠️ RISCOS IDENTIFICADOS:
{chr(10).join([f"• {risk}" for risk in business_impact.get('risks', [])]) or "• Nenhum risco específico identificado"}

💰 BENEFÍCIOS SE RESOLVIDO:
{chr(10).join([f"• {benefit}" for benefit in business_impact.get('benefits_if_resolved', [])]) or "• Nenhum benefício específico identificado"}

═══════════════════════════════════════════════════════════════
ANÁLISE DE IMPLEMENTAÇÃO
═══════════════════════════════════════════════════════════════

Esforço Estimado: {implementation.get('effort_estimate', 'Não estimado')}

📋 RECOMENDAÇÕES DE ABORDAGEM:
{chr(10).join([f"• {rec}" for rec in implementation.get('approach_recommendations', [])]) or "• Nenhuma recomendação específica"}

🔄 SOLUÇÕES ALTERNATIVAS:
{chr(10).join([f"• {alt}" for alt in implementation.get('alternative_solutions', [])]) or "• Nenhuma alternativa identificada"}

📋 PRÉ-REQUISITOS:
{chr(10).join([f"• {prereq}" for prereq in implementation.get('prerequisites', [])]) or "• Nenhum pré-requisito específico"}

═══════════════════════════════════════════════════════════════
CONCLUSÃO DO ESPECIALISTA
═══════════════════════════════════════════════════════════════

📊 RESUMO EXECUTIVO:
{conclusion.get('summary', 'Não fornecido')}

🎯 RECOMENDAÇÃO: {conclusion.get('recommendation', 'Não definida')}
🏆 PRIORIDADE: {conclusion.get('priority', 'Não definida')}
⏱️ PRAZO ESTIMADO: {conclusion.get('timeline_estimate', 'Não estimado')}

═══════════════════════════════════════════════════════════════
"""


class SAPProcessFlowAnalyzer(LLMBasedTool):
    """Ferramenta para análise de fluxo de processos em slides usando LLM"""
    
    name: str = "analyze_process_flow"
    description: str = (
        "Analisa o conteúdo de um slide de processo SAP usando IA para converter "
        "informações visuais e textuais em fluxo lógico estruturado e compreensível."
    )
    args_schema: Type[BaseModel] = ProcessFlowAnalysisInput
    
    def _run(self, slide_content: str, slide_number: int) -> str:
        """Executa a análise do fluxo de processo usando LLM"""
        try:
            system_instruction = """
Você é um especialista em SAP e análise de processos de negócio.
Sua tarefa é analisar o conteúdo de um slide de apresentação e extrair um fluxo lógico estruturado.
Foque em:
- Identificar elementos visuais descritos no texto
- Sequência lógica de ações
- Pontos de decisão e ramificações
- Transações SAP mencionadas
- Responsabilidades e papéis
- Sistemas e interfaces envolvidos
"""

            prompt = f"""
Analise o conteúdo do slide {slide_number} e retorne um JSON com a seguinte estrutura:

{{
    "slide_analysis": {{
        "slide_number": {slide_number},
        "content_type": "PROCESSO|OVERVIEW|CONFIGURACAO|INTERFACE|DECISAO|FLUXO",
        "main_topic": "Tópico principal do slide",
        "complexity_level": "SIMPLES|MODERADO|COMPLEXO"
    }},
    "process_flow": {{
        "sequential_steps": [
            {{
                "step_number": 1,
                "description": "Descrição detalhada do passo",
                "responsible_role": "Papel/função responsável",
                "sap_transaction": "Código SAP se aplicável",
                "inputs": ["Entradas necessárias"],
                "outputs": ["Saídas geradas"],
                "duration_estimate": "Estimativa de tempo"
            }}
        ],
        "decision_points": [
            {{
                "condition": "Condição para decisão",
                "true_path": "Caminho se verdadeiro",
                "false_path": "Caminho se falso",
                "criteria": "Critérios para decisão"
            }}
        ],
        "parallel_activities": [
            "Atividades que podem ser executadas em paralelo"
        ]
    }},
    "technical_elements": {{
        "sap_transactions": ["Lista de transações SAP identificadas"],
        "data_objects": ["Objetos de dados mencionados"],
        "integration_points": ["Pontos de integração com outros sistemas"],
        "reports_outputs": ["Relatórios ou saídas mencionados"]
    }},
    "business_context": {{
        "business_value": "Valor de negócio do processo",
        "stakeholders": ["Stakeholders envolvidos"],
        "kpis_metrics": ["KPIs ou métricas mencionadas"],
        "compliance_aspects": ["Aspectos de compliance/regulatórios"]
    }},
    "implementation_insights": {{
        "configuration_needed": ["Configurações necessárias"],
        "customization_points": ["Pontos que podem precisar customização"],
        "best_practices": ["Melhores práticas identificadas"],
        "potential_issues": ["Possíveis problemas ou desafios"]
    }}
}}

CONTEÚDO DO SLIDE {slide_number}:
{slide_content}
"""
            
            result = self._call_llm_with_structured_output(prompt, system_instruction)
            
            if "error" in result:
                return f"Erro na análise: {result['error']}"
            
            # Formata a resposta de forma legível
            return self._format_flow_analysis_result(result)
            
        except Exception as e:
            return f"Erro na análise do fluxo: {str(e)}"
    
    def _format_flow_analysis_result(self, analysis: Dict[str, Any]) -> str:
        """Formata o resultado da análise de fluxo de forma legível"""
        
        slide_analysis = analysis.get('slide_analysis', {})
        process_flow = analysis.get('process_flow', {})
        technical_elements = analysis.get('technical_elements', {})
        business_context = analysis.get('business_context', {})
        implementation = analysis.get('implementation_insights', {})
        
        sequential_steps = process_flow.get('sequential_steps', [])
        decision_points = process_flow.get('decision_points', [])
        
        return f"""
ANÁLISE INTELIGENTE DE FLUXO DE PROCESSO - SLIDE {slide_analysis.get('slide_number', 'N/A')}

═══════════════════════════════════════════════════════════════
INFORMAÇÕES GERAIS DO SLIDE
═══════════════════════════════════════════════════════════════

Tipo de Conteúdo: {slide_analysis.get('content_type', 'Não identificado')}
Tópico Principal: {slide_analysis.get('main_topic', 'Não identificado')}
Nível de Complexidade: {slide_analysis.get('complexity_level', 'Não avaliado')}

═══════════════════════════════════════════════════════════════
FLUXO SEQUENCIAL DO PROCESSO
═══════════════════════════════════════════════════════════════

📋 PASSOS IDENTIFICADOS ({len(sequential_steps)} passos):

{self._format_sequential_steps(sequential_steps)}

🔀 PONTOS DE DECISÃO ({len(decision_points)} identificados):

{self._format_decision_points(decision_points)}

⚡ ATIVIDADES PARALELAS:
{chr(10).join([f"• {activity}" for activity in process_flow.get('parallel_activities', [])]) or "• Nenhuma atividade paralela identificada"}

═══════════════════════════════════════════════════════════════
ELEMENTOS TÉCNICOS SAP
═══════════════════════════════════════════════════════════════

💻 TRANSAÇÕES SAP:
{chr(10).join([f"• {trans}" for trans in technical_elements.get('sap_transactions', [])]) or "• Nenhuma transação identificada"}

📊 OBJETOS DE DADOS:
{chr(10).join([f"• {obj}" for obj in technical_elements.get('data_objects', [])]) or "• Nenhum objeto identificado"}

🔗 PONTOS DE INTEGRAÇÃO:
{chr(10).join([f"• {point}" for point in technical_elements.get('integration_points', [])]) or "• Nenhuma integração identificada"}

📈 RELATÓRIOS/SAÍDAS:
{chr(10).join([f"• {report}" for report in technical_elements.get('reports_outputs', [])]) or "• Nenhum relatório identificado"}

═══════════════════════════════════════════════════════════════
CONTEXTO DE NEGÓCIO
═══════════════════════════════════════════════════════════════

💰 VALOR DE NEGÓCIO:
{business_context.get('business_value', 'Não especificado')}

👥 STAKEHOLDERS:
{chr(10).join([f"• {stakeholder}" for stakeholder in business_context.get('stakeholders', [])]) or "• Nenhum stakeholder específico identificado"}

📊 KPIs/MÉTRICAS:
{chr(10).join([f"• {kpi}" for kpi in business_context.get('kpis_metrics', [])]) or "• Nenhuma métrica específica identificada"}

⚖️ ASPECTOS DE COMPLIANCE:
{chr(10).join([f"• {aspect}" for aspect in business_context.get('compliance_aspects', [])]) or "• Nenhum aspecto de compliance identificado"}

═══════════════════════════════════════════════════════════════
INSIGHTS DE IMPLEMENTAÇÃO
═══════════════════════════════════════════════════════════════

⚙️ CONFIGURAÇÕES NECESSÁRIAS:
{chr(10).join([f"• {config}" for config in implementation.get('configuration_needed', [])]) or "• Nenhuma configuração específica identificada"}

🔧 PONTOS DE CUSTOMIZAÇÃO:
{chr(10).join([f"• {custom}" for custom in implementation.get('customization_points', [])]) or "• Nenhuma customização específica identificada"}

✅ MELHORES PRÁTICAS:
{chr(10).join([f"• {practice}" for practice in implementation.get('best_practices', [])]) or "• Nenhuma prática específica identificada"}

⚠️ POSSÍVEIS PROBLEMAS:
{chr(10).join([f"• {issue}" for issue in implementation.get('potential_issues', [])]) or "• Nenhum problema específico identificado"}

═══════════════════════════════════════════════════════════════
"""
    
    def _format_sequential_steps(self, steps: List[Dict[str, Any]]) -> str:
        """Formata os passos sequenciais"""
        if not steps:
            return "• Nenhum passo sequencial identificado"
        
        formatted_steps = []
        for step in steps:
            step_text = f"""
🔸 PASSO {step.get('step_number', 'N/A')}:
   Descrição: {step.get('description', 'Não especificada')}
   Responsável: {step.get('responsible_role', 'Não especificado')}
   Transação SAP: {step.get('sap_transaction', 'N/A')}
   Entradas: {', '.join(step.get('inputs', ['N/A']))}
   Saídas: {', '.join(step.get('outputs', ['N/A']))}
   Duração Estimada: {step.get('duration_estimate', 'Não estimada')}
"""
            formatted_steps.append(step_text)
        
        return "\n".join(formatted_steps)
    
    def _format_decision_points(self, decisions: List[Dict[str, Any]]) -> str:
        """Formata os pontos de decisão"""
        if not decisions:
            return "• Nenhum ponto de decisão identificado"
        
        formatted_decisions = []
        for i, decision in enumerate(decisions, 1):
            decision_text = f"""
🔸 DECISÃO {i}:
   Condição: {decision.get('condition', 'Não especificada')}
   Se Verdadeiro: {decision.get('true_path', 'Não especificado')}
   Se Falso: {decision.get('false_path', 'Não especificado')}
   Critérios: {decision.get('criteria', 'Não especificados')}
"""
            formatted_decisions.append(decision_text)
        
        return "\n".join(formatted_decisions)
