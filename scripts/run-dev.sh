#!/bin/bash
# MAFA Development Environment Starter
# Starts the FastAPI development server with hot-reload

set -e

# Configuration
PORT=${1:-8000}
HOST=${HOST:-0.0.0.0}
ENV=${MAFA_ENV:-development}

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Function to check if dependencies are installed
check_dependencies() {
    print_info "Checking dependencies..."
    
    # Check if Poetry is installed
    if ! command -v poetry &> /dev/null; then
        print_error "Poetry is not installed. Please install it first:"
        echo "  curl -sSL https://install.python-poetry.org | python3 -"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [ ! -d ".venv" ]; then
        print_warning "Virtual environment not found. Creating one..."
        poetry install
    fi
    
    print_success "Dependencies check completed"
}

# Function to validate configuration
validate_config() {
    print_info "Validating configuration..."
    
    CONFIG_FILE="config.json"
    if [ ! -f "$CONFIG_FILE" ]; then
        print_warning "Config file not found. Creating from example..."
        cp config.example.json "$CONFIG_FILE"
        print_warning "Please edit $CONFIG_FILE with your settings before running production tasks"
    fi
    
    # Check if required sections exist
    if ! python3 -c "
import json
with open('$CONFIG_FILE', 'r') as f:
    config = json.load(f)
required = ['personal_profile', 'search_criteria', 'notification']
missing = [r for r in required if r not in config]
if missing:
    print(f'Missing required sections: {missing}')
    exit(1)
print('Configuration valid')
" 2>/dev/null; then
        print_warning "Configuration validation failed. Some sections may be missing."
    else
        print_success "Configuration validation passed"
    fi
}

# Function to start the development server
start_dev_server() {
    print_info "Starting MAFA development server..."
    print_info "Host: $HOST"
    print_info "Port: $PORT"
    print_info "Environment: $ENV"
    echo ""
    
    # Start the server with Poetry
    poetry run uvicorn api.main:app \
        --host "$HOST" \
        --port "$PORT" \
        --reload \
        --log-level info \
        --access-log
}

# Function to show help
show_help() {
    echo "MAFA Development Server"
    echo ""
    echo "Usage: $0 [OPTIONS] [PORT]"
    echo ""
    echo "Arguments:"
    echo "  PORT          Port number (default: 8000)"
    echo ""
    echo "Environment Variables:"
    echo "  HOST          Host to bind to (default: 0.0.0.0)"
    echo "  MAF_ENV       Environment mode (default: development)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Start on port 8000"
    echo "  $0 3000              # Start on port 3000"
    echo "  HOST=127.0.0.1 $0    # Bind to localhost only"
    echo ""
    echo "The development server will automatically reload when code changes."
}

# Main execution
main() {
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    print_info "MAFA Development Environment Starting..."
    echo ""
    
    # Run pre-flight checks
    check_dependencies
    validate_config
    
    echo ""
    print_info "Starting development server..."
    print_info "Dashboard will be available at: http://$HOST:$PORT"
    print_info "API docs available at: http://$HOST:$PORT/docs"
    echo ""
    
    # Start the server
    start_dev_server
}

# Run main function
main "$@"