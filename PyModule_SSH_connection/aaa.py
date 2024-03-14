import sys
from io import StringIO

def print_to_stderr_and_capture(message):
    # Save the original sys.stderr
    original_stderr = sys.stderr

    # Redirect sys.stderr to a StringIO object
    sys.stderr = StringIO()

    # Print the message to sys.stderr
    print(message, file=sys.stderr)

    # Get the captured stderr as a string
    captured_stderr = sys.stderr.getvalue()

    # Restore the original sys.stderr
    sys.stderr = original_stderr

    # Print the captured stderr and use it as needed
    print('orig stderr:',captured_stderr, file=sys.stderr)
    print("Captured Stderr:", captured_stderr)
    return captured_stderr

# Example usage
error_message = "This is an error message."
captured_output = print_to_stderr_and_capture(error_message)

# You can use captured_output as needed

