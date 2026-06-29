#!/bin/bash

# Evita executar como root diretamente (a menos que necessário)
if [ "$EUID" -eq 0 ]; then
   echo "Aviso: É recomendado executar este script como usuário comum, não como root."
fi

# Obter o diretório onde o script está localizado
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo -e "\033[96m====================================================\033[0m"
echo -e "\033[96m    INICIALIZADOR DO CICLO DE ESTUDOS (LINUX)       \033[0m"
echo -e "\033[96m====================================================\033[0m"

# 1. Verificar se python3 está instalado
if ! command -v python3 &> /dev/null; then
    echo -e "\033[91mErro: O Python 3 não está instalado no seu sistema.\033[0m"
    echo -e "Por favor, instale o Python 3 antes de executar o script."
    read -p "Pressione Enter para sair..."
    exit 1
fi

# 2. Verificar se o módulo venv está disponível no python3
if ! python3 -c "import venv" &> /dev/null; then
    echo -e "\033[93mAviso: O módulo 'venv' (ambiente virtual) do Python não está instalado.\033[0m"
    echo -e "Este módulo é necessário para gerenciar as dependências do projeto de forma segura."
    echo -e "Como você está no Linux Mint/Ubuntu, podemos tentar instalá-lo automaticamente."
    read -p "Deseja tentar instalar 'python3-venv' e 'python3-pip' via apt? (s/N): " opcao
    if [[ "$opcao" =~ ^[Ss]$ ]]; then
        echo -e "\nInstalando dependências do sistema..."
        sudo apt update && sudo apt install -y python3-venv python3-pip
        if [ $? -ne 0 ]; then
            echo -e "\033[91mErro ao instalar as dependências automaticamente.\033[0m"
            echo -e "Por favor, execute manualmente no terminal: \033[1msudo apt update && sudo apt install python3-venv python3-pip -y\033[0m"
            read -p "Pressione Enter para sair..."
            exit 1
        fi
    else
        echo -e "\033[91mErro: O módulo 'venv' é obrigatório.\033[0m"
        echo -e "Por favor, instale o python3-venv manualmente."
        read -p "Pressione Enter para sair..."
        exit 1
    fi
fi

# 3. Criar ou validar o ambiente virtual (venv)
RECREAR_VENV=false
if [ -d "venv" ]; then
    if [ ! -f "venv/bin/python" ]; then
        echo -e "\033[93mAviso: Pasta 'venv' existente foi criada em outro sistema (ex: Windows) ou está corrompida.\033[0m"
        echo -e "Recriando o ambiente virtual para Linux..."
        rm -rf venv
        RECREAR_VENV=true
    fi
else
    RECREAR_VENV=true
fi

if [ "$RECREAR_VENV" = true ]; then
    echo -e "Criando ambiente virtual (venv)..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo -e "\033[91mErro ao criar o ambiente virtual.\033[0m"
        read -p "Pressione Enter para sair..."
        exit 1
    fi
fi

# 4. Ativar o ambiente virtual e instalar dependências
echo -e "Ativando ambiente virtual..."
source venv/bin/activate

echo -e "Verificando dependências do Python..."
pip install --disable-pip-version-check -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "\033[93mAviso: Não foi possível instalar/verificar as dependências pelo pip de forma silenciosa.\033[0m"
    echo -e "Tentando novamente com mais detalhes..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "\033[91mErro: Não foi possível instalar as dependências obrigatórias.\033[0m"
        echo -e "Por favor, verifique sua conexão com a internet."
        read -p "Pressione Enter para sair..."
        exit 1
    fi
fi

# 5. Executar o script principal
echo -e "\033[92mIniciando o Ciclo de Estudos...\033[0m\n"
python ciclo.py

# Caso o programa encerre, desativa o venv
deactivate
