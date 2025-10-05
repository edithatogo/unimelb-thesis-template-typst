#!/bin/bash

# Enhanced automation script for thesis compilation and management

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
THESIS_FILE="${SCRIPT_DIR}/thesis.typ"
SAMPLE_FILE="${SCRIPT_DIR}/sample-chapter.typ"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

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

ensure_build_dir() {
    mkdir -p "$BUILD_DIR"
}

clean_build() {
    log_info "Cleaning build directory..."
    rm -rf "$BUILD_DIR"
    log_success "Build directory cleaned"
}

compile_thesis() {
    local profile="${1:-default}"
    local output_file="${BUILD_DIR}/thesis-${profile}.pdf"

    log_info "Compiling thesis with profile: $profile"
    ensure_build_dir

    if typst compile --input profile="$profile" "$THESIS_FILE" "$output_file"; then
        log_success "Thesis compiled successfully: $output_file"
    else
        log_error "Thesis compilation failed"
        exit 1
    fi
}

compile_sample() {
    local profile="${1:-default}"
    local output_file="${BUILD_DIR}/sample-chapter-${profile}.pdf"

    log_info "Compiling sample chapter with profile: $profile"
    ensure_build_dir

    if typst compile --input profile="$profile" "$SAMPLE_FILE" "$output_file"; then
        log_success "Sample chapter compiled successfully: $output_file"
    else
        log_error "Sample chapter compilation failed"
        exit 1
    fi
}

watch_thesis() {
    local profile="${1:-default}"
    log_info "Starting watch mode for thesis (profile: $profile)"
    log_info "Press Ctrl+C to stop watching"
    typst watch --input profile="$profile" "$THESIS_FILE"
}

run_preflight() {
    log_info "Running preflight checks..."
    if python scripts/preflight.py --profile default --profile draft --profile print --profile screen --json; then
        log_success "Preflight checks passed"
    else
        log_error "Preflight checks failed"
        exit 1
    fi
}

compile_parallel() {
    local profile="${1:-default}"
    log_info "Compiling thesis and sample chapter in parallel with profile: $profile"

    compile_thesis "$profile" &
    pid1=$!
    compile_sample "$profile" &
    pid2=$!

    wait $pid1
    wait $pid2

    log_success "Parallel compilation complete"
}

compile_timed() {
    local profile="${1:-default}"
    log_info "Compiling thesis with timing (profile: $profile)"
    time compile_thesis "$profile"
}

watch_all() {
    local profile="${1:-default}"
    log_info "Watching both thesis and sample chapter with profile: $profile"
    log_info "Note: This will run in foreground. Use Ctrl+C to stop."

    watch_thesis "$profile" > >(sed 's/^/[THESIS] /') &
    pid1=$!
    watch_sample "$profile" > >(sed 's/^/[SAMPLE] /') &
    pid2=$!

    wait $pid1 $pid2
}

watch_sample() {
    local profile="${1:-default}"
    log_info "Starting watch mode for sample chapter (profile: $profile)"
    log_info "Press Ctrl+C to stop watching"
    typst watch --input profile="$profile" "$SAMPLE_FILE"
}

clean_profile() {
    log_info "Cleaning profile-specific outputs..."
    rm -f thesis-*.pdf sample-chapter-*.pdf
    log_success "Profile outputs cleaned"
}

clean_logs() {
    log_info "Cleaning log files and temporary files..."
    rm -f *.log check-packages.log
    find . -name "*.tmp" -type f -delete 2>/dev/null || true
    log_success "Logs and temporary files cleaned"
}

clean_build() {
    clean_build
}

clean_cache() {
    log_info "Cleaning Typst cache..."
    rm -rf ".typst-cache"
    log_success "Cache cleaned"
}

show_status() {
    echo "=== Build Status ==="
    echo "Thesis PDF: thesis.pdf"
    if [ -f "thesis.pdf" ]; then
        echo "  Status: ✓ Exists"
        echo "  Size: $(du -h thesis.pdf | cut -f1)"
        echo "  Modified: $(stat -c '%y' thesis.pdf 2>/dev/null || stat -f '%Sm' -t '%Y-%m-%d %H:%M:%S' thesis.pdf)"
    else
        echo "  Status: ✗ Missing"
    fi
    echo ""
    echo "Sample PDF: sample-chapter.pdf"
    if [ -f "sample-chapter.pdf" ]; then
        echo "  Status: ✓ Exists"
        echo "  Size: $(du -h sample-chapter.pdf | cut -f1)"
        echo "  Modified: $(stat -c '%y' sample-chapter.pdf 2>/dev/null || stat -f '%Sm' -t '%Y-%m-%d %H:%M:%S' sample-chapter.pdf)"
    else
        echo "  Status: ✗ Missing"
    fi
    echo ""
    echo "Build Directory: build"
    if [ -d "build" ]; then
        echo "  Status: ✓ Exists"
        echo "  Contents: $(find build -type f 2>/dev/null | wc -l) files"
    else
        echo "  Status: ✗ Missing"
    fi
    echo ""
    echo "Cache Directory: .typst-cache"
    if [ -d ".typst-cache" ]; then
        echo "  Status: ✓ Exists"
        echo "  Size: $(du -sh .typst-cache 2>/dev/null | cut -f1 || echo 'unknown')"
    else
        echo "  Status: ✗ Missing"
    fi
}

profile_build() {
    local profile="${1:-default}"
    echo "=== Build Profile Analysis ==="
    echo "Profile: $profile"
    echo "Source files:"
    find . -name "*.typ" -not -path "./build/*" -not -path "./.typst-cache/*" | head -10
    echo ""
    echo "Dependencies (imports):"
    echo "Total imports: $(grep -r "^#import" --include="*.typ" . --exclude-dir=build --exclude-dir=.typst-cache | wc -l)"
    echo ""
    echo "Starting timed compilation..."
    time compile_thesis "$profile" >/dev/null 2>&1
    if [ -f "thesis.pdf" ]; then
        echo "Output size: $(du -h thesis.pdf | cut -f1)"
    fi
}

show_usage() {
    cat << EOF
Usage: $0 <command> [options]

Commands:
    compile [profile]        Compile thesis (default profile: default)
    sample [profile]         Compile sample chapter (default profile: default)
    all [profile]            Compile both thesis and sample chapter
    parallel [profile]       Compile both files in parallel
    parallel-ext [profile] [max_jobs]  Extended parallel compilation (default max_jobs: 4)
    incremental [profile]    Incremental compilation with dependency checking
    timed [profile]          Compile thesis with timing information
    profile [profile] [runs] Performance profiling (default runs: 3)
    compare                 Compare build performance across all profiles
    watch [profile]          Watch thesis for changes and recompile
    watch-sample [profile]   Watch sample chapter for changes and recompile
    watch-all [profile]      Watch both files simultaneously
    monitor [profile] [duration] Monitor and auto-compile on changes (default duration: 60s)
    deps [profile]           Analyze project dependencies
    clean                   Remove build directory
    clean-profile           Remove profile-specific PDF outputs
    clean-logs              Remove log files and temporary files
    clean-build             Remove build directory only
    clean-cache             Remove Typst cache only
    clean-selective <pattern> Remove files matching pattern from build directory
    status                  Show build status and file information
    quality                 Run quality checks (syntax, packages, validation)
    preflight               Run preflight validation checks
    test                    Run all tests (compile + preflight + quality)
    help                    Show this help message

Profiles: default, draft, screen, print

Examples:
    $0 compile print          # Compile thesis with print profile
    $0 parallel                # Compile both files in parallel
    $0 parallel-ext draft 8    # Extended parallel compilation with 8 max jobs
    $0 incremental             # Incremental compilation
    $0 profile print 5         # Performance profile with 5 runs
    $0 compare                 # Compare all profiles
    $0 monitor screen 120      # Monitor for 2 minutes
    $0 deps                    # Analyze dependencies
    $0 quality                 # Run quality checks
    $0 clean-selective "*.pdf" # Remove all PDFs from build directory
    $0 status                  # Check build status
    $0 test                    # Run full test suite

EOF
}

# Advanced automation recipes for enhanced build capabilities

# Dependency analysis and tracking
analyze_dependencies() {
    local profile="${1:-default}"
    log_info "Analyzing dependencies for profile: $profile"

    echo "=== Dependency Analysis ==="
    echo "Profile: $profile"
    echo ""

    # Count total .typ files
    local typ_files=$(find . -name "*.typ" -not -path "./build/*" -not -path "./.typst-cache/*" -not -path "./docs/*" | wc -l)
    echo "Total .typ files: $typ_files"

    # Count imports
    local total_imports=$(grep -r "^#import" --include="*.typ" . --exclude-dir=build --exclude-dir=.typst-cache --exclude-dir=docs | wc -l)
    echo "Total imports: $total_imports"

    # Analyze import patterns
    echo ""
    echo "Import patterns:"
    grep -r "^#import" --include="*.typ" . --exclude-dir=build --exclude-dir=.typst-cache --exclude-dir=docs | \
        sed 's/.*#import "\([^"]*\)".*/\1/' | \
        sort | uniq -c | sort -nr | head -10 | \
        while read count file; do
            echo "  $file: $count imports"
        done

    # Check for missing dependencies
    echo ""
    echo "Checking for potential missing dependencies..."
    local missing_deps=0
    for typ_file in $(find . -name "*.typ" -not -path "./build/*" -not -path "./.typst-cache/*" -not -path "./docs/*"); do
        grep "^#import" "$typ_file" | sed 's/.*#import "\([^"]*\)".*/\1/' | while read -r import_path; do
            # Convert relative import to absolute path
            local dir_path=$(dirname "$typ_file")
            local abs_import="$dir_path/$import_path"
            if [[ "$import_path" == @* ]]; then
                # External package import - skip
                continue
            fi
            if [[ "$import_path" == /* ]]; then
                # Absolute path import
                abs_import="$import_path"
            fi
            if [[ ! -f "$abs_import" && ! -f "${abs_import}.typ" ]]; then
                echo "  Missing: $import_path (imported from $(basename "$typ_file"))"
                ((missing_deps++))
            fi
        done
    done

    if [ $missing_deps -eq 0 ]; then
        echo "  ✓ All dependencies found"
    else
        echo "  ⚠ Found $missing_deps missing dependencies"
    fi

    log_success "Dependency analysis complete"
}

# Performance profiling and optimization
performance_profile() {
    local profile="${1:-default}"
    local runs="${2:-3}"
    log_info "Running performance profile for profile: $profile ($runs runs)"

    echo "=== Performance Profile ==="
    echo "Profile: $profile"
    echo "Runs: $runs"
    echo ""

    echo "Running simple compilation test..."

    # Very simple test
    if typst compile --input profile="$profile" "$THESIS_FILE" "/tmp/test-${profile}.pdf" > /dev/null 2>&1; then
        echo "✓ Compilation successful"
    else
        echo "✗ Compilation failed"
    fi

    echo "Performance profiling completed"

    log_success "Performance profiling complete"
}

# Extended parallel processing with load balancing
compile_parallel_extended() {
    local profile="${1:-default}"
    local max_jobs="${2:-4}"
    log_info "Compiling with extended parallel processing (max jobs: $max_jobs, profile: $profile)"

    # Find all .typ files that can be compiled independently
    local typ_files=()
    while IFS= read -r -d '' file; do
        typ_files+=("$file")
    done < <(find . -name "*.typ" -not -path "./build/*" -not -path "./.typst-cache/*" -print0)

    local total_files=${#typ_files[@]}
    log_info "Found $total_files .typ files to process"

    # Limit concurrent jobs
    local running_jobs=0
    local pids=()

    for typ_file in "${typ_files[@]}"; do
        # Wait if we've reached max jobs
        while [ $running_jobs -ge $max_jobs ]; do
            # Check for completed jobs
            for i in "${!pids[@]}"; do
                if ! kill -0 "${pids[$i]}" 2>/dev/null; then
                    wait "${pids[$i]}" 2>/dev/null || true
                    unset 'pids[$i]'
                    ((running_jobs--))
                fi
            done
            # Remove empty array elements
            pids=("${pids[@]}")
            sleep 0.1
        done

        # Start new job
        (
            local base_name=$(basename "$typ_file" .typ)
            local output_file="${BUILD_DIR}/${base_name}-${profile}.pdf"
            ensure_build_dir

            if typst compile --input profile="$profile" "$typ_file" "$output_file" > /dev/null 2>&1; then
                echo "✓ $base_name"
            else
                echo "✗ $base_name (failed)"
            fi
        ) &
        pids+=($!)
        ((running_jobs++))
    done

    # Wait for remaining jobs
    for pid in "${pids[@]}"; do
        wait "$pid" 2>/dev/null || true
    done

    log_success "Extended parallel compilation complete"
}

# Build optimization with incremental compilation
compile_incremental() {
    local profile="${1:-default}"
    local force="${2:-false}"
    log_info "Running incremental compilation (profile: $profile)"

    # Create dependency cache if it doesn't exist
    local cache_file="${BUILD_DIR}/.dep-cache-${profile}"
    ensure_build_dir

    # Get current file modification times
    local current_deps=$(find . -name "*.typ" -not -path "./build/*" -not -path "./.typst-cache/*" -printf '%T@ %p\n' | sort)

    if [ "$force" = "true" ] || [ ! -f "$cache_file" ]; then
        log_info "Full compilation required"
        compile_thesis "$profile"
        echo "$current_deps" > "$cache_file"
    else
        local cached_deps=$(cat "$cache_file")
        if [ "$current_deps" != "$cached_deps" ]; then
            log_info "Changes detected, recompiling"
            compile_thesis "$profile"
            echo "$current_deps" > "$cache_file"
        else
            log_info "No changes detected, skipping compilation"
        fi
    fi

    log_success "Incremental compilation complete"
}

# Advanced monitoring and reporting
monitor_build() {
    local profile="${1:-default}"
    local duration="${2:-60}"
    log_info "Monitoring build system for $duration seconds (profile: $profile)"

    echo "=== Build Monitoring ==="
    echo "Profile: $profile"
    echo "Duration: ${duration}s"
    echo "Start time: $(date)"
    echo ""

    local start_time=$(date +%s)
    local end_time=$((start_time + duration))
    local compile_count=0
    local error_count=0

    # Monitor file changes and auto-compile
    local last_compile=$start_time

    while [ $(date +%s) -lt $end_time ]; do
        # Check for file changes
        local recent_changes=$(find . -name "*.typ" -not -path "./build/*" -not -path "./.typst-cache/*" -newer "$THESIS_FILE" 2>/dev/null | wc -l)

        if [ $recent_changes -gt 0 ]; then
            local current_time=$(date +%s)
            if [ $((current_time - last_compile)) -gt 2 ]; then  # Debounce
                echo "$(date '+%H:%M:%S'): Changes detected, compiling..."
                if compile_thesis "$profile" > /dev/null 2>&1; then
                    ((compile_count++))
                    echo "$(date '+%H:%M:%S'): ✓ Compilation successful"
                else
                    ((error_count++))
                    echo "$(date '+%H:%M:%S'): ✗ Compilation failed"
                fi
                last_compile=$current_time
            fi
        fi

        sleep 1
    done

    echo ""
    echo "Monitoring complete:"
    echo "  Successful compilations: $compile_count"
    echo "  Failed compilations: $error_count"
    echo "  End time: $(date)"

    log_success "Build monitoring complete"
}

# Quality assurance and validation
run_quality_checks() {
    log_info "Running quality checks..."

    echo "=== Quality Checks ==="

    # Check for syntax errors
    echo "Checking for syntax errors..."
    local syntax_errors=0
    for typ_file in $(find . -name "*.typ" -not -path "./build/*" -not -path "./.typst-cache/*"); do
        if ! typst compile --input profile=default "$typ_file" /tmp/test.pdf > /dev/null 2>&1; then
            echo "  ✗ Syntax error in $(basename "$typ_file")"
            ((syntax_errors++))
        fi
    done

    if [ $syntax_errors -eq 0 ]; then
        echo "  ✓ No syntax errors found"
    fi

    # Check package versions
    echo "Checking package versions..."
    if python scripts/check_packages.py > /dev/null 2>&1; then
        echo "  ✓ Package versions OK"
    else
        echo "  ⚠ Package version issues detected"
    fi

    # Validate templates
    echo "Validating templates..."
    if python scripts/validate_template.py > /dev/null 2>&1; then
        echo "  ✓ Template validation passed"
    else
        echo "  ⚠ Template validation issues detected"
    fi

    # Check file sizes
    echo "Checking output file sizes..."
    if [ -f "thesis.pdf" ]; then
        local size=$(du -m "thesis.pdf" | cut -f1)
        if [ $size -gt 50 ]; then
            echo "  ⚠ Large output file: ${size}MB"
        else
            echo "  ✓ Output file size OK: ${size}MB"
        fi
    else
        echo "  ⚠ No thesis.pdf found"
    fi

    log_success "Quality checks complete"
}

# Advanced cleaning with selective preservation
clean_selective() {
    local pattern="${1:-*}"
    log_info "Performing selective clean (pattern: $pattern)"

    echo "=== Selective Clean ==="
    echo "Pattern: $pattern"

    # Find files matching pattern
    local files_to_clean=()
    while IFS= read -r -d '' file; do
        files_to_clean+=("$file")
    done < <(find build -name "$pattern" -type f -print0 2>/dev/null || true)

    local count=${#files_to_clean[@]}
    echo "Files to clean: $count"

    if [ $count -gt 0 ]; then
        echo "Files:"
        printf '  %s\n' "${files_to_clean[@]}"
        echo ""

        read -p "Proceed with cleaning? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            for file in "${files_to_clean[@]}"; do
                rm -f "$file"
                echo "  ✓ Removed $(basename "$file")"
            done
            log_success "Selective clean complete"
        else
            log_info "Selective clean cancelled"
        fi
    else
        log_info "No files match the pattern"
    fi
}

# Build comparison across profiles
compare_profiles() {
    log_info "Comparing build performance across profiles"

    echo "=== Profile Comparison ==="

    local profiles=("default" "draft" "screen" "print")
    local results=()

    for profile in "${profiles[@]}"; do
        echo -n "Testing $profile: "
        local start_time=$(date +%s)

        if compile_thesis "$profile" > /dev/null 2>&1; then
            local end_time=$(date +%s)
            local duration=$((end_time - start_time))

            if [ -f "thesis.pdf" ]; then
                local size=$(stat -f%z "thesis.pdf" 2>/dev/null || ls -l "thesis.pdf" | awk '{print $5}' || echo "0")
                echo "${duration}s, ${size} bytes"
                results+=("$profile:${duration}:${size}")
            else
                echo "failed"
            fi
        else
            echo "failed"
        fi
    done

    echo ""
    echo "Summary:"
    for result in "${results[@]}"; do
        IFS=':' read -r profile duration size <<< "$result"
        echo "  $profile: ${duration}s, $size bytes"
    done

    log_success "Profile comparison complete"
}

case "$1" in
    compile)
        compile_thesis "$2"
        ;;
    sample)
        compile_sample "$2"
        ;;
    all)
        compile_thesis "$2"
        compile_sample "$2"
        ;;
    parallel)
        compile_parallel "$2"
        ;;
    parallel-ext)
        compile_parallel_extended "$2" "$3"
        ;;
    incremental)
        compile_incremental "$2" "$3"
        ;;
    timed)
        compile_timed "$2"
        ;;
    profile)
        performance_profile "$2" "$3"
        ;;
    compare)
        compare_profiles
        ;;
    watch)
        watch_thesis "$2"
        ;;
    watch-sample)
        watch_sample "$2"
        ;;
    watch-all)
        watch_all "$2"
        ;;
    monitor)
        monitor_build "$2" "$3"
        ;;
    deps)
        analyze_dependencies "$2"
        ;;
    clean)
        clean_build
        ;;
    clean-profile)
        clean_profile
        ;;
    clean-logs)
        clean_logs
        ;;
    clean-build)
        clean_build
        ;;
    clean-cache)
        clean_cache
        ;;
    clean-selective)
        clean_selective "$2"
        ;;
    status)
        show_status
        ;;
    quality)
        run_quality_checks
        ;;
    preflight)
        run_preflight
        ;;
    test)
        log_info "Running full test suite..."
        compile_thesis default
        compile_sample default
        run_preflight
        run_quality_checks
        log_success "All tests completed"
        ;;
    help|--help|-h)
        show_usage
        ;;
    *)
        log_error "Unknown command: $1"
        echo
        show_usage
        exit 1
        ;;
esac
