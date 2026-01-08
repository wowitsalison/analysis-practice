import matplotlib.pyplot as plt
import numpy as np
import requests
from datetime import datetime, timezone
from collections import defaultdict

# Most recent full moons - input latest dates
last_full_moon = '2026-01-03T23:59:59'
penult_full_moon = '2025-12-05T00:00:00'

# Set up USGS API
url = f'https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={penult_full_moon}&endtime={last_full_moon}&minmagnitude=4.5&orderby=time'

# Fetch earthquake data
response = requests.get(url)
data = response.json()

# Extract relevant information
earthquakes = data['features']
depths_by_date = defaultdict(list)
for eq in earthquakes:
    utc_time = datetime.fromtimestamp(eq['properties']['time'] / 1000, tz=timezone.utc)
    date = utc_time.date()
    place = eq['properties']['place']
    depth = eq['geometry']['coordinates'][2]
    depths_by_date[date].append(depth)

# Find the deepest earthquake per day
deepest_eqs_per_day = []
for date, depths in sorted(depths_by_date.items()):
    max_depth = max(depths)
    # Find the earthquake with this depth on this date
    for eq in earthquakes:
        utc_time = datetime.fromtimestamp(eq['properties']['time'] / 1000, tz=timezone.utc)
        if utc_time.date() == date and eq['geometry']['coordinates'][2] == max_depth:
            deepest_eqs_per_day.append(eq)
            break

# Mapping keywords in place to mountain heights (meters)
mountain_heights = {
    'Papua New Guinea': 4509,
    'Indonesia': 4884,
    'Fiji': 1324,
    'Timor Leste': 2963,
    'Kermadec': 516,
    'Colombia': 5775,
    'Japan': 3776,
    'Tonga': 1030,
    'Chile': 6893,
    'Argentina': 6967,
    'Vanuatu': 1879
}

def get_height(place):
    for key in mountain_heights:
        if key.lower() in place.lower():
            return mountain_heights[key]
    return None 

# Prepare data for the bar chart
dates = []
ratios = []

for eq in deepest_eqs_per_day:
    utc_time = datetime.fromtimestamp(eq['properties']['time'] / 1000, tz=timezone.utc)
    date = str(utc_time.date())
    depth = eq['geometry']['coordinates'][2]*1000  # Convert to meters
    place = eq['properties']['place']
    height = get_height(place)
    if height:
        ratio = height / depth
        dates.append(date)
        ratios.append(ratio)

# Create horizontal bar chart
plt.figure(figsize=(10, 8))
plt.barh(dates, ratios, color='skyblue')
plt.xlabel('Height/Depth Ratio')
plt.ylabel('Date')
plt.title('Mountain Height to Earthquake Depth Ratio by Day')
plt.tight_layout()
plt.show()