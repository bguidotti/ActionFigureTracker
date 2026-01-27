import json

with open('Models/all_figures.json', 'r', encoding='utf-8') as f:
    figures = json.load(f)

missing = [f for f in figures if not f.get('imageString') or f.get('imageString') == '']

print(f"Total missing: {len(missing)}\n")
print("First 30 figures to search:")
for i, fig in enumerate(missing[:30], 1):
    print(f"{i}. {fig['name']}")
