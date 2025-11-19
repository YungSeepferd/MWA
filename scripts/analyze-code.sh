#!/bin/bash
# MAFA Code Analysis Script
# Performs comprehensive code analysis and generates reports

set -e

# Configuration
SCOPE=${1:-"full"}
OUTPUT_DIR=${OUTPUT_DIR:-"analysis-reports"}
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

# Function to validate scope
validate_scope() {
    local scope="$1"
    local valid_scopes=("full" "security" "performance" "architecture" "quality")
    
    if [[ ! " ${valid_scopes[@]} " =~ " ${scope} " ]]; then
        print_error "Invalid scope: $scope"
        print_info "Valid scopes: ${valid_scopes[*]}"
        exit 1
    fi
}

# Function to setup output directory
setup_output_dir() {
    mkdir -p "$OUTPUT_DIR"
    print_info "Analysis reports will be saved to: $OUTPUT_DIR"
}

# Function to run security analysis
run_security_analysis() {
    print_subsection "Security Analysis"
    
    local security_report="$OUTPUT_DIR/security_analysis_$TIMESTAMP.md"
    
    cat > "$security_report" << EOF
# MAFA Security Analysis Report
Generated: $(date)

## Security Findings

EOF
    
    # Check for common security issues
    print_info "Scanning for security vulnerabilities..."
    
    # Check for eval/exec usage
    local eval_files=$(grep -r "eval(" mafa/ --include="*.py" | head -5)
    if [ -n "$eval_files" ]; then
        echo "### ⚠️  Code Injection Risk" >> "$security_report"
        echo "Found usage of eval():" >> "$security_report"
        echo "\`\`\`" >> "$security_report"
        echo "$eval_files" >> "$security_report"
        echo "\`\`\`" >> "$security_report"
        echo "" >> "$security_report"
    fi
    
    # Check for shell=True in subprocess
    local shell_files=$(grep -r "shell=True" mafa/ --include="*.py" | head -5)
    if [ -n "$shell_files" ]; then
        echo "### ⚠️  Shell Injection Risk" >> "$security_report"
        echo "Found usage of shell=True:" >> "$security_report"
        echo "\`\`\`" >> "$security_report"
        echo "$shell_files" >> "$security_report"
        echo "\`\`\`" >> "$security_report"
        echo "" >> "$security_report"
    fi
    
    # Check for hardcoded secrets
    local secret_patterns=("password" "secret" "token" "key" "webhook")
    for pattern in "${secret_patterns[@]}"; do
        local matches=$(grep -r -i "$pattern" mafa/ --include="*.py" | grep -v "test" | head -3)
        if [ -n "$matches" ]; then
            echo "### ⚠️  Potential Hardcoded Secrets" >> "$security_report"
            echo "Found potential secrets matching '$pattern':" >> "$security_report"
            echo "\`\`\`" >> "$security_report"
            echo "$matches" >> "$security_report"
            echo "\`\`\`" >> "$security_report"
            echo "" >> "$security_report"
        fi
    done
    
    # Check input validation
    local validation_files=$(find mafa/ -name "*.py" -exec grep -l "validate\|sanitize\|clean" {} \;)
    if [ -n "$validation_files" ]; then
        echo "### ✅ Input Validation Found" >> "$security_report"
        echo "Files with validation logic:" >> "$security_report"
        for file in $validation_files; do
            echo "- $file" >> "$security_report"
        done
        echo "" >> "$security_report"
    fi
    
    print_success "Security analysis completed: $security_report"
}

# Function to run performance analysis
run_performance_analysis() {
    print_subsection "Performance Analysis"
    
    local performance_report="$OUTPUT_DIR/performance_analysis_$TIMESTAMP.md"
    
    cat > "$performance_report" << EOF
# MAFA Performance Analysis Report
Generated: $(date)

## Performance Findings

EOF
    
    # Check for database queries in loops
    print_info "Analyzing database query patterns..."
    local db_loop_files=$(grep -r -A2 -B2 "for.*:" mafa/ --include="*.py" | grep -A2 -B2 "execute\|query\|select" | head -10)
    if [ -n "$db_loop_files" ]; then
        echo "### ⚠️  Potential N+1 Query Pattern" >> "$performance_report"
        echo "Found database operations in loops:" >> "$performance_report"
        echo "\`\`\`" >> "$performance_report"
        echo "$db_loop_files" >> "$performance_report"
        echo "\`\`\`" >> "$performance_report"
        echo "" >> "$performance_report"
    fi
    
    # Check for synchronous operations that could be async
    local sync_files=$(grep -r "requests\." mafa/ --include="*.py" | head -5)
    if [ -n "$sync_files" ]; then
        echo "### ⚠️  Synchronous HTTP Requests" >> "$performance_report"
        echo "Found synchronous requests (consider async alternatives):" >> "$performance_report"
        echo "\`\`\`" >> "$performance_report"
        echo "$sync_files" >> "$performance_report"
        echo "\`\`\`" >> "$performance_report"
        echo "" >> "$performance_report"
    fi
    
    # Check for large file operations
    local file_ops=$(grep -r "open.*w" mafa/ --include="*.py" | head -5)
    if [ -n "$file_ops" ]; then
        echo "### ℹ️  File Operations" >> "$performance_report"
        echo "File write operations found:" >> "$performance_report"
        echo "\`\`\`" >> "$performance_report"
        echo "$file_ops" >> "$performance_report"
        echo "\`\`\`" >> "$performance_report"
        echo "" >> "$performance_report"
    fi
    
    # Analyze function complexity
    print_info "Analyzing function complexity..."
    local complex_functions=$(find mafa/ -name "*.py" -exec wc -l {} \; | sort -nr | head -10)
    echo "### 📊 File Size Analysis" >> "$performance_report"
    echo "Largest Python files:" >> "$performance_report"
    echo "\`\`\`" >> "$performance_report"
    echo "$complex_functions" >> "$performance_report"
    echo "\`\`\`" >> "$performance_report"
    echo "" >> "$performance_report"
    
    print_success "Performance analysis completed: $performance_report"
}

# Function to run architecture analysis
run_architecture_analysis() {
    print_subsection "Architecture Analysis"
    
    local architecture_report="$OUTPUT_DIR/architecture_analysis_$TIMESTAMP.md"
    
    cat > "$architecture_report" << EOF
# MAFA Architecture Analysis Report
Generated: $(date)

## Architecture Findings

EOF
    
    # Analyze module structure
    print_info "Analyzing module structure..."
    echo "### 📁 Module Structure" >> "$architecture_report"
    echo "" >> "$architecture_report"
    
    for module in mafa/*/; do
        if [ -d "$module" ]; then
            module_name=$(basename "$module")
            file_count=$(find "$module" -name "*.py" | wc -l)
            echo "- **$module_name**: $file_count Python files" >> "$architecture_report"
            
            # List files in module
            for file in "$module"/*.py; do
                if [ -f "$file" ]; then
                    file_name=$(basename "$file")
                    line_count=$(wc -l < "$file")
                    echo "  - $file_name ($line_count lines)" >> "$architecture_report"
                fi
            done
            echo "" >> "$architecture_report"
        fi
    done
    
    # Check for circular dependencies
    print_info "Checking for circular dependencies..."
    echo "### 🔄 Dependency Analysis" >> "$architecture_report"
    echo "" >> "$architecture_report"
    
    # Simple circular dependency check
    local imports_file="$OUTPUT_DIR/imports_$TIMESTAMP.txt"
    find mafa/ -name "*.py" -exec grep -H "^from\|^import" {} \; > "$imports_file"
    
    echo "Import relationships found:" >> "$architecture_report"
    echo "\`\`\`" >> "$architecture_report"
    head -20 "$imports_file" >> "$architecture_report"
    echo "\`\`\`" >> "$architecture_report"
    echo "" >> "$architecture_report"
    
    # Analyze design patterns
    print_info "Analyzing design patterns..."
    echo "### 🎨 Design Patterns" >> "$architecture_report"
    echo "" >> "$architecture_report"
    
    # Check for factory pattern
    local factory_files=$(grep -r "def.*create\|def.*build" mafa/ --include="*.py" | head -5)
    if [ -n "$factory_files" ]; then
        echo "#### Factory Pattern" >> "$architecture_report"
        echo "Found factory methods:" >> "$architecture_report"
        echo "\`\`\`" >> "$architecture_report"
        echo "$factory_files" >> "$architecture_report"
        echo "\`\`\`" >> "$architecture_report"
        echo "" >> "$architecture_report"
    fi
    
    # Check for strategy pattern
    local strategy_files=$(grep -r "class.*Provider\|def.*scrape" mafa/ --include="*.py" | head -5)
    if [ -n "$strategy_files" ]; then
        echo "#### Strategy Pattern" >> "$architecture_report"
        echo "Found strategy implementations:" >> "$architecture_report"
        echo "\`\`\`" >> "$architecture_report"
        echo "$strategy_files" >> "$architecture_report"
        echo "\`\`\`" >> "$architecture_report"
        echo "" >> "$architecture_report"
    fi
    
    print_success "Architecture analysis completed: $architecture_report"
}

# Function to run code quality analysis
run_quality_analysis() {
    print_subsection "Code Quality Analysis"
    
    local quality_report="$OUTPUT_DIR/quality_analysis_$TIMESTAMP.md"
    
    cat > "$quality_report" << EOF
# MAFA Code Quality Analysis Report
Generated: $(date)

## Quality Findings

EOF
    
    # Check for TODO/FIXME comments
    print_info "Scanning for TODO/FIXME comments..."
    local todo_files=$(grep -r -n "TODO\|FIXME" mafa/ --include="*.py" | head -10)
    if [ -n "$todo_files" ]; then
        echo "### 📝 TODO/FIXME Comments" >> "$quality_report"
        echo "Found TODO/FIXME comments:" >> "$quality_report"
        echo "\`\`\`" >> "$quality_report"
        echo "$todo_files" >> "$quality_report"
        echo "\`\`\`" >> "$quality_report"
        echo "" >> "$quality_report"
    fi
    
    # Check for print statements
    print_info "Scanning for print statements..."
    local print_files=$(grep -r -n "print(" mafa/ --include="*.py" | head -10)
    if [ -n "$print_files" ]; then
        echo "### ⚠️  Print Statements" >> "$quality_report"
        echo "Found print statements (should use logging):" >> "$quality_report"
        echo "\`\`\`" >> "$quality_report"
        echo "$print_files" >> "$quality_report"
        echo "\`\`\`" >> "$quality_report"
        echo "" >> "$quality_report"
    fi
    
    # Check for docstring coverage
    print_info "Analyzing docstring coverage..."
    local total_functions=$(find mafa/ -name "*.py" -exec grep -c "def " {} \; | awk '{sum += $1} END {print sum}')
    local documented_functions=$(find mafa/ -name "*.py" -exec grep -c '"""' {} \; | awk '{sum += $1} END {print sum}')
    
    echo "### 📚 Documentation Coverage" >> "$quality_report"
    echo "- Total functions: $total_functions" >> "$quality_report"
    echo "- Documented functions (approx): $documented_functions" >> "$quality_report"
    
    if [ "$total_functions" -gt 0 ]; then
        local coverage=$((documented_functions * 100 / total_functions))
        echo "- Documentation coverage: ${coverage}%" >> "$quality_report"
    fi
    echo "" >> "$quality_report"
    
    # Check for exception handling
    print_info "Analyzing exception handling..."
    local exception_files=$(grep -r -n "except:" mafa/ --include="*.py" | head -5)
    if [ -n "$exception_files" ]; then
        echo "### ⚠️  Broad Exception Handling" >> "$quality_report"
        echo "Found broad exception handling:" >> "$quality_report"
        echo "\`\`\`" >> "$quality_report"
        echo "$exception_files" >> "$quality_report"
        echo "\`\`\`" >> "$quality_report"
        echo "" >> "$quality_report"
    fi
    
    print_success "Code quality analysis completed: $quality_report"
}

# Function to generate summary report
generate_summary_report() {
    print_section "Summary Report"
    
    local summary_report="$OUTPUT_DIR/analysis_summary_$TIMESTAMP.md"
    
    cat > "$summary_report" << EOF
# MAFA Code Analysis Summary
Generated: $(date)
Scope: $SCOPE

## Analysis Overview

This report provides a comprehensive analysis of the MAFA codebase across multiple dimensions:

EOF
    
    # Add sections based on scope
    if [[ "$SCOPE" == "full" || "$SCOPE" == "security" ]]; then
        echo "- [Security Analysis](security_analysis_$TIMESTAMP.md)" >> "$summary_report"
    fi
    
    if [[ "$SCOPE" == "full" || "$SCOPE" == "performance" ]]; then
        echo "- [Performance Analysis](performance_analysis_$TIMESTAMP.md)" >> "$summary_report"
    fi
    
    if [[ "$SCOPE" == "full" || "$SCOPE" == "architecture" ]]; then
        echo "- [Architecture Analysis](architecture_analysis_$TIMESTAMP.md)" >> "$summary_report"
    fi
    
    if [[ "$SCOPE" == "full" || "$SCOPE" == "quality" ]]; then
        echo "- [Code Quality Analysis](quality_analysis_$TIMESTAMP.md)" >> "$summary_report"
    fi
    
    echo "" >> "$summary_report"
    echo "## Key Metrics" >> "$summary_report"
    echo "" >> "$summary_report"
    
    # Add basic metrics
    local total_files=$(find mafa/ -name "*.py" | wc -l)
    local total_lines=$(find mafa/ -name "*.py" -exec wc -l {} \; | awk '{sum += $1} END {print sum}')
    local total_modules=$(find mafa/ -type d -mindepth 1 -maxdepth 1 | wc -l)
    
    echo "- Total Python files: $total_files" >> "$summary_report"
    echo "- Total lines of code: $total_lines" >> "$summary_report"
    echo "- Main modules: $total_modules" >> "$summary_report"
    echo "" >> "$summary_report"
    
    echo "## Recommendations" >> "$summary_report"
    echo "" >> "$summary_report"
    echo "Based on the analysis, consider the following improvements:" >> "$summary_report"
    echo "" >> "$summary_report"
    echo "1. **Security**: Review and address any security vulnerabilities found" >> "$summary_report"
    echo "2. **Performance**: Optimize database queries and consider async operations" >> "$summary_report"
    echo "3. **Architecture**: Continue following modular design patterns" >> "$summary_report"
    echo "4. **Quality**: Improve documentation coverage and replace print statements" >> "$summary_report"
    echo "" >> "$summary_report"
    
    print_success "Summary report generated: $summary_report"
}

# Function to show help
show_help() {
    echo "MAFA Code Analysis Script"
    echo ""
    echo "Usage: $0 [SCOPE]"
    echo ""
    echo "Arguments:"
    echo "  SCOPE    Analysis scope (full, security, performance, architecture, quality)"
    echo "           Default: full"
    echo ""
    echo "Environment Variables:"
    echo "  OUTPUT_DIR    Directory for analysis reports (default: analysis-reports)"
    echo ""
    echo "Examples:"
    echo "  $0                    # Full analysis"
    echo "  $0 security           # Security analysis only"
    echo "  $0 performance        # Performance analysis only"
    echo "  $0 architecture       # Architecture analysis only"
    echo "  $0 quality            # Code quality analysis only"
    echo ""
}

# Main execution
main() {
    if [ "$1" = "-h" ] || [ "$1" = "--help" ]; then
        show_help
        exit 0
    fi
    
    SCOPE="$1"
    
    print_info "MAFA Code Analysis Starting..."
    print_info "Scope: $SCOPE"
    echo ""
    
    # Validate scope
    validate_scope "$SCOPE"
    
    # Setup output directory
    setup_output_dir
    
    # Run analysis based on scope
    if [[ "$SCOPE" == "full" || "$SCOPE" == "security" ]]; then
        run_security_analysis
    fi
    
    if [[ "$SCOPE" == "full" || "$SCOPE" == "performance" ]]; then
        run_performance_analysis
    fi
    
    if [[ "$SCOPE" == "full" || "$SCOPE" == "architecture" ]]; then
        run_architecture_analysis
    fi
    
    if [[ "$SCOPE" == "full" || "$SCOPE" == "quality" ]]; then
        run_quality_analysis
    fi
    
    # Generate summary
    generate_summary_report
    
    echo ""
    print_success "Code analysis completed!"
    print_info "Reports saved in: $OUTPUT_DIR"
    print_info "Summary report: $OUTPUT_DIR/analysis_summary_$TIMESTAMP.md"
}

# Run main function
main "$@"