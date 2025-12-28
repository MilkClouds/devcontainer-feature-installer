#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
tool="$root_dir/feature-install"
version_file="$root_dir/VERSION"

fail() {
    echo "FAIL: $*" >&2
    exit 1
}

assert_eq() {
    local expected="$1"
    local actual="$2"
    local label="$3"
    if [ "$expected" != "$actual" ]; then
        echo "FAIL: $label" >&2
        echo "  expected: $expected" >&2
        echo "  actual:   $actual" >&2
        exit 1
    fi
}

assert_contains_in_order() {
    local text="$1"
    local first="$2"
    local second="$3"
    local label="$4"
    local first_line
    local second_line
    first_line="$(printf "%s\n" "$text" | grep -n -m1 -F "$first" | cut -d: -f1 || true)"
    second_line="$(printf "%s\n" "$text" | grep -n -m1 -F "$second" | cut -d: -f1 || true)"
    if [ -z "$first_line" ] || [ -z "$second_line" ] || [ "$first_line" -ge "$second_line" ]; then
        echo "FAIL: $label" >&2
        echo "  output:" >&2
        printf "%s\n" "$text" >&2
        exit 1
    fi
}

version="$("$tool" --version)"
assert_eq "$(cat "$version_file")" "$version" "version matches VERSION"

dry_dep="$("$tool" --dry-run "$root_dir/test/fixtures/dep-a")"
assert_contains_in_order "$dry_dep" "dep-b" "dep-a" "dependsOn order"

dry_after="$("$tool" --dry-run "$root_dir/test/fixtures/ia-b" "$root_dir/test/fixtures/ia-c")"
assert_contains_in_order "$dry_after" "ia-b" "ia-c" "installsAfter order"

set +e
"$tool" --dry-run \
    --features "{\"$root_dir/test/fixtures/conflict-e\":{\"opt\":\"2\"},\"$root_dir/test/fixtures/conflict-a\":{}}" \
    >/dev/null 2>&1
status=$?
set -e
if [ "$status" -eq 0 ]; then
    fail "conflict detection should fail"
fi

tmp_dir="$(mktemp -d)"
output_file="$tmp_dir/install.log"
export OUTPUT_FILE="$output_file"

"$tool" "$root_dir/test/fixtures/dep-a"
install_log="$(cat "$output_file")"
assert_contains_in_order "$install_log" "dep-b" "dep-a" "install order"

echo "OK"
