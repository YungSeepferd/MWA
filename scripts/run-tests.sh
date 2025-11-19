#!/bin/bash
# MAFA Test Runner
# Runs comprehensive test suite with coverage and linting

set -e

# Configuration
TEST_PATTERN=${1:-""}
COVERAGE_THRESHOLD=${COVERAGE_THRESHOLD:-80}
VERBOSE=${VERBOSE:-false}

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

# Function to check dependencies
check_dependencies() {
    print_info "Checking test dependencies..."
    
    if ! command -v poetry &> /dev/null; then
        print_error "Poetry is not installed"
        exit 1
    fi
    
    # Check if dev dependencies are installed
    if ! poetry run python -c "import pytest" 2>/dev/null; then
        print_info "Installing dev dependencies..."
        poetry install
    fi
    
    print_success "Dependencies check completed"
}

# Function to run linting
run_linting() {
    print_section "Code Quality Checks"
    
    print_info "Running black formatter check..."
    if poetry run black --check .; then
        print_success "Black formatting check passed"
    else
        print_warning "Black formatting issues found"
        print_info "Run 'poetry run black .' to fix formatting"
        return 1
    fi
    
    print_info "Running isort import sorting check..."
    if poetry run isort --check-only .; then
        print_success "Import sorting check passed"
    else
        print_warning "Import sorting issues found"
        print_info "Run 'poetry run isort .' to fix imports"
        return 1
    fi
    
    print_info "Running flake8 linting..."
    if poetry run flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics; then
        print_success "Flake8 linting passed"
    else
        print_warning "Flake8 linting issues found"
        return 1
    fi
}

# Function to run type checking
run_type_checking() {
    print_section "Type Checking"
    
    if command -v mypy &> /dev/null; then
        print_info "Running mypy type checking..."
        if poetry run mypy mafa/ --ignore-missing-imports; then
            print_success "Type checking passed"
        else
            print_warning "Type checking issues found"
            return 1
        fi
    else
        print_info "mypy not installed, skipping type checking"
    fi
}

# Function to run security checks
run_security_checks() {
    print_section "Security Checks"
    
    if command -v safety &> /dev/null; then
        print_info "Running safety security checks..."
        if poetry run safety check; then
            print_success "Security checks passed"
        else
            print_warning "Security vulnerabilities found"
            return 1
        fi
    else
        print_info "safety not installed, skipping security checks"
    fi
}

# Function to run tests
run_tests() {
    print_section "Unit Tests"
    
    local test_args=""
    
    # Add pattern if specified
    if [ -n "$TEST_PATTERN" ]; then
        test_args="$test_args -k '$TEST_PATTERN'"
        print_info "Running tests matching pattern: $TEST_PATTERN"
    fi
    
    # Add verbose flag if requested
    if [ "$VERBOSE" = "true" ]; then
        test_args="$test_args -v"
        print_info "Running tests in verbose mode"
    fi
    
    # Run tests with coverage
    print_info "Running tests with coverage..."
    if poetry run pytest tests/ $test_args \
        --cov=mafa \
        --cov-report=html:htmlcov \
        --cov-report=term-missing \
        --cov-report=xml \
        --cov-fail-under="$COVERAGE_THRESHOLD"; then
        print_success "All tests passed"
        
        # Show coverage summary
        print_info "Coverage report generated in htmlcov/index.html"
        
        return 0
    else
        print_error "Some tests failed"
        return 1
    fi
}

# Function to run integration tests
run_integration_tests() {
    print_section "Integration Tests"
    
    # Check if integration tests exist
    if [ -d "tests/integration" ]; then
        print_info "Running integration tests..."
        if poetry run pytest tests/integration/ -v; then
            print_success "Integration tests passed"
            return 0
        else
            print_error "Integration tests failed"
            return 1
        fi
    else
        print_info "No integration tests found, skipping"
    fi
}

# Function to generate test report
generate_report() {
    print_section "Test Report"
    
    if [ -f "coverage.xml" ]; then
        print_info "Coverage report available in coverage.xml"
    fi
    
    if [ -d "htmlcov" ]; then
        print_info "HTML coverage report available in htmlcov/index.html"
    fi
    
    if [ -f ".coverage" ]; then
        poetry run coverage report --show-missing
    fi
}

# Function to show help
show_help() {
    echo "MAFA Test Runner"
    echo ""
    echo "Usage: $0 [OPTIONS] [TEST_PATTERN]"
    echo ""
    echo "Arguments:"
    echo "  TEST_PATTERN    Pattern to match test names (optional)"
    echo ""
    echo "Environment Variables:"
    echo "  COVERAGE_THRESHOLD  Minimum coverage percentage (default: 80)"
    echo "  VERBOSE             Set to 'true' for verbose output"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  --no-lint           Skip linting checks"
    echo "  --no-types          Skip type checking"
    echo "  --no-security       Skip security checks"
    echo "  --integration       Run integration tests"
    echo "  --fast              Skip linting, types, and security checks"
    echo ""
    echo "Examples:"
    echo "  $0                          # Run all tests"
    echo "  $0 test_provider            # Run tests matching 'provider'"
    echo "  $0 --no-lint               # Skip linting"
    echo "  $0 --integration           # Include integration tests"
    echo ""
}

# Main execution
main() {
    local skip_lint=false
    local skip_types=false
    local skip_security=false
    local run_integration=false
    
    # Parse arguments
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                show_help
                exit 0
                ;;
            --no-lint)
                skip_lint=true
                shift
                ;;
            --no-types)
                skip_types=true
                shift
                ;;
            --no-security)
                skip_security=true
                shift
                ;;
            --integration)
                run_integration=true
                shift
                ;;
            --fast)
                skip_lint=true
                skip_types=true
                skip_security=true
                shift
                ;;
            -*)
                print_error "Unknown option: $1"
                show_help
                exit 1
                ;;
            *)
                TEST_PATTERN="$1"
                shift
                ;;
        esac
    done
    
    print_info "MAFA Test Suite Starting..."
    echo ""
    
    # Pre-flight checks
    check_dependencies
    
    local exit_code=0
    
    # Run quality checks (unless skipped)
    if [ "$skip_lint" = false ]; then
        if ! run_linting; then
            print_warning "Linting checks failed"
            exit_code=1
        fi
    fi
    
    if [ "$skip_types" = false ]; then
        if ! run_type_checking; then
            print_warning "Type checking failed"
            exit_code=1
        fi
    fi
    
    if [ "$skip_security" = false ]; then
        if ! run_security_checks; then
            print_warning "Security checks failed"
            exit_code=1
        fi
    fi
    
    # Run unit tests
    if ! run_tests; then
        print_error "Unit tests failed"
        exit_code=1
    fi
    
    # Run integration tests if requested
    if [ "$run_integration" = true ]; then
        if ! run_integration_tests; then
            print_error "Integration tests failed"
            exit_code=1
        fi
    fi
    
    # Generate reports
    generate_report
    
    echo ""
    if [ $exit_code -eq 0 ]; then
        print_success "All tests completed successfully!"
    else
        print_error "Some checks failed. Please review the output above."
    fi
    
    exit $exit_code
}

# Run main function
main "$@"