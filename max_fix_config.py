import json
import os

config_path = 'config/systems_config.json'

try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json.load(f)

    # Update Bonita config
    config['bonita'] = {
        "enabled": False,
        "type": "bonita",
        "name": "Bonita BPM",
        "base_url": "https://dockertst.ajover.com:8445/bonita",
        "credentials": {
            "username": "",
            "password": ""
        },
        "collection_interval": 300,
        "headless": True,
        "retry_attempts": 3,
        "filters": {
            "filter_failures": True
        }
    }

    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("Configuration updated successfully.")

except Exception as e:
    print(f"Error updating config: {e}")
