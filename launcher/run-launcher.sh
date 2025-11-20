#!/bin/bash
# MAFA Launcher Script
# Simple script to start the MAFA Launcher

set -e

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

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is not installed or not in PATH"
    exit 1
fi

# Check if launcher.py exists
if [ ! -f "launcher.py" ]; then
    print_error "launcher.py not found in current directory"
    exit 1
fi

# Check if launcher.html exists
if [ ! -f "launcher.html" ]; then
    print_warning "launcher.html not found, using default interface"
fi

# Install Flask if not available
if ! python3 -c "import flask" &> /dev/null; then
    print_info "Installing Flask..."
    pip3 install flask flask-cors
fi

# Start the launcher
print_info "Starting MAFA Launcher..."
print_info "Make sure you have Poetry installed and dependencies set up"
echo ""

python3 launcher.py "$@"

print_success "Launcher stopped"