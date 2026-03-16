# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright 2026 Canonical Ltd.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""Debcraft Rust plugin."""

import logging
from textwrap import dedent
from typing import cast

from craft_parts.plugins import rust_plugin
from craft_parts.plugins.rust_plugin import RustPluginProperties
from typing_extensions import override

logger = logging.getLogger(__name__)


class RustPlugin(rust_plugin.RustPlugin):
    """Debcraft-specific Rust plugin."""

    @override
    def get_build_commands(self) -> list[str]:
        """Return a list of commands to run during the build step."""
        options = cast(RustPluginProperties, self._options)

        rust_build_cmd: list[str] = []
        config_cmd: list[str] = []

        if options.rust_features:
            if "*" in options.rust_features:
                if len(options.rust_features) > 1:
                    raise ValueError(
                        "Please specify either the wildcard feature or a list of specific features"
                    )
                config_cmd.append("--all-features")
            else:
                features_string = " ".join(options.rust_features)
                config_cmd.extend(["--features", f"'{features_string}'"])

        if options.rust_use_global_lto:
            logger.info("Adding overrides for LTO support")
            config_cmd.extend(
                [
                    "--config 'profile.release.lto = true'",
                    "--config 'profile.release.codegen-units = 1'",
                ]
            )

        if options.rust_no_default_features:
            config_cmd.append("--no-default-features")

        if options.rust_cargo_parameters:
            config_cmd.extend(options.rust_cargo_parameters)

        if options.rust_inherit_ldflags:
            rust_build_cmd.append(
                dedent(
                    """\
                    if [ -n "${LDFLAGS}" ]; then
                        RUSTFLAGS="${RUSTFLAGS:-} -Clink-args=\"${LDFLAGS}\""
                        export RUSTFLAGS
                    fi\
                    """
                )
            )

        for crate in options.rust_path:
            logger.info("Generating build commands for %s", crate)
            config_cmd_string = " ".join(config_cmd)
            # pylint: disable=line-too-long
            rust_build_cmd_single = dedent(
                f"""\
                if cargo read-manifest --manifest-path "{crate}"/Cargo.toml > /dev/null; then
                    cargo install -f --locked --path "{crate}" --root "{self._part_info.part_install_dir}/usr" {config_cmd_string}
                    # remove the installation metadata
                    rm -f "{self._part_info.part_install_dir}"/usr/.crates{{.toml,2.json}}
                else
                    # virtual workspace is a bit tricky,
                    # we need to build the whole workspace and then copy the binaries ourselves
                    pushd "{crate}"
                    cargo build --workspace --release {config_cmd_string}
                    # install the final binaries
                    find ./target/release -maxdepth 1 -executable -exec install -Dvm755 {{}} "{self._part_info.part_install_dir}/usr" ';'
                    # remove proc_macro objects
                    for i in "{self._part_info.part_install_dir}"/*.so; do
                        readelf --wide --dyn-syms "$i" | grep -q '__rustc_proc_macro_decls_[0-9a-f]*__' && \
                        rm -fv "$i"
                    done
                    popd
                fi\
                """
            )
            rust_build_cmd.append(rust_build_cmd_single)
        return rust_build_cmd
