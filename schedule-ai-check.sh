#!/bin/bash
# Dynamic scheduler with note for next check (Multi-Provider AI Support)
# Usage: ./schedule-ai-check.sh <minutes> "<note>" [target_window] [ai_provider]
# Providers: claude (default), rovodev, gemini

MINUTES=${1:-3}
NOTE=${2:-"Standard check-in"}
TARGET=${3:-"tmux-orc:0"}
AI_PROVIDER=${4:-"claude"}

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create a note file for the next check
echo "=== Next Check Note ($(date)) ===" > "$SCRIPT_DIR/next_check_note.txt"
echo "Scheduled for: $MINUTES minutes" >> "$SCRIPT_DIR/next_check_note.txt"
echo "AI Provider: $AI_PROVIDER" >> "$SCRIPT_DIR/next_check_note.txt"
echo "" >> "$SCRIPT_DIR/next_check_note.txt"
echo "$NOTE" >> "$SCRIPT_DIR/next_check_note.txt"

echo "Scheduling AI check in $MINUTES minutes with note: $NOTE"
echo "Using AI provider: $AI_PROVIDER"

# Calculate the exact time when the check will run
CURRENT_TIME=$(date +"%H:%M:%S")
RUN_TIME=$(date -v +${MINUTES}M +"%H:%M:%S" 2>/dev/null || date -d "+${MINUTES} minutes" +"%H:%M:%S" 2>/dev/null)

# Use nohup to completely detach the sleep process
# Use bc for floating point calculation
SECONDS=$(echo "$MINUTES * 60" | bc)

# Choose the appropriate message script based on provider
if [ "$AI_PROVIDER" = "claude" ]; then
    MESSAGE_SCRIPT="send-claude-message.sh"
else
    MESSAGE_SCRIPT="send-ai-message.sh"
fi

# Create the check command
CHECK_CMD="Time for orchestrator check! cat $SCRIPT_DIR/next_check_note.txt && python3 $SCRIPT_DIR/tmux_utils.py"

nohup bash -c "sleep $SECONDS && $SCRIPT_DIR/$MESSAGE_SCRIPT $TARGET '$CHECK_CMD' $AI_PROVIDER" > /dev/null 2>&1 &

# Get the PID of the background process
SCHEDULE_PID=$!

echo "Scheduled successfully - process detached (PID: $SCHEDULE_PID)"
echo "SCHEDULED TO RUN AT: $RUN_TIME (in $MINUTES minutes from $CURRENT_TIME)"
echo "Will use: $MESSAGE_SCRIPT with provider: $AI_PROVIDER"