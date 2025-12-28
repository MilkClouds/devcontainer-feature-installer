#!/usr/bin/env bash
set -euo pipefail

fail() {
    echo "install-feature-cli: $*" >&2
    exit 1
}

require_cmd() {
    command -v "$1" >/dev/null 2>&1 || fail "Missing required command: $1"
}

require_cmd curl

repo="${FEATURE_CLI_REPO:-MilkClouds/devcontainer-feature-installer}"
ref="${FEATURE_CLI_REF:-main}"
bin_name="feature-install"
url="https://raw.githubusercontent.com/${repo}/${ref}/${bin_name}"

install_dir="/usr/local/bin"
if [ -n "${FEATURE_CLI_BIN_DIR:-}" ]; then
    install_dir="$FEATURE_CLI_BIN_DIR"
elif [ "$(id -u)" -ne 0 ]; then
    install_dir="$HOME/.local/bin"
fi

mkdir -p "$install_dir"
curl -fsSL "$url" -o "$install_dir/$bin_name"
chmod +x "$install_dir/$bin_name"

echo "Installed $bin_name to $install_dir/$bin_name"
