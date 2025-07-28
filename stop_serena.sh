#!/bin/bash

echo "🛑 Stopping Serena Services..."
echo "=============================="

# Stop Serena Agno Agent
echo "📡 Stopping Serena Agno Agent..."
if pgrep -f "agno_agent.py" > /dev/null; then
    pkill -f "agno_agent.py"
    echo "   ✅ Stopped Serena Agno Agent"
else
    echo "   ℹ️  Serena Agno Agent was not running"
fi

# Stop Agent UI
echo "🌐 Stopping Agent UI..."
if pgrep -f "npm.*dev" > /dev/null; then
    pkill -f "npm.*dev"
    echo "   ✅ Stopped Agent UI"
else
    echo "   ℹ️  Agent UI was not running"
fi

echo ""
echo "✅ All Serena services stopped!" 