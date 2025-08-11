#!/bin/bash

echo "=== SAP Accelerate Agent - Executando ==="

# Verificar se o ambiente virtual existe
if [ ! -d "venv" ]; then
    echo "Ambiente virtual não encontrado. Execute primeiro: ./setup.sh"
    exit 1
fi

# Ativar ambiente virtual
source venv/bin/activate

# Verificar se o arquivo .env existe
if [ ! -f .env ]; then
    echo "Arquivo .env não encontrado. Copie de .env.example e configure suas variáveis."
    exit 1
fi

# Verificar se o Redis está rodando
if ! redis-cli ping &> /dev/null; then
    echo "Redis não está rodando. Iniciando Redis..."
    docker run -d -p 6379:6379 --name sap-redis redis:7-alpine
    sleep 2
fi

# Executar worker Celery em background
echo "Iniciando worker Celery..."
celery -A app.services.analysis_service worker --loglevel=info &
CELERY_PID=$!

# Executar aplicação FastAPI
echo "Iniciando aplicação FastAPI..."
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
API_PID=$!

echo ""
echo "=== Aplicação iniciada ==="
echo "API disponível em: http://localhost:8000"
echo "Documentação em: http://localhost:8000/docs"
echo ""
echo "Para parar a aplicação, pressione Ctrl+C"

# Aguardar sinal de interrupção
trap "echo 'Parando aplicação...'; kill $CELERY_PID $API_PID; exit" SIGINT SIGTERM

wait
