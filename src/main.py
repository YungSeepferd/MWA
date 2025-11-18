import json
import os
from datetime import datetime

# Constants
CONFIG_PATH = "config.json"
DB_PATH = "./data/listings.db"
DATA_DIR = "./data"

def load_config(config_path):
    """Loads the application configuration from config.json."""
    if not os.path.exists(config_path):
        print(f"Error: Configuration file '{config_path}' not found.")
        print("Please copy "config.example.json" to '{config_path}' and fill in your details.")
        return None

    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Failed to parse '{config_path}'. Check for JSON syntax errors.")
        return None

def initialize_directories():
    """Ensures necessary directories exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Directory '{DATA_DIR}' checked/created.")

def display_config_summary(config):
    """Displays basic configuration for confirmation."""
    print("---------------------------------------------------------")
    print("       Munich Apartment Finder Assistant (MAFA)          ")
    print("---------------------------------------------------------")
    print(f"Config loaded successfully for user: {config["personal_profile"]["my_full_name"]}")
    print(f"Targeting {len(config["search_criteria"]["zip_codes"])} ZIP codes...")
    print(f"Max Price: €{config["search_criteria"]["max_price"]}")
    print(f"Notification via: {config["notification"]["provider"].upper()}")
    print("---------------------------------------------------------")
    print("System is initialized. Crawlers will start monitoring soon.")
    print("\nNOTE: Core crawler and notification logic is implemented in subsequent files (src/).")

def main(config_path=CONFIG_PATH):
    """Main function to start the MAFA assistant."""
    initialize_directories()
    config = load_config(config_path)

    if not config:
        return

    display_config_summary(config)
    # TODO: Start monitoring and crawlers

if __name__ == "__main__":
    import sys
    args = sys.argv[1:]
    config_path = CONFIG_PATH

    if "--config" in args:
        idx = args.index("--config")
        if len(args) > idx + 1:
            config_path = args[idx + 1]

    main(config_path)' > src/main.py