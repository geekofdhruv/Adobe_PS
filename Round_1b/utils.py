import json

def save_json(data, filepath):
    """
    Saves a dictionary to a JSON file with pretty printing.
    
    Args:
        data (dict): The dictionary to save.
        filepath (str): The path to the output JSON file.
    """
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"🔥 Error saving JSON to {filepath}: {e}")