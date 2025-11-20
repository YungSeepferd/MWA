#!/bin/bash

#==============================================================================
# MAFA Documentation Validation Script
# Comprehensive validation of all documentation files
#==============================================================================

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
DOCS_DIR="${DOCS_DIR:-docs}"
TEMPLATES_DIR="${TEMPLATES_DIR:-docs/templates}"
EXAMPLES_DIR="${EXAMPLES_DIR:-docs/examples}"
TEMP_DIR="${TEMP_DIR:-/tmp/mafa-docs-validate}"

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

# Cleanup function
cleanup() {
    log_info "Cleaning up temporary files..."
    rm -rf "$TEMP_DIR"
}

trap cleanup EXIT

# Create temporary directory
mkdir -p "$TEMP_DIR"

# Validation counters
TOTAL_ERRORS=0
TOTAL_WARNINGS=0

# Counters for different validation types
STRUCTURE_ERRORS=0
LINK_ERRORS=0
METADATA_ERRORS=0
CONTENT_ERRORS=0

#==============================================================================
# Validation Functions
#==============================================================================

validate_directory_structure() {
    log_info "Validating documentation directory structure..."
    
    local required_dirs=(
        "getting-started"
        "user-guide"
        "developer-guide"
        "architecture"
        "operations"
        "project"
    )
    
    local required_files=(
        "README.md"
        "getting-started/quick-start.md"
        "getting-started/installation.md"
        "getting-started/configuration.md"
        "user-guide/overview.md"
        "user-guide/dashboard.md"
        "user-guide/setup-wizard.md"
        "user-guide/troubleshooting.md"
        "developer-guide/contributing.md"
        "developer-guide/development-setup.md"
        "developer-guide/code-style.md"
        "architecture/system-overview.md"
        "operations/deployment.md"
        "operations/monitoring.md"
        "operations/backup-restore.md"
        "project/roadmap.md"
        "project/changelog.md"
        "project/release-notes.md"
    )
    
    # Check required directories
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$DOCS_DIR/$dir" ]]; then
            log_error "Missing required directory: $DOCS_DIR/$dir"
            ((STRUCTURE_ERRORS++))
            ((TOTAL_ERRORS++))
        fi
    done
    
    # Check required files
    for file in "${required_files[@]}"; do
        if [[ ! -f "$DOCS_DIR/$file" ]]; then
            log_warning "Missing recommended file: $DOCS_DIR/$file"
        fi
    done
    
    if [[ $STRUCTURE_ERRORS -eq 0 ]]; then
        log_success "Directory structure validation passed"
    else
        log_error "Directory structure validation failed with $STRUCTURE_ERRORS errors"
    fi
}

validate_markdown_files() {
    log_info "Validating markdown file structure..."
    
    local md_files=()
    while IFS= read -r -d '' file; do
        md_files+=("$file")
    done < <(find "$DOCS_DIR" -name "*.md" -type f -print0)
    
    log_info "Found ${#md_files[@]} markdown files to validate"
    
    for file in "${md_files[@]}"; do
        local relative_path="${file#$DOCS_DIR/}"
        
        # Check for proper heading structure
        if ! head -n 1 "$file" | grep -q "^# "; then
            log_error "Missing main heading in $relative_path"
            ((CONTENT_ERRORS++))
            ((TOTAL_ERRORS++))
        fi
        
        # Check for empty files
        if [[ ! -s "$file" ]]; then
            log_error "Empty file: $relative_path"
            ((CONTENT_ERRORS++))
            ((TOTAL_ERRORS++))
        fi
        
        # Check for trailing whitespace
        if grep -q '[[:space:]]$' "$file"; then
            log_warning "Trailing whitespace in $relative_path"
            ((TOTAL_WARNINGS++))
        fi
        
        # Check for proper line endings
        if file "$file" | grep -q "CRLF"; then
            log_warning "Windows line endings in $relative_path"
            ((TOTAL_WARNINGS++))
        fi
    done
    
    log_success "Markdown file validation completed"
}

validate_frontmatter() {
    log_info "Validating document frontmatter..."
    
    local md_files=()
    while IFS= read -r -d '' file; do
        md_files+=("$file")
    done < <(find "$DOCS_DIR" -name "*.md" -type f -print0)
    
    for file in "${md_files[@]}"; do
        local relative_path="${file#$DOCS_DIR/}"
        
        # Check if file has YAML frontmatter
        if head -n 5 "$file" | grep -q "^---"; then
            # Simple YAML syntax check using python
            if ! python3 -c "import yaml; yaml.safe_load(open('$file').read().split('---')[1].split('---')[0])" 2>/dev/null; then
                log_error "Invalid YAML frontmatter in $relative_path"
                ((METADATA_ERRORS++))
                ((TOTAL_ERRORS++))
            fi
        fi
    done
    
    log_success "Frontmatter validation completed"
}

validate_internal_links() {
    log_info "Validating internal documentation links..."
    
    local md_files=()
    while IFS= read -r -d '' file; do
        md_files+=("$file")
    done < <(find "$DOCS_DIR" -name "*.md" -type f -print0)
    
    local link_pattern='\[.*\]\(([^)]+)\)'
    
    for file in "${md_files[@]}"; do
        local relative_path="${file#$DOCS_DIR/}"
        local file_dir=$(dirname "$file")
        
        # Extract all markdown links
        while IFS= read -r link; do
            local link_target="${link#*[}"
            link_target="${link_target%]*)"
            link_target="${link_target#*]("}
            link_target="${link_target%)}"
            
            # Skip external links and anchor links
            if [[ "$link_target" =~ ^https?:// ]] || [[ "$link_target" =~ ^# ]] || [[ "$link_target" =~ ^mailto: ]]; then
                continue
            fi
            
            # Resolve relative path
            local resolved_path
            if [[ "$link_target" =~ ^/ ]]; then
                resolved_path="$DOCS_DIR${link_target#/}"
            else
                resolved_path="$file_dir/$link_target"
            fi
            
            # Check if target exists
            if [[ ! -e "$resolved_path" ]]; then
                log_error "Broken link in $relative_path: $link_target"
                ((LINK_ERRORS++))
                ((TOTAL_ERRORS++))
            fi
        done < <(grep -oP "$link_pattern" "$file" || true)
    done
    
    log_success "Internal link validation completed"
}

validate_consistency() {
    log_info "Validating cross-reference consistency..."
    
    local readme_file="$DOCS_DIR/README.md"
    
    if [[ -f "$readme_file" ]]; then
        # Check if all referenced files exist
        local reference_pattern='\]\(\./([^)]+)\)'
        
        while IFS= read -r ref; do
            local ref_path="${ref#](\./}"
            ref_path="${ref_path%)}"
            local full_path="$DOCS_DIR/$ref_path"
            
            if [[ ! -e "$full_path" ]]; then
                log_error "Reference in README.md points to non-existent file: $ref_path"
                ((STRUCTURE_ERRORS++))
                ((TOTAL_ERRORS++))
            fi
        done < <(grep -oP "$reference_pattern" "$readme_file" || true)
    fi
    
    log_success "Cross-reference consistency validation completed"
}

#==============================================================================
# Main Execution
#==============================================================================

main() {
    log_info "Starting comprehensive documentation validation..."
    log_info "Documentation directory: $DOCS_DIR"
    log_info "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    
    # Run all validation functions
    validate_directory_structure
    validate_markdown_files
    validate_frontmatter
    validate_internal_links
    validate_consistency
    
    # Print summary
    echo
    log_info "=== VALIDATION SUMMARY ==="
    log_info "Total Errors: $TOTAL_ERRORS"
    log_info "Total Warnings: $TOTAL_WARNINGS"
    log_info "Structure Errors: $STRUCTURE_ERRORS"
    log_info "Link Errors: $LINK_ERRORS"
    log_info "Metadata Errors: $METADATA_ERRORS"
    log_info "Content Errors: $CONTENT_ERRORS"
    
    if [[ $TOTAL_ERRORS -eq 0 ]]; then
        log_success "✅ All documentation validation checks passed!"
        exit 0
    else
        log_error "❌ Documentation validation failed with $TOTAL_ERRORS errors"
        exit 1
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "MAFA Documentation Validation Script"
        echo
        echo "Usage: $0 [OPTIONS]"
        echo
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --docs-dir DIR      Set documentation directory (default: docs)"
        echo "  --templates-dir DIR Set templates directory (default: docs/templates)"
        echo "  --examples-dir DIR  Set examples directory (default: docs/examples)"
        echo "  --temp-dir DIR      Set temporary directory (default: /tmp/mafa-docs-validate)"
        echo
        echo "Environment Variables:"
        echo "  DOCS_DIR           Documentation directory path"
        echo "  TEMPLATES_DIR      Templates directory path"
        echo "  EXAMPLES_DIR       Examples directory path"
        echo "  TEMP_DIR           Temporary directory path"
        exit 0
        ;;
    --docs-dir)
        DOCS_DIR="$2"
        shift 2
        ;;
    --templates-dir)
        TEMPLATES_DIR="$2"
        shift 2
        ;;
    --examples-dir)
        EXAMPLES_DIR="$2"
        shift 2
        ;;
    --temp-dir)
        TEMP_DIR="$2"
        shift 2
        ;;
esac

# Run main function
main "$@"