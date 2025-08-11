#!/usr/bin/env python3
"""
Script de exemplo para testar a API do SAP Accelerate Agent
"""

import asyncio
import httpx
import json
from datetime import datetime
import os
import tempfile
import csv


async def create_sample_requirements_file():
    """Cria um arquivo de exemplo com requisitos para teste"""
    # Dados de exemplo
    requirements_data = [
        {
            "ID": "REQ-001",
            "Descrição": "Configurar depreciação automática de ativos",
            "Categoria": "Funcional",
            "Prioridade": "Alta",
            "Status": "Pendente",
            "Processo de Negócio": "Gestão de Ativos Fixos",
            "Critérios de Aceitação": "Sistema deve calcular depreciação mensal automaticamente"
        },
        {
            "ID": "REQ-002", 
            "Descrição": "Relatório de movimentação de ativos",
            "Categoria": "Funcional",
            "Prioridade": "Média",
            "Status": "Em Análise",
            "Processo de Negócio": "Relatórios Financeiros",
            "Critérios de Aceitação": "Relatório deve mostrar todas as movimentações do período"
        },
        {
            "ID": "REQ-003",
            "Descrição": "Interface para cadastro de ativos",
            "Categoria": "Não-Funcional",
            "Prioridade": "Baixa",
            "Status": "Aprovado",
            "Processo de Negócio": "Cadastro de Ativos",
            "Critérios de Aceitação": "Interface deve ser intuitiva e responsiva"
        }
    ]
    
    # Criar arquivo temporário
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    
    # Escrever CSV manualmente para evitar dependência do pandas
    import csv
    with open(temp_file.name, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["ID", "Descrição", "Categoria", "Prioridade", "Status", "Processo de Negócio", "Critérios de Aceitação"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(requirements_data)
    
    return temp_file.name


async def test_api():
    """Testa a API de análise SAP"""
    base_url = "http://localhost:8000"
    
    # Cliente HTTP
    async with httpx.AsyncClient() as client:
        
        # 1. Verificar health check
        print("1. Verificando health check...")
        response = await client.get(f"{base_url}/health")
        print(f"Health check: {response.status_code} - {response.json()}")
        
        # 2. Criar arquivo de requisitos de exemplo
        print("\n2. Criando arquivo de requisitos de exemplo...")
        requirements_file_path = await create_sample_requirements_file()
        print(f"Arquivo criado: {requirements_file_path}")
        
        # 3. Fazer upload do arquivo de requisitos
        print("\n3. Fazendo upload do arquivo de requisitos...")
        with open(requirements_file_path, 'rb') as file:
            files = {"file": ("requirements.csv", file, "text/csv")}
            upload_response = await client.post(f"{base_url}/upload/requirements", files=files)
            
        if upload_response.status_code != 200:
            print(f"Erro no upload: {upload_response.status_code} - {upload_response.text}")
            return
            
        upload_data = upload_response.json()
        print(f"Upload realizado: {upload_data}")
        
        # 3.1. Testar preview dos dados do arquivo
        print("\n3.1. Testando preview dos dados do arquivo...")
        file_path = upload_data["file_info"]["file_path"]
        preview_response = await client.get(f"{base_url}/upload/preview", params={"file_path": file_path})
        
        if preview_response.status_code == 200:
            preview_data = preview_response.json()
            print(f"Preview dos dados:")
            print(json.dumps(preview_data, indent=2, ensure_ascii=False))
        else:
            print(f"Erro no preview: {preview_response.status_code} - {preview_response.text}")
        
        # 4. Iniciar análise com arquivo de requisitos
        print("\n4. Iniciando análise SAP com arquivo de requisitos...")
        analysis_request = {
            "presentation_id": "07e13dc1-7fc5-437c-995d-fce97acf38d4",
            "requirements_file_info": upload_data["file_info"],
            "meeting_transcript_id": "c4fa5ad2-e978-47d4-9bdf-f8580f9d468a",
            "sap_module": "FI_AA",
            "analysis_type": "full_analysis",
            "additional_context": "Análise de teste para Fixed Assets com arquivo de requisitos"
        }
        
        response = await client.post(f"{base_url}/analysis/start", json=analysis_request)
        print(f"Análise iniciada: {response.status_code}")
        
        if response.status_code == 200:
            analysis_data = response.json()
            analysis_id = analysis_data["analysis_id"]
            print(f"Analysis ID: {analysis_id}")
            
            # 5. Monitorar progresso
            print("\n5. Monitorando progresso...")
            for i in range(10):  # Máximo 10 tentativas
                await asyncio.sleep(2)  # Aguardar 2 segundos
                
                status_response = await client.get(f"{base_url}/analysis/{analysis_id}/status")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"Status: {status_data['status']} - {status_data['progress_percentage']:.1f}% - {status_data['current_stage']}")
                    
                    # Se concluído, obter resultado
                    if status_data["status"] == "completed":
                        print("\n6. Obtendo resultado...")
                        result_response = await client.get(f"{base_url}/analysis/{analysis_id}/result")
                        if result_response.status_code == 200:
                            result_data = result_response.json()
                            print("Resultado da análise:")
                            print(json.dumps(result_data, indent=2, ensure_ascii=False))
                        break
                    
                    elif status_data["status"] == "error":
                        print(f"Erro na análise: {status_data.get('error_message', 'Erro desconhecido')}")
                        break
                else:
                    print(f"Erro ao obter status: {status_response.status_code}")
                    break
            
            # 7. Listar análises ativas
            print("\n7. Listando análises ativas...")
            active_response = await client.get(f"{base_url}/analysis/active")
            if active_response.status_code == 200:
                active_data = active_response.json()
                print(f"Análises ativas: {len(active_data)}")
                for analysis in active_data:
                    print(f"  - {analysis['analysis_id']}: {analysis['status']}")
        else:
            print(f"Erro ao iniciar análise: {response.status_code} - {response.text}")
        
        # 8. Testar endpoint de análise direta com arquivo
        print("\n8. Testando análise direta com arquivo...")
        with open(requirements_file_path, 'rb') as file:
            files = {"requirements_file": ("requirements.csv", file, "text/csv")}
            data = {
                "presentation_id": "07e13dc1-7fc5-437c-995d-fce97acf38d4",
                "meeting_transcript_id": "c4fa5ad2-e978-47d4-9bdf-f8580f9d468a",
                "sap_module": "FI_AA",
                "analysis_type": "requirements_only",
                "additional_context": "Teste de análise direta com arquivo"
            }
            direct_response = await client.post(f"{base_url}/analysis/analyze-with-file", files=files, data=data)
            
        if direct_response.status_code == 200:
            direct_data = direct_response.json()
            print(f"Análise direta iniciada: {direct_data['analysis_id']}")
        else:
            print(f"Erro na análise direta: {direct_response.status_code} - {direct_response.text}")
        
        # 9. Limpar arquivo temporário
        try:
            os.unlink(requirements_file_path)
            print(f"\n9. Arquivo temporário removido: {requirements_file_path}")
        except Exception as e:
            print(f"Erro ao remover arquivo temporário: {e}")


if __name__ == "__main__":
    print("=== Teste da API SAP Accelerate Agent ===")
    print(f"Iniciando teste em: {datetime.now()}")
    
    try:
        asyncio.run(test_api())
    except Exception as e:
        print(f"Erro durante o teste: {e}")
    
    print(f"Teste finalizado em: {datetime.now()}")
