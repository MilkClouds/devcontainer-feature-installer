# feature-install

Install devcontainer Features directly inside Dockerfiles and build steps,
without dragging a full devcontainer workflow along for the ride.

WARNING: This project is designed to run inside container builds only.
Do not run it on a host system.

It pulls Features from OCI registries (e.g., GHCR) and runs each Feature's
`install.sh` with option values exported as environment variables.

## Install (containers only)

Use `/bin` inside containers:

```bash
RUN FEATURE_CLI_BIN_DIR=/bin \
  curl -fsSL https://raw.githubusercontent.com/milkclouds/devcontainer-feature-installer/main/install-feature-cli.sh | bash
```

Run this only inside containers (Dockerfile build or devcontainer image build).

## Install (uv tool, containers only)

```bash
RUN uv tool install --from git+https://github.com/milkclouds/devcontainer-feature-installer
```

## Quick start (single feature, readable CLI)

```bash
RUN feature-install ghcr.io/milkclouds/devcontainer-features/python-tools:0.1.4 \
  --set tools=ruff
```

## Advanced usage

Multiple features with options:

```bash
RUN feature-install --features '{
  "ghcr.io/milkclouds/devcontainer-features/system-tools:0.1.4": {},
  "ghcr.io/milkclouds/devcontainer-features/python-tools:0.1.4": {"tools":"ruff"}
}'
```

Read from devcontainer.json:

```bash
RUN feature-install --features-file devcontainer.json
```

Dry-run install order:

```bash
RUN feature-install --dry-run ghcr.io/milkclouds/devcontainer-features/system-tools:0.1.4
```

Local feature paths:

```bash
RUN feature-install ./src/system-tools ./src/python-tools
```

## Dockerfile example

```Dockerfile
RUN uv tool install --from git+https://github.com/milkclouds/devcontainer-feature-installer \
    && feature-install ghcr.io/milkclouds/devcontainer-features/system-tools:0.1.4 \
    && feature-install ghcr.io/milkclouds/devcontainer-features/python-tools:0.1.4 --set tools=ruff
```

## Requirements

- Python 3.9+
- `bash` (to execute `install.sh`)
- `oras` (auto-downloaded if missing)
- `uv` (installation)

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

Runner:
- `ORAS_BIN` to use a specific `oras` binary

## Limitations

- `installsAfter` does not auto-add new features

## Tests

```bash
python -m pytest
```

## CI

Workflow lives at `.github/workflows/ci.yaml`.

## License

MIT. See `LICENSE`.
