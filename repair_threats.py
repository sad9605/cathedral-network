import json

with open('threats.json', 'r') as f:
    content = f.read()

# Find the first complete JSON object by counting braces
depth = 0
in_string = False
escape = False
end = 0
for i, ch in enumerate(content):
    if escape:
        escape = False
        continue
    if ch == '\\':
        escape = True
        continue
    if ch == '"' and not escape:
        in_string = not in_string
        continue
    if not in_string:
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                end = i + 1
                break

if end == 0:
    print("Could not find a complete JSON object.")
    exit(1)

first_object = content[:end]
data = json.loads(first_object)

# Save back (overwrite) with proper formatting
with open('threats.json', 'w') as f:
    json.dump(data, f, indent=2)

print(f"Success! threats.json repaired. Contains {len(data.get('threats', []))} threats.")
