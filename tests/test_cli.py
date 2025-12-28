from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def run_cli(args: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(cwd / "src")
    return subprocess.run(
        [sys.executable, "-m", "feature_install", *args],
        cwd=cwd,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )


def test_version_matches_version_file(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    result = run_cli(["--version"], repo)
    assert result.returncode == 0
    version_file = (repo / "VERSION").read_text(encoding="utf-8").strip()
    assert result.stdout.strip() == version_file


def test_depends_on_order() -> None:
    repo = Path(__file__).resolve().parents[1]
    feature = repo / "test" / "fixtures" / "dep-a"
    result = run_cli(["--dry-run", str(feature)], repo)
    assert result.returncode == 0
    assert "dep-b" in result.stdout
    assert result.stdout.index("dep-b") < result.stdout.index("dep-a")


def test_installs_after_order() -> None:
    repo = Path(__file__).resolve().parents[1]
    a = repo / "test" / "fixtures" / "ia-b"
    b = repo / "test" / "fixtures" / "ia-c"
    result = run_cli(["--dry-run", str(a), str(b)], repo)
    assert result.returncode == 0
    assert result.stdout.index("ia-b") < result.stdout.index("ia-c")


def test_conflicting_options_fail() -> None:
    repo = Path(__file__).resolve().parents[1]
    conflict_e = repo / "test" / "fixtures" / "conflict-e"
    conflict_a = repo / "test" / "fixtures" / "conflict-a"
    features = {
        str(conflict_e): {"opt": "2"},
        str(conflict_a): {},
    }
    result = run_cli(["--dry-run", "--features", json.dumps(features)], repo)
    assert result.returncode != 0
    assert "Option conflict for feature" in result.stderr


def test_install_order_when_running_features(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    output_file = tmp_path / "install.log"
    env = os.environ.copy()
    env["OUTPUT_FILE"] = str(output_file)
    env["PYTHONPATH"] = str(repo / "src")
    feature = repo / "test" / "fixtures" / "dep-a"
    result = subprocess.run(
        [sys.executable, "-m", "feature_install", str(feature)],
        cwd=repo,
        env=env,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0
    install_log = output_file.read_text(encoding="utf-8")
    assert install_log.index("dep-b") < install_log.index("dep-a")


def test_single_feature_set_option() -> None:
    repo = Path(__file__).resolve().parents[1]
    feature = repo / "test" / "fixtures" / "conflict-e"
    result = run_cli(
        ["--dry-run", str(feature), "--set", "opt=3"],
        repo,
    )
    assert result.returncode == 0
