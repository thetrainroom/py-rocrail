@echo off
REM Quick start script for Rocrail test server (Windows)

set ACTION=%1
if "%ACTION%"=="" set ACTION=start

if "%ACTION%"=="start" goto start
if "%ACTION%"=="stop" goto stop
if "%ACTION%"=="restart" goto restart
if "%ACTION%"=="logs" goto logs
if "%ACTION%"=="status" goto status
if "%ACTION%"=="build" goto build
if "%ACTION%"=="clean" goto clean
goto usage

:start
    echo Starting Rocrail Docker test server...
    docker-compose up -d
    echo.
    echo Waiting for server to be ready...
    timeout /t 5 /nobreak >nul
    echo.
    echo [32m✓ Rocrail server is running on localhost:8051[0m
    echo.
    echo Test connection with:
    echo   python -c "from pyrocrail.pyrocrail import PyRocrail; pr = PyRocrail('localhost', 8051); pr.start(); print('Connected!'); pr.stop()"
    echo.
    echo Run integration tests with:
    echo   pytest tests/integration/test_docker_rocrail.py -v
    echo.
    echo View logs with:
    echo   docker-compose logs -f
    goto end

:stop
    echo Stopping Rocrail Docker test server...
    docker-compose down
    echo [32m✓ Server stopped[0m
    goto end

:restart
    echo Restarting Rocrail Docker test server...
    docker-compose restart
    timeout /t 5 /nobreak >nul
    echo [32m✓ Server restarted[0m
    goto end

:logs
    docker-compose logs -f rocrail
    goto end

:status
    docker-compose ps
    goto end

:build
    echo Building Rocrail Docker image...
    docker-compose build
    echo [32m✓ Build complete[0m
    goto end

:clean
    echo Removing Rocrail Docker container and volumes...
    docker-compose down -v
    echo [32m✓ Cleanup complete[0m
    goto end

:usage
    echo Usage: %0 {start^|stop^|restart^|logs^|status^|build^|clean}
    echo.
    echo Commands:
    echo   start   - Start the Rocrail test server
    echo   stop    - Stop the server
    echo   restart - Restart the server
    echo   logs    - View server logs (follow mode)
    echo   status  - Check server status
    echo   build   - Build the Docker image
    echo   clean   - Remove container and volumes
    exit /b 1

:end
