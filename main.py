import requests
import json
import argparse
import yaml
import os
from pathlib import Path
import time  # Added for rate limiting

url = "http://localhost:5000/translate"
payload = {
    "q": "hello, how are you?",
    "source": "auto",
    "target": "uk",
    "format": "text",
    "alternatives": 3,
    "api_key": ""
}

headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, headers=headers, data=json.dumps(payload))

# Print the JSON response
print(response.json())

def load_yaml(file_path):
    """Load and return YAML file content."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return yaml.safe_load(file)

def save_yaml(file_path, data):
    """Save data to YAML file."""
    with open(file_path, 'w', encoding='utf-8') as file:
        yaml.dump(data, file, allow_unicode=True, sort_keys=False)

def translate_text(text, target_lang):
    """Translate text using the translation API."""
    url = "http://localhost:5000/translate"
    payload = {
        "q": text,
        "source": "en",
        "target": target_lang,
        "format": "text",
        "alternatives": 3,
        "api_key": ""
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()  # Raise an exception for bad status codes
        result = response.json()
        translated_text = result.get('translatedText')
        
        if not translated_text:
            print(f"Warning: No translation received for text: '{text}'")
            return text
            
        print(f"Translated '{text}' → '{translated_text}'")  # Debug output
        return translated_text
        
    except Exception as e:
        print(f"Translation error for text '{text}': {str(e)}")
        return text
    finally:
        time.sleep(0.5)  # Add a small delay to prevent overwhelming the API

def get_missing_keys(source_dict, target_dict, parent_key=""):
    """Recursively find missing keys between two dictionaries."""
    missing_keys = {}
    
    for key, value in source_dict.items():
        current_key = f"{parent_key}.{key}" if parent_key else key
        
        if key not in target_dict:
            missing_keys[key] = value
        elif isinstance(value, dict) and isinstance(target_dict[key], dict):
            nested_missing = get_missing_keys(value, target_dict[key], current_key)
            if nested_missing:
                missing_keys[key] = nested_missing
                
    return missing_keys

def update_dict_with_translations(missing_dict, target_lang):
    """Recursively translate missing values in a dictionary."""
    translated_dict = {}
    
    for key, value in missing_dict.items():
        if isinstance(value, dict):
            translated_dict[key] = update_dict_with_translations(value, target_lang)
        else:
            # Convert language code format if needed (e.g., 'ar.yaml' to 'ar')
            lang_code = target_lang.split('.')[0]  # Remove .yaml extension if present
            translated_value = translate_text(str(value), lang_code)
            translated_dict[key] = translated_value
            
    return translated_dict

def merge_dicts(original, updates):
    """Recursively merge two dictionaries."""
    for key, value in updates.items():
        if key in original and isinstance(original[key], dict) and isinstance(value, dict):
            merge_dicts(original[key], value)
        else:
            original[key] = value

def main():
    parser = argparse.ArgumentParser(description='Sync translations with en-US.yaml and translate missing keys')
    parser.add_argument('folder_path', help='Path to the folder containing YAML translation files')
    parser.add_argument('--debug', action='store_true', help='Enable debug output')
    
    args = parser.parse_args()
    folder_path = Path(args.folder_path)
    
    # Load the reference English file
    en_us_path = folder_path / 'en-US.yaml'
    if not en_us_path.exists():
        print("Error: en-US.yaml not found in the specified directory")
        return
        
    en_us_data = load_yaml(en_us_path)
    
    # Process each YAML file in the directory
    for file_path in folder_path.glob('*.yaml'):
        if file_path.name == 'en-US.yaml':
            continue
            
        # Extract language code from filename (remove .yaml extension)
        lang_code = file_path.stem
        print(f"\nProcessing {lang_code}...")
        
        # Load the target language file
        target_data = load_yaml(file_path)
        
        # Find missing keys
        missing_keys = get_missing_keys(en_us_data, target_data)
        
        if missing_keys:
            print(f"Found missing keys in {lang_code}:")
            if args.debug:
                print(json.dumps(missing_keys, indent=2))
            
            # Translate missing keys
            translated_keys = update_dict_with_translations(missing_keys, lang_code)
            
            if args.debug:
                print("\nTranslated keys:")
                print(json.dumps(translated_keys, indent=2))
            
            # Merge translations into original file
            merge_dicts(target_data, translated_keys)
            
            # Save updated file
            save_yaml(file_path, target_data)
            print(f"Updated {lang_code} with translated missing keys")
        else:
            print(f"No missing keys found in {lang_code}")

if __name__ == "__main__":
    main()
