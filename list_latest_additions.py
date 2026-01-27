import json

# Load current and backup JSON
with open('Models/all_figures.json', 'r', encoding='utf-8') as f:
    current = json.load(f)

with open('Models/all_figures.json.backup', 'r', encoding='utf-8') as f:
    backup = json.load(f)

# Find new figures (by ID - highest IDs are newest)
backup_max_id = max(f['id'] for f in backup)
print(f"Backup max ID: {backup_max_id}")
print(f"Current max ID: {max(f['id'] for f in current)}")

# Get figures added in this merge (those with empty imageString and year data, with high IDs)
new_figures = [f for f in current if f['id'] > backup_max_id and f.get('imageString') == '' and f.get('year')]
new_figures.sort(key=lambda x: x['id'], reverse=True)

print(f"\nNew figures added (need images): {len(new_figures)}\n")
for i, fig in enumerate(new_figures[:20], 1):  # Show top 20
    print(f"{i}. {fig['name']}")
    print(f"   ID: {fig['id']}, Year: {fig.get('year')}, Wave: {fig.get('wave', 'N/A')}")
    print()

if len(new_figures) > 20:
    print(f"... and {len(new_figures) - 20} more")
