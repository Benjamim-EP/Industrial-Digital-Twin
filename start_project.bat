@echo off
title Launcher Digital Twin
color 0A

echo ========================================================
echo       INICIANDO SISTEMA DE DIGITAL TWIN INDUSTRIAL
echo ========================================================
echo.

:: --- 1. VERIFICACAO DE DOCKER ---
echo [1/4] Subindo Infraestrutura (Kafka + Kafdrop)...
docker-compose up -d
if %errorlevel% neq 0 (
    color 0C
    echo.
    echo [ERRO] O Docker nao parece estar rodando ou o comando falhou.
    echo Verifique se o Docker Desktop esta aberto.
    pause
    exit /b
)

:: Pausa para o Kafka respirar antes de tentar conectar
echo.
echo Aguardando 15 segundos para o Kafka inicializar...
timeout /t 4 /nobreak >nul

:: --- 2. VISUALIZADOR PYTHON ---
echo [2/4] Iniciando Visualizador 3D (Rerun)...
:: O "start" abre uma nova janela. O "cmd /k" mantem a janela aberta se der erro.
start "Visualizador 3D - Python" cmd /k "python digital_twin_viewer.py"

:: --- 3. DETECTOR DE ANOMALIAS (SPRING BOOT) ---
echo [3/4] Iniciando Detector de Anomalias (Spring Boot)...
if exist "anomaly-detector" (
    :: Entra na pasta e roda o Maven Wrapper ou Maven Global
    start "Detector Anomalias - Spring" cmd /k "cd anomaly-detector && mvn spring-boot:run"
) else (
    echo [AVISO] Pasta 'anomaly-detector' nao encontrada. Pulando...
)

:: Pequena pausa para o Spring nao competir recurso de CPU na inicializacao
timeout /t 5 /nobreak >nul

:: --- 4. EMISSOR DE SENSORES (QUARKUS) ---
echo [4/4] Iniciando Simulador de Sensores (Quarkus)...
if exist "sensor-emitter" (
    :: Entra na pasta e roda o Quarkus dev mode
    start "Sensores - Quarkus" cmd /k "cd sensor-emitter && mvn quarkus:dev"
) else (
    echo [AVISO] Pasta 'sensor-emitter' nao encontrada. Pulando...
)

echo.
echo ========================================================
echo        TODOS OS SISTEMAS FORAM INICIADOS
echo ========================================================
echo.
echo 1. O Visualizador 3D deve abrir em breve.
echo 2. Acesse o Kafdrop em: http://localhost:9000
echo.
echo Pressione qualquer tecla para fechar este launcher (as outras janelas continuarao abertas).
pause >nul