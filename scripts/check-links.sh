#!/bin/bash

#==============================================================================
# MAFA Documentation Link Checker
# Validates all internal and external links in documentation
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
OUTPUT_FORMAT="${OUTPUT_FORMAT:-console}"
REPORT_FILE="${REPORT_FILE:-/tmp/mafa-link-report.json}"
MAX_EXTERNAL_RETRIES="${MAX_EXTERNAL_RETRIES:-3}"
EXTERNAL_TIMEOUT="${EXTERNAL_TIMEOUT:-10}"

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

# JSON output functions
json_start() {
    cat <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "docs_directory": "$DOCS_DIR",
  "summary": {
    "total_links": 0,
    "valid_links": 0,
    "broken_links": 0,
    "warnings": 0
  },
  "results": []
}
EOF
}

json_add_link() {
    local status="$1"
    local file="$2"
    local line="$3"
    local link="$4"
    local type="$5"
    local target="$6"
    local error_msg="${7:-}"
    
    cat <<EOF
  {
    "status": "$status",
    "file": "$file",
    "line": $line,
    "link": "$link",
    "type": "$type",
    "target": "$target",
    "error": "$error_msg"
  }
EOF
}

# Initialize counters
TOTAL_LINKS=0
VALID_LINKS=0
BROKEN_LINKS=0
WARNINGS=0

#==============================================================================
# Link Validation Functions
#==============================================================================

check_internal_link() {
    local file="$1"
    local link="$2"
    local line_num="$3"
    local relative_file="${file#$DOCS_DIR/}"
    
    ((TOTAL_LINKS++))
    
    # Skip anchor links
    if [[ "$link" =~ ^# ]]; then
        ((VALID_LINKS++))
        return 0
    fi
    
    # Skip external links in internal check
    if [[ "$link" =~ ^https?:// ]] || [[ "$link" =~ ^mailto: ]]; then
        ((VALID_LINKS++))
        return 0
    fi
    
    # Resolve relative path
    local file_dir=$(dirname "$file")
    local resolved_path
    
    if [[ "$link" =~ ^/ ]]; then
        resolved_path="$DOCS_DIR${link#/}"
    else
        resolved_path="$file_dir/$link"
    fi
    
    # Check if target exists
    if [[ -e "$resolved_path" ]]; then
        ((VALID_LINKS++))
        
        if [[ "$OUTPUT_FORMAT" == "json" ]]; then
            json_add_link "valid" "$relative_file" "$line_num" "$link" "internal" "$resolved_path"
        else
            log_success "✓ Internal link OK: $relative_file:$line_num -> $resolved_path"
        fi
    else
        ((BROKEN_LINKS++))
        
        if [[ "$OUTPUT_FORMAT" == "json" ]]; then
            json_add_link "broken" "$relative_file" "$line_num" "$link" "internal" "$resolved_path" "File not found"
        else
            log_error "✗ Broken internal link: $relative_file:$line_num -> $resolved_path"
        fi
    fi
}

check_external_link() {
    local file="$1"
    local link="$2"
    local line_num="$3"
    local relative_file="${file#$DOCS_DIR/}"
    
    ((TOTAL_LINKS++))
    
    # Skip if not an external link
    if [[ ! "$link" =~ ^https?:// ]]; then
        return 0
    fi
    
    # Check external link with timeout and retries
    local retries=0
    local success=false
    
    while [[ $retries -lt $MAX_EXTERNAL_RETRIES ]] && [[ "$success" == "false" ]]; do
        if curl -f -s --max-time "$EXTERNAL_TIMEOUT" --retry 0 "$link" >/dev/null 2>&1; then
            success=true
            break
        fi
        ((retries++))
        sleep 1
    done
    
    if [[ "$success" == "true" ]]; then
        ((VALID_LINKS++))
        
        if [[ "$OUTPUT_FORMAT" == "json" ]]; then
            json_add_link "valid" "$relative_file" "$line_num" "$link" "external" "$link"
        else
            log_success "✓ External link OK: $relative_file:$line_num -> $link"
        fi
    else
        ((BROKEN_LINKS++))
        
        if [[ "$OUTPUT_FORMAT" == "json" ]]; then
            json_add_link "broken" "$relative_file" "$line_num" "$link" "external" "$link" "Connection failed after $MAX_EXTERNAL_RETRIES retries"
        else
            log_error "✗ Broken external link: $relative_file:$line_num -> $link"
        fi
    fi
}

check_anchor_links() {
    local file="$1"
    local line_num="$2"
    local link="$3"
    local relative_file="${file#$DOCS_DIR/}"
    
    if [[ "$link" =~ ^#(.+)$ ]]; then
        local anchor="${BASH_REMATCH[1]}"
        
        # Check if anchor exists in the file
        if grep -q "^${anchor//[-\/]/\\$&}" "$file" 2>/dev/null || \
           grep -q "^#.*$anchor" "$file" 2>/dev/null; then
            ((VALID_LINKS++))
            
            if [[ "$OUTPUT_FORMAT" == "console" ]]; then
                log_success "✓ Anchor link OK: $relative_file:$line_num -> #$anchor"
            fi
        else
            ((WARNINGS++))
            
            if [[ "$OUTPUT_FORMAT" == "json" ]]; then
                json_add_link "warning" "$relative_file" "$line_num" "$link" "anchor" "$link" "Anchor not found in file"
            else
                log_warning "⚠ Anchor not found: $relative_file:$line_num -> #$anchor"
            fi
        fi
    fi
}

#==============================================================================
# Main Processing Functions
#==============================================================================

process_markdown_file() {
    local file="$1"
    
    log_info "Processing: ${file#$DOCS_DIR/}"
    
    # Find all markdown links
    local line_num=1
    while IFS= read -r line; do
        # Extract markdown links [text](url)
        while IFS= read -r link_match; do
            local link_text="${link_match#*[}"
            link_text="${link_text%]*)"
            link_text="${link_text#]*(}"
            link_text="${link_text%)}"
            
            # Determine link type and validate
            if [[ "$link_text" =~ ^https?:// ]] || [[ "$link_text" =~ ^mailto: ]]; then
                check_external_link "$file" "$link_text" "$line_num"
            elif [[ "$link_text" =~ ^# ]]; then
                check_anchor_links "$file" "$line_num" "$link_text"
            else
                check_internal_link "$file" "$link_text" "$line_num"
            fi
        done < <(grep -oP '\[.*?\]\(\s*[^)]+\s*\)' "$line" | sed 's/\[//; s/\]//' || true)
        
        ((line_num++))
    done < "$file"
}

generate_report() {
    local report_type="$1"
    
    case "$report_type" in
        json)
            echo "," >> "$REPORT_FILE"
            echo "  \"summary\": {" >> "$REPORT_FILE"
            echo "    \"total_links\": $TOTAL_LINKS," >> "$REPORT_FILE"
            echo "    \"valid_links\": $VALID_LINKS," >> "$REPORT_FILE"
            echo "    \"broken_links\": $BROKEN_LINKS," >> "$REPORT_FILE"
            echo "    \"warnings\": $WARNINGS" >> "$REPORT_FILE"
            echo "  }" >> "$REPORT_FILE"
            echo "}" >> "$REPORT_FILE"
            ;;
        console|*)
            echo
            log_info "=== LINK VALIDATION SUMMARY ==="
            log_info "Total Links Checked: $TOTAL_LINKS"
            log_success "Valid Links: $VALID_LINKS"
            log_error "Broken Links: $BROKEN_LINKS"
            log_warning "Warnings: $WARNINGS"
            
            if [[ $BROKEN_LINKS -gt 0 ]]; then
                echo
                log_error "❌ Found $BROKEN_LINKS broken links"
                return 1
            else
                echo
                log_success "✅ All links are valid!"
                return 0
            fi
            ;;
    esac
}

#==============================================================================
# Main Execution
#==============================================================================

main() {
    log_info "Starting link validation for documentation..."
    log_info "Documentation directory: $DOCS_DIR"
    log_info "Output format: $OUTPUT_FORMAT"
    log_info "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    
    # Initialize JSON output if requested
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        json_start > "$REPORT_FILE"
    fi
    
    # Process all markdown files
    local md_files=()
    while IFS= read -r -d '' file; do
        md_files+=("$file")
    done < <(find "$DOCS_DIR" -name "*.md" -type f -print0)
    
    log_info "Found ${#md_files[@]} markdown files to process"
    
    local first=true
    for file in "${md_files[@]}"; do
        if [[ "$OUTPUT_FORMAT" == "json" && "$first" == "false" ]]; then
            echo "," >> "$REPORT_FILE"
        fi
        first=false
        
        process_markdown_file "$file"
    done
    
    # Generate final report
    generate_report "$OUTPUT_FORMAT"
    
    # Save JSON report if created
    if [[ "$OUTPUT_FORMAT" == "json" ]]; then
        log_info "JSON report saved to: $REPORT_FILE"
    fi
    
    # Return appropriate exit code
    if [[ $BROKEN_LINKS -gt 0 ]]; then
        exit 1
    else
        exit 0
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "MAFA Documentation Link Checker"
        echo
        echo "Usage: $0 [OPTIONS]"
        echo
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --docs-dir DIR      Set documentation directory (default: docs)"
        echo "  --format FORMAT     Output format: console|json (default: console)"
        echo "  --report FILE       JSON report file path (default: /tmp/mafa-link-report.json)"
        echo "  --timeout SECONDS   External link timeout (default: 10)"
        echo "  --retries COUNT     External link retry count (default: 3)"
        echo
        echo "Environment Variables:"
        echo "  DOCS_DIR            Documentation directory path"
        echo "  OUTPUT_FORMAT       Output format: console|json"
        echo "  REPORT_FILE         JSON report file path"
        echo "  MAX_EXTERNAL_RETRIES Number of retries for external links"
        echo "  EXTERNAL_TIMEOUT    Timeout for external link checks"
        exit 0
        ;;
    --docs-dir)
        DOCS_DIR="$2"
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
    --timeout)
        EXTERNAL_TIMEOUT="$2"
        shift 2
        ;;
    --retries)
        MAX_EXTERNAL_RETRIES="$2"
        shift 2
        ;;
esac

# Validate output format
if [[ "$OUTPUT_FORMAT" != "console" && "$OUTPUT_FORMAT" != "json" ]]; then
    log_error "Invalid output format: $OUTPUT_FORMAT (must be 'console' or 'json')"
    exit 1
fi

# Run main function
main "$@"