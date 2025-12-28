#!/usr/bin/env bash

assert_eq() {
  local expected="$1"
  local actual="$2"
  local label="$3"
  if [ "$expected" != "$actual" ]; then
    echo "FAIL: $label" >&2
    echo "  expected: $expected" >&2
    echo "  actual:   $actual" >&2
    return 1
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
    return 1
  fi
}
