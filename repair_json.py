import json
import re
import os

# 1. Path to your file (Assumes it is in the Models folder or root)
# We will check both locations to be safe
possible_paths = ['Models/all_figures.json', 'all_figures.json']
file_path = next((p for p in possible_paths if os.path.exists(p)), None)

if not file_path:
    print("❌ Could not find all_figures.json. Make sure it's in the Models folder.")
    exit()

print(f"📖 Reading {file_path}...")

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 2. THE FIX: Look for the specific syntax errors
# Case A: Two arrays pasted together like [...][...] -> replace with [...] , [...] -> then flatten
# Case B: Missing comma between objects like ...} { ... -> replace with ...}, { ...

# Fix improper array merge (] followed by [)
content = re.sub(r'\]\s*\[', ',', content)

# Fix missing comma between objects (} followed by {)
content = re.sub(r'\}\s*\{', '}, {', content)

# 3. Validate and Save
try:
    data = json.loads(content)
    print("✅ JSON syntax fixed!")
    print(f"🎉 Total figures found: {len(data)}")
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    print("💾 File saved successfully.")
    
except json.JSONDecodeError as e:
    print(f"❌ Automatic repair failed. Error details:\n{e}")