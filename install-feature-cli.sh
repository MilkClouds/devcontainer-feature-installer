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

repo="${FEATURE_CLI_REPO:-milkclouds/devcontainer-feature-installer}"
ref="${FEATURE_CLI_REF:-main}"
bin_name="feature-install"
url="https://raw.githubusercontent.com/${repo}/${ref}/${bin_name}"

bin_dir="${FEATURE_CLI_BIN_DIR:-}"
if [ -z "$bin_dir" ]; then
    if [ "$(id -u)" -eq 0 ] && [ -w "/bin" ]; then
        bin_dir="/bin"
    elif [ "$(id -u)" -eq 0 ] && [ -w "/usr/local/bin" ]; then
        bin_dir="/usr/local/bin"
    else
        bin_dir="$HOME/.local/bin"
    fi
fi

mkdir -p "$bin_dir"
curl -fsSL "$url" -o "$bin_dir/$bin_name"
chmod +x "$bin_dir/$bin_name"

echo "Installed $bin_name to $bin_dir/$bin_name"
