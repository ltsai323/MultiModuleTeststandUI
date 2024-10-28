import re

# Your input string
input_string = "[mesg1] [mesg2] mesg3"
input_string = "[ModulePWRUpper] [readout] 1.4973,0.0000,0.00"

# Regular expression pattern to match the messages
pattern = r"\[(.*?)\]"

# Find all matches
matches = re.findall(pattern, input_string)

# Extracting the messages
mesg1 = matches[0]
mesg2 = matches[1]
mesg3 = input_string.split(']')[-1]

print("mesg1:", mesg1)
print("mesg2:", mesg2)
print("mesg3:", mesg3)

