#!/bin/bash

# Send message to Claude agent in tmux window (LEGACY - maintained for backward compatibility)
# Usage: send-claude-message.sh <session:window> <message>
# 
# NOTE: For multi-provider support, use send-ai-message.sh instead
# This script maintains backward compatibility with existing Claude workflows

if [ $# -lt 2 ]; then
    echo "Usage: $0 <session:window> <message>"
    echo "Example: $0 agentic-seek:3 'Hello Claude!'"
    echo ""
    echo "NOTE: For multi-provider AI support, use send-ai-message.sh instead"
    exit 1
fi

WINDOW="$1"
shift  # Remove first argument, rest is the message
MESSAGE="$*"

# Get script directory for ai_provider.py
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Check if ai_provider.py exists for enhanced functionality
if [ -f "$SCRIPT_DIR/ai_provider.py" ]; then
    echo "Using enhanced AI provider (Claude mode for backward compatibility)"
    python3 "$SCRIPT_DIR/ai_provider.py" "$WINDOW" "$MESSAGE" "claude"
    exit $?
fi

# Fallback to original behavior if ai_provider.py doesn't exist
echo "Using legacy Claude messaging"

# Send the message
tmux send-keys -t "$WINDOW" "$MESSAGE"

# Wait 0.5 seconds for UI to register
sleep 0.5

# Send Enter to submit
tmux send-keys -t "$WINDOW" Enter

echo "Message sent to $WINDOW: $MESSAGE"