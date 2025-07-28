#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "🚀 Starting Serena with Agno Agent from: $SCRIPT_DIR"

# Start Serena Agno Agent in background
echo "📡 Starting Serena Agno Agent..."
cd "$SCRIPT_DIR/serena"
python scripts/agno_agent.py --project . &
SERENA_PID=$!

# Wait a moment for the agent to start
sleep 3

# Start Agent UI in background
echo "🌐 Starting Agent UI..."
cd "$SCRIPT_DIR/agent-ui"
npm run dev &
UI_PID=$!

echo "✅ Services started!"
echo "📡 Serena Agno Agent PID: $SERENA_PID"
echo "🌐 Agent UI PID: $UI_PID"
echo ""
echo "🌐 Agent UI should be available at: http://localhost:3000"
echo "📡 Serena Agent should be running on the default port"
echo ""
echo "To stop both services, run: kill $SERENA_PID $UI_PID"
echo ""
echo "Press Ctrl+C to stop both services..."

# Wait for user to stop
wait 