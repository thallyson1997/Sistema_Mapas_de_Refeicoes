@echo off
title SGMRP - Sistema de Gerenciamento de Mapas de Refeicoes Penitenciario
color 0A

echo.
echo ========================================
echo  SGMRP - Iniciando Sistema...
echo ========================================
echo.

REM Mudar para o diretório do script
cd /d "%~dp0"

REM Verificar se Python está instalado
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale o Python 3.8 ou superior.
    echo.
    pause
    exit /b 1
)

echo [OK] Python encontrado
echo.

REM Verificar se requirements estão instalados
echo Verificando dependencias...
python -c "import flask" >nul 2>&1
if %errorlevel% neq 0 (
    echo [AVISO] Dependencias nao encontradas. Instalando...
    python -m pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [ERRO] Falha ao instalar dependencias!
        pause
        exit /b 1
    )
)

echo [OK] Dependencias verificadas
echo.

REM Iniciar o sistema
echo ========================================
echo  Sistema iniciado!
echo  Acesse: http://localhost:5000
echo ========================================
echo.
echo Pressione Ctrl+C para encerrar o sistema
echo.

python main.py

REM Se o Python encerrar com erro, pausar para ver a mensagem
if %errorlevel% neq 0 (
    echo.
    echo [ERRO] O sistema encerrou com erro!
    pause
)
