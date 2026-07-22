# Agents

## Overview

`canonical/debcraft` is a Python CLI tool for building Debian packages with the
Crafting Experience.

## Craft apps and libraries

Debcraft is built on the following craft libraries:

| Package             | Role                                                                                          |
| ------------------- | --------------------------------------------------------------------------------------------- |
| `craft-application` | Application framework: CLI lifecycle, configuration, service management, remote build support |
| `craft-archives`    | Repository and package archive management (apt sources, keyrings)                             |
| `craft-cli`         | Terminal output, progress reporting, error formatting                                         |
| `craft-grammar`     | Architecture and platform-conditional YAML in project files                                   |
| `craft-parts`       | Part lifecycle (pull, build, overlay, stage, prime) steps, plugins                            |
| `craft-platforms`   | Platform and architecture abstractions                                                        |
| `craft-providers`   | Build environment manager for LXD and Multipass                                               |
| `craft-store`       | Store API client: upload, release, track management                                           |

The source code for these libraries is at https://github.com/canonical/<library>.

These libraries are used by other craft apps, including Charmcraft, Imagecraft,
Rockcraft, and Snapcraft.

Fixes or features that are generic or would benefit other craft apps must be made in the
correct craft library. Overriding an upstream function to fix a bug in the library isn't
acceptable.

## Development

Debcraft uses [uv](https://docs.astral.sh/uv/) for dependency management.

```bash
make setup
```

### Running tests

```bash
make test
make test-fast
uv run pytest tests/unit/path/to/test_file.py::test_name
```

Spread tests (`tests/spread/`) require additional setup and should be run for broad
changes that cannot be fully covered by unit and integration tests.

### Formatting and linting

```bash
make format
make lint
```

### Documentation

Documentation uses [Diátaxis](https://diataxis.fr) and the
[Sphinx Stack](https://github.com/canonical/sphinx-stack). Follow the
[Starcraft style guide](https://documentation.ubuntu.com/starflow/latest/how-to/starcraft-style-guide/)
and the [Canonical style guide](https://documentation.ubuntu.com/style-guide/).

```bash
make setup-docs
make docs
make lint-docs
```
