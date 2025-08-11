#!/bin/bash

echo "=== SAP Accelerate Agent - Setup Script ==="

# Verificar se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "Python 3 não encontrado. Por favor, instale Python 3.11 ou superior."
    exit 1
fi

# Criar ambiente virtual
echo "Criando ambiente virtual..."
python3 -m venv venv

# Ativar ambiente virtual
echo "Ativando ambiente virtual..."
source venv/bin/activate

# Atualizar pip
echo "Atualizando pip..."
pip install --upgrade pip

# Instalar dependências
echo "Instalando dependências..."
pip install -r requirements.txt

# Criar arquivo .env se não existir
if [ ! -f .env ]; then
    echo "Criando arquivo .env..."
    cp .env.example .env
    echo "Por favor, edite o arquivo .env com suas configurações:"
    echo "  - GOOGLE_API_KEY: Sua chave da API do Google/Gemini"
    echo "  - FIREBASE_PROJECT_ID: ID do seu projeto Firebase"
    echo "  - GOOGLE_APPLICATION_CREDENTIALS: Caminho para o arquivo de credenciais"
fi

echo ""
echo "=== Setup concluído! ==="
echo ""
echo "Próximos passos:"
echo "1. Edite o arquivo .env com suas configurações"
echo "2. Inicie o Redis: docker run -d -p 6379:6379 redis:7-alpine"
echo "3. Execute a aplicação: ./run.sh"
echo ""
echo "Para desenvolvimento:"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
