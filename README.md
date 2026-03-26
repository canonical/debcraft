[![Release](https://github.com/canonical/debcraft/actions/workflows/release-publish.yaml/badge.svg?branch=main&event=push)](https://github.com/canonical/debcraft/actions/workflows/release-publish.yaml)
[![Documentation](https://github.com/canonical/debcraft/actions/workflows/docs.yaml/badge.svg?branch=main&event=push)](https://github.com/canonical/debcraft/actions/workflows/docs.yaml)
[![test](https://github.com/canonical/debcraft/actions/workflows/tests.yaml/badge.svg?branch=main&event=push)](https://github.com/canonical/debcraft/actions/workflows/tests.yaml)

# Debcraft

A _crafted experience_ for creating debs. This _remains_ an experimental project.

## Basic usage

Debcraft's build configuration is stored in a project file called `debcraft.yaml`. It
tells Debcraft how to build the upstream source, fill metadata, and package generated
files in binary deb files.

From the root of the upstream source, Debcraft creates a minimal debcraft.yaml with:

```bash
debcraft init
```

Edit the file to add packages, build instructions and metadata information to the
project file. After that, create binary deb packages with:

```bash
debcraft pack
```

## Installation

Install the current development version with:

```bash
snap install debcraft --classic --edge
```

## Documentation

There is yet to be any documentation for Debcraft as it is in early design.

## Community and support

You can report any issues or bugs on the project's [GitHub
repository](https://github.com/canonical/debcraft/issues).

Debcraft is covered by the [Ubuntu Code of
Conduct](https://ubuntu.com/community/ethos/code-of-conduct).

## Contribute to Debcraft

Debcraft is open source and part of the Canonical family. We would love your help.

If you're interested, start with the [contribution guide](HACKING.md).

We welcome any suggestions and help with the docs. The [Canonical Open Documentation
Academy](https://github.com/canonical/open-documentation-academy) is the hub for doc
development, including Debcraft docs. No prior coding experience is required.

## License and copyright

Debcraft is released under the [GPL-3.0 license](LICENSE).

© 2025 Canonical Ltd.
