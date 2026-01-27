import json

# Load backup (original) and current JSON
with open('Models/all_figures.json.backup', 'r', encoding='utf-8') as f:
    backup = json.load(f)

with open('Models/all_figures.json', 'r', encoding='utf-8') as f:
    current = json.load(f)

# Create sets for comparison
backup_ids = {f['id'] for f in backup}
backup_names_lower = {f['name'].lower().strip() for f in backup}

# Find truly new figures (not in backup by ID or name)
new_figures = []
for fig in current:
    if fig['id'] not in backup_ids:
        # Check if name also doesn't exist (to be sure)
        if fig['name'].lower().strip() not in backup_names_lower:
            new_figures.append(fig)

# Sort by ID
new_figures.sort(key=lambda x: x['id'])

print(f"Found {len(new_figures)} truly new figures (not in backup):\n")
for i, fig in enumerate(new_figures, 1):
    print(f"{i}. {fig['name']}")
    print(f"   ID: {fig['id']}, Year: {fig.get('year', 'N/A')}, Wave: {fig.get('wave', 'N/A')}")
    print(f"   ImageString: {'(empty)' if not fig.get('imageString') else '(has image)'}")
    print()
