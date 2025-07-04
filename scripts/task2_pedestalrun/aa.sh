#!/bin/bash

# Log file for the first command output
FIRST_LOG="log_first.txt"
# Log file for the second command output
SECOND_LOG="log_second.txt"

# Start the first command in the background and redirect output to FIRST_LOG
# Replace 'your_first_command' with the actual command you want to run
your_first_command > "$FIRST_LOG" 2>&1 &

# Capture the PID of the background command
FIRST_CMD_PID=$!

# Wait for 5 seconds
sleep 5

# Start the second command and redirect output to SECOND_LOG
# Replace 'your_second_command' with the actual command you want to run
your_second_command > "$SECOND_LOG" 2>&1 &

# Store the PID of the second command
SECOND_CMD_PID=$!

# Function to monitor the first command output and set a timeout
check_output() {
    echo "Monitoring output of the first command..." >> "$FIRST_LOG"
    LAST_OUTPUT_TIME=$(date +%s)

    while kill -0 $FIRST_CMD_PID 2>/dev/null; do
        # Check for new output by inspecting log file size
        sleep 1
        CURRENT_SIZE=$(stat -c%s "$FIRST_LOG")
        sleep 1
        NEW_SIZE=$(stat -c%s "$FIRST_LOG")

        if [[ "$CURRENT_SIZE" -eq "$NEW_SIZE" ]]; then
            # No output for the last 2 seconds
            CURRENT_TIME=$(date +%s)
            if (( CURRENT_TIME - LAST_OUTPUT_TIME > 20 )); then
                echo "No output for 20 seconds, terminating the first command..." >> "$FIRST_LOG"
                kill -SIGTERM $FIRST_CMD_PID
                exit 1
            fi
        else
            # There is output, reset the last output time
            LAST_OUTPUT_TIME=$(date +%s)
        fi
    done
}

# Start the output checker in the background
check_output &

# Store the output checker PID
OUTPUT_CHECK_PID=$!

# Wait for the second command to finish
wait $SECOND_CMD_PID

# Once the second command is finished, terminate the output checker
kill $OUTPUT_CHECK_PID

# If the first command is still running, terminate it and log the action
if kill -0 $FIRST_CMD_PID 2>/dev/null; then
    echo "Terminating the first command..." >> "$FIRST_LOG"
    kill $FIRST_CMD_PID
fi

echo "Script finished."
#  Key Changes:
# 	1.	Logging:
# 	▪	The output of the first command is redirected to ⁠log_first.txt. 	▪	The output of the second command is redirected to ⁠log_second.txt. 	▪	Any timeout messages regarding the first command are written to ⁠log_first.txt. 	2.	Output Monitoring:
# 	▪	The monitoring function checks for content in the first log file using the file size, allowing it to determine if there has been new output.
# How to Use:
# 	•	Replace ⁠your_first_command and ⁠your_second_command with your actual commands. 	•	Save the updated script to a file. 	•	Make it executable using ⁠chmod +x your_script.sh. 	•	Run the script with ⁠./your_script.sh.
# This setup should appropriately log output from both commands and handle timeout conditions as per your requirements.
#  I also want to log output for these two commands. Please put the output of first command to log_first.txt and output of second command to log_second.txt. Also if the timeout found, put the timeout message into log_first.txt
 
