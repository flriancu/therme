import json
import re
from rapidfuzz import fuzz, process
import argparse
import sys

# Parse arguments
parser = argparse.ArgumentParser(description='Generate HTML schedule')
parser.add_argument('schedule_json', help='Input schedule JSON file path')
parser.add_argument('activities_json', help='Input detailed activities JSON file path')
parser.add_argument('output', help='Output HTML file path')
args = parser.parse_args()

# Read the schedule data
with open(args.schedule_json, 'r', encoding='utf-8') as f:
    schedule = json.load(f)

# Read the detailed activities data
with open(args.activities_json, 'r', encoding='utf-8') as f:
    activities_data = json.load(f)

# Create a mapping of activity names to their detailed data
activity_details_map = {}
activity_names = []
for activity in activities_data['activities']:
    activity_names.append(activity['title'])
    activity_details_map[activity['title']] = activity

def find_best_match(schedule_name, threshold=60):
    """Find the best matching activity using fuzzy string matching with multiple strategies"""
    # Try exact match first
    for activity_name in activity_names:
        if schedule_name.lower() == activity_name.lower():
            return activity_details_map.get(activity_name), 100
    
    # Try partial match (schedule name is contained in activity name or vice versa)
    schedule_lower = schedule_name.lower()
    for activity_name in activity_names:
        activity_lower = activity_name.lower()
        if schedule_lower in activity_lower or activity_lower in schedule_lower:
            # Calculate a similarity score
            score = max(
                fuzz.ratio(schedule_name, activity_name),
                fuzz.partial_ratio(schedule_name, activity_name),
                fuzz.token_sort_ratio(schedule_name, activity_name)
            )
            if score >= threshold:
                return activity_details_map.get(activity_name), score
    
    # Fall back to fuzzy matching with multiple scorers
    best_match = None
    best_score = 0
    
    for scorer in [fuzz.ratio, fuzz.partial_ratio, fuzz.token_sort_ratio, fuzz.token_set_ratio]:
        result = process.extractOne(
            schedule_name, 
            activity_names, 
            scorer=scorer,
            score_cutoff=threshold
        )
        if result:
            matched_name, score, _ = result
            if score > best_score:
                best_score = score
                best_match = activity_details_map.get(matched_name)
    
    return best_match, best_score

def parse_schedule_program(program_text, activity_title=None):
    if not program_text:
        return []

    lines = [line.strip() for line in program_text.split('\n') if line.strip()]
    if not lines:
        return []

    if lines and lines[0].lower() == 'program':
        lines = lines[1:]
    if activity_title and lines and lines[0].lower() == activity_title.lower():
        lines = lines[1:]

    def is_time_line(value):
        return bool(re.match(r'^\d{1,2}:\d{2}(\s*-\s*\d{1,2}:\d{2})?$', value))

    day_tokens = [
        'luni', 'marti', 'marți', 'miercuri', 'joi', 'vineri',
        'sambata', 'sâmbătă', 'duminica', 'duminică'
    ]

    def is_days_line(value):
        lower = value.lower()
        return any(token in lower for token in day_tokens)

    entries = []
    current_days = None
    current_location = None

    for line in lines:
        if is_days_line(line):
            current_days = line
            current_location = None
            continue

        if is_time_line(line):
            if current_location:
                entries.append({
                    'days': current_days or '',
                    'location': current_location,
                    'time': line
                })
                current_location = None
            continue

        # Assume any non-day/non-time line is a location
        current_location = line

    return entries

# Tier colors
TIER_COLORS = {
    'GALAXY': '#FE216E',      # Red/Pink
    'THE PALM': '#43B2D2',    # Blue/Cyan
    'ELYSIUM': '#00C754'      # Green
}

# Build unmatched activities list (activities not matched to any schedule item)
schedule_names = set()
for day_data in schedule.values():
    for activity in day_data.get('activities', []):
        schedule_names.add(activity.get('name', ''))

matched_activity_titles = set()
for schedule_name in schedule_names:
    details, _ = find_best_match(schedule_name)
    if details:
        matched_activity_titles.add(details['title'])

unmatched_activities = [
    name for name in activity_names if name not in matched_activity_titles
]

# Generate HTML
html = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Therme Bucharest Activities Schedule - Interactive Weekly Calendar</title>
    <meta name="description" content="Interactive weekly schedule for Therme Bucharest spa activities including saunas, pools, and wellness programs. View 385+ activities across GALAXY, THE PALM, and ELYSIUM zones.">
    
    <!-- Open Graph / Facebook -->
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://flriancu.github.io/therme/">
    <meta property="og:title" content="Therme Bucharest Activities Schedule">
    <meta property="og:description" content="Interactive weekly schedule for Therme Bucharest spa activities - 385+ activities including saunas, pools, and wellness programs">
    <meta property="og:image" content="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='1200' height='630'%3E%3Cdefs%3E%3ClinearGradient id='grad' x1='0%25' y1='0%25' x2='100%25' y2='100%25'%3E%3Cstop offset='0%25' style='stop-color:%2343B2D2;stop-opacity:1'/%3E%3Cstop offset='50%25' style='stop-color:%2300C754;stop-opacity:1'/%3E%3Cstop offset='100%25' style='stop-color:%23FE216E;stop-opacity:1'/%3E%3C/linearGradient%3E%3C/defs%3E%3Crect width='1200' height='630' fill='url(%23grad)'/%3E%3Ctext x='50%25' y='50%25' font-family='Arial,sans-serif' font-size='72' font-weight='bold' fill='white' text-anchor='middle' dominant-baseline='middle'%3ETherme Bucharest%3C/text%3E%3C/svg%3E">
    
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body {
            background-color: #f8f9fa;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        }
        .page-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 3rem 0;
            margin-bottom: 2rem;
        }
        .activity-card {
            background-color: white;
            border-radius: 8px;
            padding: 0;
            margin-bottom: 0.6rem;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            overflow: hidden;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .activity-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }
        .activity-header {
            padding: 0.6rem 1.2rem;
            cursor: pointer;
            transition: background-color 0.2s;
        }
        .activity-header:hover {
            background-color: #f7fafc;
        }
        .activity-name {
            font-weight: 600;
            font-size: 1rem;
            color: #2d3748;
        }
        .activity-location {
            color: #718096;
            font-size: 0.9rem;
            margin-left: 0.5rem;
        }
        .activity-time {
            color: #6141f3;
            font-weight: 500;
            font-size: 0.95rem;
        }
        .activity-details {
            padding: 1.2rem;
            border-top: 1px solid #e2e8f0;
            background-color: #fafbfc;
        }
        .activity-description {
            color: #4a5568;
            margin-bottom: 1.5rem;
            font-size: 0.95rem;
            line-height: 1.6;
        }
        .activity-section {
            margin-bottom: 1.5rem;
        }
        .activity-section h5 {
            color: #6141f3;
            font-size: 1rem;
            font-weight: 600;
            margin-bottom: 0.8rem;
        }
        .activity-section p {
            color: #4a5568;
            font-size: 0.9rem;
            line-height: 1.6;
            margin-bottom: 0.5rem;
            white-space: pre-wrap;
        }
        .activity-images {
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
            margin-top: 1rem;
        }
        .activity-image {
            height: 200px;
            width: auto;
            max-width: 300px;
            object-fit: cover;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }
        .activity-image:hover {
            transform: scale(1.05);
        }
        .schedule-info {
            background-color: #f0f4ff;
            padding: 1rem;
            border-radius: 6px;
            margin-top: 1rem;
        }
        .schedule-info h6 {
            color: #6141f3;
            font-weight: 600;
            margin-bottom: 0.8rem;
        }
        .schedule-table {
            width: 100%;
            border-collapse: collapse;
        }
        .schedule-table th {
            text-align: left;
            font-size: 0.8rem;
            color: #718096;
            padding: 0.5rem 0.5rem 0.5rem 0;
            border-bottom: 1px solid #e2e8f0;
        }
        .schedule-table td {
            padding: 0.5rem 0.5rem 0.5rem 0;
            font-size: 0.9rem;
            color: #4a5568;
            border-bottom: 1px solid #e2e8f0;
        }
        .schedule-table tr:last-child td {
            border-bottom: none;
        }
        .schedule-days {
            font-weight: 500;
            color: #6141f3;
        }
        .schedule-time {
            font-weight: 500;
            white-space: nowrap;
        }
        .expand-icon {
            transition: transform 0.3s;
            transform: rotate(0deg);
        }
        .activity-header:not([data-bs-toggle]) .expand-icon {
            display: none;
        }
        .collapsed .expand-icon {
            transform: rotate(-90deg);
        }

        .day-theme {
            color: #6141f3;
            font-size: 1.5rem;
            font-weight: 400;
            margin-bottom: 2rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #e2e8f0;
        }
        .nav-tabs .nav-link {
            color: #4a5568;
            font-weight: 500;
            border: none;
            border-bottom: 3px solid transparent;
        }
        .nav-tabs .nav-link:hover {
            border-color: transparent;
            background-color: #f7fafc;
        }
        .nav-tabs .nav-link.active {
            color: #6141f3;
            background-color: transparent;
            border-color: transparent;
            border-bottom-color: #6141f3;
        }
        .legend {
            display: flex;
            gap: 2rem;
            justify-content: center;
            margin-bottom: 2rem;
            flex-wrap: wrap;
        }
        .legend-item {
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }
        .legend-color {
            width: 30px;
            height: 4px;
            border-radius: 2px;
        }
    </style>
</head>
<body>
    <div class="page-header">
        <div class="container">
            <h1 class="text-center mb-3">Therme Activities Schedule</h1>
            <div class="legend">
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #FE216E;"></div>
                    <span>GALAXY</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #43B2D2;"></div>
                    <span>THE PALM</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background-color: #00C754;"></div>
                    <span>ELYSIUM</span>
                </div>
            </div>
        </div>
    </div>

    <div class="container mb-5">
        <ul class="nav nav-tabs mb-4" id="dayTabs" role="tablist">
"""

days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

# Generate tabs
for idx, day in enumerate(days):
    active = 'active' if idx == 0 else ''
    html += f"""            <li class="nav-item" role="presentation">
                <button class="nav-link {active}" id="{day.lower()}-tab" data-bs-toggle="tab" 
                        data-bs-target="#{day.lower()}" type="button" role="tab">
                    {day}
                </button>
            </li>
"""

# Add eighth tab for unmatched activities
html += f"""            <li class="nav-item" role="presentation">
                <button class="nav-link" id="unscheduled-tab" data-bs-toggle="tab" 
                        data-bs-target="#unscheduled" type="button" role="tab">
                    Unscheduled ({len(unmatched_activities)})
                </button>
            </li>
"""

html += """        </ul>

        <div class="tab-content" id="dayTabsContent">
"""

# Generate content for each day
for idx, day in enumerate(days):
    active = 'show active' if idx == 0 else ''
    day_data = schedule.get(day, {})
    theme = day_data.get('theme', '')
    activities = day_data.get('activities', [])
    
    html += f"""            <div class="tab-pane fade {active}" id="{day.lower()}" role="tabpanel">
                <h2 class="day-theme">{theme if theme else day}</h2>
"""
    
    if not activities:
        html += """                <div class="alert alert-info">No activities scheduled for this day.</div>
"""
    else:
        for idx, activity in enumerate(activities):
            name = activity.get('name', '')
            location = activity.get('location', '')
            time = activity.get('time', '')
            tier = activity.get('tier', '')
            
            # Get border color based on tier
            border_color = TIER_COLORS.get(tier, '#cccccc')
            
            # Find matching detailed activity data
            details, match_score = find_best_match(name)
            
            # Generate unique ID for collapse
            collapse_id = f"collapse-{day.lower()}-{idx}"
            
            # Check if we have details to show
            has_details = details is not None
            toggle_attrs = f'data-bs-toggle="collapse" data-bs-target="#{collapse_id}" aria-expanded="false" aria-controls="{collapse_id}"' if has_details else ''
            cursor_style = 'cursor: pointer;' if has_details else ''
            header_classes = 'activity-header collapsed' if has_details else 'activity-header'
            
            location_html = f'<span class="activity-location">({location})</span>' if location else ''
            
            html += f"""                <div class="activity-card" style="border-left: 4px solid {border_color};">
                    <div class="{header_classes}" {toggle_attrs} style="{cursor_style}">
                        <div class="d-flex justify-content-between align-items-center">
                            <div class="d-flex align-items-center flex-grow-1">
                                <span class="activity-name">{name}</span>
                                {location_html}
                            </div>
                            <div class="d-flex align-items-center gap-3">
                                {f'<div class="activity-time">{time}</div>' if time else ''}
"""
            
            if has_details:
                html += """                                <svg class="expand-icon" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                    <path fill-rule="evenodd" d="M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z"/>
                                </svg>
"""
            
            html += """                            </div>
                        </div>
                    </div>
"""
            
            if details:
                activity_url = details.get('url', '')
                html += f"""                    <div class="collapse" id="{collapse_id}">
                        <div class="activity-details">
                            <div style="color: #718096; font-size: 0.85rem; font-style: italic; margin-bottom: 0.8rem; padding-bottom: 0.8rem; border-bottom: 1px solid #e2e8f0;">
                                Matched activity: <strong>{details['title']}</strong> (Score: {match_score:.0f}%)
                                {f' • <a href="{activity_url}" target="_blank" rel="noopener noreferrer" style="color: #6141f3; text-decoration: none;">View original page ↗</a>' if activity_url else ''}
                            </div>
"""
                
                # Add images gallery if available
                images = details.get('images', []) or details.get('hero_image', None)
                if images:
                    if isinstance(images, str):
                        images = [images]
                    html += """                            <div class="activity-images" style="margin-bottom: 1.5rem;">
"""
                    for img_url in images:
                        html += f"""                                <img src="{img_url}" alt="{details['title']}" class="activity-image" loading="lazy" decoding="async">
"""
                    html += """                            </div>
"""
                
                # Add description
                if details.get('description'):
                    description_html = details['description'].replace('\n', '<br>')
                    html += f"""                            <div class="activity-description">
                                {description_html}
                            </div>
"""
                
                # Add sections
                for section in details.get('sections', []):
                    html += """                            <div class="activity-section">
"""
                    if section.get('heading'):
                        html += f"""                                <h5>{section['heading']}</h5>
"""
                    
                    # Add content paragraphs
                    for content in section.get('content', []):
                        content_html = content.replace('\n', '<br>')
                        html += f"""                                <p>{content_html}</p>
"""
                    
                    # Add images
                    if section.get('images'):
                        html += """                                <div class="activity-images">
"""
                        for img_url in section['images']:
                            html += f"""                                    <img src="{img_url}" alt="Activity image" class="activity-image" loading="lazy" decoding="async">
"""
                        html += """                                </div>
"""
                    
                    html += """                            </div>
"""
                
                # Add schedule if available (structured or raw)
                activity_schedule = details.get('schedule', {})
                if activity_schedule.get('entries'):
                    # Display structured schedule as a nice table
                    html += """                            <div class="schedule-info">
                                <h6>📅 Full Schedule</h6>
                                <table class="schedule-table">
                                    <thead>
                                        <tr>
                                            <th>Days</th>
                                            <th>Location</th>
                                            <th>Time</th>
                                        </tr>
                                    </thead>
                                    <tbody>
"""
                    for entry in activity_schedule['entries']:
                        html += f"""                                        <tr>
                                            <td class="schedule-days">{entry.get('days', '')}</td>
                                            <td>{entry.get('location', '')}</td>
                                            <td class="schedule-time">{entry.get('time', '')}</td>
                                        </tr>
"""
                    html += """                                    </tbody>
                                </table>
                            </div>
"""
                elif activity_schedule.get('program') or activity_schedule.get('raw'):
                    # Try parsing program/raw text into a structured table
                    schedule_text = activity_schedule.get('program') or activity_schedule.get('raw')
                    parsed_entries = parse_schedule_program(schedule_text, details.get('title'))
                    if parsed_entries:
                        html += """                            <div class="schedule-info">
                                <h6>📅 Full Schedule</h6>
                                <table class="schedule-table">
                                    <thead>
                                        <tr>
                                            <th>Days</th>
                                            <th>Location</th>
                                            <th>Time</th>
                                        </tr>
                                    </thead>
                                    <tbody>
"""
                        for entry in parsed_entries:
                            html += f"""                                        <tr>
                                            <td class="schedule-days">{entry.get('days', '')}</td>
                                            <td>{entry.get('location', '')}</td>
                                            <td class="schedule-time">{entry.get('time', '')}</td>
                                        </tr>
"""
                        html += """                                    </tbody>
                                </table>
                            </div>
"""
                    else:
                        html += f"""                            <div class="schedule-info">
                                <h6>📅 Schedule</h6>
                                <pre style="margin: 0; white-space: pre-wrap;">{schedule_text}</pre>
                            </div>
"""
                
                html += """                        </div>
                    </div>
"""
            
            html += """                </div>
"""
    
    html += """            </div>
"""

html += """        <div class="tab-pane fade" id="unscheduled" role="tabpanel">
            <h2 class="day-theme">Unscheduled Activities</h2>
"""

if not unmatched_activities:
    html += """            <div class="alert alert-info">All activities are represented in the weekly schedule.</div>
"""
else:
    for idx, activity_name in enumerate(unmatched_activities):
        details = activity_details_map.get(activity_name)
        tier = details.get('metadata', {}).get('tier', '') if details else ''
        border_color = TIER_COLORS.get(tier, '#cccccc')
        collapse_id = f"collapse-unscheduled-{idx}"
        has_details = details is not None
        toggle_attrs = f'data-bs-toggle="collapse" data-bs-target="#{collapse_id}" aria-expanded="false" aria-controls="{collapse_id}"' if has_details else ''
        cursor_style = 'cursor: pointer;' if has_details else ''
        header_classes = 'activity-header collapsed' if has_details else 'activity-header'

        html += f"""            <div class="activity-card" style="border-left: 4px solid {border_color};">
                <div class="{header_classes}" {toggle_attrs} style="{cursor_style}">
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="d-flex align-items-center flex-grow-1">
                            <span class="activity-name">{activity_name}</span>
                            <span class="activity-location">(Not in weekly schedule)</span>
                        </div>
                        <div class="d-flex align-items-center gap-3">
"""

        if has_details:
            html += """                            <svg class="expand-icon" width="16" height="16" fill="currentColor" viewBox="0 0 16 16">
                                <path fill-rule="evenodd" d="M1.646 4.646a.5.5 0 0 1 .708 0L8 10.293l5.646-5.647a.5.5 0 0 1 .708.708l-6 6a.5.5 0 0 1-.708 0l-6-6a.5.5 0 0 1 0-.708z"/>
                            </svg>
"""

        html += """                        </div>
                    </div>
                </div>
"""

        if details:
            activity_url = details.get('url', '')
            html += f"""                <div class="collapse" id="{collapse_id}">
                    <div class="activity-details">
                        <div style="color: #718096; font-size: 0.85rem; font-style: italic; margin-bottom: 0.8rem; padding-bottom: 0.8rem; border-bottom: 1px solid #e2e8f0;">
                            Activity details
                            {f' • <a href="{activity_url}" target="_blank" rel="noopener noreferrer" style="color: #6141f3; text-decoration: none;">View original page ↗</a>' if activity_url else ''}
                        </div>
"""

            images = details.get('images', []) or details.get('hero_image', None)
            if images:
                if isinstance(images, str):
                    images = [images]
                html += """                        <div class="activity-images" style="margin-bottom: 1.5rem;">
"""
                for img_url in images:
                    html += f"""                            <img src="{img_url}" alt="{details['title']}" class="activity-image" loading="lazy" decoding="async">
"""
                html += """                        </div>
"""

            if details.get('description'):
                description_html = details['description'].replace('\n', '<br>')
                html += f"""                        <div class="activity-description">
                            {description_html}
                        </div>
"""

            for section in details.get('sections', []):
                html += """                        <div class="activity-section">
"""
                if section.get('heading'):
                    html += f"""                            <h5>{section['heading']}</h5>
"""
                for content in section.get('content', []):
                    content_html = content.replace('\n', '<br>')
                    html += f"""                            <p>{content_html}</p>
"""
                if section.get('images'):
                    html += """                            <div class="activity-images">
"""
                    for img_url in section['images']:
                        html += f"""                                <img src="{img_url}" alt="Activity image" class="activity-image" loading="lazy" decoding="async">
"""
                    html += """                            </div>
"""
                html += """                        </div>
"""

            activity_schedule = details.get('schedule', {})
            if activity_schedule.get('entries'):
                html += """                        <div class="schedule-info">
                            <h6>📅 Full Schedule</h6>
                            <table class="schedule-table">
                                <thead>
                                    <tr>
                                        <th>Days</th>
                                        <th>Location</th>
                                        <th>Time</th>
                                    </tr>
                                </thead>
                                <tbody>
"""
                for entry in activity_schedule['entries']:
                    html += f"""                                    <tr>
                                        <td class="schedule-days">{entry.get('days', '')}</td>
                                        <td>{entry.get('location', '')}</td>
                                        <td class="schedule-time">{entry.get('time', '')}</td>
                                    </tr>
"""
                html += """                                </tbody>
                            </table>
                        </div>
"""
            elif activity_schedule.get('program') or activity_schedule.get('raw'):
                schedule_text = activity_schedule.get('program') or activity_schedule.get('raw')
                parsed_entries = parse_schedule_program(schedule_text, details.get('title'))
                if parsed_entries:
                    html += """                        <div class="schedule-info">
                            <h6>📅 Full Schedule</h6>
                            <table class="schedule-table">
                                <thead>
                                    <tr>
                                        <th>Days</th>
                                        <th>Location</th>
                                        <th>Time</th>
                                    </tr>
                                </thead>
                                <tbody>
"""
                    for entry in parsed_entries:
                        html += f"""                                    <tr>
                                        <td class="schedule-days">{entry.get('days', '')}</td>
                                        <td>{entry.get('location', '')}</td>
                                        <td class="schedule-time">{entry.get('time', '')}</td>
                                    </tr>
"""
                    html += """                                </tbody>
                            </table>
                        </div>
"""
                else:
                    html += f"""                        <div class="schedule-info">
                            <h6>📅 Schedule</h6>
                            <pre style="margin: 0; white-space: pre-wrap;">{schedule_text}</pre>
                        </div>
"""

            html += """                    </div>
                </div>
"""

        html += """            </div>
"""

html += """        </div>
    </div>

    <footer class="text-center py-4 text-muted">
        <div class="container">
            <p class="mb-0">Generated from <a href="https://therme.ro/activities-schedule" target="_blank">Therme Activities Schedule</a></p>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>
"""

# Save HTML file
with open(args.output, 'w', encoding='utf-8') as f:
    f.write(html)

# Calculate matching statistics
total_activities = sum(len(schedule[day]['activities']) for day in days if day in schedule)
matched_count = 0
for day in days:
    if day in schedule:
        for activity in schedule[day]['activities']:
            details, score = find_best_match(activity['name'])
            if details:
                matched_count += 1

print(f"Enhanced HTML page generated: {args.output}")
print(f"\n  Total schedule items: {total_activities}")
print(f"  Matched with details: {matched_count}")
if total_activities > 0:
    print(f"  Match rate: {matched_count/total_activities*100:.1f}%")
else:
    print("  Match rate: N/A (no activities found)")
print(f"\nYou can open {args.output} in your browser to view the interactive schedule.")
