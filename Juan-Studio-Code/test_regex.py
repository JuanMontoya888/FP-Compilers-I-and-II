import re
prompt_text = "PS C:\\Users\\Juan\\Project> "
match = re.search(r'PS (([a-zA-Z]:)?[^>]+)>', prompt_text)
if match:
    print(match.group(1).strip())
