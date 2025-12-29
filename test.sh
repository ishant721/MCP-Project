#!/bin/bash

# Exit immediately if a command exits with a non-zero status.
set -e

# Kill any existing server process
if pgrep -f "mcp_server.main:app"; then
    echo "Stopping existing MCP Server..."
    pkill -f "mcp_server.main:app"
    sleep 2
fi

# Start the MCP server
./run.sh

echo "MCP Server is running in the background."
echo "Tailing the log file: src/mcp_server/mcp-server.log"
echo "Press Ctrl+C to stop tailing the log."
echo "Now, go to your GitHub repository and trigger a webhook (e.g., by pushing a commit)."

# Tail the log file
tail -f src/mcp_server/mcp-server.log
