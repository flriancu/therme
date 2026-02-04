import requests
from bs4 import BeautifulSoup
import json
import re


def scrape_all_activities(url):
    """
    Scrapes all activities from the Therme activities page (ALL ACTIVITIES tab).
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    print("Fetching webpage...")
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    
    # Parse HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print("Parsing activities data...")
    
    activities = []
    
    # Find all activity containers (divs with class 'attactev-body')
    activity_containers = soup.find_all('div', class_='attactev-body')
    
    print(f"Found {len(activity_containers)} activity containers")
    
    # Extract activity information
    for container in activity_containers:
        # Find the h3 element (activity name)
        heading = container.find('h3')
        if not heading:
            continue
        
        activity_name = heading.get_text(strip=True)
        
        # Find location and tier information
        # Look for text elements that contain location info
        location = ''
        tier = ''
        
        # Get all text from the container
        all_text = container.get_text(strip=True)
        
        # Remove the activity name to get remaining text
        remaining_text = all_text.replace(activity_name, '').strip()
        
        # The remaining text should be the tier + location
        if remaining_text:
            # Check for tier
            if 'THE PALM' in remaining_text:
                tier = 'THE PALM'
                location = remaining_text.replace('THE PALM', '').strip()
            elif 'GALAXY' in remaining_text:
                tier = 'GALAXY'
                location = remaining_text.replace('GALAXY', '').strip()
            elif 'ELYSIUM' in remaining_text:
                tier = 'ELYSIUM'
                location = remaining_text.replace('ELYSIUM', '').strip()
            else:
                # No tier, entire text is location
                location = remaining_text
        
        activity = {
            'name': activity_name,
            'location': location if location else ''
        }
        
        if tier:
            activity['tier'] = tier
        
        activities.append(activity)
    
    return activities


def main():
    url = 'https://therme.ro/activities'
    
    print("="*60)
    print("THERME ACTIVITIES SCRAPER")
    print("="*60)
    print(f"URL: {url}\n")
    
    try:
        activities = scrape_all_activities(url)
        
        # Save to JSON
        output_file = 'therme_activities.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({'activities': activities}, f, indent=2, ensure_ascii=False)
        
        print(f"\n✓ Activities saved to {output_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total activities found: {len(activities)}")
        
        if activities:
            print("\nSample activities:")
            for activity in activities[:10]:
                tier_info = f" [{activity['tier']}]" if 'tier' in activity else ''
                location_info = f" - {activity['location']}" if activity['location'] else ''
                print(f"  - {activity['name']}{tier_info}{location_info}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
