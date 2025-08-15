# Towncrier News Fragments

This directory contains changelog fragments that will be automatically assembled into `CHANGELOG.md` during releases.

## Creating Fragments

Use the justfile commands to create fragments:

```sh
# Create a feature fragment with issue number
just news feature "Add new CLI command" 123

# Create a bugfix fragment without issue number (orphan)
just news bugfix "Fix edge case in validation"

# Edit fragment in your editor
just news-edit security 456
```

## Fragment Types

- **feature**: New features and enhancements
- **bugfix**: Bug fixes
- **doc**: Documentation updates
- **removal**: Deprecated feature removals
- **misc**: Miscellaneous changes
- **security**: Security-related fixes

## File Naming

- With issue: `{issue}.{type}.md` (e.g., `123.feature.md`)
- Without issue: `+.{type}.md` (e.g., `+.bugfix.md`)

## Content Format

Each fragment should contain a single line describing the change:

```md
Add support for custom network endpoints in CLI configuration
```

## Processing

Fragments are processed during releases using:

```sh
just changelog-preview  # Preview changes
just release 0.3.0      # Generate changelog and create release
```

After processing, fragments are removed and their content is added to `CHANGELOG.md`.
