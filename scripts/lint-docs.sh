#!/bin/bash

#==============================================================================
# MAFA Documentation Linter
# Markdown linting and formatting validation for documentation
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
RULES_FILE="${RULES_FILE:-.markdownlint.json}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-console}"
REPORT_FILE="${REPORT_FILE:-/tmp/mafa-lint-report.json}"
AUTO_FIX="${AUTO_FIX:-false}"
STRICT_MODE="${STRICT_MODE:-true}"

# Linting tools configuration
MARKDOWNLINT_CONFIG="${MARKDOWNLINT_CONFIG:-$RULES_FILE}"

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
    echo -e "${PURPLE}[LINT]${NC} $1"
}

# Validation counters
TOTAL_FILES=0
VALID_FILES=0
INVALID_FILES=0
WARNING_FILES=0
TOTAL_ISSUES=0
FIXED_ISSUES=0

# Issue tracking
declare -A ISSUE_COUNTS
ISSUE_COUNTS=(
    ["heading"]=0
    ["link"]=0
    ["code"]=0
    ["formatting"]=0
    ["structure"]=0
    ["style"]=0
)

#==============================================================================
# Initialization Functions
#==============================================================================

create_default_markdownlint_config() {
    local config_file="$1"
    
    if [[ ! -f "$config_file" ]]; then
        log_info "Creating default markdownlint configuration: $config_file"
        
        cat > "$config_file" <<'EOF'
{
  "default": true,
  "MD013": {
    "line_length": 120,
    "heading_line_length": 80,
    "code_block_line_length": 120,
    "stern": false
  },
  "MD004": {
    "style": "dash"
  },
  "MD007": {
    "indent": 2
  },
  "MD009": {
    "br_spaces": 2
  },
  "MD010": {
    "code_blocks": true
  },
  "MD012": {
    "maximum": 1
  },
  "MD024": {
    "allow_different_nesting": true
  },
  "MD025": {
    "level": 1,
    "front_matter_title": ""
  },
  "MD026": {
    "punctuation": ".,;:!?"
  },
  "MD029": {
    "style": "ordered"
  },
  "MD030": {
    "ul_single": 1,
    "ol_single": 1,
    "ul_multi": 3,
    "ol_multi": 2
  },
  "MD031": {
    "list_items": true
  },
  "MD033": {
    "allowed_elements": ["img", "br", "hr", "span"]
  },
  "MD034": {
    "allow_bare_html": false
  },
  "MD035": {
    "style": "dash"
  },
  "MD036": {
    "emphasis_mark": "_",
    "strong_mark": "**"
  },
  "MD037": {
    "space_inside": false
  },
  "MD038": {
    "space_after": false
  },
  "MD039": {
    "space_after_links": false
  },
  "MD040": {
    "fenced_code_language": true
  },
  "MD041": {
    "level": 1,
    "front_matter_title": ""
  },
  "MD042": {
    "ignored_terms": ["TBD", "TODO"]
  },
  "MD043": {
    "headings": false
  },
  "MD044": {
    "proper_names": [],
    "code_blocks": false
  },
  "MD045": {
    "allow_images": false
  },
  "MD046": {
    "code_block_style": "fenced"
  },
  "MD047": {
    "single_trailing_newline": true
  },
  "MD048": {
    "code_fence_style": "backtick"
  },
  "MD049": {
    "emphasis_style": "_"
  },
  "MD050": {
    "strong_style": "**"
  },
  "MD051": {
    "link_length": "inflated"
  },
  "MD052": {
    "link_reference_style": "full"
  },
  "MD053": {
    "link_reference_definition": false
  }
}
EOF
    fi
}

create_mafa_specific_config() {
    local config_file="$DOCS_DIR/.markdownlint.json"
    
    if [[ ! -f "$config_file" ]]; then
        log_info "Creating MAFA-specific markdownlint configuration"
        
        cat > "$config_file" <<'EOF'
{
  "default": true,
  "MD013": {
    "line_length": 120,
    "heading_line_length": 80,
    "code_block_line_length": 120
  },
  "MD024": {
    "allow_different_nesting": true
  },
  "MD025": false,
  "MD033": {
    "allowed_elements": ["img", "br", "hr", "span", "details", "summary"]
  },
  "MD042": {
    "ignored_terms": ["TBD", "TODO", "MAFA", "API", "UI", "UX"]
  },
  "MD044": {
    "proper_names": ["MAFA", "MüncheWohnungsAssistent", "ImmoScout", "WG-Gesucht", "Discord", "Telegram"],
    "code_blocks": false
  },
  "MD047": {
    "single_trailing_newline": true
  },
  "MD048": {
    "code_fence_style": "backtick"
  }
}
EOF
    fi
}

#==============================================================================
# Validation Functions
#==============================================================================

validate_basic_markdown_syntax() {
    local file="$1"
    local relative_file="${file#$DOCS_DIR/}"
    
    ((TOTAL_FILES++))
    
    # Check for basic syntax errors
    local syntax_errors=0
    
    # Unclosed code blocks
    if grep -q '```' "$file"; then
        local open_blocks=$(grep -c '^```' "$file" || true)
        if [[ $((open_blocks % 2)) -ne 0 ]]; then
            log_error "Unclosed code block in: $relative_file"
            ((syntax_errors++))
            ((TOTAL_ISSUES++))
            ((ISSUE_COUNTS["code"]++))
        fi
    fi
    
    # Unclosed emphasis markers
    local emphasis_errors=0
    emphasis_errors+=$(grep -o '\*' "$file" | wc -l || true)
    emphasis_errors+=$(grep -o '_' "$file" | wc -l || true)
    
    if [[ $((emphasis_errors % 2)) -ne 0 ]]; then
        log_warning "Potential unclosed emphasis marker in: $relative_file"
        ((WARNING_FILES++))
        ((TOTAL_ISSUES++))
        ((ISSUE_COUNTS["formatting"]++))
    fi
    
    # Malformed links
    while IFS= read -r malformed_link; do
        local link_text="${malformed_link#*[}"
        link_text="${link_text%]*)"
        local link_url="${link_text#*]("}"
        link_url="${link_url%)}"
        
        # Check for common link issues
        if [[ ! "$link_url" =~ ^https?:// ]] && [[ ! "$link_url" =~ ^mailto: ]] && \
           [[ ! "$link_url" =~ ^# ]] && [[ ! "$link_url" =~ ^./ ]] && [[ ! "$link_url" =~ ^/ ]]; then
            log_warning "Potentially malformed link in: $relative_file - $link_url"
            ((WARNING_FILES++))
            ((TOTAL_ISSUES++))
            ((ISSUE_COUNTS["link"]++))
        fi
    done < <(grep -oP '\[[^\]]*\]\([^)]*\)' "$file" 2>/dev/null || true)
    
    if [[ $syntax_errors -eq 0 ]]; then
        ((VALID_FILES++))
    else
        ((INVALID_FILES++))
    fi
}

validate_heading_structure() {
    local file="$1"
    local relative_file="${file#$DOCS_DIR/}"
    
    local heading_issues=0
    
    # Check for consistent heading levels
    local current_level=0
    local line_num=0
    
    while IFS= read -r line; do
        ((line_num++))
        
        if [[ "$line" =~ ^#{1,6}\ + ]]; then
            local level="${#line%% *}"
            level=$((level))
            
            # Check for skipping heading levels
            if [[ $current_level -gt 0 && $level -gt $((current_level + 1)) ]]; then
                log_warning "Skipped heading level in: $relative_file:$line_num"
                ((heading_issues++))
                ((TOTAL_ISSUES++))
                ((ISSUE_COUNTS["heading"]++))
            fi
            
            current_level=$level
            
            # Check heading text format
            local heading_text="${line#"#"* }"
            heading_text="${heading_text#"#"* }"
            
            # Avoid trailing punctuation in headings
            if [[ "$heading_text" =~ [.!?]+$ ]] && [[ "$heading_text" != *"..." ]]; then
                log_warning "Heading should not end with punctuation: $relative_file:$line_num"
                ((heading_issues++))
                ((TOTAL_ISSUES++))
                ((ISSUE_COUNTS["heading"]++))
            fi
        fi
    done < "$file"
    
    # Check for duplicate first-level headings (if not allowed)
    if [[ "$STRICT_MODE" == "true" ]]; then
        local first_level_count=$(grep -c '^# ' "$file" || true)
        if [[ $first_level_count -gt 1 ]]; then
            log_warning "Multiple first-level headings in: $relative_file ($first_level_count found)"
            ((heading_issues++))
            ((TOTAL_ISSUES++))
            ((ISSUE_COUNTS["heading"]++))
        fi
    fi
}

validate_code_formatting() {
    local file="$1"
    local relative_file="${file#$DOCS_DIR/}"
    
    # Check for proper code fence formatting
    local code_fence_issues=0
    
    while IFS= read -r line; do
        if [[ "$line" =~ ^```[a-zA-Z]*$ ]]; then
            local language="${line#\`\`\`}"
            
            # Check for lowercase language specification
            if [[ -n "$language" && "$language" != "$(echo "$language" | tr '[:upper:]' '[:lower:]')" ]]; then
                log_warning "Code fence language should be lowercase: $relative_file - $language"
                ((code_fence_issues++))
                ((TOTAL_ISSUES++))
                ((ISSUE_COUNTS["code"]++))
            fi
        fi
    done < "$file"
    
    # Check for inline code formatting
    while IFS= read -r line; do
        local inline_code=$(grep -o '`[^`]*`' "$line" | wc -l || true)
        if [[ $inline_code -gt 0 ]]; then
            # Check for proper spacing around inline code
            local malformatted=$(echo "$line" | grep -oP '[^`]`[^`]*`[^`]' | wc -l || true)
            if [[ $malformatted -gt 0 ]]; then
                log_warning "Inline code may need spacing: $relative_file"
                ((code_fence_issues++))
                ((TOTAL_ISSUES++))
                ((ISSUE_COUNTS["code"]++))
                break
            fi
        fi
    done < "$file"
}

validate_list_formatting() {
    local file="$1"
    local relative_file="${file#$DOCS_DIR/}"
    
    # Check for consistent list markers
    local unordered_markers=()
    local ordered_markers=()
    
    while IFS= read -r line; do
        if [[ "$line" =~ ^[\ \t]*[\*\-\+]\ + ]] || [[ "$line" =~ ^[\ \t]*[\*\-\+]$ ]]; then
            local marker="${line%% *}"
            marker="${marker#[\ \t]*}"
            unordered_markers+=("$marker")
        elif [[ "$line" =~ ^[\ \t]*[0-9]+\. ]] || [[ "$line" =~ ^[\ \t]*[0-9]+\)$ ]]; then
            local marker=$(echo "$line" | grep -oP '^[\ \t]*\K[0-9]+' || echo "1")
            ordered_markers+=("$marker")
        fi
    done < "$file"
    
    # Check for mixed unordered list markers
    if [[ ${#unordered_markers[@]} -gt 1 ]]; then
        local unique_markers=$(printf '%s\n' "${unordered_markers[@]}" | sort -u | wc -l)
        if [[ $unique_markers -gt 1 ]]; then
            log_warning "Mixed unordered list markers in: $relative_file"
            ((TOTAL_ISSUES++))
            ((ISSUE_COUNTS["formatting"]++))
        fi
    fi
}

validate_link_consistency() {
    local file="$1"
    local relative_file="${file#$DOCS_DIR/}"
    
    # Check for consistent link formatting
    local link_issues=0
    
    # Find all internal links
    while IFS= read -r link_match; do
        local link_text="${link_match#*[}"
        link_text="${link_text%]*)"
        link_text="${link_text#]*(}"
        link_text="${link_text%)}"
        
        # Check for relative paths consistency
        if [[ "$link_text" =~ ^[^/].*\.md$ ]] && [[ ! "$link_text" =~ ^./ ]]; then
            log_warning "Relative link should start with ./ : $relative_file - $link_text"
            ((link_issues++))
            ((TOTAL_ISSUES++))
            ((ISSUE_COUNTS["link"]++))
        fi
    done < <(grep -oP '\[[^\]]*\]\([^)]*\.md[^)]*\)' "$file" 2>/dev/null || true)
}

validate_metadata_consistency() {
    local file="$1"
    local relative_file="${file#$DOCS_DIR/}"
    
    # Check for consistent frontmatter usage
    if head -n 5 "$file" | grep -q "^---"; then
        if ! tail -n +$(($(grep -n "^---" "$file" | head -n 2 | tail -n 1 | cut -d: -f1) + 1)) "$file" | grep -q "^---"; then
            log_warning "Malformed or missing closing frontmatter in: $relative_file"
            ((TOTAL_ISSUES++))
            ((ISSUE_COUNTS["structure"]++))
        fi
    fi
    
    # Check for consistent title metadata
    local title_in_frontmatter=false
    local title_in_heading=false
    
    if head -n 10 "$file" | grep -q "^title:"; then
        title_in_frontmatter=true
    fi
    
    if head -n 1 "$file" | grep -q "^# "; then
        title_in_heading=true
    fi
    
    if [[ "$title_in_frontmatter" == "true" && "$title_in_heading" == "true" ]]; then
        log_info "Document has both frontmatter and heading title: $relative_file"
    elif [[ "$title_in_frontmatter" == "false" && "$title_in_heading" == "false" ]]; then
        log_warning "Document missing title (both frontmatter and heading): $relative_file"
        ((TOTAL_ISSUES++))
        ((ISSUE_COUNTS["structure"]++))
    fi
}

#==============================================================================
# Main Processing Functions
#==============================================================================

process_markdown_file() {
    local file="$1"
    
    log_purple "Linting: ${file#$DOCS_DIR/}"
    
    # Run all validation checks
    validate_basic_markdown_syntax "$file"
    validate_heading_structure "$file"
    validate_code_formatting "$file"
    validate_list_formatting "$file"
    validate_link_consistency "$file"
    validate_metadata_consistency "$file"
    
    # Check if markdownlint is available and run it
    if command -v markdownlint >/dev/null 2>&1; then
        local lint_output
        if [[ "$AUTO_FIX" == "true" ]]; then
            lint_output=$(markdownlint "$file" --fix --config "$MARKDOWNLINT_CONFIG" 2>&1 || true)
            if [[ -n "$lint_output" ]]; then
                ((TOTAL_ISSUES++))
                ((ISSUE_COUNTS["style"]++))
                log_warning "Auto-fixed linting issues in: ${file#$DOCS_DIR/}"
            else
                log_success "No linting issues found in: ${file#$DOCS_DIR/}"
            fi
        else
            lint_output=$(markdownlint "$file" --config "$MARKDOWNLINT_CONFIG" 2>&1 || true)
            if [[ -n "$lint_output" ]]; then
                ((TOTAL_ISSUES++))
                ((ISSUE_COUNTS["style"]++))
                log_warning "Linting issues found in: ${file#$DOCS_DIR/}"
            else
                log_success "No linting issues found in: ${file#$DOCS_DIR/}"
            fi
        fi
    else
        log_info "markdownlint not available, using basic validation only"
    fi
}

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
    "total_issues": $TOTAL_ISSUES,
    "fixed_issues": $FIXED_ISSUES
  },
  "issue_breakdown": {
    "heading_issues": ${ISSUE_COUNTS["heading"]},
    "link_issues": ${ISSUE_COUNTS["link"]},
    "code_issues": ${ISSUE_COUNTS["code"]},
    "formatting_issues": ${ISSUE_COUNTS["formatting"]},
    "structure_issues": ${ISSUE_COUNTS["structure"]},
    "style_issues": ${ISSUE_COUNTS["style"]}
  }
}
EOF
}

generate_console_report() {
    echo
    log_info "=== DOCUMENTATION LINTING SUMMARY ==="
    log_info "Total Files Processed: $TOTAL_FILES"
    log_success "Valid Files: $VALID_FILES"
    log_error "Invalid Files: $INVALID_FILES"
    log_warning "Files with Warnings: $WARNING_FILES"
    log_info "Total Issues Found: $TOTAL_ISSUES"
    
    if [[ $TOTAL_ISSUES -gt 0 ]]; then
        echo
        log_info "Issue Breakdown:"
        log_info "  Heading Issues: ${ISSUE_COUNTS["heading"]}"
        log_info "  Link Issues: ${ISSUE_COUNTS["link"]}"
        log_info "  Code Issues: ${ISSUE_COUNTS["code"]}"
        log_info "  Formatting Issues: ${ISSUE_COUNTS["formatting"]}"
        log_info "  Structure Issues: ${ISSUE_COUNTS["structure"]}"
        log_info "  Style Issues: ${ISSUE_COUNTS["style"]}"
    fi
    
    echo
    if [[ $INVALID_FILES -eq 0 ]]; then
        log_success "✅ All documentation files pass basic validation!"
        return 0
    else
        log_error "❌ $INVALID_FILES files have validation errors"
        return 1
    fi
}

#==============================================================================
# Main Execution
#==============================================================================

main() {
    log_info "Starting documentation linting..."
    log_info "Documentation directory: $DOCS_DIR"
    log_info "Auto-fix mode: $AUTO_FIX"
    log_info "Strict mode: $STRICT_MODE"
    log_info "Output format: $OUTPUT_FORMAT"
    log_info "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    
    # Create configuration files
    create_default_markdownlint_config "$RULES_FILE"
    create_mafa_specific_config
    
    # Process all markdown files
    local md_files=()
    while IFS= read -r -d '' file; do
        md_files+=("$file")
    done < <(find "$DOCS_DIR" -name "*.md" -type f -print0)
    
    log_info "Found ${#md_files[@]} markdown files to process"
    
    for file in "${md_files[@]}"; do
        process_markdown_file "$file"
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
        echo "MAFA Documentation Linter"
        echo
        echo "Usage: $0 [OPTIONS]"
        echo
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --docs-dir DIR      Set documentation directory (default: docs)"
        echo "  --rules FILE        Set markdownlint rules file (default: .markdownlint.json)"
        echo "  --auto-fix          Enable automatic fixing of issues"
        echo "  --strict            Enable strict validation mode"
        echo "  --format FORMAT     Output format: console|json (default: console)"
        echo "  --report FILE       JSON report file path (default: /tmp/mafa-lint-report.json)"
        echo
        echo "Environment Variables:"
        echo "  DOCS_DIR            Documentation directory path"
        echo "  RULES_FILE          Markdownlint rules file path"
        echo "  AUTO_FIX            Enable auto-fix mode: true|false"
        echo "  STRICT_MODE         Enable strict validation: true|false"
        echo "  OUTPUT_FORMAT       Output format: console|json"
        echo "  REPORT_FILE         JSON report file path"
        exit 0
        ;;
    --docs-dir)
        DOCS_DIR="$2"
        shift 2
        ;;
    --rules)
        RULES_FILE="$2"
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

# Run main function
main "$@"