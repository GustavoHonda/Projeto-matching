#!/bin/bash

echo "Detectando sistema operacional..."

if [[ "$OSTYPE" == "linux-gnu"* ]]; then

    echo "Linux detectado"
    PROJECT_DIR="/home/metamorfose/git/Projeto-metAMORfose"

    # Verifica Python 3.12
    if ! command -v python3.12 &> /dev/null; then
        echo "❌ Python 3.12 não encontrado. Instale usando seu gerenciador de pacotes ou pyenv."
        pause
    else
        python3.12 --version
    fi
    
    cd "$PROJECT_DIR" || exit 1

    if [[ -f "venv/bin/activate" ]]; then
        echo "✅ venv já existe (Linux/macOS)"
    else
        python3.12 -m venv venv

        echo "pip está localizado em: $(which pip)"
        sleep 2
        echo "Instalando dependências..."
        pip install -r requirements.txt
    fi

    source venv/bin/activate
    python3 main.py

else
    echo "⚠️ Este script é para Linux."
    pause
fi

pause