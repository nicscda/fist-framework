# Makefile for launching FIST Framework site.
# Supports environment-specific configurations and step filtering.

# ------------------------------------------------------------------------------
# 1. ENVIRONMENT AND CONSTANTS
# ------------------------------------------------------------------------------

# Load environment variables from .env file if it exists.
-include .env
export

# Terminal color output constants for logging.
override CYAN  := $(shell printf '\\033[36m')
override GREEN := $(shell printf '\\033[32m')
override RED   := $(shell printf '\\033[31m')
override RESET := $(shell printf '\\033[0m')

# ENV: Deployment environment (dev, prod).
# Precedence: CLI > .env file > Default
# Supports aliases: prod/production → production, others → development (default)
override ENV := $(shell echo "$(ENV)" | tr '[:upper:]' '[:lower:]')
ifneq ($(filter prod production,$(ENV)),)
override ENV := production
else ifneq ($(filter dev development,$(ENV)),)
override ENV := development
else
ifdef ENV
$(warning Unknown ENV '$(ENV)', defaulting to 'development')
endif
override ENV := development
endif

# Pipeline step definitions and filtering.
# ALL_STEPS: Complete list of available pipeline steps.
# ONLY/SKIP: User-specified inclusion/exclusion filters (via CLI).
override ALL_STEPS    := install config lint locale build assemble serve
override SKIP         := $(sort $(SKIP) $(filter-out $(ONLY),$(if $(filter production,$(ENV)),lint)))
override VALID_ONLY   := $(filter $(ALL_STEPS),$(or $(ONLY),$(ALL_STEPS)))
override FINAL_STEPS  := $(filter-out $(SKIP),$(VALID_ONLY))
override INVALID_ONLY := $(filter-out $(ALL_STEPS),$(ONLY))


# ------------------------------------------------------------------------------
# 2. BUILD CONFIGURATION
# ------------------------------------------------------------------------------

# Automatic default settings.
ifeq ($(ENV), production)
BUNDLE_DEPLOYMENT ?= true
DEBUG ?= false
override FIST := fist
override SITE := $(or $(SITE),docs)
UV_NO_DEV ?= true
UV_NO_EDITABLE ?= true
UV_NO_SYNC ?= true
UV_FROZEN ?= true
else
BUNDLE_DEPLOYMENT ?= false
DEBUG ?= true
override FIST := python -m src.cli
override SITE := $(or $(SITE),site)
endif
override JEKYLL_ENV := $(ENV)

ifeq ($(MAKELEVEL),0)
FIST_OUTPUT_DIR ?= out

# INTERACTIVE: Controls terminal features (e.g., open browser, editor prompts).
# Forced to false in CI; defaults to false in production, true in development.
ifneq ($(shell echo "$$CI"),)
override INTERACTIVE := false
else ifdef INTERACTIVE
override INTERACTIVE := $(if $(filter false no 0,$(INTERACTIVE)),false,true)
else ifeq ($(ENV), production)
override INTERACTIVE := false
else
override INTERACTIVE := true
endif

endif

NEEDED := $(MAKECMDGOALS) $(if $(filter start,$(MAKECMDGOALS)),$(FINAL_STEPS))

# ------------------------------------------------------------------------------
# 3. MAIN TARGETS
# ------------------------------------------------------------------------------

.PHONY: help start $(ALL_STEPS)
.DEFAULT_GOAL := help

help: ## Show this help message and exit.
	@echo "Usage: make start [ONLY=\"...\"] [SKIP=\"...\"] [ENV=\"dev|prod\"] [INTERACTIVE=\"true|false\"]"
	@echo ""
	@echo "Current Status:"
	@echo "  Environment : $(CYAN)$(ENV)$(RESET)"
	@echo "  Debug Mode  : $(CYAN)$(DEBUG)$(RESET)"
	@echo "  Steps       : $(CYAN)$(FINAL_STEPS)$(RESET)"
	@echo ""
	@echo "Available Commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' Makefile | sort | \
		awk -v skip="$(SKIP)" 'BEGIN {FS = ":.*?## "}; \
		{printf "$(CYAN)%-12s$(RESET) %s %s\n", $$1, $$2, (index(skip, $$1) ? "[SKIPPED]" : "")}'

start: ## Run the configured pipeline steps.
ifneq ($(INVALID_ONLY),)
	@echo "$(RED)[WARN]$(RESET) Ignoring unknown steps: $(INVALID_ONLY)"
endif
ifeq ($(FINAL_STEPS),)
	@echo "$(RED)[ERROR]$(RESET) No valid steps to execute."; exit 1
endif
	@echo "$(CYAN)[INFO]$(RESET) Starting pipeline for [$(ENV)] environment..."
	@$(foreach step,$(FINAL_STEPS),\
		"$(MAKE)" --no-print-directory $(step) \
			ENV=$(ENV) DEBUG=$(DEBUG) SITE=$(SITE) INTERACTIVE=$(INTERACTIVE);)

# ------------------------------------------------------------------------------
# 4. TASK DEFINITIONS
# ------------------------------------------------------------------------------

install: ## Install prerequisites and dependencies.
	@echo "$(CYAN)[INFO]$(RESET) Checking prerequisites..."
	@uv --version >/dev/null 2>&1 || { \
		if command -v apt-get >/dev/null 2>&1; then \
			echo "$(CYAN)[INFO]$(RESET) Installing uv..."; \
			apt-get update -qq && apt-get install -y -qq curl || { \
				echo "$(RED)[ERROR]$(RESET) Failed to install curl via apt-get."; \
				exit 1; \
			}; \
			curl -LsSf https://astral.sh/uv/install.sh | sh || { \
				echo "$(RED)[ERROR]$(RESET) Failed to install uv via curl."; \
				exit 1; \
			}; \
		elif command -v brew >/dev/null 2>&1; then \
			echo "$(CYAN)[INFO]$(RESET) Installing uv..."; \
			brew update --quiet && brew install --quiet uv >/dev/null 2>&1 || { \
				echo "$(RED)[ERROR]$(RESET) Failed to install uv via brew."; \
				exit 1; \
			}; \
		elif command -v winget >/dev/null 2>&1; then \
			echo "$(CYAN)[INFO]$(RESET) Installing uv..."; \
			winget install --id=astral-sh.uv -e || { \
				echo "$(RED)[ERROR]$(RESET) Failed to install uv via winget."; \
				exit 1; \
			}; \
		else \
			echo "$(RED)[ERROR]$(RESET) uv not found."; \
			echo "	See: https://docs.astral.sh/uv"; \
			exit 1; \
		fi; \
	}
	@gem --version >/dev/null 2>&1 || { \
		if command -v apt-get >/dev/null 2>&1; then \
			echo "$(CYAN)[INFO]$(RESET) Installing Ruby..."; \
			apt-get update -qq && apt-get install -y -qq ruby-full || { \
				echo "$(RED)[ERROR]$(RESET) Failed to install Ruby via apt-get."; \
				exit 1; \
			}; \
		elif command -v brew >/dev/null 2>&1; then \
			echo "$(CYAN)[INFO]$(RESET) Installing Ruby..."; \
			brew update --quiet && brew install --quiet ruby >/dev/null 2>&1 || { \
				echo "$(RED)[ERROR]$(RESET) Failed to install Ruby via brew."; \
				exit 1; \
			}; \
		elif command -v winget >/dev/null 2>&1; then \
			echo "$(CYAN)[INFO]$(RESET) Installing Ruby..."; \
			winget install --id=RubyInstallerTeam.Ruby.$$(head -1 .ruby-version | grep -oEm1 '[0-9]+\.[0-9]+') -e || { \
				echo "$(RED)[ERROR]$(RESET) Failed to install Ruby via winget."; \
				exit 1; \
			}; \
		else \
			echo "$(RED)[ERROR]$(RESET) Ruby not found."; \
			echo "	See: https://www.ruby-lang.org"; \
			exit 1; \
		fi; \
	}
	@bundle --version >/dev/null 2>&1 || { \
		echo "$(CYAN)[INFO]$(RESET) Installing Bundler..."; \
		gem install bundler >/dev/null 2>&1 || { \
			echo "$(RED)[ERROR]$(RESET) Failed to install Bundler."; \
			exit 1; \
		}; \
	}
	@printf "$(GREEN)[OK]$(RESET) "; uv --version
	@printf "$(GREEN)[OK]$(RESET) "; uv run python --version 2>/dev/null
	@printf "$(GREEN)[OK]$(RESET) "; ruby --version
	@printf "$(GREEN)[OK]$(RESET) Bundler "; bundle --version
ifneq ($(filter build locale serve,$(NEEDED)),)
	@echo "$(CYAN)[INFO]$(RESET) Installing dependencies..."
ifneq ($(filter build locale,$(NEEDED)),)
ifneq ($(filter locale,$(NEEDED)),)
	@command -v xgettext >/dev/null 2>&1 || { \
		if command -v apt-get >/dev/null 2>&1; then \
			echo "$(CYAN)[INFO]$(RESET) Installing gettext..."; \
			apt-get update -qq && apt-get install -y -qq gettext || { \
				echo "$(RED)[ERROR]$(RESET) Failed to install gettext via apt-get."; \
				exit 1; \
			}; \
		elif command -v brew >/dev/null 2>&1; then \
			echo "$(CYAN)[INFO]$(RESET) Installing gettext..."; \
			brew update --quiet && brew install --quiet gettext && brew link --force gettext || { \
				echo "$(RED)[ERROR]$(RESET) Failed to install gettext via brew."; \
				exit 1; \
			}; \
		elif command -v winget >/dev/null 2>&1; then \
			echo "$(CYAN)[INFO]$(RESET) Installing gettext..."; \
			winget install --id=mlocati.GetText -e || { \
				echo "$(RED)[ERROR]$(RESET) Failed to install gettext via winget."; \
				exit 1; \
			}; \
		else \
			echo "$(RED)[ERROR]$(RESET) gettext not found."; \
			echo "	See: https://www.gnu.org/software/gettext"; \
			exit 1; \
		fi; \
	}
endif
	@uv sync
	@printf "$(GREEN)[OK]$(RESET) "; uv run $(FIST) --version
endif
ifneq ($(filter serve,$(NEEDED)),)
	@bundle check || bundle install
	@printf "$(GREEN)[OK]$(RESET) "; bundle exec jekyll --version
endif
endif

config: ## Configure environment variables.
	@uv run python -c "import pathlib, shutil; not pathlib.Path('.env').exists() and shutil.copy('.env.sample', '.env');"
ifeq ($(INTERACTIVE), true)
	@uv run python -c "import os, subprocess, sys; subprocess.run([os.getenv('EDITOR', 'notepad' if 'win32'==sys.platform else 'nano'), '.env']);"
else
	@echo "$(CYAN)[INFO]$(RESET) Skipping editor (non-interactive mode)."
endif

lint: ## Lint source code.
ifeq ($(INTERACTIVE), true)
	@uv run isort .
	@uv run black .
	@uv run ruff check --fix .
else
	@uv run isort --check-only .
	@uv run black --check .
	@uv run ruff check .
endif
	@uv run --with mypy mypy .

locale: ## Compile translations and link locale files.
	@uv run $(FIST) transl
	@echo "$(CYAN)[INFO]$(RESET) Refreshing locale links..."
	@uv run python -c "\
	import shutil, os, pathlib; \
	dir = pathlib.Path('docs', '_data', 'locales'); \
	shutil.rmtree(dir, ignore_errors=True); \
	os.makedirs(dir, exist_ok=True); \
	[os.symlink(os.path.relpath(src, dir), dst) \
	for src in pathlib.Path('i18n').glob('*/locale.yaml') \
	if (lang := src.parent.name.replace('_', '-')) \
	and (dst := dir / f'{lang}.yml')];"
	@echo "$(GREEN)[OK]$(RESET) Locales linked"

build: ## Generate STIX bundle and documentation.
	@echo "$(CYAN)[INFO]$(RESET) Building artifacts..."
	@uv run $(FIST) build -R data --clean

assemble: ## Merge docs and build output into site directory.
ifeq ($(SITE),$(FIST_OUTPUT_DIR))
	@echo "$(RED)[ERROR]$(RESET) SITE and FIST_OUTPUT_DIR cannot be the same directory."; exit 1
endif
	@echo "$(CYAN)[INFO]$(RESET) Merging site source..."
	@uv run python -c "\
	import shutil, os, pathlib; \
	docs, out, site = pathlib.Path('docs'), pathlib.Path('$(FIST_OUTPUT_DIR)'), pathlib.Path('$(SITE)'); \
	docs.resolve() != site.resolve() and \
	[shutil.rmtree(site, ignore_errors=True), \
	os.makedirs(site, exist_ok=True), \
	shutil.copytree(docs, site, dirs_exist_ok=True)]; \
	pages = site / '_data' / 'pages'; \
	shutil.rmtree(pages, ignore_errors=True); \
	out.exists() and shutil.copytree(out, pages, dirs_exist_ok=True);"
	@echo "$(GREEN)[OK]$(RESET) Site assembled"

serve: ## Start Jekyll local server.
	@echo "$(CYAN)[INFO]$(RESET) Serving site..."
	bundle exec jekyll serve \
		--source "$(SITE)" \
		$(if $(filter true,$(INTERACTIVE)),--open-url) \
		$(if $(filter development,$(ENV)),--incremental --livereload)
