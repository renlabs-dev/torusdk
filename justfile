# justfile for torusdk
# Shell safety everywhere:
set shell := ["bash", "-eu", "-o", "pipefail", "-c"]

# Load .env if present (secrets like PYPI_API_TOKEN, etc.)
set dotenv-load := true

# === Variables ===

# Directory where Towncrier news fragments live:
FRAG_DIR := "changes"

# Supported Towncrier fragment types (see pyproject and towncrier docs)
FRAG_TYPES := "feature bugfix doc removal misc security"

# ==== Meta/Help ====

# List all recipes with docstrings
default:
    @just --list

# Print full details for a recipe: `just help lint`
# Example: just help news
help target:
    @just --show {{target}}

# ==== Environment ====

# Create venv and install deps (includes dev/lint groups if configured in [tool.uv])
# Use this first after cloning.
boot:
    uv venv
    uv sync

# Sync dependencies (respecting lockfile)
sync:
    uv sync

# Install dependencies (alias for sync)
install: sync

# Update dependencies
update:
    uv lock --upgrade

# ==== Code Quality ====

# Check formatting without changing files
fmt-check:
    uv run ruff format --check ./src

# Format files
fmt:
    uv run ruff format ./src

# Static analysis: lints + types (CI and local)
lint:
    uv run ruff check ./src

# Run typechecker
typecheck:
    uv run basedpyright ./src

# Run all checks
check: lint typecheck fmt-check

# ==== Tests & Coverage ====

# Run tests (when they exist)
test:
    uv run pytest -q

# Coverage in terminal + XML (coverage.xml) for CI artifacts
cov:
    uv run pytest --cov=torusdk --cov-report=term-missing --cov-report=xml

# Optional HTML coverage report
cov-html:
    uv run pytest --cov=torusdk --cov-report=html

# ==== Build & Release ====

# Build sdist & wheels
build:
    uv build

# Clean build artifacts
clean:
    rm -rf __pycache__
    rm -rf .pytest_cache
    rm -rf .ruff_cache
    rm -rf dist
    rm -rf build
    rm -rf *.egg-info

# Publish to PyPI (expects PYPI_API_TOKEN in env)
publish:
    uv publish --token "${PYPI_API_TOKEN:?Missing PYPI_API_TOKEN}"

# Preview changelog from fragments without writing files
changelog-preview:
    uv run towncrier build --draft --version unreleased

# Cut a release: bump version, rebuild lock, generate CHANGELOG, tag commit
# Usage: just release 0.3.0
release VERSION:
    @echo "Releasing {{VERSION}}"
    sed -i.bak -E 's/^version = ".*"/version = "{{VERSION}}"/' pyproject.toml && rm pyproject.toml.bak
    uv lock --upgrade
    uv run towncrier build --yes --version "{{VERSION}}"
    git add CHANGELOG.md pyproject.toml uv.lock
    git commit -m "release: {{VERSION}}"
    git tag "v{{VERSION}}"

# ==== Towncrier: News Fragments ====

# Create a news fragment:
#   just news TYPE "Message" [ISSUE]
# Examples:
#   just news feature "Add foo()" 123
#   just news bugfix "Fix bar edge-case"
# If ISSUE omitted, makes an orphan fragment (+…)
news TYPE MESSAGE ISSUE="":
    @case " {{FRAG_TYPES}} " in \
      *" {{TYPE}} "*) : ;; \
      *) echo "Invalid TYPE '{{TYPE}}'. Allowed: {{FRAG_TYPES}}"; exit 1 ;; \
    esac
    mkdir -p "{{FRAG_DIR}}"
    if [ -n "{{ISSUE}}" ]; then \
      FILE="{{FRAG_DIR}}/{{ISSUE}}.{{TYPE}}.md"; \
    else \
      FILE="{{FRAG_DIR}}/+.{{TYPE}}.md"; \
    fi
    # Use towncrier's official CLI to create/populate the fragment:
    uv run towncrier create --no-edit --content "{{MESSAGE}}" "${FILE}"
    @echo "Created ${FILE}"

# Open the new fragment in $EDITOR instead of passing content:
#   just news-edit TYPE [ISSUE]
news-edit TYPE ISSUE="":
    @case " {{FRAG_TYPES}} " in \
      *" {{TYPE}} "*) : ;; \
      *) echo "Invalid TYPE '{{TYPE}}'. Allowed: {{FRAG_TYPES}}"; exit 1 ;; \
    esac
    mkdir -p "{{FRAG_DIR}}"
    if [ -n "{{ISSUE}}" ]; then \
      FILE="{{FRAG_DIR}}/{{ISSUE}}.{{TYPE}}.md"; \
    else \
      FILE="{{FRAG_DIR}}/+.{{TYPE}}.md"; \
    fi
    uv run towncrier create --edit "${FILE}"
    @echo "Created ${FILE} and opened \$EDITOR"

# Verify that the branch adds at least one fragment vs origin/main
news-check:
    uv run towncrier check --compare-with origin/main

# ==== Documentation ====

# Run documentation server locally
docs-run:
    @echo "URL: http://localhost:8080/torusdk"
    uv run pdoc -n --docformat google ./src/torusdk

# Generate documentation to files
docs-generate:
    uv run pdoc torusdk \
        --docformat google \
        --output-directory ./docs/_build \
        --favicon /assets/favicon.ico \
        --logo-link https://github.com/renlabs-dev/torusdk \
        --logo /assets/logo.png \
        --edit-url torusdk=https://github.com/renlabs-dev/torusdk/blob/main/src/torusdk/

# Copy documentation assets
docs-copy-assets:
    mkdir -p ./docs/_build/assets
    cp -r ./docs/assets ./docs/_build/

# Build documentation with assets
docs-build: docs-copy-assets docs-generate
    mkdir -p ./docs/_build/assets
    cp -r ./docs/assets ./docs/_build/
    @echo "Documentation built to ./docs/_build"

# ==== Nix Integration ====

# Run command in Nix development shell
nix-run COMMAND:
    nix develop --command {{COMMAND}}

# Check Nix flake
nix-check:
    nix flake check

# Update Nix flake inputs
nix-update:
    nix flake update

# ==== CI Orchestration ====

# What CI runs for each job (matches existing Makefile)
ci:
    just lint
    just typecheck

# Full CI including build
ci-full: ci build

# Check that everything is ready for release
pre-release:
    just ci-full
    just changelog-preview
