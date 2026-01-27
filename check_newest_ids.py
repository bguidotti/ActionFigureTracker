import json

# Load current JSON
with open('Models/all_figures.json', 'r', encoding='utf-8') as f:
    current = json.load(f)

# Find max ID
max_id = max(f['id'] for f in current)
print(f"Max ID in current file: {max_id}")

# Get figures with IDs near the max (likely the newest ones)
# Get the 9 highest IDs with empty imageString and year
figures_with_year = [f for f in current if f.get('year') and f.get('imageString') == '']
figures_with_year.sort(key=lambda x: x['id'], reverse=True)

print(f"\nTop 9 figures with empty imageString, year data, and highest IDs:")
print("(These are likely the ones that need images)\n")
for i, fig in enumerate(figures_with_year[:9], 1):
    print(f"{i}. {fig['name']}")
    print(f"   ID: {fig['id']}, Year: {fig.get('year')}, Wave: {fig.get('wave', 'N/A')}")
    print()
