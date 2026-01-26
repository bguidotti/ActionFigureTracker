# Action Figure Tracker

A fun, kid-friendly iOS app for tracking your action figure collection!

Built with SwiftUI for iOS 17+.

## Features

- **Track 3 Figure Lines:**
  - DC Multiverse (McFarlane Toys)
  - Masters of the Universe (Mattel)
  - Marvel Legends (Hasbro)

- **Kid-Friendly Design:**
  - BIG buttons and images
  - Simple "I Have It!" / "I Want It!" toggles
  - Fun confetti animation when you add a figure!
  - Colorful, easy-to-read interface

- **Collection Features:**
  - Browse all figures in a grid
  - Filter by figure line
  - Separate tabs for "I Have" and "I Want"
  - Add notes to each figure
  - Mark favorites with a heart
  - Fun stats showing your collection progress

## Setup Instructions

### Step 1: Create the Xcode Project (on Mac)

1. Open **Xcode** on your Mac
2. Select **Create New Project**
3. Choose **App** under iOS
4. Configure:
   - **Product Name:** ActionFigureTracker
   - **Interface:** SwiftUI
   - **Language:** Swift
   - **Minimum Deployment:** iOS 17.0
5. Click **Create** and save to your preferred location

### Step 2: Copy the Swift Files

Copy all `.swift` files from this folder structure into your Xcode project:

```
ActionFigureTracker/
├── ActionFigureTrackerApp.swift
├── Models/
│   ├── ActionFigure.swift
│   ├── FigureDataStore.swift
│   └── MockData.swift
└── Views/
    ├── ContentView.swift
    ├── FigureGridView.swift
    ├── FigureDetailView.swift
    ├── FilteredFigureView.swift
    ├── StatsView.swift
    ├── AddFigureView.swift
    └── ConfettiView.swift
```

**In Xcode:**
1. Delete the auto-generated `ContentView.swift` (it will be replaced)
2. Create **New Group** called `Models`
3. Create **New Group** called `Views`
4. Drag the files from this folder into the appropriate groups

### Step 3: Add Figure Images

This is the fun part you can do with your son!

1. **Take Photos:**
   - Set up his action figures
   - Take clear photos against a plain background
   - Have him help with the "photo shoot"!

2. **AirDrop to Mac:**
   - Send photos from your iPhone to your Mac

3. **Add to Xcode:**
   - Open `Assets.xcassets` in Xcode
   - Drag each image into the assets
   - **Important:** Name them to match the `imageName` in `MockData.swift`:
     - `batman_hush`
     - `superman_ac1000`
     - `flash_rebirth`
     - etc.

4. **Or use placeholder images:**
   - The app shows a gradient if an image isn't found
   - You can add images later!

### Step 4: Run the App

1. Select an iPhone simulator (or your device)
2. Press **Cmd + R** to build and run
3. The app will show 30 sample figures to start

### Step 5: Customize with Your Son!

This is where you become the "Product Manager" and he becomes the "Lead Tester"!

**Things to customize:**

1. **Edit `MockData.swift`:**
   - Add figures he actually owns
   - Remove ones he doesn't care about
   - Change wave names
   - Update notes

2. **Add more figures:**
   - Use the "+" button in the app
   - Or edit `MockData.swift`

3. **Ask him for feedback:**
   - "Are the buttons big enough?"
   - "What color should this be?"
   - "Should we add more animations?"

## Using Cursor to Customize

Open this folder in Cursor on your Mac and try these prompts:

### Make Text Bigger
```
"Make the figure names larger and bolder, like size 24 font"
```

### Add a New Figure Line
```
"Add a new figure line called 'Transformers' with a robot emoji"
```

### Change Colors
```
"Change the 'I Have It' button to be bright blue instead of green"
```

### Add Sound Effects
```
"Add a fun 'ding' sound when I mark a figure as collected"
```

### Add More Animations
```
"Add a bounce animation when I tap on a figure card"
```

## File Structure

```
ActionFigureTracker/
├── ActionFigureTrackerApp.swift  # App entry point
├── Models/
│   ├── ActionFigure.swift        # Figure data model
│   ├── FigureDataStore.swift     # Data storage & persistence
│   └── MockData.swift            # Sample figures
├── Views/
│   ├── ContentView.swift         # Main tab view
│   ├── FigureGridView.swift      # Grid of all figures
│   ├── FigureDetailView.swift    # Single figure view
│   ├── FilteredFigureView.swift  # "I Have" / "I Want" tabs
│   ├── StatsView.swift           # Collection stats
│   ├── AddFigureView.swift       # Add new figures
│   └── ConfettiView.swift        # Fun confetti animation!
└── Assets.xcassets/              # Images and colors
```

## Data Persistence

The app automatically saves:
- Which figures you have/want
- Notes for each figure
- Favorite figures

Data is stored in `UserDefaults` and persists between app launches.

## Future Ideas

Things you could add with Cursor:

- **Photo import:** Let him take photos directly in the app
- **Barcode scanner:** Scan figure packaging
- **Sharing:** Export wishlist as a photo
- **Trading:** Mark figures available for trade
- **Price tracking:** How much each figure costs
- **Release dates:** When new figures come out

## Requirements

- macOS with Xcode 15+
- iOS 17.0+
- iPhone or iPad (or Simulator)

## Have Fun!

The goal is to make something YOUR son loves, not something perfect. Let him drive the design decisions and have fun coding together!
