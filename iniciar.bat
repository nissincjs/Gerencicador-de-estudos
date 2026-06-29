@echo off
chcp 65001 > nul
setlocal enabledelayedexpansion

echo ====================================================
echo     INICIALIZADOR DO CICLO DE ESTUDOS (WINDOWS)
echo ====================================================

:: 1. Verificar se python está instalado
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo Erro: O Python não foi encontrado no sistema.
    echo Por favor, instale o Python (marque a opção "Add Python to PATH" no instalador).
    pause
    exit /b 1
)

:: 2. Criar ou validar o ambiente virtual (venv)
set RECREAR_VENV=false
if exist venv (
    if not exist venv\Scripts\python.exe (
        echo Aviso: Pasta 'venv' existente foi criada em outro sistema (ex: Linux) ou está corrompida.
        echo Recriando o ambiente virtual para Windows...
        rmdir /s /q venv
        set RECREAR_VENV=true
    )
) else (
    set RECREAR_VENV=true
)

if "!RECREAR_VENV!"=="true" (
    echo Criando ambiente virtual (venv)...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo Erro ao criar o ambiente virtual.
        pause
        exit /b 1
    )
)

:: 3. Ativar o ambiente virtual e instalar dependências
echo Ativando ambiente virtual...
call venv\Scripts\activate.bat

echo Verificando dependências do Python...
pip install --disable-pip-version-check -q -r requirements.txt
if !errorlevel! neq 0 (
    echo Aviso: Não foi possível instalar/verificar as dependências pelo pip de forma silenciosa.
    echo Tentando novamente com mais detalhes...
    pip install -r requirements.txt
    if !errorlevel! neq 0 (
        echo Erro: Não foi possível instalar as dependências obrigatórias.
        echo Por favor, verifique sua conexão com a internet.
        pause
        exit /b 1
    )
)

:: 4. Executar o script principal
echo Iniciando o Ciclo de Estudos...
python ciclo.py

pause
