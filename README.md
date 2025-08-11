# SAP Accelerate Agent

Backend em Python com suporte a múltiplas requisições em paralelo implementando fluxo de multi-agentes de IA usando o framework CrewAI para análise de processos SAP.

## 🚀 Funcionalidades

- **Multi-Agent AI System**: Sistema de múltiplos agentes especializados usando CrewAI
- **Análise de Processos SAP**: Análise inteligente de módulos SAP (FI, MM, SD, etc.)
- **Upload de Arquivos**: Suporte a upload e processamento de arquivos XLSX/CSV de requisitos
- **Análise de Gap**: Identificação de gaps entre requisitos e funcionalidades SAP standard
- **API RESTful**: Interface FastAPI com documentação automática
- **Processamento Paralelo**: Suporte a múltiplas análises simultâneas com Celery + Redis
- **Integração Firestore**: Armazenamento de dados com Google Firestore

## 🏗️ Arquitetura

### Crews Especializadas
- **ProcessAnalysisCrew**: Análise de processos de negócio
- **RequirementsAnalysisCrew**: Análise de requisitos funcionais
- **GapAnalysisCrew**: Identificação de gaps e soluções
- **MeetingAnalysisCrew**: Análise de transcrições de reuniões
- **ReportGenerationCrew**: Geração de relatórios consolidados

### Tecnologias
- **Framework**: FastAPI + CrewAI
- **LLM**: Google Gemini 2.5 Flash
- **Database**: Google Firestore
- **Queue**: Celery + Redis
- **File Processing**: Pandas + OpenPyXL
- **Logging**: Structlog

## 📋 Pré-requisitos

- Python 3.9+
- Redis (para Celery)
- Conta Google Cloud (para Firestore e Gemini API)

## 🛠️ Instalação

1. Clone o repositório:
```bash
git clone https://github.com/paulovsm/fit-gap-analyzer-agent.git
cd fit-gap-analyzer-agent
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

5. Configure as credenciais do Google Cloud:
- Baixe o arquivo de credenciais JSON do Google Cloud
- Configure a variável `GOOGLE_APPLICATION_CREDENTIALS`

## ⚙️ Configuração

### Variáveis de Ambiente (.env)
```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=true
LOG_LEVEL=INFO

# Google Cloud
GOOGLE_API_KEY=your_gemini_api_key
GOOGLE_APPLICATION_CREDENTIALS=path/to/credentials.json
FIRESTORE_PROJECT_ID=your_project_id

# LLM Configuration
GEMINI_MODEL=gemini-2.5-flash-thinking-exp-01-21

# CrewAI Configuration
CREW_VERBOSE=true
CREW_MEMORY=true

# Redis Configuration
REDIS_URL=redis://localhost:6379/0

# File Upload
UPLOAD_DIR=uploads
MAX_FILE_SIZE=10485760
```

## 🚀 Execução

### Iniciar a API
```bash
python -m app.main
```

### Iniciar Worker Celery (em outro terminal)
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

### Iniciar Redis (se não estiver rodando)
```bash
redis-server
```

## 📚 Uso da API

### Documentação Interativa
Acesse `http://localhost:8000/docs` para a documentação Swagger.

### Endpoints Principais

#### Upload de Arquivo de Requisitos
```bash
curl -X POST "http://localhost:8000/upload/requirements" \
     -H "accept: application/json" \
     -H "Content-Type: multipart/form-data" \
     -F "file=@requirements.xlsx"
```

#### Iniciar Análise
```bash
curl -X POST "http://localhost:8000/analysis/start" \
     -H "Content-Type: application/json" \
     -d '{
       "presentation_id": "pres_123",
       "requirements_file_info": {...},
       "sap_module": "FI_AA",
       "analysis_type": "full_analysis"
     }'
```

#### Verificar Status
```bash
curl -X GET "http://localhost:8000/analysis/{analysis_id}/status"
## 📁 Estrutura do Projeto

```
app/
├── api/
│   ├── routes.py              # Endpoints principais
│   └── upload_routes.py       # Endpoints de upload
├── crews/
│   ├── process_analysis_crew/
│   ├── requirements_analysis_crew/
│   ├── gap_analysis_crew/
│   ├── meeting_analysis_crew/
│   └── report_generation_crew/
├── flows/
│   └── sap_analysis_flow.py   # Orquestração multi-crew
├── models/
│   └── api_models.py          # Modelos Pydantic
├── services/
│   ├── analysis_service.py
│   └── requirements_processor.py
├── tools/
│   ├── firestore_tools.py
│   ├── requirements_tools.py
│   └── sap_tools.py
├── config/
│   └── settings.py
└── main.py
```

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📞 Suporte

Para suporte e dúvidas, abra uma issue no GitHub ou entre em contato através do email.

---

**Desenvolvido com ❤️ usando CrewAI e FastAPI**
