#!/bin/bash

echo "🔍 Checking Serena Services Status..."
echo "======================================"

# Check Serena Agno Agent
echo "📡 Serena Agno Agent:"
if pgrep -f "agno_agent.py" > /dev/null; then
    echo "   ✅ Running (PID: $(pgrep -f "agno_agent.py"))"
else
    echo "   ❌ Not running"
fi

# Check Agent UI
echo "🌐 Agent UI:"
if pgrep -f "npm.*dev" > /dev/null; then
    echo "   ✅ Running (PID: $(pgrep -f "npm.*dev"))"
else
    echo "   ❌ Not running"
fi

echo ""
echo "🌐 Agent UI URL: http://localhost:3000"
echo "📡 Serena Agent: Running on default port"

# Check if ports are accessible
echo ""
echo "🔌 Port Status:"
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "   ✅ Port 3000 (Agent UI): Accessible"
else
    echo "   ❌ Port 3000 (Agent UI): Not accessible"
fi 