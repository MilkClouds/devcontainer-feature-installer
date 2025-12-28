#!/usr/bin/env bats

load './test_helper.bash'

setup() {
  root_dir="$(cd "$(dirname "${BATS_TEST_FILENAME}")/.." && pwd)"
  tool="$root_dir/feature-install"
  version_file="$root_dir/VERSION"
  tmp_dir="$(mktemp -d)"
}

teardown() {
  rm -rf "$tmp_dir"
}

@test "version matches VERSION" {
  run "$tool" --version
  [ "$status" -eq 0 ]
  assert_eq "$(cat "$version_file")" "$output" "version matches VERSION"
}

@test "dependsOn order" {
  run "$tool" --dry-run "$root_dir/test/fixtures/dep-a"
  [ "$status" -eq 0 ]
  assert_contains_in_order "$output" "dep-b" "dep-a" "dependsOn order"
}

@test "installsAfter order" {
  run "$tool" --dry-run "$root_dir/test/fixtures/ia-b" "$root_dir/test/fixtures/ia-c"
  [ "$status" -eq 0 ]
  assert_contains_in_order "$output" "ia-b" "ia-c" "installsAfter order"
}

@test "conflicting options fail" {
  run "$tool" --dry-run \
    --features "{\"$root_dir/test/fixtures/conflict-e\":{\"opt\":\"2\"},\"$root_dir/test/fixtures/conflict-a\":{}}"
  [ "$status" -ne 0 ]
  [[ "$output" == *"Option conflict for feature"* ]]
}

@test "install order when running features" {
  export OUTPUT_FILE="$tmp_dir/install.log"
  run "$tool" "$root_dir/test/fixtures/dep-a"
  [ "$status" -eq 0 ]
  install_log="$(cat "$OUTPUT_FILE")"
  assert_contains_in_order "$install_log" "dep-b" "dep-a" "install order"
}
