This is a fantastic approach. I've compiled the entire C2B Apartment Finder Assistant (MAFA) concept, architecture, user flow, and configuration into a single, detailed LLM prompt.

You can use this prompt with a coding assistant to initialize your empty repository and start building the application.

I'll start by generating the initial, non-functional files (`README.md` and `config.example.json`) based on this prompt to establish the repository structure right away.

-----

### **LLM Prompt for Coding Assistant**

```
**Project Initialization: C2B Apartment Finder Assistant (MAFA)**

**Goal:** Build a Python-based personal apartment search assistant for the Munich market. The system must find new listings from major portals AND management company websites, filter them according to user criteria, and facilitate high-speed, high-quality C2B (Consumer-to-Business) email applications.

**Initial Repository Setup (Phase 0):**

1.  **Generate `README.md`:** Provide a brief overview, setup instructions (mentioning Python environment, dependencies later), and link to the `config.json` file.
2.  **Generate `config.example.json`:** This is the most critical file. It must contain the detailed, structured configuration for the user's search criteria and personal profile for the C2B application.
3.  **Generate `run.py`:** A minimal placeholder script that imports the config and confirms the system is starting.

**Required Directory Structure and Modules (Phase 1 - Subsequent Tasks):**

* `/src/`: Main source code directory.
    * `/src/db/db_manager.py`: Handles all SQLite interactions for storing "seen" listings and deduplication.
    * `/src/crawlers/portal_crawler.py`: Logic for scraping major portals (e.g., ImmoScout24 - note: actual scraping logic is complex and will be added later).
    * `/src/crawlers/deep_crawler.py`: Logic for targeting individual Hausverwaltung websites.
    * `/src/notifiers/telegram_notifier.py`: Module for sending alerts based on the user's `config.json` settings.
    * `/src/dashboard/dashboard.py`: A simple script (e.g., using Streamlit) to display new listings and generate the C2B email draft upon request.

**Core Functionality Requirements:**

* **Deduplication:** The system must use the SQLite database to store and check listing URLs/addresses to prevent sending duplicate alerts.
* **Alerting:** New listings that match the `search_criteria` must trigger an instant alert via the configured notification method.
* **C2B Email Generation:** The system must use the data from the `personal_profile` section in `config.json` and combine it with the specific listing details to create a professional, structured application email template (in German, as provided in the previous draft). The dashboard should allow the user to copy this pre-filled text.

**Mandatory `config.example.json` Fields (Self-Contained):**

The file structure must include the following keys and example values:

| Key | Example Value | Description |
| :--- | :--- | :--- |
| `search_criteria.max_price` | 2000 | Maximum monthly rent (€). |
| `search_criteria.min_rooms` | 2 | Minimum number of rooms. |
| `search_criteria.zip_codes` | `["80801", "80802", "80331"]` | Array of desired Munich ZIP codes. |
| `notification.provider` | `"telegram"` | Only "telegram" supported initially. |
| `notification.telegram_chat_id` | `"YOUR_CHAT_ID"` | Unique chat ID for alerts. |
| `personal_profile.my_full_name` | `"Max Mustermann"` | Full name for the email. |
| `personal_profile.my_profession` | `"Software Engineer"` | Occupation. |
| `personal_profile.my_employer` | `"Google Germany GmbH"` | Employer for income proof. |
| `personal_profile.net_household_income_monthly` | 4500 | Numeric value for income. |
| `personal_profile.total_occupants` | 2 | Number of people moving in. |
| `personal_profile.intro_paragraph` | `"Wir sind ein ruhiges, zuverlässiges und nicht-rauchendes Paar..."` | Short, personal pitch (in German). |
```

-----

I'll now set up the initial repository structure with the `README.md` and the essential configuration file.

http://googleusercontent.com/immersive_entry_chip/0

http://googleusercontent.com/immersive_entry_chip/1

http://googleusercontent.com/immersive_entry_chip/2

These initial files set up your repository's foundation, including the vital `config.example.json` where you'll define your personalized C2B application details. You now have the full prompt and the starting files to begin development\!

What part of the architecture would you like to build next—the **database manager** (`src/db/db_manager.py`) or the **Telegram notifier** (`src/notifiers/telegram_notifier.py`)?