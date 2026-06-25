#!/bin/bash

# claude /logout
unset ANTHROPIC_AUTH_TOKEN
TUNNEL_URL="https://webcast-explore-justice-resorts.trycloudflare.com"

echo "🔗 Testing connection to Ollama..."
STATUS=$(curl -s "$TUNNEL_URL/v1/models")
if [ -z "$STATUS" ]; then
  echo "❌ Cannot reach tunnel. Start Kaggle session first."
  exit 1
fi
echo "✅ Connected — model: qwen2.5-coder:7b"
echo ""

# export ANTHROPIC_BASE_URL="$TUNNEL_URL/v1"
# export ANTHROPIC_API_KEY="ollama"

# ANTHROPIC_BASE_URL="https://webcast-explore-justice-resorts.trycloudflare.com/v1" \
# ANTHROPIC_API_KEY="ollama" \
# claude --model qwen2.5-coder:7b

# echo "🚀 Starting Claude Code..."
# echo "   Project: $(pwd)"
# echo ""

# claude --model qwen2.5-coder:7b

# Format 1: with ollama/ prefix
export ANTHROPIC_BASE_URL="https://webcast-explore-justice-resorts.trycloudflare.com/v1" \
ANTHROPIC_API_KEY="ollama" \
claude --model ollama/qwen2.5-coder:7b

# Format 2: without tag
# ANTHROPIC_BASE_URL="https://webcast-explore-justice-resorts.trycloudflare.com/v1" \
# ANTHROPIC_API_KEY="ollama" \
# claude --model qwen2.5-coder

