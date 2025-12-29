#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Add the src directory to the PYTHONPATH
export PYTHONPATH=$PYTHONPATH:./src

# Load environment variables from .env file
export $(grep -v '^#' .env | xargs)

# Start the MCP server in the background
echo "Starting MCP Server (http://localhost:8000)..."
python3 -m uvicorn mcp_server.main:app --host 0.0.0.0 --port 8000 >> src/mcp_server/mcp-server.log 2>&1 &
MCP_SERVER_PID=$!
echo "MCP Server PID: $MCP_SERVER_PID"

echo "MCP Server started. Press Ctrl+C to stop it."

# Trap Ctrl+C to gracefully kill background processes
trap "echo 'Stopping MCP Server...'; kill $MCP_SERVER_PID; wait $MCP_SERVER_PID 2>/dev/null; echo 'MCP Server stopped.'; exit" INT TERM

# Wait for the process to exit
wait $MCP_SERVER_PID
