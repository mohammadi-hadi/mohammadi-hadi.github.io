#!/bin/bash

echo "🔧 Setting up Claude Code MCP with Serena..."
echo "============================================="

# Check if Claude Code is installed
if ! command -v claude &> /dev/null; then
    echo "❌ Claude Code is not installed or not in PATH"
    echo "Please install Claude Code first: npm install -g @anthropic-ai/claude-code"
    exit 1
fi

echo "✅ Claude Code found: $(claude --version)"

# Create MCP configuration directory
echo "📁 Creating MCP configuration directory..."
mkdir -p ~/.claude/mcp

# Copy the MCP configuration
echo "📄 Setting up Serena MCP configuration..."
cp ~/.claude/mcp/serena-simple.json ~/.claude/mcp/serena.json

echo ""
echo "✅ MCP Configuration Complete!"
echo ""
echo "🔧 Next Steps:"
echo "1. Restart Claude Code"
echo "2. Run: claude mcp list"
echo "3. You should see 'serena' in the list"
echo ""
echo "📝 To test the connection:"
echo "   claude mcp test serena"
echo ""
echo "🌐 To use Serena in Claude Code:"
echo "   claude --mcp-config ~/.claude/mcp/serena.json"
echo ""
echo "📚 For more info: https://docs.anthropic.com/en/docs/claude-code/mcp" 