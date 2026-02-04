import requests
from bs4 import BeautifulSoup
import json
import argparse
import re

# Color to tier mapping based on the website's color coding
COLOR_TO_TIER = {
    '#FE216E': 'GALAXY',      # Red/Pink
    '#43B2D2': 'THE PALM',    # Blue/Cyan
    '#00C754': 'ELYSIUM'      # Green
}


def parse_therme_schedule(url):
    """
    Scrapes the Therme activities schedule and returns structured data.
    """
    # Fetch the webpage
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print("Fetching webpage...")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Initialize schedule for all days
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    schedule = {day: {'theme': '', 'activities': []} for day in days}
    
    print("Parsing schedule data...")
    
    # The page uses tab structure with data-tab-id attributes
    # Find all tab content divs
    tab_divs = soup.find_all('div', class_='page-tab')
    
    print(f"Found {len(tab_divs)} tab panels")
    
    # Map Romanian day names to English
    day_mapping = {
        'luni': 'Monday',
        'marti': 'Tuesday', 
        'miercuri': 'Wednesday',
        'joi': 'Thursday',
        'vineri': 'Friday',
        'sambata': 'Saturday',
        'duminica': 'Sunday'
    }
    
    for tab_div in tab_divs:
        # Get the data-tab-id for this div
        tab_id = tab_div.get('data-tab-id')
        
        # Extract theme
        theme_elem = tab_div.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        theme = theme_elem.get_text(strip=True) if theme_elem else ''
        
        if not theme:
            continue
        
        # Determine which day this is
        current_day = None
        for day in days:
            if day in theme:
                current_day = day
                break
        
        # If not found in theme, check tab navigation
        if not current_day and tab_id:
            # Find the corresponding navigation link
            nav_link = soup.find('a', {'data-tab-id': tab_id})
            if nav_link:
                nav_text = nav_link.get_text(strip=True).lower()
                for ro_day, en_day in day_mapping.items():
                    if ro_day in nav_text:
                        current_day = en_day
                        break
        
        if not current_day:
            continue
        
        schedule[current_day]['theme'] = theme
        print(f"Found: {theme} ({current_day})")
        
        # Find all activity divs (they have inline styles with border-left color)
        activity_divs = tab_div.find_all('div', style=re.compile(r'border-left.*solid'))
        
        for activity_div in activity_divs:
            # Extract color from style
            style = activity_div.get('style', '')
            color_match = re.search(r'border-left:\s*3px\s+solid\s+(#[0-9A-Fa-f]{6})', style, re.IGNORECASE)
            tier = None
            if color_match:
                color = color_match.group(1).upper()
                tier = COLOR_TO_TIER.get(color)
            
            # Extract activity text
            text = activity_div.get_text(strip=True)
            
            # Split into activity info and time
            parts = text.rsplit(')', 1)
            if len(parts) == 2:
                activity_part = parts[0] + ')'
                time_part = parts[1].strip()
            else:
                activity_part = text
                time_part = ''
            
            # Parse activity name and location
            match = re.match(r'^(.+?)\s*\(([^)]+)\)\s*$', activity_part)
            if match:
                activity_name = match.group(1).strip()
                location = match.group(2).strip()
                
                activity = {
                    'name': activity_name,
                    'location': location,
                    'time': time_part if time_part else ''
                }
                
                if tier:
                    activity['tier'] = tier
                
                schedule[current_day]['activities'].append(activity)
    
    # Fallback: If the above approach didn't work well, try parsing the entire page text
    if sum(len(schedule[day]['activities']) for day in days) < 10:
        print("Trying alternative parsing method...")
        text_content = soup.get_text()
        lines = [line.strip() for line in text_content.split('\n') if line.strip()]
        
        current_day = None
        i = 0
        section_start_index = {}
        
        # First pass: identify where each day section starts
        for idx, line in enumerate(lines):
            for day in days:
                # Look for day names in short lines (likely headings)
                if day in line and len(line) < 50 and any(keyword in line.lower() for keyword in ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']):
                    if day not in section_start_index:
                        section_start_index[day] = idx
                        if not schedule[day]['theme']:
                            schedule[day]['theme'] = line
                            print(f"Found: {line}")
        
        # Second pass: parse activities for each day within its section boundaries
        for day in days:
            if day not in section_start_index:
                continue
            
            start_idx = section_start_index[day]
            # Find where this day's section ends (next day starts or end of content)
            next_day_indices = [section_start_index[d] for d in days if d in section_start_index and section_start_index[d] > start_idx]
            end_idx = min(next_day_indices) if next_day_indices else len(lines)
            
            # Parse activities only within this day's section
            i = start_idx + 1
            while i < end_idx:
                line = lines[i]
                
                # Pattern: "Activity Name (Location)"
                match = re.match(r'^(.+?)\s*\(([^)]+)\)\s*$', line)
                if match:
                    activity_name = match.group(1).strip()
                    location = match.group(2).strip()
                    
                    # Look ahead for the time
                    time = ''
                    if i + 1 < len(lines):
                        next_line = lines[i + 1].strip()
                        if re.match(r'^\d{1,2}:\d{2}', next_line):
                            time = next_line
                            i += 1
                    
                    # Check if this activity already exists for this day
                    activity = {
                        'name': activity_name,
                        'location': location,
                        'time': time
                    }
                    if activity not in schedule[day]['activities']:
                        schedule[day]['activities'].append(activity)
                
                i += 1
    
    return schedule


def main():
    parser = argparse.ArgumentParser(description='Scrape Therme schedule')
    parser.add_argument('output', help='Output JSON file path')
    args = parser.parse_args()
    
    url = 'https://therme.ro/activities-schedule'
    
    print("="*60)
    print("THERME ACTIVITIES SCHEDULE SCRAPER")
    print("="*60)
    print(f"URL: {url}\n")
    
    try:
        # Scrape the schedule
        schedule = parse_therme_schedule(url)
        
        # Save to JSON
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(schedule, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Schedule saved to {args.output}")
        
        # Print summary
        print("\n" + "="*60)
        print("SCHEDULE SUMMARY")
        print("="*60)
        
        for day, data in schedule.items():
            activity_count = len(data['activities'])
            print(f"\n{day.upper()}")
            if data['theme']:
                print(f"  Theme: {data['theme']}")
            print(f"  Activities: {activity_count}")
            
            if activity_count > 0:
                print("  Sample activities:")
                for activity in data['activities'][:3]:  # Show first 3
                    tier_info = f" [{activity['tier']}]" if 'tier' in activity else ''
                    print(f"    - {activity['name']} at {activity['location']}{tier_info}")
                    if activity['time']:
                        print(f"      Time: {activity['time']}")
        
        # Total activities count
        total = sum(len(data['activities']) for data in schedule.values())
        print(f"\n{'='*60}")
        print(f"TOTAL ACTIVITIES: {total}")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
