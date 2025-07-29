#!/bin/bash

# Send message to AI agent in tmux window (multi-provider support)
# Usage: send-ai-message.sh <session:window> <message> [provider]
# Providers: claude (default), rovodev, gemini

if [ $# -lt 2 ]; then
    echo "Usage: $0 <session:window> <message> [provider]"
    echo "Example: $0 agentic-seek:3 'Hello AI!' rovodev"
    echo "Providers: claude (default), rovodev, gemini"
    exit 1
fi

WINDOW="$1"
shift  # Remove first argument
MESSAGE="$1"
shift  # Remove message argument
PROVIDER="$1"  # Optional provider

# Get script directory for ai_provider.py
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Use Python orchestrator for multi-provider support
if [ -n "$PROVIDER" ]; then
    python3 "$SCRIPT_DIR/ai_provider.py" "$WINDOW" "$MESSAGE" "$PROVIDER"
else
    python3 "$SCRIPT_DIR/ai_provider.py" "$WINDOW" "$MESSAGE"
fi

# Check exit status
if [ $? -eq 0 ]; then
    echo "Message sent successfully to $WINDOW"
else
    echo "Failed to send message to $WINDOW"
    exit 1
fi