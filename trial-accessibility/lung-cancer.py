import requests
import time
import re
import json

def get_trials(start_date, end_date):
    base_url = "https://clinicaltrials.gov/api/v2/studies"
    params = {
        "query.cond": "Lung Cancer",
        "query.term": f"AREA[StudyType]INTERVENTIONAL AND AREA[StudyFirstPostDate]RANGE[{start_date},{end_date}]",
        "pageSize": 100,
        "format": "json"
    }

    trials = []
    next_page_token = None
    
    while True:
        if next_page_token:
            params["pageToken"] = next_page_token
            
        response = requests.get(base_url, params=params)
        
        if response.status_code != 200:
            print(f"Error: HTTP {response.status_code}")
            print(f"Response text: {response.text[:500]}")
            break
            
        try:
            data = response.json()
        except json.JSONDecodeError:
            print(f"Failed to parse JSON. Response text: {response.text[:500]}")
            break
        
        if "studies" in data:
            trials.extend(data["studies"])
            print(f"Retrieved {len(data['studies'])} trials (total: {len(trials)})")
            
        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break
        time.sleep(1)
        
    return trials

def calculate_barrier_score(eligibility_text):
    if not eligibility_text:
        return None, 0, 0
    
    # Normalize text
    text = eligibility_text.replace('\r', '\n')
    
    # Split into Inclusion and Exclusion
    split_pattern = re.compile(r'\n\s*Exclusion Criteria:?', re.IGNORECASE)
    parts = split_pattern.split(text)
    
    if len(parts) != 2:
        return None, 0, 0
        
    inclusion_text = parts[0].replace("Inclusion Criteria:", "").strip()
    exclusion_text = parts[1].strip()
    
    # Simple whitespace tokenization
    inc_count = len(inclusion_text.split())
    exc_count = len(exclusion_text.split())
    
    if inc_count == 0:
        return None, 0, exc_count
        
    score = exc_count / inc_count
    return score, inc_count, exc_count

def find_facility_info(nct_id):
    """Search for facility information for a given NCT ID"""
    search_url = f"https://clinicaltrials.gov/api/v2/studies/{nct_id}"
    
    try:
        response = requests.get(search_url)
        data = response.json()
        
        protocol = data.get('protocolSection', {})
        contacts = protocol.get('contactsLocationsModule', {})
        locations = contacts.get('locations', [])
        
        if locations:
            primary_location = locations[0]
            return {
                "facility_name": primary_location.get('facility', 'Unknown'),
                "city": primary_location.get('city', 'Unknown'),
                "state_province": primary_location.get('state', primary_location.get('country', 'Unknown')),
                "country": primary_location.get('country', 'Unknown')
            }
    except:
        pass
    
    return {
        "facility_name": "Unknown",
        "city": "Unknown",
        "state_province": "Unknown",
        "country": "Unknown"
    }

# Execution Parameters
start_date = "2025-12-01"
end_date = "2025-12-31"

print("Fetching trials...")
trials = get_trials(start_date, end_date)
print(f"\nTotal trials found: {len(trials)}\n")

# Process each trial
trial_scores = []
for trial in trials:
    protocol = trial.get('protocolSection', {})
    nct_id = protocol.get('identificationModule', {}).get('nctId', 'Unknown')
    title = protocol.get('identificationModule', {}).get('briefTitle', 'Unknown')
    
    eligibility_module = protocol.get('eligibilityModule', {})
    eligibility_text = eligibility_module.get('eligibilityCriteria', '')
    
    score, inc_count, exc_count = calculate_barrier_score(eligibility_text)
    
    if score is not None:
        trial_scores.append({
            'nct_id': nct_id,
            'title': title,
            'score': score,
            'inc_count': inc_count,
            'exc_count': exc_count
        })

print(f"Successfully calculated barrier scores for {len(trial_scores)} trials\n")

# Calculate average
if trial_scores:
    avg_score = sum(t['score'] for t in trial_scores) / len(trial_scores)
    
    # Determine status
    baseline = 1.15
    if avg_score > baseline:
        status = "High Selectivity"
    elif avg_score < baseline:
        status = "Broad Access"
    else:
        status = "Neutral"
    
    # Find highest barrier trial
    highest_trial = max(trial_scores, key=lambda x: x['score'])
    
    print(f"Average Barrier Score: {avg_score:.2f}")
    print(f"Status: {status}")
    print(f"Highest Barrier Trial: {highest_trial['nct_id']} (Score: {highest_trial['score']:.2f})")
    
    # Get facility info for highest barrier trial
    print(f"\nSearching for facility information for {highest_trial['nct_id']}...")
    facility_info = find_facility_info(highest_trial['nct_id'])
    
    # Generate JSON output
    output = {
        "report_metadata": {
            "report_type": "Patient Accessibility Analysis",
            "condition": "Lung Cancer",
            "trial_type": "Interventional",
            "reporting_period": {
                "start_date": start_date,
                "end_date": end_date
            }
        },
        "analysis_metrics": {
            "total_trials_analyzed": len(trial_scores),
            "average_barrier_score": round(avg_score, 2),
            "baseline_comparison": {
                "baseline": baseline,
                "status": status,
                "delta": f"{avg_score - baseline:+.2f}"
            }
        },
        "highest_barrier_trial": {
            "nct_id": highest_trial['nct_id'],
            "barrier_score": round(highest_trial['score'], 2),
            "title": highest_trial['title'],
            "facility_location": facility_info
        }
    }
    
    # Print JSON
    print("\n" + "="*80)
    print("FINAL JSON REPORT:")
    print("="*80)
    print(json.dumps(output, indent=2))
    
    # Save to file
    with open('lung_cancer_accessibility_report.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print("\nReport saved to: lung_cancer_accessibility_report.json")
else:
    print("No trials with valid eligibility criteria found.")