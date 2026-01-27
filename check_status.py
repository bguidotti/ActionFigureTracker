#!/usr/bin/env python3
import json

with open(r'Models\all_figures.json', encoding='utf-8') as f:
    figures = json.load(f)

dc = [x for x in figures if x.get('series') == 'dc-multiverse']
missing = [x for x in dc if not x.get('imageString')]

print(f"DC Multiverse figures: {len(dc)}")
print(f"With images: {len(dc) - len(missing)}")
print(f"Missing images: {len(missing)}")

if missing:
    print("\nMissing:")
    for x in missing:
        print(f"  - {x['name']}")
