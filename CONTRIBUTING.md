# Contributing

Thanks for your interest in improving `feature-install`.

## Development

Requirements:
- bash
- jq
- bats
- shellcheck

Run tests:

```bash
bats test/feature-install.bats
```

Run lint:

```bash
make lint
```

## Release

1. Update `VERSION`
2. Update `CHANGELOG.md`
3. Tag the release
