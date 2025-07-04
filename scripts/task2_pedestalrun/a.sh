#!/bin/bash

# Start the first command in the background
# Replace 'your_first_command' with the actual command you want to run
your_first_command &

# Capture the PID of the background command
FIRST_CMD_PID=$!

# Temporary file to capture the output
OUTPUT_FILE=$(mktemp)

# Function to monitor output and set a timeout
check_output() {
    echo "Monitoring output of the first command..."
    while kill -0 $FIRST_CMD_PID 2>/dev/null; do
        # Check if there's output
        if ! read -t 1 line < $OUTPUT_FILE; then
            # No output for 1 second
            continue
        else
            # There's output, reset the timer
            LAST_OUTPUT_TIME=$(date +%s)
        fi
        # Check if the last output time has exceeded 20 seconds
        CURRENT_TIME=$(date +%s)
        if (( CURRENT_TIME - LAST_OUTPUT_TIME > 20 )); then
            echo "No output for 20 seconds, terminating the first command..."
            kill $FIRST_CMD_PID
            exit 1
        fi
    done
}

# Redirect output to a temporary file and start the monitoring in the background
exec > >(tee -a "$OUTPUT_FILE") 2>&1

# Start the output checker in the background
LAST_OUTPUT_TIME=$(date +%s)
check_output &

# Allow the check_output function to run in parallel
OUTPUT_CHECK_PID=$!

# Wait for 5 seconds
sleep 5

# Start the second command
# Replace 'your_second_command' with the actual command you want to run
your_second_command

# Once the second command is finished, kill the output checker
kill $OUTPUT_CHECK_PID

# If you want to kill the first command if it's still running
if kill -0 $FIRST_CMD_PID 2>/dev/null; then
    echo "Terminating the first command..."
    kill $FIRST_CMD_PID
fi

# Clean up the temporary output file
rm "$OUTPUT_FILE"

echo "Script finished."
