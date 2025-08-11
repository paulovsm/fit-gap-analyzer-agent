#!/usr/bin/env python3
"""
Teste das ferramentas SAP com LLM
"""

import asyncio
import os
import sys
from pathlib import Path

# Adicionar o diretório raiz ao path
sys.path.append(str(Path(__file__).parent))

from app.tools.sap_tools import SAPProcessAnalysisTool, SAPGapAnalysisTool, SAPProcessFlowAnalyzer
from app.config.settings import settings


async def test_sap_tools():
    """Testa as ferramentas SAP com dados de exemplo"""
    
    print("=== Teste das Ferramentas SAP com LLM ===\n")
    
    # Verificar configurações
    if not settings.google_api_key:
        print("❌ GOOGLE_API_KEY não configurada")
        return
    
    print("✅ Configurações validadas\n")
    
    # Dados de exemplo
    sample_presentation_data = """
    SAP Fixed Assets (FI-AA) Implementation
    
    Core Processes:
    1. Asset Master Data Management
       - Asset classes configuration
       - Depreciation areas setup
       - Chart of depreciation setup
    
    2. Asset Acquisition
       - Purchase with automatic asset creation
       - Manual asset posting
       - Asset under construction (AuC)
    
    3. Asset Depreciation
       - Planned depreciation runs
       - Unplanned depreciation
       - Special depreciation
    
    4. Asset Retirement/Disposal
       - Asset sale with customer
       - Asset scrapping
       - Asset transfer between company codes
    
    Integration Points:
    - MM (Materials Management) for purchase orders
    - FI (Financial Accounting) for G/L postings
    - CO (Controlling) for cost center assignments
    """
    
    sample_requirements = """
    Business Requirements for Fixed Assets:
    
    1. MANDATORY: Track depreciation for 15 different asset classes
    2. MANDATORY: Integration with procurement system for automatic asset creation
    3. OPTIONAL: Mobile app for asset verification
    4. MANDATORY: Monthly depreciation reporting
    5. OPTIONAL: Asset barcode scanning
    6. MANDATORY: Multi-currency support (USD, EUR, BRL)
    7. CRITICAL: Compliance with local tax regulations (IFRS, Brazilian GAAP)
    8. OPTIONAL: Integration with IoT sensors for usage-based depreciation
    """
    
    # 1. Teste do SAPProcessAnalysisTool
    print("1. Testando SAPProcessAnalysisTool...")
    process_tool = SAPProcessAnalysisTool()
    
    try:
        process_result = await process_tool._arun(sample_presentation_data)
        print("✅ Análise de Processo concluída:")
        print(f"📊 Resultado: {process_result[:200]}...\n")
    except Exception as e:
        print(f"❌ Erro na análise de processo: {e}\n")
    
    # 2. Teste do SAPGapAnalysisTool
    print("2. Testando SAPGapAnalysisTool...")
    gap_tool = SAPGapAnalysisTool()
    
    try:
        gap_input = f"CORE_PROCESSES:\n{sample_presentation_data}\n\nBUSINESS_REQUIREMENTS:\n{sample_requirements}"
        gap_result = await gap_tool._arun(gap_input)
        print("✅ Análise de Gap concluída:")
        print(f"📊 Resultado: {gap_result[:200]}...\n")
    except Exception as e:
        print(f"❌ Erro na análise de gap: {e}\n")
    
    # 3. Teste do SAPProcessFlowAnalyzer
    print("3. Testando SAPProcessFlowAnalyzer...")
    flow_tool = SAPProcessFlowAnalyzer()
    
    try:
        flow_result = await flow_tool._arun(sample_presentation_data)
        print("✅ Análise de Fluxo concluída:")
        print(f"📊 Resultado: {flow_result[:200]}...\n")
    except Exception as e:
        print(f"❌ Erro na análise de fluxo: {e}\n")
    
    print("=== Teste Concluído ===")


if __name__ == "__main__":
    # Verificar se as variáveis de ambiente estão configuradas
    if not os.getenv("GOOGLE_API_KEY"):
        print("❌ Por favor, configure a variável GOOGLE_API_KEY")
        print("   export GOOGLE_API_KEY='sua_chave_aqui'")
        sys.exit(1)
    
    asyncio.run(test_sap_tools())
