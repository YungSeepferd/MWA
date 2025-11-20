#!/bin/bash

#==============================================================================
# MAFA Documentation Statistics and Metrics Generator
# Analyzes documentation coverage, metrics, and quality indicators
#==============================================================================

set -euo pipefail

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
DOCS_DIR="${DOCS_DIR:-docs}"
TEMPLATES_DIR="${TEMPLATES_DIR:-docs/templates}"
EXAMPLES_DIR="${EXAMPLES_DIR:-docs/examples}"
OUTPUT_FORMAT="${OUTPUT_FORMAT:-console}"
REPORT_FILE="${REPORT_FILE:-/tmp/mafa-docs-stats.json}"
DETAILED="${DETAILED:-false}"
SECTION_ANALYSIS="${SECTION_ANALYSIS:-true}"

# Metrics storage
declare -A METRICS
METRICS=(
    ["total_files"]=0
    ["total_lines"]=0
    ["total_words"]=0
    ["total_characters"]=0
    ["total_headings"]=0
    ["total_links"]=0
    ["total_code_blocks"]=0
    ["total_images"]=0
    ["avg_words_per_file"]=0
    ["avg_lines_per_file"]=0
)

# Section metrics
declare -A SECTION_METRICS
declare -A SECTION_FILES

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
    echo -e "${PURPLE}[STATS]${NC} $1"
}

log_cyan() {
    echo -e "${CYAN}[METRICS]${NC} $1"
}

#==============================================================================
# Analysis Functions
#==============================================================================

analyze_file() {
    local file="$1"
    local relative_file="${file#$DOCS_DIR/}"
    
    # Count lines
    local lines=$(wc -l < "$file")
    
    # Count words
    local words=$(wc -w < "$file" 2>/dev/null || echo 0)
    
    # Count characters
    local chars=$(wc -c < "$file" 2>/dev/null || echo 0)
    
    # Count headings
    local headings=$(grep -c "^#" "$file" || echo 0)
    
    # Count links
    local links=$(grep -c '\[[^\]]*\]([^)]*)' "$file" || echo 0)
    
    # Count code blocks
    local code_blocks=$(grep -c "^```" "$file" || echo 0)
    code_blocks=$((code_blocks / 2))  # Each code block has opening and closing
    
    # Count images
    local images=$(grep -c '!\[.*\](' "$file" || echo 0)
    
    # Store in section metrics
    local section_dir=$(dirname "$relative_file")
    SECTION_FILES["$section_dir"]=$((${SECTION_FILES["$section_dir"]:-$lines} + 1))
    
    # Accumulate section metrics
    SECTION_METRICS["${section_dir}_lines"]=$((${SECTION_METRICS["${section_dir}_lines"]:-$lines} + $lines))
    SECTION_METRICS["${section_dir}_words"]=$((${SECTION_METRICS["${section_dir}_words"]:-$words} + $words))
    SECTION_METRICS["${section_dir}_headings"]=$((${SECTION_METRICS["${section_dir}_headings"]:-$headings} + $headings))
    SECTION_METRICS["${section_dir}_links"]=$((${SECTION_METRICS["${section_dir}_links"]:-$links} + $links))
    SECTION_METRICS["${section_dir}_code_blocks"]=$((${SECTION_METRICS["${section_dir}_code_blocks"]:-$code_blocks} + $code_blocks))
    
    # Accumulate global metrics
    METRICS["total_files"]=$((${METRICS["total_files"]} + 1))
    METRICS["total_lines"]=$((${METRICS["total_lines"]} + $lines))
    METRICS["total_words"]=$((${METRICS["total_words"]} + $words))
    METRICS["total_characters"]=$((${METRICS["total_characters"]} + $chars))
    METRICS["total_headings"]=$((${METRICS["total_headings"]} + $headings))
    METRICS["total_links"]=$((${METRICS["total_links"]} + $links))
    METRICS["total_code_blocks"]=$((${METRICS["total_code_blocks"]} + $code_blocks))
    METRICS["total_images"]=$((${METRICS["total_images"]} + $images))
    
    if [[ "$DETAILED" == "true" ]]; then
        log_info "Analyzed: $relative_file ($lines lines, $words words, $headings headings)"
    fi
}

analyze_documentation_coverage() {
    log_info "Analyzing documentation coverage..."
    
    # Define expected documentation areas with descriptions
    declare -A expected_areas=(
        ["getting-started"]="Quick start, Installation, Configuration"
        ["user-guide"]="User workflows, Dashboard, Setup wizard, Troubleshooting"
        ["developer-guide"]="Contributing, Development setup, API integration, Testing"
        ["architecture"]="System overview, Repository structure, Data models"
        ["operations"]="Deployment, Monitoring, Backup & restore, Security"
        ["project"]="Roadmap, Changelog, Release notes, Governance"
    )
    
    local coverage_score=0
    local max_score=0
    local coverage_details=""
    
    for area in "${!expected_areas[@]}"; do
        local area_dir="$DOCS_DIR/$area"
        local area_description="${expected_areas[$area]}"
        
        if [[ -d "$area_dir" ]]; then
            local file_count=$(find "$area_dir" -name "*.md" -type f | wc -l)
            local total_lines=$(find "$area_dir" -name "*.md" -type f -exec wc -l {} + | tail -1 | awk '{print $1}' || echo 0)
            
            # Calculate area completeness (simple heuristic)
            local completeness=0
            case "$area" in
                "getting-started")
                    completeness=$((file_count * 10))  # Each file worth 10 points
                    ;;
                "user-guide")
                    completeness=$((file_count * 8))   # Each file worth 8 points
                    ;;
                "developer-guide")
                    completeness=$((file_count * 12))  # Each file worth 12 points
                    ;;
                "architecture")
                    completeness=$((file_count * 15))  # Each file worth 15 points
                    ;;
                "operations")
                    completeness=$((file_count * 10))  # Each file worth 10 points
                    ;;
                "project")
                    completeness=$((file_count * 6))   # Each file worth 6 points
                    ;;
            esac
            
            coverage_score=$((coverage_score + completeness))
            max_score=$((max_score + 20))  # Each area max 20 points
            
            coverage_details="${coverage_details}\n- ✅ **$area**: $area_description\n  - Files: $file_count, Lines: $total_lines, Score: $completeness/20"
        else
            coverage_details="${coverage_details}\n- ❌ **$area**: $area_description\n  - Missing directory"
        fi
    done
    
    local coverage_percentage=0
    if [[ $max_score -gt 0 ]]; then
        coverage_percentage=$((coverage_score * 100 / max_score))
    fi
    
    echo -e "$coverage_details"
    echo "$coverage_percentage"
}

analyze_content_quality() {
    log_info "Analyzing content quality indicators..."
    
    local quality_issues=0
    local quality_score=100
    
    # Check for files with very few words (potentially incomplete)
    local small_files=0
    while IFS= read -r file; do
        local words=$(wc -w < "$file" 2>/dev/null || echo 0)
        if [[ $words -lt 50 ]]; then
            ((small_files++))
            ((quality_issues++))
        fi
    done < <(find "$DOCS_DIR" -name "*.md" -type f)
    
    # Check for files with no headings (poor structure)
    local unstructured_files=0
    while IFS= read -r file; do
        local headings=$(grep -c "^#" "$file" 2>/dev/null || echo 0)
        if [[ $headings -eq 0 ]]; then
            ((unstructured_files++))
            ((quality_issues++))
        fi
    done < <(find "$DOCS_DIR" -name "*.md" -type f)
    
    # Check for files with no links (poor navigation)
    local isolated_files=0
    while IFS= read -r file; do
        local links=$(grep -c '\[[^\]]*\]([^)]*)' "$file" 2>/dev/null || echo 0)
        if [[ $links -eq 0 ]]; then
            ((isolated_files++))
            ((quality_issues++))
        fi
    done < <(find "$DOCS_DIR" -name "*.md" -type f)
    
    # Deduct points for issues
    quality_score=$((quality_score - small_files * 2))
    quality_score=$((quality_score - unstructured_files * 3))
    quality_score=$((quality_score - isolated_files * 1))
    
    if [[ $quality_score -lt 0 ]]; then
        quality_score=0
    fi
    
    echo "Small files (< 50 words): $small_files"
    echo "Unstructured files (no headings): $unstructured_files"
    echo "Isolated files (no links): $isolated_files"
    echo "Quality score: $quality_score/100"
}

analyze_readability() {
    log_info "Analyzing readability metrics..."
    
    # Calculate average words per sentence (simple heuristic)
    local total_sentences=0
    local total_words_sentences=0
    
    while IFS= read -r file; do
        # Count sentences (periods, exclamation marks, question marks)
        local sentences=$(grep -o '[.!?]' "$file" | wc -l 2>/dev/null || echo 0)
        local words=$(wc -w < "$file" 2>/dev/null || echo 0)
        
        total_sentences=$((total_sentences + sentences))
        total_words_sentences=$((total_words_sentences + words))
    done < <(find "$DOCS_DIR" -name "*.md" -type f)
    
    local avg_words_per_sentence=0
    if [[ $total_sentences -gt 0 ]]; then
        avg_words_per_sentence=$((total_words_sentences / total_sentences))
    fi
    
    # Analyze heading distribution
    local heading_distribution=""
    local level_counts=()
    
    for level in {1..6}; do
        local count=$(grep -c "^#{${level}} " "$DOCS_DIR"/*.md "$DOCS_DIR"/*/*.md "$DOCS_DIR"/*/*/*.md 2>/dev/null | awk -F: '{sum+=$2} END {print sum+0}')
        heading_distribution="${heading_distribution}Level $level: $count\n"
        level_counts[$level]=$count
    done
    
    echo "Average words per sentence: $avg_words_per_sentence"
    echo -e "Heading distribution:\n$heading_distribution"
}

generate_section_analysis() {
    if [[ "$SECTION_ANALYSIS" != "true" ]]; then
        return 0
    fi
    
    log_info "Generating detailed section analysis..."
    
    local sections=("${!SECTION_FILES[@]}")
    
    for section in "${sections[@]}"; do
        local file_count=${SECTION_FILES[$section]:-0}
        local lines=${SECTION_METRICS["${section}_lines"]:-0}
        local words=${SECTION_METRICS["${section}_words"]:-0}
        local headings=${SECTION_METRICS["${section}_headings"]:-0}
        local links=${SECTION_METRICS["${section}_links"]:-0}
        local code_blocks=${SECTION_METRICS["${section}_code_blocks"]:-0}
        
        if [[ $file_count -gt 0 ]]; then
            local avg_words=$((words / file_count))
            local avg_lines=$((lines / file_count))
            
            log_cyan "Section: $section"
            log_cyan "  Files: $file_count"
            log_cyan "  Total Lines: $lines (avg: $avg_lines per file)"
            log_cyan "  Total Words: $words (avg: $avg_words per file)"
            log_cyan "  Headings: $headings"
            log_cyan "  Links: $links"
            log_cyan "  Code Blocks: $code_blocks"
        fi
    done
}

#==============================================================================
# Report Generation Functions
#==============================================================================

generate_json_report() {
    local coverage_data=$(analyze_documentation_coverage)
    local coverage_percentage=$(echo "$coverage_data" | tail -n 1)
    local quality_data=$(analyze_content_quality)
    local readability_data=$(analyze_readability)
    
    cat > "$REPORT_FILE" <<EOF
{
  "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "repository": "MAFA",
  "docs_directory": "$DOCS_DIR",
  "summary": {
    "total_files": ${METRICS["total_files"]},
    "total_lines": ${METRICS["total_lines"]},
    "total_words": ${METRICS["total_words"]},
    "total_characters": ${METRICS["total_characters"]},
    "total_headings": ${METRICS["total_headings"]},
    "total_links": ${METRICS["total_links"]},
    "total_code_blocks": ${METRICS["total_code_blocks"]},
    "total_images": ${METRICS["total_images"]},
    "average_words_per_file": $((METRICS["total_words"] / METRICS["total_files"])),
    "average_lines_per_file": $((METRICS["total_lines"] / METRICS["total_files"]))
  },
  "coverage": {
    "percentage": $coverage_percentage,
    "areas_analyzed": $(echo "${!expected_areas[@]}" | wc -w)
  },
  "section_breakdown": {
EOF
    
    # Add section data
    local first=true
    for section in "${!SECTION_FILES[@]}"; do
        if [[ "$first" == "false" ]]; then
            echo "," >> "$REPORT_FILE"
        fi
        first=false
        
        cat >> "$REPORT_FILE" <<EOF
    "$section": {
      "files": ${SECTION_FILES[$section]},
      "lines": ${SECTION_METRICS["${section}_lines"]:-0},
      "words": ${SECTION_METRICS["${section}_words"]:-0},
      "headings": ${SECTION_METRICS["${section}_headings"]:-0},
      "links": ${SECTION_METRICS["${section}_links"]:-0},
      "code_blocks": ${SECTION_METRICS["${section}_code_blocks"]:-0}
    }
EOF
    done
    
    cat >> "$REPORT_FILE" <<EOF

  },
  "quality_indicators": {
    "small_files_count": $(echo "$quality_data" | grep "Small files" | awk '{print $4}'),
    "unstructured_files_count": $(echo "$quality_data" | grep "Unstructured files" | awk '{print $4}'),
    "isolated_files_count": $(echo "$quality_data" | grep "Isolated files" | awk '{print $4}'),
    "quality_score": $(echo "$quality_data" | grep "Quality score" | awk '{print $3}')
  }
}
EOF
}

generate_console_report() {
    echo
    log_info "=== DOCUMENTATION STATISTICS SUMMARY ==="
    echo
    
    # Overall metrics
    log_info "📊 Overall Metrics:"
    log_info "  Total Files: ${METRICS["total_files"]}"
    log_info "  Total Lines: ${METRICS["total_lines"]}"
    log_info "  Total Words: ${METRICS["total_words"]}"
    log_info "  Total Characters: ${METRICS["total_characters"]}"
    log_info "  Total Headings: ${METRICS["total_headings"]}"
    log_info "  Total Links: ${METRICS["total_links"]}"
    log_info "  Total Code Blocks: ${METRICS["total_code_blocks"]}"
    log_info "  Total Images: ${METRICS["total_images"]}"
    echo
    
    # Average metrics
    if [[ ${METRICS["total_files"]} -gt 0 ]]; then
        local avg_words=$((METRICS["total_words"] / METRICS["total_files"]))
        local avg_lines=$((METRICS["total_lines"] / METRICS["total_files"]))
        
        log_info "📈 Averages:"
        log_info "  Words per file: $avg_words"
        log_info "  Lines per file: $avg_lines"
        echo
    fi
    
    # Coverage analysis
    log_info "📋 Documentation Coverage:"
    local coverage_data=$(analyze_documentation_coverage)
    local coverage_percentage=$(echo "$coverage_data" | tail -n 1)
    echo "$coverage_data" | head -n -1
    
    if [[ $coverage_percentage -ge 80 ]]; then
        log_success "Coverage Score: $coverage_percentage% (Excellent)"
    elif [[ $coverage_percentage -ge 60 ]]; then
        log_info "Coverage Score: $coverage_percentage% (Good)"
    else
        log_warning "Coverage Score: $coverage_percentage% (Needs Improvement)"
    fi
    echo
    
    # Quality indicators
    log_info "🔍 Quality Indicators:"
    local quality_data=$(analyze_content_quality)
    echo "$quality_data"
    echo
    
    # Readability analysis
    log_info "📖 Readability Analysis:"
    local readability_data=$(analyze_readability)
    echo "$readability_data"
    echo
    
    # Section analysis
    generate_section_analysis
    echo
    
    # Recommendations
    log_info "💡 Recommendations:"
    
    if [[ ${METRICS["total_files"]} -lt 20 ]]; then
        log_warning "  - Consider adding more documentation files"
    fi
    
    if [[ $coverage_percentage -lt 80 ]]; then
        log_warning "  - Improve documentation coverage in missing areas"
    fi
    
    if [[ $(echo "$quality_data" | grep "Small files" | awk '{print $4}') -gt 0 ]]; then
        log_warning "  - Expand or merge files with very few words"
    fi
    
    if [[ $(echo "$quality_data" | grep "Unstructured files" | awk '{print $4}') -gt 0 ]]; then
        log_warning "  - Add proper heading structure to unstructured files"
    fi
    
    if [[ ${METRICS["total_links"]} -lt $((METRICS["total_files"] * 2)) ]]; then
        log_warning "  - Add more internal links for better navigation"
    fi
    
    log_success "✅ Documentation statistics analysis completed!"
}

#==============================================================================
# Main Execution
#==============================================================================

main() {
    log_info "Starting documentation statistics analysis..."
    log_info "Documentation directory: $DOCS_DIR"
    log_info "Detailed analysis: $DETAILED"
    log_info "Section analysis: $SECTION_ANALYSIS"
    log_info "Output format: $OUTPUT_FORMAT"
    log_info "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    
    # Process all markdown files
    local md_files=()
    while IFS= read -r -d '' file; do
        md_files+=("$file")
    done < <(find "$DOCS_DIR" -name "*.md" -type f -print0)
    
    log_info "Found ${#md_files[@]} markdown files to analyze"
    
    if [[ ${#md_files[@]} -eq 0 ]]; then
        log_error "No markdown files found in $DOCS_DIR"
        exit 1
    fi
    
    for file in "${md_files[@]}"; do
        analyze_file "$file"
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
    
    exit 0
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "MAFA Documentation Statistics Generator"
        echo
        echo "Usage: $0 [OPTIONS]"
        echo
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --docs-dir DIR      Set documentation directory (default: docs)"
        echo "  --detailed          Enable detailed file-by-file analysis"
        echo "  --no-section        Disable detailed section analysis"
        echo "  --format FORMAT     Output format: console|json (default: console)"
        echo "  --report FILE       JSON report file path (default: /tmp/mafa-docs-stats.json)"
        echo
        echo "Environment Variables:"
        echo "  DOCS_DIR            Documentation directory path"
        echo "  DETAILED            Enable detailed analysis: true|false"
        echo "  SECTION_ANALYSIS    Enable section analysis: true|false"
        echo "  OUTPUT_FORMAT       Output format: console|json"
        echo "  REPORT_FILE         JSON report file path"
        exit 0
        ;;
    --docs-dir)
        DOCS_DIR="$2"
        shift 2
        ;;
    --detailed)
        DETAILED="true"
        shift
        ;;
    --no-section)
        SECTION_ANALYSIS="false"
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