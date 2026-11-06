PYTHON ?= python3
VENV ?= venv
VENV_PYTHON := $(VENV)/bin/python
PRE_COMMIT ?= $(VENV)/bin/pre-commit
TREESTAMP ?= $(VENV)/bin/treestamp
NPM ?= npm
CLAUDE ?= claude
EVAL_CASES ?=
EVAL_REPEAT ?= 1
EVAL_OUTPUT ?= .cache/releases/skill-evals.json
OSV_SCANNER ?= osv-scanner
PLAYWRIGHT_CLI ?= playwright-cli
PLAYWRIGHT_SESSION ?= assessment
BADGE_REPO ?= ../best-practices-badge
CRITERIA_SNAPSHOT ?= .cache/criteria/site
UPSTREAM_REF ?=
RELEASE_BASE ?= HEAD^
RELEASE_HEAD ?= HEAD
RELEASE_PLAN ?= .cache/releases/plan.json
export TAG REPO RUN OSV_SCANNER
RSVG ?= rsvg-convert
PNGQUANT ?= pngquant
OXIPNG ?= oxipng
ASSETS ?= docs/assets
SVG ?=
BADGE_BUDDY := plugins/badge-buddy
PLUGINS := $(BADGE_BUDDY) plugins/starter-buddy plugins/release-buddy
# Mods: plugins of TypeScript function hooks, tested with the Claude Code CLI.
MODS := plugins/badge-progress plugins/workflow-guard
TEST_DIRS := $(foreach plugin,$(PLUGINS),tests/$(notdir $(plugin))) tests/maintenance
PY_DIRS := $(wildcard $(foreach plugin,$(PLUGINS),$(plugin)/scripts $(plugin)/skills)) $(TEST_DIRS) tools

.DEFAULT_GOAL := help

.PHONY: help setup dev-deps test check plugin-validate refresh-criteria refresh-upstream check-criteria clean
.PHONY: analyze-tests analyze-test-history
.PHONY: check-board-browser render-assets
.PHONY: eval-release-skills mod-test
.PHONY: format-deps hooks-install hooks-check hooks-uninstall
.PHONY: treestamp-check treestamp-update
.PHONY: download-criteria compare-criteria release-check checkout-upstream release-plan release-finalize dependency-scan

help: ## Show available targets.
	@awk 'BEGIN {FS = ":.*## "; printf "Usage: make <target>\n\nTargets:\n"} /^[a-zA-Z0-9_-]+:.*## / {printf "  %-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

setup: $(VENV_PYTHON) ## Create the local Python virtual environment.

$(VENV_PYTHON):
	$(PYTHON) -m venv $(VENV)

test: dev-deps ## Run plugin and maintainer tests without accessing the application website.
	@# Tests create temporary repositories; do not inherit the invoking hook's Git context.
	@git_env_vars=$$(git rev-parse --local-env-vars) && unset $$git_env_vars || exit 1; \
	for suite in $(TEST_DIRS); do \
		echo "==> $$suite"; \
		$(VENV_PYTHON) -m unittest discover -s "$$suite" -v || exit 1; \
	done

check: test ## Run tests and compile every Python source file in every plugin.
	$(VENV_PYTHON) -m compileall -q $(PY_DIRS)

eval-release-skills: setup ## Run opt-in live Claude skill evaluations (may consume paid usage).
	$(VENV_PYTHON) tests/release-buddy/run_skill_evals.py --claude "$(CLAUDE)" --output "$(EVAL_OUTPUT)" --repeat "$(EVAL_REPEAT)" $(foreach case,$(EVAL_CASES),--case "$(case)")

check-board-browser: ## Check board behavior in an open Playwright CLI tab (PLAYWRIGHT_SESSION).
	$(PLAYWRIGHT_CLI) -s=$(PLAYWRIGHT_SESSION) run-code --filename tests/badge-buddy/board-browser.js

plugin-validate: ## Validate every plugin's structure when Claude is installed.
	@for plugin in $(PLUGINS) $(MODS); do \
		echo "==> $$plugin"; \
		$(CLAUDE) plugin validate "$$plugin" || exit 1; \
	done

mod-test: ## Run the mods' tests (needs the Claude Code CLI).
	@for mod in $(MODS); do \
		echo "==> $$mod"; \
		$(CLAUDE) plugin test "$$mod" || exit 1; \
	done

dev-deps: $(VENV)/.maintenance-deps ## Install the pinned development-only dependencies.

$(VENV)/.maintenance-deps: requirements-dev.txt $(VENV_PYTHON)
	$(VENV_PYTHON) -m pip install --quiet -r requirements-dev.txt
	@touch "$@"

format-deps: node_modules/.format-deps ## Install the locked development-only formatter with npm.

node_modules/.format-deps: package.json package-lock.json
	$(NPM) ci --ignore-scripts
	@touch "$@"

hooks-install: dev-deps format-deps ## Install commit formatting and pre-push checks for this clone.
	$(PRE_COMMIT) install --install-hooks --hook-type pre-commit --hook-type pre-push

hooks-check: dev-deps format-deps ## Run formatting and quick checks against staged files.
	$(PRE_COMMIT) run --hook-stage pre-commit

hooks-uninstall: dev-deps ## Remove the installed local commit and push hooks.
	$(PRE_COMMIT) uninstall --hook-type pre-commit --hook-type pre-push

treestamp-check: dev-deps ## Check the README tree against the Git index without modifying it.
	$(TREESTAMP) check README.md

treestamp-update: dev-deps ## Refresh the README tree from the Git index using its saved settings.
	$(TREESTAMP) update README.md

download-criteria: dev-deps ## Download a complete public application snapshot.
	$(VENV_PYTHON) tools/criteria_sync.py download --snapshot "$(CRITERIA_SNAPSHOT)"

compare-criteria: dev-deps ## Compare the bundled catalog with the saved application snapshot.
	$(VENV_PYTHON) tools/criteria_sync.py compare --snapshot "$(CRITERIA_SNAPSHOT)"

refresh-criteria: dev-deps ## Verify a repository-derived candidate against the snapshot, then update the catalog.
	$(VENV_PYTHON) tools/criteria_sync.py refresh --badge-repo "$(BADGE_REPO)" --snapshot "$(CRITERIA_SNAPSHOT)"
	$(VENV_PYTHON) tools/upstream_refresh.py pins

refresh-upstream: dev-deps ## Download, compare, and refresh the criteria from $(BADGE_REPO).
	$(MAKE) download-criteria
	$(MAKE) refresh-criteria

checkout-upstream: setup ## Create a clean upstream clone at UPSTREAM_REF (default: catalog revision).
	$(VENV_PYTHON) tools/upstream_refresh.py checkout --destination "$(BADGE_REPO)" $(if $(UPSTREAM_REF),--ref "$(UPSTREAM_REF)",)

release-plan: setup ## Preview manifest version changes between RELEASE_BASE and RELEASE_HEAD.
	$(VENV_PYTHON) tools/plugin_release.py plan --base "$(RELEASE_BASE)" --head "$(RELEASE_HEAD)" --output "$(RELEASE_PLAN)"

release-finalize: setup ## Verify and publish the prepared immutable draft (REPO, TAG and RUN from its Actions summary).
	$(VENV_PYTHON) tools/finalize_release.py

dependency-scan: setup ## Scan resolved maintainer dependencies with OSV-Scanner; save evidence under .cache/dependency-scan.
	$(VENV_PYTHON) tools/scan_dependencies.py --scanner "$$OSV_SCANNER" --output .cache/dependency-scan

check-criteria: dev-deps ## Check the bundled catalog, selected checkout, and application snapshot agree.
	$(VENV_PYTHON) tools/criteria_sync.py check --badge-repo "$(BADGE_REPO)" --snapshot "$(CRITERIA_SNAPSHOT)"

release-check: dev-deps ## Explicitly verify the catalog against the live site and run local checks.
	$(MAKE) download-criteria
	$(MAKE) check-criteria
	$(MAKE) check

render-assets: ## Re-render and compress the PNG beside each SVG in ASSETS, or only SVG=<file>.
	RSVG="$(RSVG)" PNGQUANT="$(PNGQUANT)" OXIPNG="$(OXIPNG)" tools/render-assets.sh $(if $(SVG),$(SVG),$(ASSETS))

clean: ## Remove generated local test and Python cache files.
	find $(PY_DIRS) -type d -name __pycache__ -prune -exec rm -r {} + 2>/dev/null || true
	find $(PY_DIRS) -type f -name '*.pyc' -delete 2>/dev/null || true
