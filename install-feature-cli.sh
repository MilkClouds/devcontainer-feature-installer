#!/usr/bin/env bash
set -euo pipefail

fail() {
    echo "install-feature-cli: $*" >&2
    exit 1
}

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"
}

if ! command -v uv >/dev/null 2>&1; then
    echo "uv not found; installing via https://astral.sh/uv/install.sh" >&2
    require_cmd curl
    curl -fsSL https://astral.sh/uv/install.sh | sh
    if [ -d "$HOME/.local/bin" ]; then
        export PATH="$HOME/.local/bin:$PATH"
    fi
fi
require_cmd uv

repo="${FEATURE_CLI_REPO:-milkclouds/devcontainer-feature-installer}"
ref="${FEATURE_CLI_REF:-main}"
package="feature-install"
source_url="git+https://github.com/${repo}@${ref}"

bin_dir="${FEATURE_CLI_BIN_DIR:-}"

uv tool install --from "$source_url" "$package"

local_bin="$HOME/.local/bin/$package"
if [ ! -x "$local_bin" ]; then
    if [ -d "$HOME/.local/bin" ]; then
        export PATH="$HOME/.local/bin:$PATH"
    fi
    local_bin="$(command -v "$package" || true)"
fi

[ -n "$local_bin" ] || fail "Unable to locate $package after installation"

if [ -n "$bin_dir" ]; then
    mkdir -p "$bin_dir"
    cp "$local_bin" "$bin_dir/$package"
    chmod +x "$bin_dir/$package"
    local_bin="$bin_dir/$package"
fi

echo "Installed $package to $local_bin"
