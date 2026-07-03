#!/bin/bash

# Detectar se está executando no Termux
IS_TERMUX=false
if [ -d "/data/data/com.termux/files/usr/bin" ] || [ -n "$TERMUX_VERSION" ]; then
    IS_TERMUX=true
fi

# Evita executar como root diretamente (a menos que necessário)
if [ "$EUID" -eq 0 ] && [ "$IS_TERMUX" = false ]; then
   echo "Aviso: É recomendado executar este script como usuário comum, não como root."
fi

# Obter o diretório onde o script está localizado
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo -e "\033[96m====================================================\033[0m"
if [ "$IS_TERMUX" = true ]; then
    echo -e "\033[96m    INICIALIZADOR DO CICLO DE ESTUDOS (TERMUX)      \033[0m"
else
    echo -e "\033[96m    INICIALIZADOR DO CICLO DE ESTUDOS (LINUX)       \033[0m"
fi
echo -e "\033[96m====================================================\033[0m"

# 1. Verificar se python3 ou python está instalado
PYTHON_BIN=""
if command -v python3 &> /dev/null; then
    PYTHON_BIN="python3"
elif command -v python &> /dev/null; then
    if python -c "import sys; sys.exit(0 if sys.version_info.major == 3 else 1)" &> /dev/null; then
        PYTHON_BIN="python"
    fi
fi

if [ -z "$PYTHON_BIN" ]; then
    echo -e "\033[91mErro: O Python 3 não está instalado no seu sistema.\033[0m"
    if [ "$IS_TERMUX" = true ]; then
        echo -e "Como você está no Termux, podemos tentar instalar automaticamente."
        read -p "Deseja instalar o Python agora via 'pkg install python'? (S/n): " opcao_py
        if [[ ! "$opcao_py" =~ ^[Nn]$ ]]; then
            pkg install -y python
            PYTHON_BIN="python"
        fi
    fi
    if [ -z "$PYTHON_BIN" ]; then
        echo -e "Por favor, instale o Python 3 antes de executar o script."
        read -p "Pressione Enter para sair..."
        exit 1
    fi
fi

# 2. No Termux, garantir que python-cryptography esteja instalado no sistema
if [ "$IS_TERMUX" = true ]; then
    echo -e "Verificando pacote 'python-cryptography' no Termux..."
    if ! dpkg -s python-cryptography &> /dev/null; then
        echo -e "\033[93mAviso: O pacote 'python-cryptography' do Termux não está instalado.\033[0m"
        echo -e "Para evitar erros complexos de compilação (Rust/Clang), recomenda-se instalar o pacote pré-compilado."
        read -p "Deseja instalar 'python-cryptography' automaticamente? (S/n): " opcao_crypt
        if [[ ! "$opcao_crypt" =~ ^[Nn]$ ]]; then
            pkg update && pkg install -y python-cryptography
            if [ $? -ne 0 ]; then
                echo -e "\033[91mAviso: Falha ao instalar automaticamente. Tentando prosseguir...\033[0m"
            fi
        fi
    fi
fi

# 3. Verificar se o módulo venv está disponível no python
if ! $PYTHON_BIN -c "import venv" &> /dev/null; then
    if [ "$IS_TERMUX" = true ]; then
        echo -e "\033[91mErro: O módulo 'venv' do Python não está funcionando no Termux.\033[0m"
        echo -e "Tente reinstalar o Python com 'pkg reinstall python'."
        read -p "Pressione Enter para sair..."
        exit 1
    else
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
fi

# 4. Criar ou validar o ambiente virtual (venv)
RECREAR_VENV=false
if [ -d "venv" ]; then
    if [ ! -f "venv/bin/python" ] || [ ! -f "venv/bin/pip" ]; then
        echo -e "\033[93mAviso: Pasta 'venv' existente foi criada em outro sistema ou está incompleta/corrompida.\033[0m"
        echo -e "Recriando o ambiente virtual para este sistema..."
        rm -rf venv
        RECREAR_VENV=true
    fi
    # Se estiver no Termux, o venv DEVE ter include-system-site-packages = true
    if [ "$IS_TERMUX" = true ] && [ "$RECREAR_VENV" = false ]; then
        if ! grep -q "include-system-site-packages = true" venv/pyvenv.cfg 2>/dev/null; then
            echo -e "\033[93mAviso: No Termux, o ambiente virtual precisa ter acesso aos pacotes globais do sistema.\033[0m"
            echo -e "Recriando o ambiente virtual com suporte a pacotes globais..."
            rm -rf venv
            RECREAR_VENV=true
        fi
    fi
else
    RECREAR_VENV=true
fi

if [ "$RECREAR_VENV" = true ]; then
    echo -e "Criando ambiente virtual (venv)..."
    if [ "$IS_TERMUX" = true ]; then
        $PYTHON_BIN -m venv --system-site-packages venv
    else
        $PYTHON_BIN -m venv venv
    fi
    if [ $? -ne 0 ] || [ ! -f "venv/bin/pip" ]; then
        echo -e "\033[91mErro ao criar o ambiente virtual ou o 'pip' não foi instalado no venv.\033[0m"
        echo -e "Certifique-se de que o pacote 'python3-venv' está corretamente instalado."
        read -p "Pressione Enter para sair..."
        exit 1
    fi
fi

# 5. Ativar o ambiente virtual e instalar dependências
echo -e "Ativando ambiente virtual..."
. venv/bin/activate

echo -e "Verificando dependências do Python..."

# No Termux, o pip não reconhece as wheels linux_aarch64 como compatíveis com
# aarch64-linux-android. Solução: baixar a wheel (.whl = ZIP) diretamente do
# GitHub e extraí-la no site-packages do venv, contornando 100% as verificações.
if [ "$IS_TERMUX" = true ]; then
    echo -e "Preparando dependências compatíveis com Termux (evitando compilação Rust)..."

    # Detectar versão do Python (ex: 3.13 -> cp313)
    PY_VER=$(venv/bin/python -c "import sys; print(f'cp{sys.version_info.major}{sys.version_info.minor}')")
    # Detectar arquitetura (ex: aarch64, armv7l, x86_64, i686)
    ARCH=$(uname -m)
    # Obter caminho do site-packages do venv
    SITE_PACKAGES=$(venv/bin/python -c "import site; print(site.getsitepackages()[0])")

    PYDANTIC_CORE_VER="2.41.5"
    WHEEL_NAME="pydantic_core-${PYDANTIC_CORE_VER}-${PY_VER}-${PY_VER}-linux_${ARCH}.whl"
    WHEEL_URL="https://github.com/Eutalix/android-pydantic-core/releases/download/v${PYDANTIC_CORE_VER}/${WHEEL_NAME}"
    WHEEL_PATH="/data/data/com.termux/files/usr/tmp/${WHEEL_NAME}"

    # Verificar se pydantic-core já está instalado na versão correta
    INSTALLED_PC_VER=$(venv/bin/pip show pydantic-core 2>/dev/null | grep "^Version:" | awk '{print $2}')
    if [ "$INSTALLED_PC_VER" != "$PYDANTIC_CORE_VER" ]; then
        echo -e "Baixando pydantic-core ${PYDANTIC_CORE_VER} pré-compilado para ${ARCH}..."
        curl -sL -o "$WHEEL_PATH" "$WHEEL_URL"
        if [ $? -eq 0 ] && [ -f "$WHEEL_PATH" ]; then
            echo -e "Extraindo pydantic-core no ambiente virtual..."
            # Uma .whl é um ZIP — extrair direto no site-packages contorna
            # a verificação de plataforma do pip completamente
            unzip -qo "$WHEEL_PATH" -d "$SITE_PACKAGES"
            rm -f "$WHEEL_PATH"
            if [ $? -eq 0 ]; then
                echo -e "\033[92m✔ pydantic-core ${PYDANTIC_CORE_VER} instalado com sucesso!\033[0m"
            else
                echo -e "\033[93mAviso: Falha ao extrair pydantic-core. Tentando continuar...\033[0m"
            fi
        else
            echo -e "\033[93mAviso: Não foi possível baixar a wheel de pydantic-core. Tentando continuar...\033[0m"
        fi

        # Instalar pydantic na versão compatível com o pydantic-core pré-compilado
        echo -e "Instalando pydantic==2.12.5 (compatível com pydantic-core ${PYDANTIC_CORE_VER})..."
        venv/bin/pip install --disable-pip-version-check -q --no-deps "pydantic==2.12.5" "annotated-types>=0.6.0" "typing-extensions>=4.12.0"
    else
        echo -e "pydantic-core ${PYDANTIC_CORE_VER} já instalado."
    fi
fi

# Instalar dependências do requirements.txt
venv/bin/pip install --disable-pip-version-check -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo -e "\033[93mAviso: Não foi possível instalar/verificar as dependências pelo pip de forma silenciosa.\033[0m"
    echo -e "Tentando novamente com mais detalhes..."
    venv/bin/pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "\033[91mErro: Não foi possível instalar as dependências obrigatórias.\033[0m"
        echo -e "Por favor, verifique sua conexão com a internet."
        read -p "Pressione Enter para sair..."
        exit 1
    fi
fi

# 6. Executar o script principal
echo -e "\033[92mIniciando o Ciclo de Estudos...\033[0m\n"
venv/bin/python ciclo.py

# Caso o programa encerre, desativa o venv
deactivate
