#!/bin/bash
# MAFA System Health Check Script
# Performs comprehensive system health checks and diagnostics

set -e

# Configuration
CHECK_TYPE=${1:-"full"}
OUTPUT_DIR=${OUTPUT_DIR:-"health-checks"}
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
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

print_subsection() {
    echo -e "\n${CYAN}--- $1 ---${NC}"
}

# Function to validate check type
validate_check_type() {
    local check_type="$1"
    local valid_types=("full" "basic" "security" "performance" "dependencies")
    
    if [[ ! " ${valid_types[@]} " =~ " ${check_type} " ]]; then
        print_error "Invalid check type: $check_type"
        print_info "Valid types: ${valid_types[*]}"
        exit 1
    fi
}

# Function to setup output directory
setup_output_dir() {
    mkdir -p "$OUTPUT_DIR"
    print_info "Health check reports will be saved to: $OUTPUT_DIR"
}

# Function to check basic system health
check_basic_health() {
    print_subsection "Basic System Health"
    
    local health_report="$OUTPUT_DIR/basic_health_$TIMESTAMP.txt"
    
    echo "MAFA Basic Health Check" > "$health_report"
    echo "Generated: $(date)" >> "$health_report"
    echo "================================" >> "$health_report"
    echo "" >> "$health_report"
    
    # Check Python environment
    print_info "Checking Python environment..."
    local python_version=$(python3 --version 2>&1)
    echo "Python Version: $python_version" >> "$health_report"
    
    if command -v poetry &> /dev/null; then
        local poetry_version=$(poetry --version 2>&1)
        echo "Poetry Version: $poetry_version" >> "$health_report"
        print_success "Poetry available: $poetry_version"
    else
        echo "Poetry: NOT FOUND" >> "$health_report"
        print_error "Poetry not found"
    fi
    
    # Check project structure
    print_info "Checking project structure..."
    local required_files=("pyproject.toml" "run.py" "mafa/orchestrator/__init__.py")
    local structure_ok=true
    
    for file in "${required_files[@]}"; do
        if [ -f "$file" ]; then
            echo "✓ $file" >> "$health_report"
        else
            echo "✗ $file (MISSING)" >> "$health_report"
            structure_ok=false
        fi
    done
    
    if [ "$structure_ok" = true ]; then
        print_success "Project structure intact"
    else
        print_warning "Some project files missing"
    fi
    
    # Check configuration
    print_info "Checking configuration..."
    if [ -f "config.json" ]; then
        if python3 -c "import json; json.load(open('config.json'))" 2>/dev/null; then
            echo "✓ config.json (valid JSON)" >> "$health_report"
            print_success "Configuration valid"
        else
            echo "✗ config.json (invalid JSON)" >> "$health_report"
            print_error "Configuration invalid"
        fi
    else
        echo "✗ config.json (missing)" >> "$health_report"
        print_warning "Configuration file missing"
    fi
    
    # Check data directory
    print_info "Checking data directory..."
    if [ -d "data" ]; then
        local data_files=$(find data/ -type f | wc -l)
        echo "✓ data/ directory exists ($data_files files)" >> "$health_report"
        print_success "Data directory exists with $data_files files"
    else
        echo "✗ data/ directory (missing)" >> "$health_report"
        print_warning "Data directory missing"
    fi
    
    echo "" >> "$health_report"
    echo "Basic Health Status: $([ "$structure_ok" = true ] && echo "HEALTHY" || echo "DEGRADED")" >> "$health_report"
    
    print_success "Basic health check completed: $health_report"
}

# Function to check dependencies
check_dependencies() {
    print_subsection "Dependency Health"
    
    local dep_report="$OUTPUT_DIR/dependencies_$TIMESTAMP.txt"
    
    echo "MAFA Dependency Health Check" > "$dep_report"
    echo "Generated: $(date)" >> "$dep_report"
    echo "================================" >> "$dep_report"
    echo "" >> "$dep_report"
    
    # Check Poetry dependencies
    if command -v poetry &> /dev/null; then
        print_info "Checking Poetry dependencies..."
        
        # Check if virtual environment exists
        if [ -d ".venv" ]; then
            echo "✓ Virtual environment exists" >> "$dep_report"
            print_success "Virtual environment found"
        else
            echo "✗ Virtual environment missing" >> "$dep_report"
            print_warning "Virtual environment not found"
        fi
        
        # Check dependency installation
        if poetry check 2>/dev/null; then
            echo "✓ Poetry configuration valid" >> "$dep_report"
            print_success "Poetry configuration valid"
        else
            echo "✗ Poetry configuration invalid" >> "$dep_report"
            print_error "Poetry configuration invalid"
        fi
        
        # Check critical dependencies
        local critical_deps=("selenium" "fastapi" "uvicorn" "loguru" "apscheduler")
        local missing_deps=()
        
        for dep in "${critical_deps[@]}"; do
            if poetry run python -c "import $dep" 2>/dev/null; then
                echo "✓ $dep" >> "$dep_report"
            else
                echo "✗ $dep (missing)" >> "$dep_report"
                missing_deps+=("$dep")
            fi
        done
        
        if [ ${#missing_deps[@]} -eq 0 ]; then
            print_success "All critical dependencies available"
        else
            print_warning "Missing dependencies: ${missing_deps[*]}"
        fi
    else
        echo "Poetry not available - skipping dependency checks" >> "$dep_report"
        print_error "Poetry not available"
    fi
    
    # Check system dependencies
    print_info "Checking system dependencies..."
    local system_deps=("git" "docker" "chrome" "chromedriver")
    
    for dep in "${system_deps[@]}"; do
        if command -v "$dep" &> /dev/null; then
            echo "✓ $dep" >> "$dep_report"
        else
            echo "✗ $dep (missing)" >> "$dep_report"
        fi
    done
    
    echo "" >> "$dep_report"
    echo "Dependency Health: CHECKED" >> "$dep_report"
    
    print_success "Dependency check completed: $dep_report"
}

# Function to check security
check_security() {
    print_subsection "Security Health"
    
    local security_report="$OUTPUT_DIR/security_$TIMESTAMP.txt"
    
    echo "MAFA Security Health Check" > "$security_report"
    echo "Generated: $(date)" >> "$security_report"
    echo "================================" >> "$security_report"
    echo "" >> "$security_report"
    
    # Check for exposed secrets
    print_info "Checking for exposed secrets..."
    local secret_patterns=("password" "secret" "token" "key" "webhook")
    local secrets_found=false
    
    for pattern in "${secret_patterns[@]}"; do
        local matches=$(grep -r -i "$pattern" mafa/ --include="*.py" | grep -v "test" | head -3)
        if [ -n "$matches" ]; then
            echo "⚠️  Potential secrets matching '$pattern':" >> "$security_report"
            echo "$matches" >> "$security_report"
            echo "" >> "$security_report"
            secrets_found=true
        fi
    done
    
    if [ "$secrets_found" = false ]; then
        echo "✓ No obvious secrets exposed" >> "$security_report"
        print_success "No obvious secrets exposed"
    else
        print_warning "Potential secrets found - review needed"
    fi
    
    # Check file permissions
    print_info "Checking file permissions..."
    local sensitive_files=("config.json" ".env*" "*.key" "*.pem")
    local permission_issues=false
    
    for pattern in "${sensitive_files[@]}"; do
        for file in $pattern; do
            if [ -f "$file" ]; then
                local perms=$(ls -l "$file" | cut -d' ' -f1)
                if [[ "$perms" =~ r..r..r.. ]]; then
                    echo "⚠️  $file has world-readable permissions" >> "$security_report"
                    permission_issues=true
                fi
            fi
        done
    done
    
    if [ "$permission_issues" = false ]; then
        echo "✓ File permissions appear secure" >> "$security_report"
        print_success "File permissions secure"
    else
        print_warning "File permission issues found"
    fi
    
    # Check for unsafe code patterns
    print_info "Checking for unsafe code patterns..."
    local unsafe_patterns=("eval(" "exec(" "shell=True")
    local unsafe_found=false
    
    for pattern in "${unsafe_patterns[@]}"; do
        local matches=$(grep -r "$pattern" mafa/ --include="*.py" | head -3)
        if [ -n "$matches" ]; then
            echo "⚠️  Unsafe pattern '$pattern':" >> "$security_report"
            echo "$matches" >> "$security_report"
            echo "" >> "$security_report"
            unsafe_found=true
        fi
    done
    
    if [ "$unsafe_found" = false ]; then
        echo "✓ No obvious unsafe patterns found" >> "$security_report"
        print_success "No unsafe patterns found"
    else
        print_warning "Unsafe code patterns found"
    fi
    
    echo "" >> "$security_report"
    echo "Security Health: $([ "$secrets_found" = false ] && [ "$permission_issues" = false ] && [ "$unsafe_found" = false ] && echo "SECURE" || echo "NEEDS_ATTENTION")" >> "$security_report"
    
    print_success "Security check completed: $security_report"
}

# Function to check performance
check_performance() {
    print_subsection "Performance Health"
    
    local perf_report="$OUTPUT_DIR/performance_$TIMESTAMP.txt"
    
    echo "MAFA Performance Health Check" > "$perf_report"
    echo "Generated: $(date)" >> "$perf_report"
    echo "================================" >> "$perf_report"
    echo "" >> "$perf_report"
    
    # Check code complexity
    print_info "Analyzing code complexity..."
    local total_files=$(find mafa/ -name "*.py" | wc -l)
    local total_lines=$(find mafa/ -name "*.py" -exec wc -l {} \; | awk '{sum += $1} END {print sum}')
    local avg_lines=$((total_lines / total_files))
    
    echo "Code Metrics:" >> "$perf_report"
    echo "  Total Python files: $total_files" >> "$perf_report"
    echo "  Total lines of code: $total_lines" >> "$perf_report"
    echo "  Average lines per file: $avg_lines" >> "$perf_report"
    echo "" >> "$perf_report"
    
    # Check for large files
    print_info "Checking for large files..."
    local large_files=$(find mfa/ -name "*.py" -exec wc -l {} \; | sort -nr | head -5)
    echo "Largest files:" >> "$perf_report"
    echo "$large_files" >> "$perf_report"
    echo "" >> "$perf_report"
    
    # Check database performance
    print_info "Checking database performance..."
    if [ -f "data/contacts.db" ]; then
        local db_size=$(du -h "data/contacts.db" | cut -f1)
        echo "Database size: $db_size" >> "$perf_report"
        
        # Check if database is locked
        if sqlite3 "data/contacts.db" "SELECT 1;" 2>/dev/null; then
            echo "✓ Database accessible" >> "$perf_report"
            print_success "Database accessible"
        else
            echo "✗ Database locked or inaccessible" >> "$perf_report"
            print_warning "Database may be locked"
        fi
    else
        echo "✗ Database not found" >> "$perf_report"
        print_info "Database not created yet"
    fi
    
    # Check for potential performance issues
    print_info "Checking for performance issues..."
    local perf_issues=0
    
    # Check for synchronous operations
    local sync_ops=$(grep -r "requests\." mafa/ --include="*.py" | wc -l)
    if [ "$sync_ops" -gt 0 ]; then
        echo "⚠️  Found $sync_ops synchronous HTTP requests" >> "$perf_report"
        perf_issues=$((perf_issues + 1))
    fi
    
    # Check for database operations in loops
    local db_loops=$(grep -r -A2 -B2 "for.*:" mafa/ --include="*.py" | grep -c "execute\|query\|select")
    if [ "$db_loops" -gt 0 ]; then
        echo "⚠️  Found potential database operations in loops" >> "$perf_report"
        perf_issues=$((perf_issues + 1))
    fi
    
    if [ "$perf_issues" -eq 0 ]; then
        echo "✓ No obvious performance issues found" >> "$perf_report"
        print_success "No obvious performance issues"
    else
        print_warning "Found $perf_issues potential performance issues"
    fi
    
    echo "" >> "$perf_report"
    echo "Performance Health: $([ "$perf_issues" -eq 0 ] && echo "GOOD" || echo "NEEDS_OPTIMIZATION")" >> "$perf_report"
    
    print_success "Performance check completed: $perf_report"
}

# Function to generate health summary
generate_health_summary() {
    print_section "Health Check Summary"
    
    local summary_file="$OUTPUT_DIR/health_summary_$TIMESTAMP.md"
    
    cat > "$summary_file" << EOF
# MAFA Health Check Summary
Generated: $(date)
Check Type: $CHECK_TYPE

## Health Check Overview

This report provides a comprehensive health assessment of the MAFA system:

EOF
    
    # Add sections based on check type
    if [ -f "$OUTPUT_DIR/basic_health_$TIMESTAMP.txt" ]; then
        echo "- [Basic Health](basic_health_$TIMESTAMP.txt) - System fundamentals" >> "$summary_file"
    fi
    
    if [ -f "$OUTPUT_DIR/dependencies_$TIMESTAMP.txt" ]; then
        echo "- [Dependencies](dependencies_$TIMESTAMP.txt) - Package and system dependencies" >> "$summary_file"
    fi
    
    if [ -f "$OUTPUT_DIR/security_$TIMESTAMP.txt" ]; then
        echo "- [Security](security_$TIMESTAMP.txt) - Security assessment" >> "$summary_file"
    fi
    
    if [ -f "$OUTPUT_DIR/performance_$TIMESTAMP.txt" ]; then
        echo "- [Performance](performance_$TIMESTAMP.txt) - Performance metrics" >> "$summary_file"
    fi
    
    echo "" >> "$summary_file"
    echo "## Overall Health Status" >> "$summary_file"
    echo "" >> "$summary_file"
    
    # Calculate overall status
    local issues=0
    
    if [ -f "$OUTPUT_DIR/basic_health_$TIMESTAMP.txt" ]; then
        if grep -q "DEGRADED" "$OUTPUT_DIR/basic_health_$TIMESTAMP.txt"; then
            issues=$((issues + 1))
        fi
    fi
    
    if [ -f "$OUTPUT_DIR/security_$TIMESTAMP.txt" ]; then
        if grep -q "NEEDS_ATTENTION" "$OUTPUT_DIR/security_$TIMESTAMP.txt"; then
            issues=$((issues + 1))
        fi
    fi
    
    if [ -f "$OUTPUT_DIR/performance_$TIMESTAMP.txt" ]; then
        if grep -q "NEEDS_OPTIMIZATION" "$OUTPUT_DIR/performance_$TIMESTAMP.txt"; then
            issues=$((issues + 1))
        fi
    fi
    
    if [ "$issues" -eq 0 ]; then
        echo "🟢 **HEALTHY** - No critical issues found" >> "$summary_file"
    elif [ "$issues" -le 2 ]; then
        echo "🟡 **DEGRADED** - Some issues need attention" >> "$summary_file"
    else
        echo "🔴 **UNHEALTHY** - Multiple issues require immediate attention" >> "$summary_file"
    fi
    
    echo "" >> "$summary_file"
    echo "## Recommendations" >> "$summary_file"
    echo "" >> "$summary_file"
    
    if [ "$issues" -gt 0 ]; then
        echo "1. Review the detailed health check reports" >> "$summary_file"
        echo "2. Address critical issues first" >> "$summary_file"
        echo "3. Set up regular health monitoring" >> "$summary_file"
        echo "4. Consider implementing automated health checks" >> "$summary_file"
    else
        echo "1. Continue regular health monitoring" >> "$summary_file"
        echo "2. Set up automated health checks" >> "$summary_file"
        echo "3. Monitor system performance over time" >> "$summary_file"
    fi
    
    echo "" >> "$summary_file"
    echo "## Next Health Check" >> "$summary_file"
    echo "" >> "$summary_file"
    echo "Schedule the next health check:" >> "$summary_file"
    echo "- **Daily**: Basic health check" >> "$summary_file"
    echo "- **Weekly**: Full health check" >> "$summary_file"
    echo "- **Monthly**: Comprehensive security and performance review" >> "$summary_file"
    echo "" >> "$summary_file"
    
    print_success "Health summary generated: $summary_file"
}

# Function to show help
show_help() {
    echo "MAFA System Health Check Script"
    echo ""
    echo "Usage: $0 [CHECK_TYPE]"
    echo ""
    echo "Arguments:"
    echo "  CHECK_TYPE    Type of health check (full, basic, security, performance, dependencies)"
    echo "                Default: full"
    echo ""
    echo "Environment Variables:"
    echo "  OUTPUT_DIR    Directory for health check reports (default: health-checks)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Full health check"
    echo "  $0 basic              # Basic health check only"
    echo "  $0 security           # Security check only"
    echo "  $0 performance        # Performance check only"
    echo "  $0 dependencies       # Dependency check only"
    echo ""
    echo "Check Types:"
    echo "  basic         - System fundamentals (Python, Poetry, config, structure)"
    echo "  dependencies  - Package and system dependencies"
    echo "  security      - Security assessment (secrets, permissions, unsafe patterns)"
    echo "  performance   - Performance metrics (code complexity, database, bottlenecks)"
    echo "  full          - All of the above"
    echo ""
}

# Main execution
main() {
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    CHECK_TYPE="$1"
    
    print_info "MAFA System Health Check Starting..."
    print_info "Check Type: $CHECK_TYPE"
    echo ""
    
    # Validate check type
    validate_check_type "$CHECK_TYPE"
    
    # Setup output directory
    setup_output_dir
    
    # Run checks based on type
    if [[ "$CHECK_TYPE" == "full" || "$CHECK_TYPE" == "basic" ]]; then
        check_basic_health
    fi
    
    if [[ "$CHECK_TYPE" == "full" || "$CHECK_TYPE" == "dependencies" ]]; then
        check_dependencies
    fi
    
    if [[ "$CHECK_TYPE" == "full" || "$CHECK_TYPE" == "security" ]]; then
        check_security
    fi
    
    if [[ "$CHECK_TYPE" == "full" || "$CHECK_TYPE" == "performance" ]]; then
        check_performance
    fi
    
    # Generate summary
    generate_health_summary
    
    echo ""
    print_success "Health check completed!"
    print_info "Reports saved in: $OUTPUT_DIR"
    print_info "Summary: $OUTPUT_DIR/health_summary_$TIMESTAMP.md"
}

# Run main function
main "$@"