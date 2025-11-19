#!/bin/bash
# MAFA Scraper Dry-Run Script
# Runs the scraper in dry-run mode for testing without sending notifications

set -e

# Configuration
PROVIDER=${1:-"all"}
CONFIG_FILE=${CONFIG_FILE:-"config.json"}
DRY_RUN_MODE=${DRY_RUN_MODE:-"true"}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_section() {
    echo -e "\n${PURPLE}=== $1 ===${NC}"
}

# Function to validate provider
validate_provider() {
    local provider="$1"
    local valid_providers=("immoscout" "wg_gesucht" "all")
    
    if [[ ! " ${valid_providers[@]} " =~ " ${provider} " ]]; then
        print_error "Invalid provider: $provider"
        print_info "Valid providers: ${valid_providers[*]}"
        exit 1
    fi
}

# Function to check dependencies
check_dependencies() {
    print_info "Checking dependencies..."
    
    if ! command -v poetry &> /dev/null; then
        print_error "Poetry is not installed"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        print_warning "Virtual environment not found. Installing dependencies..."
        poetry install
    fi
    
    print_success "Dependencies check completed"
}

# Function to validate configuration
validate_config() {
    print_info "Validating configuration..."
    
    if [ ! -f "$CONFIG_FILE" ]; then
        print_error "Configuration file not found: $CONFIG_FILE"
        print_info "Please copy config.example.json to $CONFIG_FILE and configure it"
        exit 1
    fi
    
    # Basic JSON validation
    if ! python3 -c "
import json
try:
    with open('$CONFIG_FILE', 'r') as f:
        config = json.load(f)
    print('Configuration JSON is valid')
except json.JSONDecodeError as e:
    print(f'Invalid JSON: {e}')
    exit(1)
except Exception as e:
    print(f'Error reading config: {e}')
    exit(1)
" 2>/dev/null; then
        print_error "Configuration validation failed"
        exit 1
    fi
    
    print_success "Configuration validation passed"
}

# Function to create dry-run config
create_dryrun_config() {
    print_info "Creating dry-run configuration..."
    
    # Create a temporary config file for dry-run
    local dryrun_config="config.dryrun.json"
    
    python3 -c "
import json
import sys

# Load original config
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)

# Modify for dry-run
config['notification']['provider'] = 'dryrun'
config['notification']['dryrun_mode'] = True
config['scrapers'] = ['$PROVIDER'] if '$PROVIDER' != 'all' else config.get('scrapers', ['immoscout', 'wg_gesucht'])

# Add dry-run specific settings
config['dry_run'] = {
    'enabled': True,
    'skip_notifications': True,
    'skip_database_persistence': False,
    'max_listings': 5,
    'log_level': 'DEBUG'
}

# Save dry-run config
with open('$dryrun_config', 'w') as f:
    json.dump(config, f, indent=2)

print(f'Dry-run configuration created: {dryrun_config}')
"
    
    echo "$dryrun_config"
}

# Function to run scraper dry-run
run_scraper_dryrun() {
    print_section "Running Scraper in Dry-Run Mode"
    
    local dryrun_config
    dryrun_config=$(create_dryrun_config)
    
    print_info "Provider: $PROVIDER"
    print_info "Configuration: $dryrun_config"
    print_info "Dry-run mode: Enabled"
    echo ""
    
    # Set environment variables for dry-run
    export MAFA_DRY_RUN=true
    export MAFA_SKIP_NOTIFICATIONS=true
    export MAFA_LOG_LEVEL=DEBUG
    
    print_info "Starting scraper in dry-run mode..."
    print_warning "This will not send real notifications or persist data permanently"
    echo ""
    
    # Run the scraper with dry-run config
    if poetry run python run.py --config "$dryrun_config" --dry-run; then
        print_success "Dry-run completed successfully"
        
        # Show results summary
        show_dryrun_results "$dryrun_config"
    else
        print_error "Dry-run failed"
        return 1
    fi
    
    # Clean up temporary config
    rm -f "$dryrun_config"
}

# Function to show dry-run results
show_dryrun_results() {
    local dryrun_config="$1"
    
    print_section "Dry-Run Results"
    
    # Check for generated reports
    local report_files=(data/report_*.csv)
    if [ -f "${report_files[0]}" ]; then
        print_info "Generated reports:"
        for report in "${report_files[@]}"; do
            if [ -f "$report" ]; then
                local line_count=$(wc -l < "$report")
                print_info "  - $report ($line_count lines)"
                
                # Show first few lines
                if [ "$line_count" -gt 1 ]; then
                    print_info "    Sample data:"
                    head -3 "$report" | sed 's/^/      /'
                fi
            fi
        done
    else
        print_info "No reports generated"
    fi
    
    # Check for log files
    local log_files=(logs/mafa_*.log)
    if [ -f "${log_files[0]}" ]; then
        print_info "Log files created:"
        for log in "${log_files[@]}"; do
            if [ -f "$log" ]; then
                local size=$(du -h "$log" | cut -f1)
                print_info "  - $log ($size)"
            fi
        done
    fi
    
    # Show configuration summary
    print_info "Configuration used:"
    python3 -c "
import json
with open('$dryrun_config', 'r') as f:
    config = json.load(f)
print(f'  Providers: {config.get(\"scrapers\", [])}')
print(f'  Dry-run: {config.get(\"dry_run\", {}).get(\"enabled\", False)}')
print(f'  Skip notifications: {config.get(\"dry_run\", {}).get(\"skip_notifications\", False)}')
print(f'  Max listings: {config.get(\"dry_run\", {}).get(\"max_listings\", \"unlimited\")}')
"
}

# Function to run specific provider test
run_provider_test() {
    local provider="$1"
    
    print_section "Testing Provider: $provider"
    
    # Create a minimal test script for the provider
    local test_script="test_${provider}_dryrun.py"
    
    cat > "$test_script" << EOF
#!/usr/bin/env python3
"""Dry-run test for $provider provider"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from mafa.providers.$provider import ${provider^}Provider
from mafa.config.settings import Settings
import json

def main():
    print(f"Testing {provider^} provider...")
    
    try:
        # Load settings
        settings = Settings.load()
        
        # Create provider instance
        provider = ${provider^}Provider(settings)
        
        # Test scraping (limited scope for dry-run)
        print(f"Scraping {provider^}...")
        listings = provider.scrape()
        
        print(f"Found {len(listings)} listings")
        
        # Show sample listings
        for i, listing in enumerate(listings[:3]):
            print(f"  Listing {i+1}:")
            print(f"    Title: {listing.get('title', 'N/A')}")
            print(f"    Price: {listing.get('price', 'N/A')}")
            print(f"    Source: {listing.get('source', 'N/A')}")
        
        print(f"{provider^} provider test completed successfully")
        
    except Exception as e:
        print(f"Error testing {provider} provider: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
EOF
    
    # Run the test
    if poetry run python "$test_script"; then
        print_success "$provider provider test passed"
    else
        print_error "$provider provider test failed"
        return 1
    fi
    
    # Clean up test script
    rm -f "$test_script"
}

# Function to show help
show_help() {
    echo "MAFA Scraper Dry-Run Script"
    echo ""
    echo "Usage: $0 [PROVIDER]"
    echo ""
    echo "Arguments:"
    echo "  PROVIDER    Provider to test (immoscout, wg_gesucht, all)"
    echo "              Default: all"
    echo ""
    echo "Environment Variables:"
    echo "  CONFIG_FILE    Configuration file to use (default: config.json)"
    echo "  DRY_RUN_MODE   Enable/disable dry-run mode (default: true)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Test all providers"
    echo "  $0 immoscout          # Test only ImmoScout provider"
    echo "  $0 wg_gesucht         # Test only WG-Gesucht provider"
    echo ""
    echo "Dry-run mode:"
    echo "  - No real notifications sent"
    echo "  - Limited scraping scope"
    echo "  - Debug logging enabled"
    echo "  - Temporary configuration used"
    echo ""
}

# Main execution
main() {
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    PROVIDER="$1"
    
    print_info "MAFA Scraper Dry-Run Starting..."
    echo ""
    
    # Validate provider
    validate_provider "$PROVIDER"
    
    # Pre-flight checks
    check_dependencies
    validate_config
    
    # Create logs directory
    mkdir -p logs data
    
    if [ "$PROVIDER" = "all" ]; then
        # Run full dry-run
        run_scraper_dryrun
    else
        # Run specific provider test
        run_provider_test "$PROVIDER"
    fi
    
    echo ""
    print_success "Dry-run completed!"
    print_info "Check the logs directory for detailed output"
}

# Run main function
main "$@"