@echo off
REM Production MCP Inspector Launcher for Windows
REM This script starts the MCP Inspector to test the PUBLISHED yfin-mcp package

echo ========================================
echo Starting Production MCP Inspector
echo ========================================
echo.
echo This script tests the server via 'uvx yfin-mcp'
echo The inspector will start on http://localhost:6274
echo Press Ctrl+C to stop the server
echo.

npx @modelcontextprotocol/inspector uvx yfin-mcp
