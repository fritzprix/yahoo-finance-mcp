#!/bin/bash
# MCP Inspector Launcher for Unix/Linux/macOS
# This script starts the MCP Inspector to test the Yahoo Finance MCP server

echo "========================================"
echo "Starting MCP Inspector"
echo "========================================"
echo ""
echo "The inspector will start on http://localhost:6274"
echo "Press Ctrl+C to stop the server"
echo ""

npx @modelcontextprotocol/inspector uv --directory . run yfin-mcp
