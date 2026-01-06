import requests
import json
import csv
import io
import datetime
import os
import re

# Constants
CSV_URL = "https://gorilla.cs.berkeley.edu/data_overall.csv"
JSON_FILE_PATH = "bfcl-leaderboard.json"
TOP_N = 20  # Store top 20 models to keep the file size manageable and relevant

def fetch_csv_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"Error fetching CSV data: {e}")
        return None

def parse_model_string(model_str):
    """
    Parses strings like "Claude-Sonnet-4-5-20250929 (FC)"
    Returns (model_name, model_type)
    """
    match = re.match(r"(.*)\s+\((.*)\)$", model_str)
    if match:
        return match.group(1).strip(), match.group(2).strip()
    return model_str.strip(), "Unknown"

def process_data(csv_text):
    leaderboard = []
    
    # Parse CSV
    reader = csv.DictReader(io.StringIO(csv_text))
    
    for row in reader:
        try:
            # Extract and transform fields
            rank = int(row.get('Rank', 0))
            raw_model = row.get('Model', '')
            provider = row.get('Organization', 'Unknown')
            accuracy_str = row.get('Overall Acc', '0').replace('%', '')
            accuracy = float(accuracy_str)
            
            model_name, model_type = parse_model_string(raw_model)
            
            # Map specific types if needed or just use what's in parens
            # The CSV seems to have 'FC', 'Prompt', 'FC thinking', etc.
            # We'll normalize 'FC thinking' to 'FC' if desired, or keep as is.
            # For now, let's clean it up slightly if it contains 'FC'.
            if 'FC' in model_type:
                clean_type = 'FC'
            elif 'Prompt' in model_type:
                clean_type = 'Prompt'
            else:
                clean_type = model_type

            entry = {
                "rank": rank,
                "model": model_name,
                "provider": provider,
                "accuracy": accuracy,
                "type": clean_type
            }
            leaderboard.append(entry)
            
        except ValueError as e:
            print(f"Skipping row due to error: {e}, Row: {row}")
            continue

    # Sort by rank just in case, though CSV is usually sorted
    leaderboard.sort(key=lambda x: x['rank'])
    
    return leaderboard[:TOP_N]

def update_json_file(leaderboard_data):
    # Read existing file to preserve meta or creating new if not exists
    if os.path.exists(JSON_FILE_PATH):
        with open(JSON_FILE_PATH, 'r') as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {"meta": {}}
    else:
        data = {"meta": {}}

    # Update Meta
    data["meta"]["source"] = "Berkeley Function-Calling Leaderboard (BFCL) V4"
    data["meta"]["url"] = "https://gorilla.cs.berkeley.edu/leaderboard.html"
    data["meta"]["last_updated"] = datetime.date.today().strftime("%Y-%m-%d")
    if "description" not in data["meta"]:
        data["meta"]["description"] = "Evaluates LLM ability to call functions/tools accurately"

    # Update Leaderboard
    data["leaderboard"] = leaderboard_data

    # Write back
    with open(JSON_FILE_PATH, 'w') as f:
        json.dump(data, f, indent=4)
        print(f"Successfully updated {JSON_FILE_PATH} with {len(leaderboard_data)} entries.")

def main():
    print("Fetching data from BFCL...")
    csv_text = fetch_csv_data(CSV_URL)
    if not csv_text:
        print("Failed to fetch data.")
        exit(1)

    print("Processing data...")
    leaderboard_data = process_data(csv_text)
    
    print("Updating JSON file...")
    update_json_file(leaderboard_data)
    print("Done.")

if __name__ == "__main__":
    main()
