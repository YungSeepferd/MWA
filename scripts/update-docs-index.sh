#!/bin/bash

#==============================================================================
# MAFA Documentation Index Updater
# Automatically generates and updates documentation indexes and tables of contents
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
OUTPUT_FORMAT="${OUTPUT_FORMAT:-console}"
BACKUP_DIR="${BACKUP_DIR:-docs/.index-backups}"
DRY_RUN="${DRY_RUN:-false}"

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
    echo -e "${PURPLE}[INDEX]${NC} $1"
}

# Index counters
UPDATED_FILES=0
CREATED_FILES=0
SKIPPED_FILES=0

#==============================================================================
# File Processing Functions
#==============================================================================

create_backup() {
    local file="$1"
    local backup_path="$BACKUP_DIR/$(date +%Y%m%d_%H%M%S)_$(basename "$file")"
    
    mkdir -p "$BACKUP_DIR"
    cp "$file" "$backup_path"
    log_info "Created backup: $(basename "$backup_path")"
}

generate_toc() {
    local file="$1"
    local toc_level="${2:-3}"  # Default to 3 heading levels
    
    # Extract headings up to specified level
    local toc_content=""
    local current_level=0
    
    while IFS= read -r line; do
        if [[ "$line" =~ ^#{1,$toc_level}\ + ]]; then
            local level="${#line%% *}"
            level=$((level))
            local heading_text="${line#"#"* }"
            heading_text="${heading_text#"#"* }"
            heading_text="${heading_text#"#"* }"
            
            # Create anchor from heading text
            local anchor="${heading_text,,}"  # Convert to lowercase
            anchor="${anchor// /-}"  # Replace spaces with hyphens
            anchor="${anchor//[^a-zA-Z0-9\-]/}"  # Remove special characters except hyphens
            
            # Add appropriate indentation
            local indent=""
            for ((i=1; i<level; i++)); do
                indent="${indent}  "
            done
            
            # Build TOC entry
            toc_content="${toc_content}${indent}- [$heading_text](#$anchor)\n"
        fi
    done < "$file"
    
    echo -e "$toc_content"
}

update_readme_toc() {
    local readme_file="$DOCS_DIR/README.md"
    
    if [[ ! -f "$readme_file" ]]; then
        log_warning "README.md not found, skipping TOC update"
        return 1
    fi
    
    log_info "Updating README.md table of contents..."
    
    # Create backup
    if [[ "$DRY_RUN" != "true" ]]; then
        create_backup "$readme_file"
    fi
    
    # Extract existing content sections
    local content_before_toc=""
    local toc_section=""
    local content_after_toc=""
    
    local in_toc_section=false
    local toc_started=false
    
    while IFS= read -r line; do
        if [[ "$line" =~ ^##\ +📁\ Documentation\ Structure$ ]] || \
           [[ "$line" =~ ^##\ +Table\ of\ Contents$ ]] || \
           [[ "$line" =~ ^##\ +Contents$ ]]; then
            in_toc_section=true
            toc_started=true
            toc_section="${toc_section}${line}\n"
        elif [[ "$in_toc_section" == "true" && "$line" =~ ^##\ + ]] && [[ "$toc_started" == "true" ]]; then
            in_toc_section=false
            content_after_toc="${content_after_toc}${line}\n"
        elif [[ "$in_toc_section" == "false" ]]; then
            if [[ "$toc_started" == "false" ]]; then
                content_before_toc="${content_before_toc}${line}\n"
            else
                content_after_toc="${content_after_toc}${line}\n"
            fi
        else
            toc_section="${toc_section}${line}\n"
        fi
    done < "$readme_file"
    
    # Generate new TOC
    local new_toc=""
    new_toc="${new_toc}## 📁 Documentation Structure\n\n"
    
    # Add section links
    local sections=(
        "getting-started:🚀 Getting Started"
        "user-guide:👥 User Guide"
        "developer-guide:🛠️ Developer Guide"
        "architecture:🏗️ Architecture"
        "operations:⚙️ Operations"
        "project:📋 Project Management"
    )
    
    for section_pair in "${sections[@]}"; do
        local section="${section_pair%%:*}"
        local emoji_title="${section_pair##*:}"
        
        if [[ -d "$DOCS_DIR/$section" ]]; then
            # Find files in the section
            local files=()
            while IFS= read -r file; do
                files+=("$file")
            done < <(find "$DOCS_DIR/$section" -name "*.md" -type f | sort)
            
            new_toc="${new_toc}### $emoji_title\n"
            
            for file in "${files[@]}"; do
                local relative_file="${file#$DOCS_DIR/}"
                local filename=$(basename "$file" .md)
                filename="${filename//-/ }"
                filename="${filename^}"  # Capitalize first letter
                
                # Skip index files in TOC for cleaner display
                if [[ "$filename" != "Index" ]]; then
                    new_toc="${new_toc}- [$filename](./$relative_file)\n"
                fi
            done
            new_toc="${new_toc}\n"
        fi
    done
    
    # Add QA Reports section if it exists
    if [[ -d "$DOCS_DIR/project/qa-reports" ]]; then
        new_toc="${new_toc}### 📊 Quality Assurance Reports\n"
        
        local qa_files=()
        while IFS= read -r file; do
            qa_files+=("$file")
        done < <(find "$DOCS_DIR/project/qa-reports" -name "*.md" -type f | sort)
        
        for file in "${qa_files[@]}"; do
            local relative_file="${file#$DOCS_DIR/}"
            local filename=$(basename "$file" .md)
            filename="${filename//-/ }"
            filename="${filename^}"
            
            new_toc="${new_toc}- [$filename](./$relative_file)\n"
        done
        new_toc="${new_toc}\n"
    fi
    
    # Add navigation links
    new_toc="${new_toc}## 🔗 Quick Navigation\n\n"
    new_toc="${new_toc}### For New Users\n"
    new_toc="${new_toc}1. [User Flows](./user-guide/workflows/user-flows.md) - Recommended user interactions\n"
    new_toc="${new_toc}2. [Setup Guide](./getting-started/quick-start.md) - Get started quickly\n"
    new_toc="${new_toc}3. [Configuration](./getting-started/configuration.md) - Configure MAFA\n\n"
    
    new_toc="${new_toc}### For Developers\n"
    new_toc="${new_toc}1. [Development Setup](./developer-guide/development-setup.md) - Set up development environment\n"
    new_toc="${new_toc}2. [API Integration](./developer-guide/api/integration-guide.md) - Integrate with MAFA APIs\n"
    new_toc="${new_toc}3. [Contributing Guide](./developer-guide/contributing.md) - How to contribute\n\n"
    
    new_toc="${new_toc}### For Operators\n"
    new_toc="${new_toc}1. [Deployment Guide](./operations/deployment.md) - Deploy MAFA\n"
    new_toc="${new_toc}2. [Monitoring](./operations/monitoring.md) - Monitor system health\n"
    new_toc="${new_toc}3. [Security](./operations/security.md) - Security guidelines\n\n"
    
    # Write updated content
    local updated_content="${content_before_toc}${new_toc}${content_after_toc}"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_purple "DRY RUN: Would update README.md with new TOC"
        ((SKIPPED_FILES++))
    else
        echo -e "$updated_content" > "$readme_file"
        log_success "Updated README.md with new table of contents"
        ((UPDATED_FILES++))
    fi
}

update_section_indexes() {
    local section_dir="$1"
    
    log_info "Processing section: $(basename "$section_dir")"
    
    # Find all markdown files in the directory
    local files=()
    while IFS= read -r file; do
        files+=("$file")
    done < <(find "$section_dir" -name "*.md" -type f | sort)
    
    # Skip if no files found
    if [[ ${#files[@]} -eq 0 ]]; then
        return 0
    fi
    
    # Create or update index file
    local index_file="$section_dir/README.md"
    local section_name=$(basename "$section_dir")
    section_name="${section_name//-/ }"
    section_name="${section_name^}"  # Capitalize
    
    # Check if index already exists
    local index_exists=false
    if [[ -f "$index_file" ]]; then
        index_exists=true
    fi
    
    if [[ "$DRY_RUN" != "true" && "$index_exists" == "true" ]]; then
        create_backup "$index_file"
    fi
    
    # Generate index content
    local index_content="# $section_name\n\n"
    
    # Add description based on section
    case "$section_name" in
        "Getting Started")
            index_content="${index_content}Welcome to MAFA! This section contains everything you need to get up and running with the MüncheWohnungsAssistent.\n\n"
            ;;
        "User Guide")
            index_content="${index_content}Complete user documentation for MAFA. Learn how to use all features and workflows effectively.\n\n"
            ;;
        "Developer Guide")
            index_content="${index_content}Technical documentation for developers working on or integrating with MAFA.\n\n"
            ;;
        "Architecture")
            index_content="${index_content}System architecture, design decisions, and technical implementation details.\n\n"
            ;;
        "Operations")
            index_content="${index_content}Operational documentation for deploying, monitoring, and maintaining MAFA.\n\n"
            ;;
        "Project")
            index_content="${index_content}Project management, planning, and quality assurance documentation.\n\n"
            ;;
    esac
    
    index_content="${index_content}## 📋 Contents\n\n"
    
    # Add files to index
    for file in "${files[@]}"; do
        local relative_file="${file#$DOCS_DIR/}"
        local filename=$(basename "$file" .md)
        filename="${filename//-/ }"
        filename="${filename^}"
        
        # Skip the index file itself
        if [[ "$filename" != "Index" && "$filename" != "$section_name" ]]; then
            # Try to extract title from first heading
            local file_title="$filename"
            if [[ -f "$file" ]]; then
                local first_heading=$(head -n 1 "$file" | sed 's/^# *//' | tr -d '\r\n')
                if [[ -n "$first_heading" ]]; then
                    file_title="$first_heading"
                fi
            fi
            
            index_content="${index_content}- [$file_title](./${relative_file#$section_dir/})\n"
        fi
    done
    
    index_content="${index_content}\n"
    
    # Add generation timestamp
    index_content="${index_content}---\n\n"
    index_content="${index_content}*Last updated: $(date +"%B %d, %Y")*\n"
    index_content="${index_content}*Auto-generated by documentation index updater*\n"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_purple "DRY RUN: Would update index for $section_name"
        ((SKIPPED_FILES++))
    else
        if [[ "$index_exists" == "true" ]]; then
            echo -e "$index_content" > "$index_file"
            log_success "Updated index for $section_name"
            ((UPDATED_FILES++))
        else
            echo -e "$index_content" > "$index_file"
            log_success "Created index for $section_name"
            ((CREATED_FILES++))
        fi
    fi
}

update_file_toc() {
    local file="$1"
    local max_toc_level="${2:-3}"
    
    # Check if file already has a TOC
    local has_toc=false
    if head -n 20 "$file" | grep -q "^## *\(Table of Contents\|Contents\|📋 Contents\)"; then
        has_toc=true
    fi
    
    if [[ "$has_toc" == "true" ]]; then
        log_info "File already has TOC: ${file#$DOCS_DIR/}"
        ((SKIPPED_FILES++))
        return 0
    fi
    
    # Generate TOC
    local toc=$(generate_toc "$file" "$max_toc_level")
    
    if [[ -n "$toc" ]]; then
        # Create backup
        if [[ "$DRY_RUN" != "true" ]]; then
            create_backup "$file"
        fi
        
        # Find insertion point (after first heading)
        local insert_line=$(grep -n "^#" "$file" | head -n 1 | cut -d: -f1)
        
        if [[ -n "$insert_line" ]]; then
            # Build updated content
            local content_before=""
            local content_after=""
            
            # Split file at insertion point
            local line_num=0
            while IFS= read -r line; do
                ((line_num++))
                if [[ $line_num -le $insert_line ]]; then
                    content_before="${content_before}${line}\n"
                else
                    content_after="${content_after}${line}\n"
                fi
            done < "$file"
            
            # Create TOC section
            local toc_section="## 📋 Table of Contents\n\n$toc\n"
            
            # Combine all parts
            local updated_content="${content_before}${toc_section}${content_after}"
            
            if [[ "$DRY_RUN" == "true" ]]; then
                log_purple "DRY RUN: Would add TOC to ${file#$DOCS_DIR/}"
                ((SKIPPED_FILES++))
            else
                echo -e "$updated_content" > "$file"
                log_success "Added TOC to ${file#$DOCS_DIR/}"
                ((UPDATED_FILES++))
            fi
        fi
    fi
}

#==============================================================================
# Main Processing Functions
#==============================================================================

process_all_sections() {
    log_info "Processing all documentation sections..."
    
    # Process main sections
    local sections=(
        "getting-started"
        "user-guide"
        "developer-guide"
        "architecture"
        "operations"
        "project"
    )
    
    for section in "${sections[@]}"; do
        local section_dir="$DOCS_DIR/$section"
        if [[ -d "$section_dir" ]]; then
            update_section_indexes "$section_dir"
            
            # Also update individual files with TOC if they're long enough
            local files=()
            while IFS= read -r file; do
                files+=("$file")
            done < <(find "$section_dir" -name "*.md" -type f)
            
            for file in "${files[@]}"; do
                local line_count=$(wc -l < "$file")
                if [[ $line_count -gt 50 ]]; then  # Only add TOC to files with significant content
                    update_file_toc "$file" 3
                fi
            done
        fi
    done
}

generate_master_index() {
    local master_index="$DOCS_DIR/INDEX.md"
    
    log_info "Generating master documentation index..."
    
    local master_content="# MAFA Documentation Master Index\n\n"
    master_content="${master_content}*Generated automatically on $(date +"%B %d, %Y at %H:%M")*\n\n"
    
    master_content="${master_content}## 📚 Section Index\n\n"
    
    local sections=(
        "getting-started:🚀 Getting Started:Everything you need to get started with MAFA"
        "user-guide:👥 User Guide:Complete user documentation and workflows"
        "developer-guide:🛠️ Developer Guide:Technical documentation for developers"
        "architecture:🏗️ Architecture:System design and technical architecture"
        "operations:⚙️ Operations:Deployment, monitoring, and maintenance"
        "project:📋 Project Management:Planning, QA, and project documentation"
    )
    
    for section_info in "${sections[@]}"; do
        local section="${section_info%%:*}"
        local emoji_title="${section_info##*:}"
        local description="${emoji_title##*:}"
        emoji_title="${emoji_title%%:*}"
        
        local section_dir="$DOCS_DIR/$section"
        if [[ -d "$section_dir" ]]; then
            local file_count=$(find "$section_dir" -name "*.md" -type f | wc -l)
            master_content="${master_content}### [$emoji_title](./$section/README.md)\n"
            master_content="${master_content}$description\n"
            master_content="${master_content}- *$file_count documents*\n\n"
        fi
    done
    
    # Add statistics
    local total_files=$(find "$DOCS_DIR" -name "*.md" -type f | wc -l)
    local total_dirs=$(find "$DOCS_DIR" -type d | wc -l)
    
    master_content="${master_content}## 📊 Statistics\n\n"
    master_content="${master_content}- **Total Documents**: $total_files\n"
    master_content="${master_content}- **Total Sections**: $((total_dirs - 1))  # Exclude docs root\n"
    master_content="${master_content}- **Last Updated**: $(date +"%B %d, %Y")\n"
    master_content="${master_content}- **Update Tool**: Documentation Index Updater v1.0\n\n"
    
    master_content="${master_content}## 🔧 Maintenance\n\n"
    master_content="${master_content}This index is automatically generated and updated by the documentation maintenance tools.\n\n"
    master_content="${master_content}To regenerate this index:\n"
    master_content="${master_content}\`\`\`bash\n"
    master_content="${master_content}./scripts/update-docs-index.sh\n"
    master_content="${master_content}\`\`\`\n"
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_purple "DRY RUN: Would create master index at INDEX.md"
        ((SKIPPED_FILES++))
    else
        echo -e "$master_content" > "$master_index"
        log_success "Created master documentation index"
        ((CREATED_FILES++))
    fi
}

#==============================================================================
# Main Execution
#==============================================================================

main() {
    log_info "Starting documentation index update..."
    log_info "Documentation directory: $DOCS_DIR"
    log_info "Dry run mode: $DRY_RUN"
    log_info "Output format: $OUTPUT_FORMAT"
    log_info "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Update README.md
    update_readme_toc
    
    # Process all sections
    process_all_sections
    
    # Generate master index
    generate_master_index
    
    # Print summary
    echo
    log_info "=== INDEX UPDATE SUMMARY ==="
    log_info "Updated Files: $UPDATED_FILES"
    log_info "Created Files: $CREATED_FILES"
    log_info "Skipped Files: $SKIPPED_FILES"
    log_info "Backup Directory: $BACKUP_DIR"
    
    if [[ $((UPDATED_FILES + CREATED_FILES)) -gt 0 ]]; then
        log_success "✅ Documentation indexes updated successfully!"
        exit 0
    else
        log_info "ℹ️  No index updates were necessary"
        exit 0
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "MAFA Documentation Index Updater"
        echo
        echo "Usage: $0 [OPTIONS]"
        echo
        echo "Options:"
        echo "  --help, -h          Show this help message"
        echo "  --docs-dir DIR      Set documentation directory (default: docs)"
        echo "  --templates-dir DIR Set templates directory (default: docs/templates)"
        echo "  --backup-dir DIR    Set backup directory (default: docs/.index-backups)"
        echo "  --dry-run           Preview changes without applying them"
        echo "  --format FORMAT     Output format: console|json (default: console)"
        echo
        echo "Environment Variables:"
        echo "  DOCS_DIR            Documentation directory path"
        echo "  TEMPLATES_DIR       Templates directory path"
        echo "  BACKUP_DIR          Backup directory path"
        echo "  DRY_RUN             Preview mode: true|false"
        echo "  OUTPUT_FORMAT       Output format: console|json"
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
    --backup-dir)
        BACKUP_DIR="$2"
        shift 2
        ;;
    --dry-run)
        DRY_RUN="true"
        shift
        ;;
    --format)
        OUTPUT_FORMAT="$2"
        shift 2
        ;;
esac

# Run main function
main "$@"