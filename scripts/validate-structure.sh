#!/bin/bash

#==============================================================================
# MAFA Documentation Structure Validator
# Validates the documentation directory structure and file organization
#==============================================================================

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
DOCS_DIR="${DOCS_DIR:-docs}"
TOLERANCE="${TOLERANCE:-strict}" # strict|lenient|minimal
OUTPUT_FORMAT="${OUTPUT_FORMAT:-console}"
REPORT_FILE="${REPORT_FILE:-/tmp/mafa-structure-report.json}"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_purple() {
    echo -e "${PURPLE}[STRUCTURE]${NC} $1"
}

# Validation counters
TOTAL_CHECKS=0
PASSED_CHECKS=0
FAILED_CHECKS=0
WARNING_CHECKS=0

# Structure categories
REQUIRED_DIRS=()
REQUIRED_FILES=()
OPTIONAL_DIRS=()
OPTIONAL_FILES=()
CUSTOM_RULES=()

#==============================================================================
# Structure Definition Functions
#==============================================================================

define_structure() {
    case "$TOLERANCE" in
        strict)
            define_strict_structure
            ;;
        lenient)
            define_lenient_structure
            ;;
        minimal)
            define_minimal_structure
            ;;
        *)
            log_error "Invalid tolerance level: $TOLERANCE (must be strict|lenient|minimal)"
            exit 1
            ;;
    esac
}

define_strict_structure() {
    log_info "Defining STRICT documentation structure requirements..."
    
    # Required directories for complete MAFA documentation
    REQUIRED_DIRS=(
        "getting-started"
        "user-guide"
        "user-guide/workflows"
        "developer-guide"
        "developer-guide/api"
        "developer-guide/testing"
        "architecture"
        "operations"
        "project"
        "project/implementation"
        "project/qa-reports"
    )
    
    # Required files for complete documentation
    REQUIRED_FILES=(
        "README.md"
        "getting-started/quick-start.md"
        "getting-started/installation.md"
        "getting-started/configuration.md"
        "user-guide/overview.md"
        "user-guide/dashboard.md"
        "user-guide/setup-wizard.md"
        "user-guide/troubleshooting.md"
        "user-guide/workflows/user-flows.md"
        "user-guide/workflows/detailed-workflows.md"
        "developer-guide/contributing.md"
        "developer-guide/development-setup.md"
        "developer-guide/code-style.md"
        "developer-guide/documentation-guidelines.md"
        "developer-guide/api/integration-guide.md"
        "developer-guide/testing/qa-test-plan.md"
        "developer-guide/testing/ux-test-scenarios.md"
        "architecture/system-overview.md"
        "architecture/repository-structure.md"
        "architecture/contact-discovery.md"
        "architecture/data-models.md"
        "architecture/database-schema.md"
        "operations/deployment.md"
        "operations/monitoring.md"
        "operations/backup-restore.md"
        "operations/security.md"
        "project/roadmap.md"
        "project/development-plan.md"
        "project/changelog.md"
        "project/release-notes.md"
        "project/governance.md"
        "project/implementation/short-term-enhancements.md"
    )
    
    # Optional but recommended directories
    OPTIONAL_DIRS=(
        "templates"
        "examples"
        "api-reference"
        "tutorials"
        "troubleshooting"
    )
    
    # Optional but recommended files
    OPTIONAL_FILES=(
        "templates/guide-template.md"
        "templates/api-reference-template.md"
        "templates/release-notes-template.md"
        "examples/markdown-examples.md"
        "api-reference/README.md"
        "tutorials/README.md"
    )
}

define_lenient_structure() {
    log_info "Defining LENIENT documentation structure requirements..."
    
    # Required directories
    REQUIRED_DIRS=(
        "getting-started"
        "user-guide"
        "developer-guide"
        "architecture"
        "operations"
        "project"
    )
    
    # Required files (minimal set)
    REQUIRED_FILES=(
        "README.md"
        "getting-started/quick-start.md"
        "user-guide/overview.md"
        "developer-guide/contributing.md"
        "project/roadmap.md"
    )
    
    # Optional directories
    OPTIONAL_DIRS=(
        "user-guide/workflows"
        "developer-guide/api"
        "developer-guide/testing"
        "project/implementation"
        "project/qa-reports"
    )
    
    # Optional files
    OPTIONAL_FILES=(
        "getting-started/installation.md"
        "getting-started/configuration.md"
        "user-guide/dashboard.md"
        "developer-guide/development-setup.md"
        "architecture/system-overview.md"
        "operations/deployment.md"
        "project/changelog.md"
    )
}

define_minimal_structure() {
    log_info "Defining MINIMAL documentation structure requirements..."
    
    # Required directories
    REQUIRED_DIRS=(
        "user-guide"
        "developer-guide"
    )
    
    # Required files (absolute minimum)
    REQUIRED_FILES=(
        "README.md"
        "user-guide/overview.md"
        "developer-guide/contributing.md"
    )
    
    # Optional directories
    OPTIONAL_DIRS=(
        "getting-started"
        "architecture"
        "project"
    )
    
    # Optional files
    OPTIONAL_FILES=(
        "project/roadmap.md"
        "architecture/system-overview.md"
    )
}

#==============================================================================
# Validation Functions
#==============================================================================

validate_directory_exists() {
    local dir="$1"
    local full_path="$DOCS_DIR/$dir"
    
    ((TOTAL_CHECKS++))
    
    if [[ -d "$full_path" ]]; then
        ((PASSED_CHECKS++))
        log_purple "✓ Directory exists: $dir"
        return 0
    else
        ((FAILED_CHECKS++))
        log_error "✗ Missing required directory: $dir"
        return 1
    fi
}

validate_file_exists() {
    local file="$1"
    local full_path="$DOCS_DIR/$file"
    
    ((TOTAL_CHECKS++))
    
    if [[ -f "$full_path" ]]; then
        ((PASSED_CHECKS++))
        log_purple "✓ File exists: $file"
        return 0
    else
        ((FAILED_CHECKS++))
        log_error "✗ Missing required file: $file"
        return 1
    fi
}

validate_optional_directory() {
    local dir="$1"
    local full_path="$DOCS_DIR/$dir"
    
    ((TOTAL_CHECKS++))
    
    if [[ -d "$full_path" ]]; then
        ((PASSED_CHECKS++))
        log_success "✓ Optional directory exists: $dir"
        return 0
    else
        ((WARNING_CHECKS++))
        log_warning "⚠ Optional directory missing: $dir"
        return 1
    fi
}

validate_optional_file() {
    local file="$1"
    local full_path="$DOCS_DIR/$file"
    
    ((TOTAL_CHECKS++))
    
    if [[ -f "$full_path" ]]; then
        ((PASSED_CHECKS++))
        log_success "✓ Optional file exists: $file"
        return 0
    else
        ((WARNING_CHECKS++))
        log_warning "⚠ Optional file missing: $file"
        return 1
    fi
}

validate_naming_conventions() {
    log_info "Validating naming conventions..."
    
    local md_files=()
    while IFS= read -r -d '' file; do
        md_files+=("$file")
    done < <(find "$DOCS_DIR" -name "*.md" -type f -print0)
    
    local naming_errors=0
    
    for file in "${md_files[@]}"; do
        local relative_path="${file#$DOCS_DIR/}"
        local filename=$(basename "$file")
        
        # Check for spaces in filenames (should use hyphens)
        if [[ "$filename" =~ [[:space:]] ]]; then
            log_warning "File contains spaces (should use hyphens): $relative_path"
            ((WARNING_CHECKS++))
            ((naming_errors++))
        fi
        
        # Check for uppercase letters in middle of filename
        if [[ "$filename" =~ [a-z][A-Z] ]]; then
            log_warning "Filename contains uppercase letters (should be lowercase): $relative_path"
            ((WARNING_CHECKS++))
            ((naming_errors++))
        fi
        
        # Check for special characters (except hyphens and underscores)
        if [[ "$filename" =~ [^a-zA-Z0-9._-] ]]; then
            log_error "Filename contains special characters: $relative_path"
            ((FAILED_CHECKS++))
            ((naming_errors++))
        fi
    done
    
    ((TOTAL_CHECKS++))
    
    if [[ $naming_errors -eq 0 ]]; then
        ((PASSED_CHECKS++))
        log_success "✓ All files follow naming conventions"
    else
        ((FAILED_CHECKS++))
        log_error "✗ Found $naming_errors naming convention violations"
    fi
}

validate_directory_structure_balance() {
    log_info "Validating directory structure balance..."
    
    # Check for empty directories
    local empty_dirs=0
    while IFS= read -r dir; do
        if [[ -d "$dir" && -z "$(ls -A "$dir")" ]]; then
            log_warning "Empty directory found: ${dir#$DOCS_DIR/}"
            ((WARNING_CHECKS++))
            ((empty_dirs++))
        fi
    done < <(find "$DOCS_DIR" -type d -print0)
    
    # Check for directories with too many files (potential organization issues)
    local overcrowded_dirs=0
    while IFS= read -r dir; do
        local file_count=$(find "$dir" -maxdepth 1 -type f | wc -l)
        if [[ $file_count -gt 20 ]]; then
            log_warning "Directory may be overcrowded (${file_count} files): ${dir#$DOCS_DIR/}"
            ((WARNING_CHECKS++))
            ((overcrowded_dirs++))
        fi
    done < <(find "$DOCS_DIR" -type d -print0)
    
    ((TOTAL_CHECKS++))
    
    if [[ $empty_dirs -eq 0 && $overcrowded_dirs -eq 0 ]]; then
        ((PASSED_CHECKS++))
        log_success "✓ Directory structure is well balanced"
    else
        ((WARNING_CHECKS++))
        log_warning "⚠ Directory structure balance issues found"
    fi
}

validate_readme_consistency() {
    log_info "Validating README.md consistency..."
    
    local readme_file="$DOCS_DIR/README.md"
    
    if [[ ! -f "$readme_file" ]]; then
        log_error "README.md is missing"
        ((FAILED_CHECKS++))
        ((TOTAL_CHECKS++))
        return 1
    fi
    
    # Check if README contains expected sections
    local expected_sections=("getting-started" "user-guide" "developer-guide" "architecture")
    local missing_sections=0
    
    for section in "${expected_sections[@]}"; do
        if ! grep -qi "$section" "$readme_file"; then
            log_warning "README.md may be missing section: $section"
            ((WARNING_CHECKS++))
            ((missing_sections++))
        fi
    done
    
    # Check for broken internal references in README
    local broken_refs=0
    while IFS= read -r ref; do
        local ref_path="${ref#](\./}"
        ref_path="${ref_path%)}"
        local full_path="$DOCS_DIR/$ref_path"
        
        if [[ ! -e "$full_path" ]]; then
            log_error "Broken reference in README.md: $ref_path"
            ((FAILED_CHECKS++))
            ((broken_refs++))
        fi
    done < <(grep -oP '\]\(\./[^)]+\)' "$readme_file" 2>/dev/null || true)
    
    ((TOTAL_CHECKS++))
    
    if [[ $missing_sections -eq 0 && $broken_refs -eq 0 ]]; then
        ((PASSED_CHECKS++))
        log_success "✓ README.md is consistent with structure"
    else
        ((FAILED_CHECKS++))
        log_error "✗ README.md has consistency issues"
    fi
}

#==============================================================================
# Report Generation
#==============================================================================

generate_json_report() {
    cat > "$REPORT_FILE" <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "docs_directory": "$DOCS_DIR",
  "tolerance": "$TOLERANCE",
  "summary": {
    "total_checks": $TOTAL_CHECKS,
    "passed_checks": $PASSED_CHECKS,
    "failed_checks": $FAILED_CHECKS,
    "warning_checks": $WARNING_CHECKS,
    "success_rate": $(echo "scale=2; $PASSED_CHECKS * 100 / $TOTAL_CHECKS" | bc -l)
  },
  "structure_validation": {
    "required_dirs": $(printf '%s\n' "${REQUIRED_DIRS[@]}" | jq -R . | jq -s .),
    "required_files": $(printf '%s\n' "${REQUIRED_FILES[@]}" | jq -R . | jq -s .),
    "optional_dirs": $(printf '%s\n' "${OPTIONAL_DIRS[@]}" | jq -R . | jq -s .),
    "optional_files": $(printf '%s\n' "${OPTIONAL_FILES[@]}" | jq -R . | jq -s .)
  }
}
EOF
}

generate_console_report() {
    echo
    log_info "=== STRUCTURE VALIDATION SUMMARY ==="
    log_info "Tolerance Level: $TOLERANCE"
    log_info "Total Checks: $TOTAL_CHECKS"
    log_success "Passed: $PASSED_CHECKS"
    log_error "Failed: $FAILED_CHECKS"
    log_warning "Warnings: $WARNING_CHECKS"
    
    if [[ $TOTAL_CHECKS -gt 0 ]]; then
        local success_rate=$(echo "scale=1; $PASSED_CHECKS * 100 / $TOTAL_CHECKS" | bc -l 2>/dev/null || echo "N/A")
        log_info "Success Rate: ${success_rate}%"
    fi
    
    echo
    if [[ $FAILED_CHECKS -eq 0 ]]; then
        log_success "✅ Structure validation passed!"
        return 0
    else
        log_error "❌ Structure validation failed with $FAILED_CHECKS errors"
        return 1
    fi
}

#==============================================================================
# Main Execution
#==============================================================================

main() {
    log_info "Starting documentation structure validation..."
    log_info "Documentation directory: $DOCS_DIR"
    log_info "Tolerance level: $TOLERANCE"
    log_info "Output format: $OUTPUT_FORMAT"
    log_info "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    
    # Define structure requirements
    define_structure
    
    # Validate required directories
    log_info "Validating required directories..."
    for dir in "${REQUIRED_DIRS[@]}"; do
        validate_directory_exists "$dir"
    done
    
    # Validate required files
    log_info "Validating required files..."
    for file in "${REQUIRED_FILES[@]}"; do
        validate_file_exists "$file"
    done
    
    # Validate optional directories
    log_info "Validating optional directories..."
    for dir in "${OPTIONAL_DIRS[@]}"; do
        validate_optional_directory "$dir"
    done
    
    # Validate optional files
    log_info "Validating optional files..."
    for file in "${OPTIONAL_FILES[@]}"; do
        validate_optional_file "$file"
    done
    
    # Run additional validation checks
    validate_naming_conventions
    validate_directory_structure_balance
    validate_readme_consistency
    
    # Generate reports
    case "$OUTPUT_FORMAT" in
        json)
            generate_json_report
            log_info "JSON report saved to: $REPORT_FILE"
            ;;
        console|*)
            generate_console_report
            ;;
    esac
    
    # Return appropriate exit code
    if [[ $FAILED_CHECKS -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "MAFA Documentation Structure Validator"
        echo
        echo "Usage: $0 [OPTIONS]"
        echo
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --docs-dir DIR      Set documentation directory (default: docs)"
        echo "  --tolerance LEVEL   Validation tolerance: strict|lenient|minimal (default: strict)"
        echo "  --format FORMAT     Output format: console|json (default: console)"
        echo "  --report FILE       JSON report file path (default: /tmp/mafa-structure-report.json)"
        echo
        echo "Environment Variables:"
        echo "  DOCS_DIR            Documentation directory path"
        echo "  TOLERANCE           Validation tolerance level"
        echo "  OUTPUT_FORMAT       Output format: console|json"
        echo "  REPORT_FILE         JSON report file path"
        echo
        echo "Tolerance Levels:"
        echo "  strict   - Complete MAFA documentation structure (default)"
        echo "  lenient  - Core structure with optional components"
        echo "  minimal  - Absolute minimum requirements"
        exit 0
        ;;
    --docs-dir)
        DOCS_DIR="$2"
        shift 2
        ;;
    --tolerance)
        TOLERANCE="$2"
        shift 2
        ;;
    --format)
        OUTPUT_FORMAT="$2"
        shift 2
        ;;
    --report)
        REPORT_FILE="$2"
        shift 2
        ;;
esac

# Validate tolerance level
if [[ "$TOLERANCE" != "strict" && "$TOLERANCE" != "lenient" && "$TOLERANCE" != "minimal" ]]; then
    log_error "Invalid tolerance level: $TOLERANCE (must be strict|lenient|minimal)"
    exit 1
fi

# Validate output format
if [[ "$OUTPUT_FORMAT" != "console" && "$OUTPUT_FORMAT" != "json" ]]; then
    log_error "Invalid output format: $OUTPUT_FORMAT (must be 'console' or 'json')"
    exit 1
fi

# Check for bc command for calculations
if ! command -v bc >/dev/null 2>&1; then
    log_warning "bc command not found - some calculations may be limited"
fi

# Run main function
main "$@"