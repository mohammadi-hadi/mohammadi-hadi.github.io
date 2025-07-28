#!/bin/bash

echo "🌐 Starting Local Website Server"
echo "==============================="
echo ""

# Check if port 8000 is available
if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️  Port 8000 is already in use. Using port 8001 instead..."
    PORT=8001
else
    PORT=8000
fi

echo "🚀 Starting local server on port $PORT..."
echo ""

# Try different server options
if command -v python3 &> /dev/null; then
    echo "🐍 Using Python 3 HTTP server..."
    echo "📱 Open your browser and go to: http://localhost:$PORT"
    echo ""
    echo "🛑 To stop the server, press Ctrl+C"
    echo ""
    python3 -m http.server $PORT
elif command -v python &> /dev/null; then
    echo "🐍 Using Python HTTP server..."
    echo "📱 Open your browser and go to: http://localhost:$PORT"
    echo ""
    echo "🛑 To stop the server, press Ctrl+C"
    echo ""
    python -m http.server $PORT
elif command -v php &> /dev/null; then
    echo "🐘 Using PHP server..."
    echo "📱 Open your browser and go to: http://localhost:$PORT"
    echo ""
    echo "🛑 To stop the server, press Ctrl+C"
    echo ""
    php -S localhost:$PORT
else
    echo "❌ No suitable server found. Please install Python or PHP."
    echo ""
    echo "📦 Installation options:"
    echo "   - Python: brew install python"
    echo "   - PHP: brew install php"
    exit 1
fi 