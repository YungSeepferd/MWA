#!/bin/bash

#==============================================================================
# MAFA Documentation Metadata Validator
# Validates document frontmatter, metadata consistency, and formatting standards
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
TEMPLATES_DIR="${TEMPLATES_DIR:-docs/templates}"
EXAMPLES_DIR="${EXAMPLES_DIR:-docs/examples}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-console}"
REPORT_FILE="${REPORT_FILE:-/tmp/mafa-metadata-report.json}"
AUTO_FIX="${AUTO_FIX:-false}"
STRICT_MODE="${STRICT_MODE:-true}"

# Metadata validation standards
VALID_CATEGORIES=("getting-started" "user-guide" "developer-guide" "architecture" "operations" "project")
VALID_TYPES=("guide" "reference" "tutorial" "api" "troubleshooting" "overview" "setup" "configuration")
VALID_AUDIENCES=("new-user" "user" "developer" "operator" "admin" "contributor")

# Validation counters
TOTAL_FILES=0
VALID_FILES=0
INVALID_FILES=0
WARNING_FILES=0
FIXED_FILES=0

# Issue tracking
declare -A ISSUE_COUNTS
ISSUE_COUNTS=(
    ["missing-frontmatter"]=0
    ["invalid-yaml"]=0
    ["missing-required-fields"]=0
    ["invalid-category"]=0
    ["invalid-type"]=0
    ["missing-title"]=0
    ["invalid-date-format"]=0
    ["missing-authors"]=0
    ["invalid-tags"]=0
    ["consistency-issues"]=0
)

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
    echo -e "${PURPLE}[METADATA]${NC} $1"
}

#==============================================================================
# Metadata Standard Templates
#==============================================================================

get_standard_frontmatter() {
    local category="$1"
    local doc_type="$2"
    local title="$3"
    local description="$4"
    local audience="$5"
    
    cat <<EOF
---
title: "$title"
description: "$description"
category: "$category"
type: "$doc_type"
audience: "$audience"
version: "1.0.0"
last_updated: "$(date +%Y-%m-%d)"
authors:
  - name: "MAFA Documentation Team"
    email: "docs@mafa.example.com"
tags:
  - "$category"
  - "$doc_type"
  - "$audience"
review_status: "draft"
review_date: "$(date +%Y-%m-%d)"
EOF
}

#==============================================================================
# Validation Functions
#==============================================================================

validate_yaml_syntax() {
    local file="$1"
    local relative_file="${file#$DOCS_DIR/}"
    
    # Check if file has frontmatter
    if ! head -n 5 "$file" | grep -q "^---"; then
        log_warning "No frontmatter found in: $relative_file"
        ((ISSUE_COUNTS["missing-frontmatter"]++))
        return 1
    fi
    
    # Extract frontmatter for validation
    local frontmatter=""
    local in_frontmatter=false
    
    while IFS= read -r line; do
        if [[ "$line" == "---" ]]; then
            if [[ "$in_frontmatter" == "false" ]]; then
                in_frontmatter=true
            else
                break
            fi
        elif [[ "$in_frontmatter" == "true" ]]; then
            frontmatter="${frontmatter}${line}\n"
        fi
    done < "$file"
    
    # Validate YAML syntax using Python
    if ! python3 -c "
import yaml
import sys
try:
    yaml.safe_load('''$frontmatter''')
    sys.exit(0)
except Exception as e:
    print(f'YAML validation error: {e}')
    sys.exit(1)
" 2>/dev/null; then
        log_error "Invalid YAML syntax in: $relative_file"
        ((ISSUE_COUNTS["invalid-yaml"]++))
        return 1
    fi
    
    return 0
}

validate_required_fields() {
    local file="$1"
    local relative_file="${file#$DOCS_DIR/}"
    
    # Required fields for documentation
    local required_fields=("title" "description" "category" "type")
    local missing_fields=()
    
    for field in "${required_fields[@]}"; do
        if ! grep -q "^${field}:" "$file"; then
            missing_fields+=("$field")
        fi
    done
    
    if [[ ${#missing_fields[@]} -gt 0 ]]; then
        log_error "Missing required fields in $relative_file: ${missing_fields[*]}"
        ((ISSUE_COUNTS["missing-required-fields"]++))
        return 1
    fi
    
    return 0
}

validate_field_values() {
    local file="$1"
    local relative_file="${file#$DOCS_DIR/}"
    
    # Validate category
    local category=$(grep "^category:" "$file" | cut -d: -f2- | tr -d ' "' || echo "")
    if [[ -n "$category" && ! " ${VALID_CATEGORIES[@]} " =~ " ${category} " ]]; then
        log_error "Invalid category in $relative_file: '$category' (valid: ${VALID_CATEGORIES[*]})"
        ((ISSUE_COUNTS["invalid-category"]++))
    fi
    
    # Validate type
    local doc_type=$(grep "^type:" "$file" | cut -d: -f2- | tr -d ' "' || echo "")
    if [[ -n "$doc_type" && ! " ${VALID_TYPES[@]} " =~ " ${doc_type} " ]]; then
        log_error "Invalid type in $relative_file: '$doc_type' (valid: ${VALID_TYPES[*]})"
        ((ISSUE_COUNTS["invalid-type"]++))
    fi
    
    # Validate audience
    local audience=$(grep "^audience:" "$file" | cut -d: -f2- | tr -d ' "' || echo "")
    if [[ -n "$audience" && ! " ${VALID_AUDIENCES[@]} " =~ " ${audience} " ]]; then
        log_warning "Invalid audience in $relative_file: '$audience' (valid: ${VALID_AUDIENCES[*]})"
        ((ISSUE_COUNTS["invalid-tags"]++))
    fi
    
    # Validate date format
    local last_updated=$(grep "^last_updated:" "$file" | cut -d: -f2- | tr -d ' "' || echo "")
    if [[ -n "$last_updated" && ! "$last_updated" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        log_error "Invalid date format in $relative_file: '$last_updated' (should be YYYY-MM-DD)"
        ((ISSUE_COUNTS["invalid-date-format"]++))
    fi
    
    # Check for authors
    if ! grep -q "^authors:" "$file"; then
        log_warning "Missing authors field in $relative_file"
        ((ISSUE_COUNTS["missing-authors"]++))
    fi
    
    # Validate tags format
    if grep -q "^tags:" "$file"; then
        local tags_line=$(grep "^tags:" "$file")
        if [[ ! "$tags_line" =~ ^tags:\ *$ ]]; then
            # Check if tags are properly formatted as array
            if ! echo "$tags_line" | grep -q "^\-"; then
                log_warning "Tags should be formatted as array in $relative_file"
                ((ISSUE_COUNTS["invalid-tags"]++))
            fi
        fi
    fi
}

validate_title_consistency() {
    local file="$1"
    local relative_file="${file#$DOCS_DIR/}"
    
    # Extract title from frontmatter
    local frontmatter_title=""
    if grep -q "^title:" "$file"; then
        frontmatter_title=$(grep "^title:" "$file" | cut -d: -f2- | tr -d ' "')
    fi
    
    # Extract first heading
    local heading_title=""
    if grep -q "^# " "$file"; then
        heading_title=$(grep "^# " "$file" | sed 's/^# *//' | tr -d '\r')
    fi
    
    # Check consistency
    if [[ -n "$frontmatter_title" && -n "$heading_title" ]]; then
        # Remove common prefixes/suffixes for comparison
        local fm_clean=$(echo "$frontmatter_title" | sed 's/^MAFA *//' | sed 's/ *documentation$//')
        local heading_clean=$(echo "$heading_title" | sed 's/^MAFA *//' | sed 's/ *documentation$//')
        
        if [[ "$fm_clean" != "$heading_clean" ]]; then
            log_warning "Title mismatch in $relative_file:"
            log_warning "  Frontmatter: '$frontmatter_title'"
            log_warning "  Heading: '$heading_title'"
            ((ISSUE_COUNTS["consistency-issues"]++))
        fi
    elif [[ -n "$frontmatter_title" && -z "$heading_title" ]]; then
        log_warning "Missing heading title in $relative_file (has frontmatter title)"
        ((ISSUE_COUNTS["missing-title"]++))
    elif [[ -z "$frontmatter_title" && -n "$heading_title" ]]; then
        log_warning "Missing frontmatter title in $relative_file (has heading title)"
        ((ISSUE_COUNTS["missing-title"]++))
    fi
}

validate_file_metadata() {
    local file="$1"
    local relative_file="${file#$DOCS_DIR/}"
    
    ((TOTAL_FILES++))
    
    log_purple "Validating metadata: $relative_file"
    
    local has_errors=false
    local has_warnings=false
    
    # Validate YAML syntax
    if ! validate_yaml_syntax "$file"; then
        has_errors=true
    fi
    
    # Validate required fields (only if YAML is valid)
    if [[ "$has_errors" != "true" ]]; then
        if ! validate_required_fields "$file"; then
            has_errors=true
        fi
    fi
    
    # Validate field values
    if [[ "$has_errors" != "true" ]]; then
        validate_field_values "$file"
    fi
    
    # Validate title consistency
    validate_title_consistency "$file"
    
    # Determine overall status
    if [[ "$has_errors" == "true" ]]; then
        ((INVALID_FILES++))
        return 1
    elif [[ "$has_warnings" == "true" ]]; then
        ((WARNING_FILES++))
    else
        ((VALID_FILES++))
    fi
    
    return 0
}

#==============================================================================
# Auto-fix Functions
#==============================================================================

add_missing_frontmatter() {
    local file="$1"
    local relative_file="${file#$DOCS_DIR/}"
    
    # Extract information from filename and content
    local filename=$(basename "$file" .md)
    local first_heading=""
    if grep -q "^# " "$file"; then
        first_heading=$(grep "^# " "$file" | sed 's/^# *//' | tr -d '\r')
    fi
    
    # Determine category from file path
    local category="general"
    if [[ "$file" =~ /getting-started/ ]]; then
        category="getting-started"
    elif [[ "$file" =~ /user-guide/ ]]; then
        category="user-guide"
    elif [[ "$file" =~ /developer-guide/ ]]; then
        category="developer-guide"
    elif [[ "$file" =~ /architecture/ ]]; then
        category="architecture"
    elif [[ "$file" =~ /operations/ ]]; then
        category="operations"
    elif [[ "$file" =~ /project/ ]]; then
        category="project"
    fi
    
    # Determine document type
    local doc_type="guide"
    case "$filename" in
        *"install"*|*"setup"*|*"configuration"*) doc_type="setup" ;;
        *"api"*|*"reference"*) doc_type="api" ;;
        *"troubleshoot"*|*"faq"*) doc_type="troubleshooting" ;;
        *"overview"*|*"intro"*) doc_type="overview" ;;
        *"tutorial"*|*"how-to"*) doc_type="tutorial" ;;
    esac
    
    # Determine audience
    local audience="user"
    case "$category" in
        "getting-started") audience="new-user" ;;
        "developer-guide") audience="developer" ;;
        "operations") audience="operator" ;;
        "project") audience="contributor" ;;
    esac
    
    # Generate description
    local description="${first_heading:-Documentation for $filename}"
    description="${description^}"
    
    # Create frontmatter
    local frontmatter=$(get_standard_frontmatter "$category" "$doc_type" "$first_heading" "$description" "$audience")
    
    # Insert frontmatter at the beginning of the file
    local content=""
    while IFS= read -r line; do
        if [[ "$line" != "---" && -z "$content" ]]; then
            # First non-frontmatter line, add frontmatter before it
            content="${frontmatter}\n---\n\n${line}"
        elif [[ -z "$content" ]]; then
            # Still in frontmatter or empty lines before content
            continue
        else
            content="${content}\n${line}"
        fi
    done < "$file"
    
    if [[ -z "$content" ]]; then
        content="${frontmatter}\n---\n\n$(cat "$file")"
    fi
    
    echo -e "$content" > "$file"
    log_success "Added frontmatter to: $relative_file"
    ((FIXED_FILES++))
}

fix_metadata_issues() {
    local file="$1"
    local relative_file="${file#$DOCS_DIR/}"
    
    local fixes_applied=false
    
    # Fix invalid category
    if grep -q "category:" "$file"; then
        local category=$(grep "^category:" "$file" | cut -d: -f2- | tr -d ' "' || echo "")
        if [[ -n "$category" && ! " ${VALID_CATEGORIES[@]} " =~ " ${category} " ]]; then
            # Try to map common variations
            local fixed_category="$category"
            case "$category" in
                "getting"*) fixed_category="getting-started" ;;
                "user") fixed_category="user-guide" ;;
                "dev"|"developer") fixed_category="developer-guide" ;;
                "arch"|"architecture") fixed_category="architecture" ;;
                "ops"|"operations"|"operational") fixed_category="operations" ;;
                "proj"|"project") fixed_category="project" ;;
            esac
            
            if [[ "$fixed_category" != "$category" ]]; then
                sed -i.bak "s/^category: $category/category: $fixed_category/" "$file"
                log_success "Fixed category in $relative_file: $category -> $fixed_category"
                ((FIXED_FILES++))
                fixes_applied=true
            fi
        fi
    fi
    
    # Fix date format
    if grep -q "last_updated:" "$file"; then
        local last_updated=$(grep "^last_updated:" "$file" | cut -d: -f2- | tr -d ' "' || echo "")
        if [[ -n "$last_updated" && ! "$last_updated" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
            local fixed_date=$(date -j -f "%a %b %d %H:%M:%S %Z %Y" "$last_updated" +"%Y-%m-%d" 2>/dev/null || date +"%Y-%m-%d")
            sed -i.bak "s/^last_updated: $last_updated/last_updated: $fixed_date/" "$file"
            log_success "Fixed date format in $relative_file: $last_updated -> $fixed_date"
            ((FIXED_FILES++))
            fixes_applied=true
        fi
    fi
    
    # Add missing authors if none exist
    if ! grep -q "^authors:" "$file"; then
        local insert_line=$(grep -n "^---" "$file" | head -n 1 | cut -d: -f1)
        if [[ -n "$insert_line" ]]; then
            ((insert_line++))
            sed -i.bak "${insert_line}i\\
authors:\\n  - name: \\"MAFA Documentation Team\\"\\
    email: \\"docs@mafa.example.com\\"" "$file"
            log_success "Added authors to: $relative_file"
            ((FIXED_FILES++))
            fixes_applied=true
        fi
    fi
    
    if [[ "$fixes_applied" == "true" ]]; then
        rm -f "${file}.bak"
    fi
}

#==============================================================================
# Report Generation Functions
#==============================================================================

generate_json_report() {
    cat > "$REPORT_FILE" <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "docs_directory": "$DOCS_DIR",
  "auto_fix": $AUTO_FIX,
  "strict_mode": $STRICT_MODE,
  "summary": {
    "total_files": $TOTAL_FILES,
    "valid_files": $VALID_FILES,
    "invalid_files": $INVALID_FILES,
    "warning_files": $WARNING_FILES,
    "fixed_files": $FIXED_FILES
  },
  "issue_breakdown": {
    "missing_frontmatter": ${ISSUE_COUNTS["missing-frontmatter"]},
    "invalid_yaml": ${ISSUE_COUNTS["invalid-yaml"]},
    "missing_required_fields": ${ISSUE_COUNTS["missing-required-fields"]},
    "invalid_category": ${ISSUE_COUNTS["invalid-category"]},
    "invalid_type": ${ISSUE_COUNTS["invalid-type"]},
    "missing_title": ${ISSUE_COUNTS["missing-title"]},
    "invalid_date_format": ${ISSUE_COUNTS["invalid-date-format"]},
    "missing_authors": ${ISSUE_COUNTS["missing-authors"]},
    "invalid_tags": ${ISSUE_COUNTS["invalid-tags"]},
    "consistency_issues": ${ISSUE_COUNTS["consistency-issues"]}
  },
  "standards": {
    "valid_categories": $(printf '"%s",' "${VALID_CATEGORIES[@]}" | sed 's/,$//'),
    "valid_types": $(printf '"%s",' "${VALID_TYPES[@]}" | sed 's/,$//'),
    "valid_audiences": $(printf '"%s",' "${VALID_AUDIENCES[@]}" | sed 's/,$//')
  }
}
EOF
}

generate_console_report() {
    echo
    log_info "=== METADATA VALIDATION SUMMARY ==="
    log_info "Total Files Processed: $TOTAL_FILES"
    log_success "Valid Files: $VALID_FILES"
    log_error "Invalid Files: $INVALID_FILES"
    log_warning "Files with Warnings: $WARNING_FILES"
    log_info "Files Fixed: $FIXED_FILES"
    echo
    
    if [[ ${#ISSUE_COUNTS[@]} -gt 0 ]]; then
        log_info "Issue Breakdown:"
        for issue_type in "${!ISSUE_COUNTS[@]}"; do
            local count=${ISSUE_COUNTS[$issue_type]}
            if [[ $count -gt 0 ]]; then
                log_info "  ${issue_type//_/ }: $count"
            fi
        done
        echo
    fi
    
    log_info "Standards Reference:"
    log_info "  Valid Categories: ${VALID_CATEGORIES[*]}"
    log_info "  Valid Types: ${VALID_TYPES[*]}"
    echo
    
    if [[ $INVALID_FILES -eq 0 ]]; then
        log_success "✅ All files have valid metadata!"
        return 0
    else
        log_error "❌ $INVALID_FILES files have metadata issues"
        if [[ $FIXED_FILES -gt 0 ]]; then
            log_info "Fixed $FIXED_FILES issues automatically"
        fi
        return 1
    fi
}

#==============================================================================
# Main Execution
#==============================================================================

main() {
    log_info "Starting documentation metadata validation..."
    log_info "Documentation directory: $DOCS_DIR"
    log_info "Auto-fix mode: $AUTO_FIX"
    log_info "Strict mode: $STRICT_MODE"
    log_info "Output format: $OUTPUT_FORMAT"
    log_info "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    
    # Process all markdown files
    local md_files=()
    while IFS= read -r -d '' file; do
        md_files+=("$file")
    done < <(find "$DOCS_DIR" -name "*.md" -type f -print0)
    
    log_info "Found ${#md_files[@]} markdown files to validate"
    
    for file in "${md_files[@]}"; do
        if validate_file_metadata "$file"; then
            # File is valid, but check if we can auto-fix minor issues
            if [[ "$AUTO_FIX" == "true" ]]; then
                fix_metadata_issues "$file"
            fi
        else
            # File has errors, try to add missing frontmatter
            if [[ "$AUTO_FIX" == "true" ]]; then
                add_missing_frontmatter "$file"
            fi
        fi
    done
    
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
    if [[ $INVALID_FILES -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "MAFA Documentation Metadata Validator"
        echo
        echo "Usage: $0 [OPTIONS]"
        echo
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --docs-dir DIR      Set documentation directory (default: docs)"
        echo "  --auto-fix          Enable automatic fixing of metadata issues"
        echo "  --strict            Enable strict validation mode"
        echo "  --format FORMAT     Output format: console|json (default: console)"
        echo "  --report FILE       JSON report file path (default: /tmp/mafa-metadata-report.json)"
        echo
        echo "Environment Variables:"
        echo "  DOCS_DIR            Documentation directory path"
        echo "  AUTO_FIX            Enable auto-fix mode: true|false"
        echo "  STRICT_MODE         Enable strict validation: true|false"
        echo "  OUTPUT_FORMAT       Output format: console|json"
        echo "  REPORT_FILE         JSON report file path"
        echo
        echo "Standards:"
        echo "  Categories: ${VALID_CATEGORIES[*]}"
        echo "  Types: ${VALID_TYPES[*]}"
        echo "  Audiences: ${VALID_AUDIENCES[*]}"
        exit 0
        ;;
    --docs-dir)
        DOCS_DIR="$2"
        shift 2
        ;;
    --auto-fix)
        AUTO_FIX="true"
        shift
        ;;
    --strict)
        STRICT_MODE="true"
        shift
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

# Validate output format
if [[ "$OUTPUT_FORMAT" != "console" && "$OUTPUT_FORMAT" != "json" ]]; then
    log_error "Invalid output format: $OUTPUT_FORMAT (must be 'console' or 'json')"
    exit 1
fi

# Check for required tools
if ! command -v python3 >/dev/null 2>&1; then
    log_error "Python 3 is required for YAML validation"
    exit 1
fi

# Run main function
main "$@"