import json
import os

# Define file paths
CONFIG_PATH = 'config.json'
DB_PATH = 'data/mafa_listings.db'
DATA_DIR = 'data'

def load_config():
    """Loads the application configuration from config.json."""
    if not os.path.exists(CONFIG_PATH):
        print(f"Error: Configuration file '{CONFIG_PATH}' not found.")
        print("Please copy 'config.example.json' to 'config.json' and fill in your details.")
        return None
    
    try:
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error: Failed to parse '{CONFIG_PATH}'. Check for JSON syntax errors.")
        return None

def initialize_directories():
    """Ensures necessary directories exist."""
    os.makedirs(DATA_DIR, exist_ok=True)
    print(f"Directory '{DATA_DIR}' checked/created.")

def main():
    """Main function to start the MAFA assistant."""
    initialize_directories()
    config = load_config()
    
    if not config:
        return

    # Display basic configuration for confirmation
    print("---------------------------------------------------------")
    print("       Munich Apartment Finder Assistant (MAFA)          ")
    print("---------------------------------------------------------")
    print(f"Config loaded successfully for user: {config['personal_profile']['my_full_name']}")
    print(f"Targeting {len(config['search_criteria']['zip_codes'])} ZIP codes...")
    print(f"Max Price: €{config['search_criteria']['max_price']}")
    print(f"Notification via: {config['notification']['provider'].upper()}")
    print("---------------------------------------------------------")
    print("System is initialized. Crawlers will start monitoring soon.")
    print("\nNOTE: Core crawler and notification logic is implemented in subsequent files (src/).")


if __name__ == "__main__":
    main()