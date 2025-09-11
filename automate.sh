#!/bin/bash

# =================================
# University of Melbourne Typst Thesis Template - Automation Script
# =================================

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[TASK]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "thesis.typ" ]; then
    print_error "Please run this script from the root of the thesis template directory"
    exit 1
fi

print_header "University of Melbourne Typst Thesis Template Automation"
echo "======================================================"

# Function to compile thesis
compile_thesis() {
    print_header "Compiling thesis template..."
    if typst compile thesis.typ; then
        print_status "Thesis compiled successfully!"
        return 0
    else
        print_error "Thesis compilation failed!"
        return 1
    fi
}

# Function to run validation scripts
run_validation() {
    print_header "Running validation scripts..."

    # Check if validation scripts exist
    if [ -f "scripts/validate_template.py" ]; then
        print_status "Running template validation..."
        python3 scripts/validate_template.py
    fi

    if [ -f "scripts/check_packages.py" ]; then
        print_status "Checking package compatibility..."
        python3 scripts/check_packages.py
    fi
}

# Function to check for updates
check_updates() {
    print_header "Checking for updates..."

    # Check Typst version
    if command -v typst &> /dev/null; then
        TYPST_VERSION=$(typst --version)
        print_status "Typst version: $TYPST_VERSION"
    else
        print_warning "Typst not found in PATH"
    fi

    # Check git status
    if [ -d ".git" ]; then
        print_status "Checking git status..."
        git status --porcelain
    fi
}

# Function to create backup
create_backup() {
    print_header "Creating backup..."

    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # Copy important files
    cp thesis.typ "$BACKUP_DIR/" 2>/dev/null || true
    cp -r pages/ "$BACKUP_DIR/" 2>/dev/null || true
    cp -r utils/ "$BACKUP_DIR/" 2>/dev/null || true
    cp -r assets/ "$BACKUP_DIR/" 2>/dev/null || true

    print_status "Backup created in: $BACKUP_DIR"
}

# Function to clean build artifacts
clean_artifacts() {
    print_header "Cleaning build artifacts..."

    # Remove generated PDFs
    find . -name "*.pdf" -type f -delete 2>/dev/null || true

    # Remove temporary files
    find . -name "*.tmp" -type f -delete 2>/dev/null || true
    find . -name "*.log" -type f -delete 2>/dev/null || true

    print_status "Build artifacts cleaned"
}

# Function to update packages
update_packages() {
    print_header "Checking for package updates..."

    # This would require more sophisticated package management
    # For now, just check if packages are accessible
    if [ -f "utils/style.typ" ]; then
        print_status "Package imports found in utils/style.typ"
        print_warning "Manual package updates recommended - check Typst Universe for latest versions"
    fi
}

# Main menu
show_menu() {
    echo
    echo "Available automation tasks:"
    echo "1) Compile thesis"
    echo "2) Run validation"
    echo "3) Check for updates"
    echo "4) Create backup"
    echo "5) Clean artifacts"
    echo "6) Update packages"
    echo "7) Full workflow (compile + validate)"
    echo "8) Exit"
    echo
}

# Main workflow
main_workflow() {
    compile_thesis
    run_validation
    print_status "Full workflow completed successfully!"
}

# Parse command line arguments
case "${1:-}" in
    "compile")
        compile_thesis
        ;;
    "validate")
        run_validation
        ;;
    "update")
        check_updates
        ;;
    "backup")
        create_backup
        ;;
    "clean")
        clean_artifacts
        ;;
    "packages")
        update_packages
        ;;
    "full")
        main_workflow
        ;;
    *)
        # Interactive mode
        while true; do
            show_menu
            read -p "Choose an option (1-8): " choice

            case $choice in
                1)
                    compile_thesis
                    ;;
                2)
                    run_validation
                    ;;
                3)
                    check_updates
                    ;;
                4)
                    create_backup
                    ;;
                5)
                    clean_artifacts
                    ;;
                6)
                    update_packages
                    ;;
                7)
                    main_workflow
                    ;;
                8)
                    print_status "Goodbye!"
                    exit 0
                    ;;
                *)
                    print_error "Invalid option. Please choose 1-8."
                    ;;
            esac

            echo
            read -p "Press Enter to continue..."
        done
        ;;
esac
