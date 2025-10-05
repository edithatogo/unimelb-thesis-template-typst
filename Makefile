# Makefile for University of Melbourne Thesis Template
# Provides automated compile/watch/clean recipes with profile support

.PHONY: help compile compile-sample compile-all compile-parallel compile-timed watch watch-sample watch-all clean clean-all clean-profile clean-logs clean-build clean-cache full-clean profiles test validate status profile-build

# Default target
help:
	@echo "University of Melbourne Thesis Template Build System"
	@echo ""
	@echo "Available targets:"
	@echo "  compile [PROFILE=<profile>]     - Compile thesis with optional profile"
	@echo "  compile-sample [PROFILE=<profile>] - Compile sample chapter with optional profile"
	@echo "  compile-all [PROFILE=<profile>] - Compile both thesis and sample chapter"
	@echo "  compile-parallel [PROFILE=<profile>] - Compile both files in parallel"
	@echo "  compile-timed [PROFILE=<profile>] - Compile thesis with timing information"
	@echo "  watch [PROFILE=<profile>]       - Watch thesis for changes and recompile"
	@echo "  watch-sample [PROFILE=<profile>] - Watch sample chapter for changes and recompile"
	@echo "  watch-all [PROFILE=<profile>]   - Watch both files simultaneously"
	@echo "  clean                           - Remove generated PDF files"
	@echo "  clean-all                       - Remove all generated files and caches"
	@echo "  clean-profile                   - Remove profile-specific PDF outputs"
	@echo "  clean-logs                      - Remove log files and temporary files"
	@echo "  clean-build                     - Remove build directory only"
	@echo "  clean-cache                     - Remove Typst cache only"
	@echo "  full-clean                      - Alias for clean-all"
	@echo "  profiles                        - List available build profiles"
	@echo "  status                          - Show build status and file information"
	@echo "  profile-build [PROFILE=<profile>] - Analyze build performance and dependencies"
	@echo "  test                            - Run validation tests"
	@echo "  validate                        - Run preflight validation"
	@echo "  help                            - Show this help message"
	@echo ""
	@echo "Profiles: default, draft, screen, print"
	@echo ""
	@echo "Examples:"
	@echo "  make compile PROFILE=draft        # Compile thesis with draft profile"
	@echo "  make compile-parallel             # Compile both files in parallel"
	@echo "  make watch-all PROFILE=screen     # Watch both files with screen profile"
	@echo "  make status                       # Check build status"
	@echo "  make profile-build PROFILE=print  # Analyze print build performance"

# Build profiles
PROFILES := default draft screen print
PROFILE ?= default

# File paths
THESIS_SRC := thesis.typ
SAMPLE_SRC := sample-chapter.typ
THESIS_OUT := thesis.pdf
SAMPLE_OUT := sample-chapter.pdf
BUILD_DIR := build
CACHE_DIR := .typst-cache

# Typst command with profile support
TYPST_COMPILE := typst compile --root .
TYPST_WATCH := typst watch --root .

# Validate profile
validate_profile:
	@if ! echo "$(PROFILES)" | grep -q "\b$(PROFILE)\b"; then \
		echo "Error: Invalid profile '$(PROFILE)'. Available profiles: $(PROFILES)"; \
		exit 1; \
	fi

# Compile thesis
compile: validate_profile
	@echo "Compiling thesis with profile: $(PROFILE)"
	@if [ "$(PROFILE)" = "default" ]; then \
		$(TYPST_COMPILE) $(THESIS_SRC) $(THESIS_OUT); \
	else \
		$(TYPST_COMPILE) --input profile=$(PROFILE) $(THESIS_SRC) $(THESIS_OUT); \
	fi
	@echo "Thesis compiled: $(THESIS_OUT)"

# Compile sample chapter
compile-sample: validate_profile
	@echo "Compiling sample chapter with profile: $(PROFILE)"
	@if [ "$(PROFILE)" = "default" ]; then \
		$(TYPST_COMPILE) $(SAMPLE_SRC) $(SAMPLE_OUT); \
	else \
		$(TYPST_COMPILE) --input profile=$(PROFILE) $(SAMPLE_SRC) $(SAMPLE_OUT); \
	fi
	@echo "Sample chapter compiled: $(SAMPLE_OUT)"

# Compile all
compile-all: compile compile-sample

# Parallel compilation targets
compile-parallel: validate_profile
	@echo "Compiling thesis and sample chapter in parallel with profile: $(PROFILE)"
	@if [ "$(PROFILE)" = "default" ]; then \
		($(TYPST_COMPILE) $(THESIS_SRC) $(THESIS_OUT) && echo "Thesis compiled: $(THESIS_OUT)") & \
		($(TYPST_COMPILE) $(SAMPLE_SRC) $(SAMPLE_OUT) && echo "Sample chapter compiled: $(SAMPLE_OUT)") & \
		wait; \
	else \
		($(TYPST_COMPILE) --input profile=$(PROFILE) $(THESIS_SRC) $(THESIS_OUT) && echo "Thesis compiled: $(THESIS_OUT)") & \
		($(TYPST_COMPILE) --input profile=$(PROFILE) $(SAMPLE_SRC) $(SAMPLE_OUT) && echo "Sample chapter compiled: $(SAMPLE_OUT)") & \
		wait; \
	fi
	@echo "Parallel compilation complete"

# Timed compilation
compile-timed: validate_profile
	@echo "Compiling thesis with timing (profile: $(PROFILE))"
	@time -p sh -c '\
		if [ "$(PROFILE)" = "default" ]; then \
			$(TYPST_COMPILE) $(THESIS_SRC) $(THESIS_OUT); \
		else \
			$(TYPST_COMPILE) --input profile=$(PROFILE) $(THESIS_SRC) $(THESIS_OUT); \
		fi'
	@echo "Thesis compiled with timing: $(THESIS_OUT)"

# Watch thesis
watch: validate_profile
	@echo "Watching thesis with profile: $(PROFILE)"
	@if [ "$(PROFILE)" = "default" ]; then \
		$(TYPST_WATCH) $(THESIS_SRC) $(THESIS_OUT); \
	else \
		$(TYPST_WATCH) --input profile=$(PROFILE) $(THESIS_SRC) $(THESIS_OUT); \
	fi

# Watch sample chapter
watch-sample: validate_profile
	@echo "Watching sample chapter with profile: $(PROFILE)"
	@if [ "$(PROFILE)" = "default" ]; then \
		$(TYPST_WATCH) $(SAMPLE_SRC) $(SAMPLE_OUT); \
	else \
		$(TYPST_WATCH) --input profile=$(PROFILE) $(SAMPLE_SRC) $(SAMPLE_OUT); \
	fi

# Watch both files simultaneously
watch-all: validate_profile
	@echo "Watching both thesis and sample chapter with profile: $(PROFILE)"
	@echo "Note: This will run in foreground. Use Ctrl+C to stop."
	@if [ "$(PROFILE)" = "default" ]; then \
		($(TYPST_WATCH) $(THESIS_SRC) $(THESIS_OUT) 2>&1 | sed 's/^/[THESIS] /') & \
		($(TYPST_WATCH) $(SAMPLE_SRC) $(SAMPLE_OUT) 2>&1 | sed 's/^/[SAMPLE] /') & \
		wait; \
	else \
		($(TYPST_WATCH) --input profile=$(PROFILE) $(THESIS_SRC) $(THESIS_OUT) 2>&1 | sed 's/^/[THESIS] /') & \
		($(TYPST_WATCH) --input profile=$(PROFILE) $(SAMPLE_SRC) $(SAMPLE_OUT) 2>&1 | sed 's/^/[SAMPLE] /') & \
		wait; \
	fi

# Clean generated PDFs
clean:
	@echo "Cleaning generated PDF files..."
	@rm -f $(THESIS_OUT) $(SAMPLE_OUT)
	@echo "Clean complete"

# Clean all generated files and caches
clean-all: clean
	@echo "Cleaning all generated files and caches..."
	@rm -rf $(BUILD_DIR) $(CACHE_DIR)
	@echo "Clean-all complete"

# Clean specific profile outputs
clean-profile:
	@echo "Cleaning profile-specific outputs..."
	@rm -f thesis-*.pdf sample-chapter-*.pdf
	@echo "Profile outputs cleaned"

# Clean logs and temporary files
clean-logs:
	@echo "Cleaning log files and temporary files..."
	@rm -f *.log check-packages.log
	@find . -name "*.tmp" -type f -delete 2>/dev/null || true
	@echo "Logs and temporary files cleaned"

# Clean build artifacts only
clean-build:
	@echo "Cleaning build directory..."
	@rm -rf $(BUILD_DIR)
	@echo "Build directory cleaned"

# Clean cache only
clean-cache:
	@echo "Cleaning Typst cache..."
	@rm -rf $(CACHE_DIR)
	@echo "Cache cleaned"

# Full clean (equivalent to clean-all)
full-clean: clean-all

# List available profiles
profiles:
	@echo "Available build profiles:"
	@echo "  default  - Standard thesis compilation"
	@echo "  draft    - Draft mode (faster compilation, reduced quality)"
	@echo "  screen   - Screen-optimized (digital viewing)"
	@echo "  print    - Print-optimized (high quality, CMYK colors)"

# Run validation tests
test: validate
	@echo "Running validation tests..."
	@python scripts/validate_template.py
	@python scripts/check_packages.py

# Run preflight validation
validate:
	@echo "Running preflight validation..."
	@python scripts/preflight.py

# Development targets
dev: watch

dev-sample: watch-sample

# CI targets (used by GitHub Actions)
ci-compile: compile-all

ci-validate: validate test

# Quick compile (for development)
quick: compile

quick-sample: compile-sample

# Build status reporting
status:
	@echo "=== Build Status ==="
	@echo "Thesis PDF: $(THESIS_OUT)"
	@if [ -f "$(THESIS_OUT)" ]; then \
		echo "  Status: ✓ Exists"; \
		echo "  Size: $$(du -h "$(THESIS_OUT)" | cut -f1)"; \
		echo "  Modified: $$(stat -c '%y' "$(THESIS_OUT)" 2>/dev/null || stat -f '%Sm' -t '%Y-%m-%d %H:%M:%S' "$(THESIS_OUT)")"; \
	else \
		echo "  Status: ✗ Missing"; \
	fi
	@echo ""
	@echo "Sample PDF: $(SAMPLE_OUT)"
	@if [ -f "$(SAMPLE_OUT)" ]; then \
		echo "  Status: ✓ Exists"; \
		echo "  Size: $$(du -h "$(SAMPLE_OUT)" | cut -f1)"; \
		echo "  Modified: $$(stat -c '%y' "$(SAMPLE_OUT)" 2>/dev/null || stat -f '%Sm' -t '%Y-%m-%d %H:%M:%S' "$(SAMPLE_OUT)")"; \
	else \
		echo "  Status: ✗ Missing"; \
	fi
	@echo ""
	@echo "Build Directory: $(BUILD_DIR)"
	@if [ -d "$(BUILD_DIR)" ]; then \
		echo "  Status: ✓ Exists"; \
		echo "  Contents: $$(find "$(BUILD_DIR)" -type f | wc -l) files"; \
	else \
		echo "  Status: ✗ Missing"; \
	fi
	@echo ""
	@echo "Cache Directory: $(CACHE_DIR)"
	@if [ -d "$(CACHE_DIR)" ]; then \
		echo "  Status: ✓ Exists"; \
		echo "  Size: $$(du -sh "$(CACHE_DIR)" 2>/dev/null | cut -f1 || echo 'unknown')"; \
	else \
		echo "  Status: ✗ Missing"; \
	fi

# Build profiling
profile-build: validate_profile
	@echo "=== Build Profile Analysis ==="
	@echo "Profile: $(PROFILE)"
	@echo "Source files:"
	@find . -name "*.typ" -not -path "./$(BUILD_DIR)/*" -not -path "./$(CACHE_DIR)/*" | head -10
	@echo ""
	@echo "Dependencies (imports):"
	@grep -r "^#import" --include="*.typ" . --exclude-dir=$(BUILD_DIR) --exclude-dir=$(CACHE_DIR) | wc -l | xargs echo "Total imports:"
	@echo ""
	@echo "Starting timed compilation..."
	@time -p sh -c '\
		if [ "$(PROFILE)" = "default" ]; then \
			$(TYPST_COMPILE) $(THESIS_SRC) $(THESIS_OUT) >/dev/null 2>&1; \
		else \
			$(TYPST_COMPILE) --input profile=$(PROFILE) $(THESIS_SRC) $(THESIS_OUT) >/dev/null 2>&1; \
		fi'
	@if [ -f "$(THESIS_OUT)" ]; then \
		echo "Output size: $$(du -h "$(THESIS_OUT)" | cut -f1)"; \
	fi