# Image Search Script Instructions

## Overview
The `find_all_images.py` script automatically searches for and finds image URLs for all figures missing images in your JSON file.

## How It Works
1. **Loads** your `all_figures.json` file
2. **Finds** all figures with empty `imageString` fields
3. **Searches** actionfigure411.com for each figure
4. **Extracts** image URLs from the search results
5. **Updates** the JSON file with found images
6. **Saves progress** every 10 figures (so you can stop and resume)

## Usage

### First Time Setup
The required libraries should already be installed, but if you get an error:
```bash
pip install requests beautifulsoup4
```

### Running the Script
```bash
cd c:\Code\ActionFigureTracker
python find_all_images.py
```

### What to Expect
- The script will process ~226 figures missing images
- It shows progress: `[1/226] Figure Name`
- Results: `[FOUND]` or `[NOT FOUND]`
- Progress saves every 10 figures
- Takes about 2 seconds per figure (with delays)
- **Total time: ~7-8 minutes for all figures**

### Rate Limiting
- The script includes 2-second delays between requests
- If you get blocked/rate limited:
  1. Wait 5-10 minutes
  2. Run the script again - it will resume where it left off
  3. Already searched figures are skipped

### Progress File
The script creates `image_search_progress.json` to track:
- Which figures have been searched
- Which images were found
- Allows resuming if interrupted

### Results
- Found images are automatically added to `all_figures.json`
- The script shows a summary at the end:
  - Images found: X
  - Figures updated: X
  - Errors: X

## Troubleshooting

### "Missing required libraries" error
```bash
pip install requests beautifulsoup4
```

### Script stops/crashes
- Just run it again - it will resume from where it stopped
- Progress is saved every 10 figures

### No images found
- Some figures may not be on actionfigure411.com
- You can manually add those images later
- The script will mark them as "searched" so it won't try again

### Rate limited / Blocked
- Wait 10-15 minutes
- Run the script again
- It will continue from where it left off

## Manual Image Addition
If the script can't find an image, you can manually add it:
1. Find the image URL on actionfigure411.com or legendsverse.com
2. Edit `all_figures.json`
3. Find the figure by name
4. Update the `imageString` field with the URL

## Notes
- The script is respectful with delays between requests
- It only searches actionfigure411.com (most reliable source)
- Images are verified to exist before being added
- All changes are saved to the JSON file automatically
