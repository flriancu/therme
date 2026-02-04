# Therme Bucharest Schedule Scraper

This project scrapes the activities schedule from [Therme Bucharest](https://therme.ro) and generates an interactive HTML page displaying all activities with detailed information.

## Features

- Scrapes the weekly schedule from [therme.ro/activities-schedule](https://therme.ro/activities-schedule)
- Extracts detailed information from individual activity pages
- Color-codes activities by tier (GALAXY, THE PALM, ELYSIUM)
- Fuzzy matching to link schedule items with detailed activity data (96%+ match rate)
- Responsive Bootstrap HTML interface with expandable activity cards
- Structured schedule display with days, locations, and times in a table format
- Mobile and desktop friendly design

## Requirements

- Python 3.10+
- Virtual environment (recommended)

## Installation

1. **Clone or download this project**

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv .venv
   .venv\Scripts\activate  # Windows
   source .venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Step 1: Scrape the Weekly Schedule

Scrapes all activities from the weekly schedule page (7 days):

```bash
python src/scrape_schedule.py artifacts/therme_schedule.json
```

**Output:** `artifacts/therme_schedule.json` (385 activities across 7 days)

### Step 2: Scrape Activities List

Extracts the complete list of activities from the activities page:

```bash
python src/scrape_activities.py artifacts/therme_activities.json
```

**Output:** `artifacts/therme_activities.json` (65 activities)

### Step 3: Scrape Activity Details

Fetches detailed content from each activity page including descriptions, images, and schedules:

```bash
python src/scrape_activity_details.py artifacts/therme_activities.json artifacts/therme_activities_detailed.json
```

**Optional:** Scrape a specific range of activities:

```bash
python src/scrape_activity_details.py artifacts/therme_activities.json artifacts/therme_activities_detailed.json 1 10
python src/scrape_activity_details.py artifacts/therme_activities.json artifacts/therme_activities_detailed.json 15 15
```

**Ctrl+C Support:** Press Ctrl+C to stop scraping early. Progress is saved automatically.

**Output:** `artifacts/therme_activities_detailed.json` (65 activities with full details)

### Step 4: Generate HTML Page

Creates an interactive Bootstrap HTML page with all the data:

```bash
python src/generate_html.py artifacts/therme_schedule.json artifacts/therme_activities_detailed.json docs/index.html
```

**Output:** `docs/index.html`

Open `docs/index.html` in your browser to view the interactive schedule.

**Live Demo:** [https://flriancu.github.io/therme/](https://flriancu.github.io/therme/)

## Project Structure

```
therme/
├── src/
│   ├── scrape_schedule.py              # Scrapes weekly schedule
│   ├── scrape_activities.py            # Scrapes activities list
│   ├── scrape_activity_details.py      # Scrapes detailed activity content
│   └── generate_html.py                # Generates interactive HTML page
├── artifacts/                          # Generated data files
│   ├── therme_schedule.json            # Weekly schedule data
│   ├── therme_activities.json          # Activities list
│   └── therme_activities_detailed.json # Detailed activity data
├── docs/
│   └── index.html                      # Generated HTML page (GitHub Pages)
└── requirements.txt                    # Python dependencies
```

## Scripts Overview

### `src/scrape_schedule.py`

- Scrapes the activities schedule for all 7 days
- Extracts activity name, location, time, and tier
- Handles tier color mapping:
  - `#FE216E` → GALAXY (red)
  - `#43B2D2` → THE PALM (blue)
  - `#00C754` → ELYSIUM (green)

### `src/scrape_activities.py`

- Extracts all activities from the `/activities` page
- Saves activity names and URLs for further processing

### `src/scrape_activity_details.py`

- Fetches full content from each activity page
- Extracts:
  - Title and description
  - All images (hero images + section images)
  - Content sections with headings
  - Structured schedule information (days, location, time)
  - Tier/location metadata
- Supports range-based scraping and Ctrl+C interruption

### `src/generate_html.py`

- Generates responsive Bootstrap 5 HTML page
- Features:
  - 7 tabs for each day of the week
  - Color-coded activity cards by tier
  - Expandable cards with detailed information
  - Fuzzy matching to link schedule items with detailed data
  - Structured schedule tables
  - Image galleries with CSS Grid
  - Responsive design for mobile and desktop

## Data Structure

### `therme_schedule.json`

```json
{
  "Monday": {
    "theme": "Monday theme text",
    "activities": [
      {
        "name": "Activity Name",
        "location": "Location",
        "time": "10:30 - 11:00",
        "tier": "THE PALM"
      }
    ]
  }
}
```

### `therme_activities_detailed.json`

```json
{
  "activities": [
    {
      "title": "Activity Title",
      "description": "Description text",
      "images": ["url1", "url2"],
      "sections": [
        {
          "heading": "Section Heading",
          "content": ["Paragraph 1", "Paragraph 2"],
          "images": ["url"]
        }
      ],
      "schedule": {
        "entries": [
          {
            "days": "Luni - Duminica",
            "location": "Sauna Himalaya",
            "time": "12:30 - 13:00"
          }
        ],
        "activity_name": "Activity Name",
        "raw": "Raw schedule text"
      },
      "metadata": {
        "tier": "THE PALM"
      },
      "url": "https://therme.ro/activitati/activity-slug"
    }
  ],
  "total": 65,
  "interrupted": false
}
```

## Fuzzy Matching

The HTML generator uses multiple fuzzy matching strategies to link schedule items with detailed activity data:

- Exact match (case-insensitive)
- Substring matching
- `fuzz.ratio` - Simple string similarity
- `fuzz.partial_ratio` - Substring similarity
- `fuzz.token_sort_ratio` - Word order independent
- `fuzz.token_set_ratio` - Common token similarity

**Match threshold:** 60%  
**Current match rate:** ~96% (370/385 items)

## Technologies Used

- **Python 3.10**
- **BeautifulSoup4** - HTML parsing
- **lxml** - Fast XML/HTML parser
- **requests** - HTTP library
- **rapidfuzz** - Fast fuzzy string matching
- **Bootstrap 5** - Responsive UI framework

## License
