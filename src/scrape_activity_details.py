import requests
from bs4 import BeautifulSoup
import json
import time
import sys
import re
import argparse


def fetch_activity_details(url, name):
    """Fetch detailed content from an activity page"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title from the hero section
        title_text = name
        hero = soup.find('div', class_='pagecover')
        if hero:
            h1 = hero.find('h1')
            if h1:
                title_text = h1.get_text(strip=True)
        
        # Extract hero description
        description = ""
        if hero:
            hero_content = hero.find('div', class_='element-content')
            if hero_content:
                desc_p = hero_content.find('p')
                if desc_p:
                    description = desc_p.get_text(strip=True)
        
        # Extract ALL images from the page (bg-image divs with mytherme CDN URLs)
        # Filter out common background image that appears on every page
        EXCLUDED_IMAGES = {
            'https://cdn.mytherme.app/serve/6c654bc1-d1f0-49d3-80b0-4b8680b072ff'
        }
        
        all_images = []
        bg_image_divs = soup.find_all('div', class_='bg-image')
        for bg in bg_image_divs:
            style = bg.get('style', '')
            match = re.search(r"url\('([^']+)'\)", style)
            if match:
                img_url = match.group(1)
                if ('mytherme.app' in img_url or '/serve/' in img_url) and img_url not in EXCLUDED_IMAGES:
                    all_images.append(img_url)
        
        # Extract content sections
        sections = []
        
        # Find all content sections (media23-latcontent, media23-carousel, combo-largesmall-content)
        # Exclude htmlcontent since it's usually just schedule info which we capture separately
        content_divs = soup.find_all('div', class_=lambda x: x and any(
            cls in str(x) for cls in ['media23-latcontent', 'media23-carousel', 'combo-largesmall-content']
        ))
        
        for div in content_divs:
            section_data = {}
            
            # Get section heading
            h2 = div.find('h2')
            if h2:
                section_data['heading'] = h2.get_text(strip=True)
            
            # Get section content (paragraphs)
            paragraphs = div.find_all('p')
            section_text = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if text and len(text) > 10:
                    section_text.append(text)
            
            if section_text:
                section_data['content'] = section_text
            
            # Get images from this section
            section_images = []
            for img in div.find_all('img'):
                src = img.get('src', '')
                if 'mytherme.app' in src or '/serve/' in src:
                    section_images.append(src)
            
            # Also check for background images
            bg_imgs = div.find_all('div', class_='bg-image')
            for bg in bg_imgs:
                style = bg.get('style', '')
                match = re.search(r"url\('([^']+)'\)", style)
                if match:
                    img_url = match.group(1)
                    if 'mytherme.app' in img_url or '/serve/' in img_url:
                        section_images.append(img_url)
            
            if section_images:
                section_data['images'] = section_images
            
            if section_data:  # Only add non-empty sections
                sections.append(section_data)
        
        # Extract schedule/program information (if htmlcontent exists)
        schedule = {}
        htmlcontent = soup.find('div', class_='htmlcontent')
        if htmlcontent:
            schedule_text = htmlcontent.get_text(separator='\n', strip=True)
            # Clean up the schedule text
            if schedule_text:
                schedule['program'] = schedule_text
        
        # Extract tier/location from schedule styling
        metadata = {}
        tier_divs = soup.find_all('div', style=lambda x: x and 'border-left' in str(x))
        for div in tier_divs:
            style = div.get('style', '')
            if '#6141f3' in style.lower() or 'rgb(97, 65, 243)' in style:
                metadata['tier'] = 'THE PALM'
                break
            elif '#FE216E' in style.lower() or 'rgb(254, 33, 110)' in style:
                metadata['tier'] = 'GALAXY'
                break
            elif '#00C754' in style.lower() or 'rgb(0, 199, 84)' in style:
                metadata['tier'] = 'ELYSIUM'
                break
        
        return {
            'title': title_text,
            'description': description,
            'images': all_images,
            'sections': sections,
            'schedule': schedule,
            'metadata': metadata,
            'url': url
        }
        
    except Exception as e:
        print(f"  ✗ Error fetching {name}: {str(e)}")
        return None


def main():
    parser = argparse.ArgumentParser(description='Scrape detailed activity information')
    parser.add_argument('activities_json', help='Input activities JSON file path')
    parser.add_argument('output', help='Output detailed JSON file path')
    parser.add_argument('start', nargs='?', type=int, help='Start index (1-based, optional)')
    parser.add_argument('end', nargs='?', type=int, help='End index (inclusive, optional)')
    args = parser.parse_args()
    
    # Load activities list
    with open(args.activities_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    activities = data['activities']
    
    # Check for range arguments
    start_idx = 0
    end_idx = len(activities)
    
    if args.start and args.end:
        start_idx = args.start - 1  # Convert to 0-based index
        end_idx = args.end
        print(f"Processing activities {args.start} to {args.end}")
    
    # Filter activities by range
    activities = activities[start_idx:end_idx]
    
    results = []
    total_sections = 0
    total_images = 0
    
    print(f"\nFetching details for {len(activities)} activities...")
    print("=" * 60)
    
    try:
        for idx, activity in enumerate(activities, 1):
            name = activity['name']
            url = activity['link']
            
            print(f"\n[{idx}/{len(activities)}] {name}")
            print(f"  URL: {url}")
            
            details = fetch_activity_details(url, name)
            
            if details:
                results.append(details)
                
                num_sections = len(details.get('sections', []))
                num_images = sum(len(s.get('images', [])) for s in details.get('sections', []))
                
                total_sections += num_sections
                total_images += num_images
                
                print(f"  ✓ Fetched: {num_sections} sections, {num_images} images")
                
                if details.get('metadata', {}).get('tier'):
                    print(f"  Tier: {details['metadata']['tier']}")
            
            # Be polite, add delay
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user (Ctrl+C)")
        print(f"Saving progress: {len(results)} activities processed")
        
        # Save with interrupted flag
        output = {
            'activities': results,
            'total': len(results),
            'interrupted': True
        }
        
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output, f, ensure_ascii=False, indent=2)
        
        print(f"✓ Saved to {args.output}")
        return
    
    # Save results
    output = {
        'activities': results,
        'total': len(results),
        'interrupted': False
    }
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    
    print("\n" + "=" * 60)
    print(f"✓ Successfully fetched {len(results)} activities")
    print(f"  Total sections: {total_sections}")
    print(f"  Total images: {total_images}")
    print(f"  Saved to: {args.output}")


if __name__ == '__main__':
    main()
