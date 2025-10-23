@echo off
cd /d "%~dp0"
poetry run python -m mcp_pyrocrail.server
