import re

string = "Hello, World! @2023 #Python-+_;: okj<F4><F5>!@#$%^&*()_="
cleaned_string = re.sub(r'[^A-Za-z0-9]+', '', string)

print(cleaned_string)  # Output: Hello World 2023 Python
