[![Release](https://github.com/canonical/debcraft/actions/workflows/release-publish.yaml/badge.svg?branch=main&event=push)](https://github.com/canonical/debcraft/actions/workflows/release-publish.yaml)
[![Documentation](https://github.com/canonical/debcraft/actions/workflows/docs.yaml/badge.svg?branch=main&event=push)](https://github.com/canonical/debcraft/actions/workflows/docs.yaml)
[![test](https://github.com/canonical/debcraft/actions/workflows/tests.yaml/badge.svg?branch=main&event=push)](https://github.com/canonical/debcraft/actions/workflows/tests.yaml)

# Debcraft

**Debcraft** is a command-line tool for creating Debian packages, the traditional
software format for Debian-based Linux distributions. It makes it simpler for
developers to rapidly build and iterate on packages that comply with Debian
packaging policies. It has YAML build configuration syntax including expressions
for multiple architectures, automatically populates Debian manifest files, and manages
build containers on its own.

## Basic usage

Debcraft stores its build configuration in a project file called `debcraft.yaml`.

From the root of the upstream source, Debcraft creates a minimal `debcraft.yaml` with:

```bash
debcraft init
```

After you add all your project's build and runtime details to the project file, bundle
your project into a `.deb` file with:

```bash
debcraft pack
```

## Installation

Install the latest development version with:

```bash
snap install debcraft --classic --edge
```

## Documentation

There is yet to be any documentation for Debcraft as it is in early design.

## Community and support

Ask your questions about Debcraft and what's on the horizon, and see who's working on
what in the [Debcraft Matrix channel](https://matrix.to/#/!A7c56rXV6qlYhxp9mZUqzri_eykG1WEWpb035uIGNME).

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
