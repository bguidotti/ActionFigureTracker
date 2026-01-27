# Sorting Functionality Added ✅

## Sort Options

Four sorting options are now available on all figure list pages:

1. **Newest First** ⬇️ - Shows most recently added figures first
2. **Oldest First** ⬆️ - Shows oldest figures first
3. **A-Z** 🔤 - Alphabetical by name
4. **Z-A** 🔤 - Reverse alphabetical by name

## Where It Appears

### 1. Main Grid View (All Figures)
- Sort menu button in top-right toolbar (next to + button)
- Icon: `arrow.up.arrow.down.circle`

### 2. I Have Tab
- Sort menu button in top-right toolbar
- Applies to filtered "I Have It!" figures

### 3. I Want Tab
- Sort menu button in top-right toolbar
- Applies to filtered "I Want It!" figures

## How It Works

- **Default Sort:** Newest First (most recently added figures appear first)
- **Persistent:** Sort preference is maintained per view (each tab remembers its sort)
- **Works with Filters:** Sorting applies after filtering by line
- **Works with Search:** Sorting applies after search filtering

## Technical Details

### SortOption Enum
Added to `Models/ActionFigure.swift`:
- `newestFirst` - Sorts by `dateAdded` descending
- `oldestFirst` - Sorts by `dateAdded` ascending
- `alphabetical` - Sorts by `name` ascending (case-insensitive)
- `reverseAlphabetical` - Sorts by `name` descending (case-insensitive)

### Updated Views
- `FigureGridView.swift` - Added sort state and menu
- `FilteredFigureView.swift` - Added sort state and menu
- `FigureDataStore.swift` - Removed default alphabetical sort (now handled in views)

## User Experience

1. Tap the sort icon (↕️) in the toolbar
2. Select desired sort option from menu
3. List immediately updates with new sort order
4. Sort preference persists while viewing that tab

## Future Enhancements (Optional)

- Save sort preference to UserDefaults
- Add more sort options (by line, by status, etc.)
- Visual indicator of current sort in UI
- Quick sort buttons instead of menu
