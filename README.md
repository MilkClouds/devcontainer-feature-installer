# feature-install

Minimal CLI to install devcontainer Features directly in a Dockerfile or a
plain container build step.

It pulls Features from OCI registries (e.g., GHCR) and runs each Feature's
`install.sh` as root with option values exported as environment variables.

## Install (one-liner)

```bash
curl -fsSL https://raw.githubusercontent.com/milkclouds/devcontainer-feature-installer/main/install-feature-cli.sh | bash
```

By default it installs to:
- `/usr/local/bin` when run as root
- `~/.local/bin` when run as a normal user

## Usage

```bash
feature-install ghcr.io/milkclouds/devcontainer-features/system-tools:0.1.4

feature-install --features '{"ghcr.io/milkclouds/devcontainer-features/python-tools:0.1.4":{"tools":"ruff"}}'

feature-install --features-file devcontainer.json

feature-install --version

feature-install --dry-run ghcr.io/milkclouds/devcontainer-features/system-tools:0.1.4
```

You can also pass local feature paths:

```bash
feature-install ./src/system-tools ./src/python-tools
```

## Dockerfile example

```Dockerfile
RUN curl -fsSL https://raw.githubusercontent.com/milkclouds/devcontainer-feature-installer/main/install-feature-cli.sh | bash \
    && feature-install --features '{"ghcr.io/milkclouds/devcontainer-features/system-tools:0.1.4": {}, "ghcr.io/milkclouds/devcontainer-features/python-tools:0.1.4": {}}'
```

## Requirements

- `bash`
- `jq`
- `curl`
- `tar`
- `oras` (auto-downloaded if missing)

## Options resolution

- Defaults come from `devcontainer-feature.json` (`options.*.default`)
- User-provided options override defaults
- Conflicting options for the same feature cause a failure
- Option names are exported as uppercase env vars
  - `tools` -> `TOOLS`
  - `myOption` -> `MYOPTION`
- `dependsOn` is resolved and dependencies are installed automatically
- `installsAfter` is respected when the referenced feature is already selected

## Environment variables

Installer:
- `FEATURE_CLI_REPO` (default: `milkclouds/devcontainer-feature-installer`)
- `FEATURE_CLI_REF` (default: `main`)
- `FEATURE_CLI_BIN_DIR` (default: `/usr/local/bin` or `~/.local/bin`)

Runner:
- `ORAS_BIN` to use a specific `oras` binary

## Limitations

- `installsAfter` does not auto-add new features

## Tests

Use `bats-core`:

```bash
bats test/feature-install.bats
```

## CI

Workflow lives at `.github/workflows/ci.yaml`.

## License

MIT. See `LICENSE`.
