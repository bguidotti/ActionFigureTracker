import json

# Load JSON
with open('Models/all_figures.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find figures with empty imageString and year data (these are the new ones)
new_figures = [f for f in data if f.get('imageString') == '' and f.get('year')]

# Sort by year, then name
new_figures.sort(key=lambda x: (x.get('year', 9999), x['name']))

print(f"Found {len(new_figures)} figures with empty imageString and year data:\n")
for i, fig in enumerate(new_figures, 1):
    print(f"{i}. {fig['name']}")
    print(f"   Year: {fig.get('year')}, Wave: {fig.get('wave', 'N/A')}")
    print(f"   ID: {fig.get('id')}")
    print()
