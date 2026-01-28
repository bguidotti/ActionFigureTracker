# Action Figure Image Search Server

A Flask backend that scrapes action figure websites to provide image search functionality for the ActionFigureTracker iOS app.

## Quick Start

1. Install dependencies:
```bash
cd ImageServer
pip install -r requirements.txt
```

2. Run the server:
```bash
python app.py
```

The server will start on `http://localhost:5050`

## API Endpoints

### GET /api/search

Search for action figure images across multiple sources.

**Parameters:**
- `q` (required): Search query (e.g., "Batman Detective Comics")
- `sources` (optional): Comma-separated list of sources to search
  - `actionfigure411` - ActionFigure411.com
  - `legendsverse` - LegendsVerse.com  
  - `mcfarlane` - McFarlane.com
  - `google` - Google Images
  - Default: `all` (searches all sources)

**Example:**
```
GET /api/search?q=Batman&sources=actionfigure411,mcfarlane
```

**Response:**
```json
{
  "query": "Batman",
  "count": 15,
  "results": [
    {
      "url": "https://www.actionfigure411.com/dc/images/batman-4950.jpg",
      "title": "Batman Detective Comics #1000",
      "source": "ActionFigure411",
      "source_icon": "star.fill"
    }
  ]
}
```

### GET /api/health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "ActionFigure Image Search"
}
```

## iOS App Configuration

In `ImageSearchView.swift`, update the `apiBaseURL` to point to your server:

```swift
private let apiBaseURL = "http://localhost:5050"
```

For testing on a physical device, use your computer's local IP:
```swift
private let apiBaseURL = "http://192.168.1.100:5050"
```

## Notes

- The server scrapes websites, so results depend on the current structure of those sites
- Google Images may be limited due to anti-scraping measures
- For best results, run the server on the same machine as the iOS Simulator
