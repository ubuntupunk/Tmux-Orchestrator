#!/bin/bash
# Dynamic scheduler with note for next check
# Usage: ./schedule_with_note.sh <minutes> "<note>" [target_window]

MINUTES=${1:-3}
NOTE=${2:-"Standard check-in"}
TARGET=${3:-"tmux-orc:0"}

# Get the directory where the script is located, and handle spaces in path
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &> /dev/null && pwd)"
NOTE_FILE="$SCRIPT_DIR/next_check_note.txt"
TMUX_UTILS_FILE="$SCRIPT_DIR/tmux_utils.py"

# Create a note file for the next check
echo "=== Next Check Note ($(date)) ===" > "$NOTE_FILE"
echo "Scheduled for: $MINUTES minutes" >> "$NOTE_FILE"
echo "" >> "$NOTE_FILE"
echo "$NOTE" >> "$NOTE_FILE"

echo "Scheduling check in $MINUTES minutes with note: $NOTE"

# Calculate the exact time when the check will run
CURRENT_TIME=$(date +"%H:%M:%S")
RUN_TIME=$(date -v +${MINUTES}M +"%H:%M:%S" 2>/dev/null || date -d "+${MINUTES} minutes" +"%H:%M:%S" 2>/dev/null)

# Use nohup to completely detach the sleep process
# Use bc for floating point calculation
SECONDS=$(echo "$MINUTES * 60" | bc)
# The command to be sent to tmux. Note the escaping for the inner command.
COMMAND_TO_RUN="Time for orchestrator check! cat \"$NOTE_FILE\" && python3 \"$TMUX_UTILS_FILE\""

nohup bash -c "sleep $SECONDS && tmux send-keys -t \"$TARGET\" \"$COMMAND_TO_RUN\" && sleep 1 && tmux send-keys -t \"$TARGET\" Enter" > /dev/null 2>&1 &

# Get the PID of the background process
SCHEDULE_PID=$!

echo "Scheduled successfully - process detached (PID: $SCHEDULE_PID)"
echo "SCHEDULED TO RUN AT: $RUN_TIME (in $MINUTES minutes from $CURRENT_TIME)"
