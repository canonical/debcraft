:relatedlinks: https://www.debian.org/doc/debian-policy/

.. meta::
    :description: Learn the essentials of Debcraft by packaging htop as a Debian package.


.. _craft-a-debian-package:

Craft a Debian package
======================

In this tutorial, we'll craft a Debian package for htop, a popular command-line process
viewer. We'll work through everything from project setup to Debian policy compliance.

The tutorial takes about 20 minutes to complete. It doesn't require an intimate
understanding of software packaging, but you'll need to be familiar with Linux paradigms
and using the terminal.


What we'll build
----------------

After installing the necessary tools, we'll craft a personal Debian package for htop
3.5.3. The package is considered *non-native* in the Debian world because it adds
Debian-specific files and exists independent of the upstream release.

The package won't be uploaded to any archives---htop already has an official Debian
package---but we'll craft it according to Debian policies. We'll check for compliance by
running Lintian against the package and resolving any issues raised. When we're done,
the only thing differentiating the package from its official counterpart will be the
``debian/control`` and ``debian/rules`` files, which Debcraft replaces with its own
project file.

Once you've completed the tutorial, you'll have practical experience with the Debcraft
packaging process that you can adapt and apply to your own software projects.


What you'll need
----------------

For this tutorial, you'll need:

* An AMD64 machine running Ubuntu 24.04 LTS or higher
* Super user privileges on your machine
* 10 GiB of free storage


Install Debcraft and LXD
------------------------

To begin, let's install the Debcraft snap. Open a terminal and run:

.. literalinclude:: code/craft-a-debian-package/task.yaml
    :language: bash
    :dedent: 2
    :start-at: snap install debcraft --edge --classic
    :end-at: snap install debcraft --edge --classic

Next, install and initialize LXD, which creates the environment for Debcraft builds:

.. literalinclude:: code/craft-a-debian-package/task.yaml
    :language: bash
    :dedent: 2
    :start-at: sudo snap install lxd
    :end-at: sudo lxd init --auto


Set up the project
------------------

We'll need a directory to work in. Create a directory wherever you like to keep your
software projects:

.. literalinclude:: code/craft-a-debian-package/task.yaml
    :language: bash
    :dedent: 2
    :start-at: mkdir htop
    :end-at: cd htop

Debian packages built with Debcraft are configured through a ``debcraft.yaml`` file,
called the *project file*. Let's create one with the ``init`` command:

.. literalinclude:: code/craft-a-debian-package/task.yaml
    :language: bash
    :dedent: 2
    :start-at: debcraft init
    :end-at: debcraft init

Open the generated project file with your preferred text editor. This is where we'll
work for most of the tutorial.


Describe the project
--------------------

A Debian package's project file starts with details like its name, version, and build
environment. Debcraft initialized these keys with some generic values, so let's make
them meaningful for the htop project. Replace the first stanza with the following keys:

.. literalinclude:: code/craft-a-debian-package/debcraft.yaml
    :caption: debcraft.yaml
    :language: yaml
    :start-at: name: htop
    :end-at: section: utils

Debcraft matches the ``name`` key to the parent directory, so we left this unchanged.

We set the ``version`` key to ``3.5.3-1``. Debian policy states that, for non-native
packages, a package release number should be appended to the upstream version. So, our
version number shows that we're packaging version 3.5.3 of htop, and that this is the
first revision of that version's Debian package.

The ``summary`` and ``description`` keys provide a one-line summary and a longer
description of what the software is, respectively. To represent the software as its
developers intended, we copied both descriptions from the official package.

The ``base`` key determines the features available in the Debcraft project file and the
base system used for the build environment. To make sure we're using the most current
software, we set the ``base`` key to ``ubuntu@26.04``.

We set the ``maintainer`` key to a placeholder name and e-mail address, but this
typically declares the information of the package maintainer. The
``original-maintainer`` key should always credit the upstream developer.

Lastly, we left the ``section`` key set to ``utils`` to match how the official package
is categorized.


Declare related packages
------------------------

Now that the top-level keys are in order, let's declare the htop binary and its related
packages. Replace the generated ``packages`` key with:

.. literalinclude:: code/craft-a-debian-package/debcraft.yaml
    :caption: debcraft.yaml
    :language: yaml
    :start-at: packages:
    :end-at: - strace

The suggested packages are those that provide optional features. These are shown in the
package's metadata so they can be referenced when installing the package.

You may be curious as to why we don't list any runtime dependencies here. This is
because htop only depends on dynamically linked code, known as *shared libraries* in the
Debian ecosystem, which Debcraft automatically resolves during the build. If we had any
additional dependencies, they'd be listed with the ``htop`` package's ``depends`` key.


Declare the build details
-------------------------

With our package declared, it's time to build htop from its source. We'll do so by
declaring a part, which is a piece of software or a clump of files we want to process.
Replace the generated ``parts`` key with:

.. literalinclude:: code/craft-a-debian-package/debcraft.yaml
    :caption: debcraft.yaml
    :language: yaml
    :start-at: parts:
    :end-at: - --enable-unicode

First, we declared the location of the htop source code, its format, and our desired
version with the ``source``, ``source-type``, and ``source-tag`` keys, respectively. The
htop source is hosted on GitHub, but parts can also use local files and packages as
sources. We'll see how that works later on.

Because htop is a C program built with GNU Autotools, we set the ``plugin`` key to
``autotools``. The plugin handles most of the build for us, but it isn't aware of
certain project-specific details like the build dependencies we subsequently listed with
the ``build-packages`` key. We also set the install root to the ``usr/`` directory and
enabled all the optional features for htop with the ``autotools-configure-parameters``
key.


Pack the software
-----------------

We now have everything we need for a functional Debian package. After saving the latest
changes to your project file, pack the software by running:

.. literalinclude:: code/craft-a-debian-package/task.yaml
    :language: bash
    :dedent: 2
    :start-at: debcraft pack
    :end-at: debcraft pack

The build should only take a few minutes. Once it's done, install and run the new Debian
package to make sure everything is working:

.. literalinclude:: code/craft-a-debian-package/task.yaml
    :language: bash
    :dedent: 2
    :start-at: sudo apt install ./htop_3.5.3-1_amd64.deb
    :end-at: htop

When you're done trying things out, exit the program.


Check for problems
------------------

We've verified that our package can be installed and run, but we haven't checked it for
Debian policy compliance. Let's find out what changes we'll need to make by running
Lintian:

.. literalinclude:: code/craft-a-debian-package/task.yaml
    :language: bash
    :dedent: 2
    :start-at: lintian htop_3.5.3-1_amd64.deb
    :end-at: lintian htop_3.5.3-1_amd64.deb

The output should read as follows:

.. terminal::
    :scroll:

    lintian -i htop_3.5.3-1_amd64.deb

    N:
    E: htop: no-changelog usr/share/doc/htop/changelog.Debian.gz (non-native package)
    N:
    N:   A Debian package that provides a /usr/share/doc/*pkg* directory must install a changelog file.
    N:
    N:   For native packages the best name is /usr/share/doc/*pkg*/changelog.gz.
    N:
    N:   For non-native packages the best name is /usr/share/doc/*pkg*/changelog.Debian.gz.
    N:
    N:   This tag may also be emitted when the changelog exists but does not otherwise resemble a Debian changelog.
    N:
    N:   Please refer to Changelog files and release notes (Section 12.7) in the Debian Policy Manual for details.
    N:
    N:   Visibility: error
    N:   Show-Always: no
    N:   Check: debian/changelog
    N:   Renamed from: changelog-file-missing-in-native-package debian-changelog-file-missing
    N:
    N:
    E: htop: no-copyright-file
    N:
    N:   Each binary package has to include a plain file /usr/share/doc/*pkg*/copyright
    N:
    N:   Please refer to Copyright information (Section 12.5) in the Debian Policy Manual for details.
    N:
    N:   Visibility: error
    N:   Show-Always: no
    N:   Check: debian/copyright
    N:

These issues are to be expected for a non-native package like htop, whose source code
doesn't contain any Debian-specific files. Let's inspect the package contents to see
what we're missing:

.. literalinclude:: code/craft-a-debian-package/task.yaml
    :language: bash
    :dedent: 2
    :start-at: dpkg -c htop_3.5.3-1_amd64.deb
    :end-at: dpkg -c htop_3.5.3-1_amd64.deb

The output should read as follows:

.. terminal::

    dpkg -c htop_3.5.3-1_amd64.deb

    drwxr-xr-x root/root         0 2026-11-05 15:41 usr/
    drwxr-xr-x root/root         0 2026-11-05 15:41 usr/bin/
    -rwxr-xr-x root/root    555584 2026-11-05 15:41 usr/bin/htop
    drwxr-xr-x root/root         0 2026-11-05 15:41 usr/share/
    drwxr-xr-x root/root         0 2026-11-05 15:41 usr/share/applications/
    -rw-r--r-- root/root      2797 2026-11-05 15:41 usr/share/applications/htop.desktop
    drwxr-xr-x root/root         0 2026-11-05 15:41 usr/share/icons/
    drwxr-xr-x root/root         0 2026-11-05 15:41 usr/share/icons/hicolor/
    drwxr-xr-x root/root         0 2026-11-05 15:41 usr/share/icons/hicolor/scalable/
    drwxr-xr-x root/root         0 2026-11-05 15:41 usr/share/icons/hicolor/scalable/apps/
    -rw-r--r-- root/root     11202 2026-11-05 15:41 usr/share/icons/hicolor/scalable/apps/htop.svg
    drwxr-xr-x root/root         0 2026-11-05 15:41 usr/share/man/
    drwxr-xr-x root/root         0 2026-11-05 15:41 usr/share/man/man1/
    -rw-r--r-- root/root      9959 2026-11-05 15:41 usr/share/man/man1/htop.1.gz
    drwxr-xr-x root/root         0 2026-11-05 15:41 usr/share/pixmaps/
    -rw-r--r-- root/root      2616 2026-11-05 15:41 usr/share/pixmaps/htop.png

Aside from the manual pages, which Debcraft handles automatically, our package doesn't
contain any supporting docs. We'll need to add these for our Debian package to be fully
compliant.


Add Debian policy files
-----------------------

Debian policy states that supporting docs, either from the upstream source or written
specifically for Debian archives, should be compressed and placed in the
``usr/share/doc/`` directory for your package.

Let's start with the files that are already in the htop source. Add the following
``organize`` key to the ``htop`` part:

.. literalinclude:: code/craft-a-debian-package/debcraft.yaml
    :caption: debcraft.yaml
    :language: yaml
    :start-at: parts:
    :end-at: (build)/AUTHORS: usr/share/doc/htop/
    :emphasize-lines: 19-23

This key maps the top-level docs from their location in the build directory to the
``usr/share/doc/htop/`` directory in the final package. These files aren't strictly
required, which is why they weren't flagged by Lintian, but Debian policy strongly
recommends their inclusion.

Now, let's create the copyright and changelog files:

.. literalinclude:: code/craft-a-debian-package/task.yaml
    :language: bash
    :dedent: 2
    :start-at: mkdir debian
    :end-at: touch debian/changelog.Debian debian/copyright

Both of these files have specific formatting requirements, but for our purposes, there's
no need to dive into the details. Copy the following snippets into their respective
files:

.. literalinclude:: code/craft-a-debian-package/debian/changelog.Debian
    :caption: debian/changelog.Debian

.. literalinclude:: code/craft-a-debian-package/debian/copyright
    :caption: debian/copyright

The changelog entry is just a model that demonstrates the entry format, but the
copyright file is an exact copy of the one that ships with the official htop package.

To get these files into the final package, we'll add a part that uses the ``debian/``
directory as its source. Copy the following part into your project file:

.. literalinclude:: code/craft-a-debian-package/debcraft.yaml
    :caption: debcraft.yaml
    :language: yaml
    :start-at: distro-files:
    :end-at: copyright: usr/share/doc/htop/

The Dump plugin copies the source files into the package without modifying their
content. The only other thing this part does is map the files to the correct directory,
similar to what we did for the top-level docs in the ``htop`` part.


Check the package contents
--------------------------

Let's rebuild the package so we can verify the changes:

.. literalinclude:: code/craft-a-debian-package/task.yaml
    :language: bash
    :dedent: 2
    :start-at: debcraft pack
    :end-at: debcraft pack

Once Debcraft is done repacking, inspect the package's contents again with:

.. literalinclude:: code/craft-a-debian-package/task.yaml
    :language: bash
    :dedent: 2
    :start-at: dpkg -c htop_3.5.3-1_amd64.deb
    :end-at: dpkg -c htop_3.5.3-1_amd64.deb

Along with the files from before, the output now includes:

.. terminal::
    :output-only:

    drwxr-xr-x root/root         0 2026-11-05 15:39 usr/share/doc/
    drwxr-xr-x root/root         0 2026-11-05 15:39 usr/share/doc/htop/
    -rw-r--r-- root/root       226 2026-11-05 15:39 usr/share/doc/htop/AUTHORS
    -rw-r--r-- root/root       105 2026-11-05 15:39 usr/share/doc/htop/NEWS.gz
    -rw-r--r-- root/root      3477 2026-11-05 15:39 usr/share/doc/htop/README.md.gz
    -rw-r--r-- root/root       156 2026-11-05 10:38 usr/share/doc/htop/changelog.Debian.gz
    -rw-r--r-- root/root     21943 2026-11-05 15:39 usr/share/doc/htop/changelog.gz
    -rw-r--r-- root/root      1256 2026-10-07 15:23 usr/share/doc/htop/copyright

During the build, Debcraft automatically compresses the supporting docs with Gzip. The
only exceptions are the ``copyright`` file, which remains uncompressed per Debian
policy, and the ``AUTHORS`` file, which is an optional inclusion specific to htop.

To close out the tutorial, run Lintian again to confirm that the errors from before have
been resolved:

.. literalinclude:: code/craft-a-debian-package/task.yaml
    :language: bash
    :dedent: 2
    :start-at: lintian htop_3.5.3-1_amd64.deb
    :end-at: lintian htop_3.5.3-1_amd64.deb

These changes won't yield any functional differences. You can install and run htop just
as we did earlier.


Conclusion
----------

You're all done! You've built a complete, policy-compliant Debian package for htop.

Here's the complete project file if you'd like to review it:

.. dropdown:: debcraft.yaml file for htop

    .. literalinclude:: code/craft-a-debian-package/debcraft.yaml
        :language: yaml
