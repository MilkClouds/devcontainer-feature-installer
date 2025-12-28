from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional

import typer

from feature_install.core import (
    FeatureInstallError,
    abs_path,
    install_features,
    is_local_ref,
    read_version,
)

app = typer.Typer(
    add_completion=False,
    no_args_is_help=False,
    context_settings={"allow_interspersed_args": True},
)


def _fail(message: str) -> None:
    typer.secho(f"feature-install: {message}", err=True, fg=typer.colors.RED)
    raise typer.Exit(code=1)


def _parse_features_json(raw: str) -> Dict[str, Dict[str, object]]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FeatureInstallError(f"Invalid JSON for --features: {exc}") from exc
    if not isinstance(data, dict):
        raise FeatureInstallError("--features must be a JSON object mapping feature -> options")
    return {str(key): (value or {}) for key, value in data.items()}


def _parse_features_file(path: Path) -> Dict[str, Dict[str, object]]:
    if not path.exists():
        raise FeatureInstallError(f"Features file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict) and "features" in data:
        data = data["features"]
    if not isinstance(data, dict):
        raise FeatureInstallError("Features file must be a JSON object or include a features map")
    return {str(key): (value or {}) for key, value in data.items()}


def _apply_single_feature_overrides(
    features: Dict[str, Dict[str, object]],
    overrides: List[str],
) -> Dict[str, Dict[str, object]]:
    if not overrides:
        return features
    if len(features) != 1:
        raise FeatureInstallError("--set is only supported when installing a single feature")
    feature_ref = next(iter(features))
    merged = dict(features[feature_ref])
    for item in overrides:
        if "=" not in item:
            raise FeatureInstallError(f"Invalid --set value (expected key=value): {item}")
        key, value = item.split("=", 1)
        merged[key] = value
    features[feature_ref] = merged
    return features


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    feature: List[str] = typer.Argument(
        None,
        help="Feature refs or local paths.",
    ),
    features: Optional[str] = typer.Option(
        None,
        "--features",
        help="JSON map of feature refs to options.",
    ),
    features_file: Optional[Path] = typer.Option(
        None,
        "--features-file",
        exists=False,
        help="Path to devcontainer.json or features JSON file.",
    ),
    set_option: List[str] = typer.Option(
        None,
        "--set",
        "-s",
        help="Option key=value (single-feature only).",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Print install order without executing install.sh.",
    ),
    version: bool = typer.Option(
        False,
        "--version",
        help="Show version and exit.",
    ),
) -> None:
    if version:
        typer.echo(read_version())
        raise typer.Exit()

    if ctx.invoked_subcommand is not None:
        return

    if features and features_file:
        _fail("Use only one of --features or --features-file")

    try:
        if features_file:
            feature_map = _parse_features_file(features_file)
        elif features:
            feature_map = _parse_features_json(features)
        else:
            if not feature:
                raise FeatureInstallError("No features provided.")
            feature_map = {ref: {} for ref in feature}

        normalized: Dict[str, Dict[str, object]] = {}
        for ref, opts in feature_map.items():
            if is_local_ref(ref):
                ref = abs_path(ref)
            normalized[ref] = dict(opts or {})

        normalized = _apply_single_feature_overrides(normalized, set_option or [])
        order = install_features(normalized, dry_run=dry_run)
    except FeatureInstallError as exc:
        _fail(str(exc))
        return

    if dry_run:
        typer.echo("Install order:")
        for item in order:
            typer.echo(f"  {item}")


if __name__ == "__main__":
    app()
