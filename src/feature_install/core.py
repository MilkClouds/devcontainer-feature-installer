from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import tarfile
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.request import urlretrieve


class FeatureInstallError(RuntimeError):
    pass


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def read_version() -> str:
    version_path = repo_root() / "VERSION"
    if version_path.exists():
        return version_path.read_text(encoding="utf-8").strip()
    return "0.0.0"


def sanitize_var_name(name: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in name.upper())


def require_command(name: str) -> None:
    if shutil.which(name) is None:
        raise FeatureInstallError(f"Missing required command: {name}")


def abs_path(path: str | Path) -> str:
    return str(Path(path).resolve())


def is_local_ref(ref: str) -> bool:
    if ref.startswith(("/", "./", "../")):
        return True
    return Path(ref).is_dir()


def ensure_valid_ref(ref: str) -> None:
    ref_no_digest = ref.split("@", 1)[0]
    if ref_no_digest.endswith(":"):
        raise FeatureInstallError("Invalid feature reference: tag is empty (e.g. use ':latest' or a version tag)")

    repo = ref_no_digest
    last_segment = repo.rsplit("/", 1)[-1]
    if ":" in last_segment:
        repo = repo.rsplit(":", 1)[0]

    if any(ch.isupper() for ch in repo):
        raise FeatureInstallError(
            "Invalid feature reference: repository path must be lowercase (e.g. ghcr.io/milkclouds/...)"
        )


def extract_feature_layer_if_needed(feature_dir: Path) -> None:
    feature_json = feature_dir / "devcontainer-feature.json"
    if feature_json.exists():
        return

    for file_path in feature_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if not tarfile.is_tarfile(file_path):
            continue
        with tarfile.open(file_path, "r:*") as tar:
            if any("devcontainer-feature.json" in member.name for member in tar.getmembers()):
                tar.extractall(feature_dir)
                return


def resolve_ref(ref: str, base_dir: Path) -> str:
    if is_local_ref(ref) or (base_dir / ref).is_dir():
        if Path(ref).is_absolute():
            return abs_path(ref)
        return abs_path(base_dir / ref)
    return ref


@dataclass
class RunContext:
    oras_tmp_dir: Optional[tempfile.TemporaryDirectory] = None
    oras_bin: Optional[str] = None
    feature_tmp_dirs: List[tempfile.TemporaryDirectory] = field(default_factory=list)

    def cleanup(self) -> None:
        if self.oras_tmp_dir is not None:
            self.oras_tmp_dir.cleanup()
        for tmp in self.feature_tmp_dirs:
            tmp.cleanup()


def ensure_oras(ctx: RunContext) -> str:
    if ctx.oras_bin:
        return ctx.oras_bin

    env_oras = os.environ.get("ORAS_BIN")
    if env_oras:
        if shutil.which(env_oras) is None:
            raise FeatureInstallError(f"ORAS_BIN is set but not found: {env_oras}")
        ctx.oras_bin = env_oras
        return env_oras

    oras_in_path = shutil.which("oras")
    if oras_in_path:
        ctx.oras_bin = "oras"
        return "oras"

    arch = platform.machine().lower()
    if arch in ("x86_64", "amd64"):
        arch = "amd64"
    elif arch in ("aarch64", "arm64"):
        arch = "arm64"
    else:
        raise FeatureInstallError(f"Unsupported architecture for oras: {arch}")

    version = "1.1.0"
    ctx.oras_tmp_dir = tempfile.TemporaryDirectory()
    tmp_dir = Path(ctx.oras_tmp_dir.name)
    tarball = tmp_dir / "oras.tar.gz"
    url = f"https://github.com/oras-project/oras/releases/download/v{version}/oras_{version}_linux_{arch}.tar.gz"

    urlretrieve(url, tarball)
    with tarfile.open(tarball, "r:gz") as tar:
        tar.extractall(tmp_dir)
    oras_path = tmp_dir / "oras"
    oras_path.chmod(0o755)
    ctx.oras_bin = str(oras_path)
    return ctx.oras_bin


def fetch_feature(feature_ref: str, ctx: RunContext) -> Path:
    if is_local_ref(feature_ref):
        feature_dir = Path(feature_ref)
        if not feature_dir.is_dir():
            raise FeatureInstallError(f"Feature path not found: {feature_dir}")
        return feature_dir

    ensure_valid_ref(feature_ref)

    oras_bin = ensure_oras(ctx)

    tmp_dir = tempfile.TemporaryDirectory()
    ctx.feature_tmp_dirs.append(tmp_dir)
    feature_dir = Path(tmp_dir.name)
    result = subprocess.run(
        [oras_bin, "pull", "--output", str(feature_dir), feature_ref],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise FeatureInstallError(result.stderr.strip() or "oras pull failed")
    extract_feature_layer_if_needed(feature_dir)
    return feature_dir


def read_depends_on(feature_json: Path) -> Iterable[Tuple[str, Dict[str, object]]]:
    data = json.loads(feature_json.read_text(encoding="utf-8"))
    depends_on = data.get("dependsOn", {}) or {}
    for ref, opts in depends_on.items():
        yield ref, opts or {}


def read_installs_after(feature_json: Path) -> List[str]:
    data = json.loads(feature_json.read_text(encoding="utf-8"))
    installs_after = data.get("installsAfter", []) or []
    return [str(item) for item in installs_after]


def feature_defaults(feature_json: Path) -> Dict[str, object]:
    data = json.loads(feature_json.read_text(encoding="utf-8"))
    defaults: Dict[str, object] = {}
    options = data.get("options", {}) or {}
    for key, value in options.items():
        defaults[key] = value.get("default", "")
    return defaults


def resolve_features(
    feature_opts: Dict[str, Dict[str, object]],
    *,
    ctx: RunContext,
) -> Tuple[List[str], Dict[str, Path], Dict[str, Dict[str, object]]]:
    feature_dirs: Dict[str, Path] = {}
    feature_seen: Dict[str, bool] = {}
    adj: Dict[str, List[str]] = {}
    installs_after: Dict[str, List[str]] = {}
    queue: List[str] = list(feature_opts.keys())
    while queue:
        ref = queue.pop(0)
        if feature_seen.get(ref):
            continue
        feature_seen[ref] = True

        dir_path = fetch_feature(ref, ctx)
        feature_dirs[ref] = dir_path

        feature_json = dir_path / "devcontainer-feature.json"
        if not feature_json.exists():
            raise FeatureInstallError(
                "Missing devcontainer-feature.json in "
                f"{dir_path} (artifact is not a devcontainer feature, ref/tag is wrong, "
                "or layer archive could not be unpacked)"
            )

        installs_after[ref] = []
        for after_ref in read_installs_after(feature_json):
            if after_ref:
                resolved_after = resolve_ref(after_ref, dir_path)
                installs_after[ref].append(resolved_after)

        for dep_ref, dep_opts in read_depends_on(feature_json):
            resolved_dep = resolve_ref(dep_ref, dir_path)
            existing_opts = feature_opts.get(resolved_dep)
            if existing_opts is None:
                feature_opts[resolved_dep] = dep_opts
            elif existing_opts != dep_opts:
                raise FeatureInstallError(
                    f"Option conflict for feature {resolved_dep}. Existing: {existing_opts} New: {dep_opts}"
                )
            adj.setdefault(resolved_dep, []).append(ref)
            queue.append(resolved_dep)

    for ref, after_refs in installs_after.items():
        for after_ref in after_refs:
            if after_ref in feature_seen:
                adj.setdefault(after_ref, []).append(ref)

    indegree: Dict[str, int] = {ref: 0 for ref in feature_seen}
    for dep_ref, nodes in adj.items():
        for node in nodes:
            indegree[node] = indegree.get(node, 0) + 1

    ready = [ref for ref, count in indegree.items() if count == 0]
    ordered: List[str] = []
    while ready:
        ref = ready.pop(0)
        ordered.append(ref)
        for node in adj.get(ref, []):
            indegree[node] -= 1
            if indegree[node] == 0:
                ready.append(node)

    if len(ordered) != len(feature_seen):
        raise FeatureInstallError("Dependency cycle detected in dependsOn/installsAfter")

    return ordered, feature_dirs, feature_opts


def install_features(
    features: Dict[str, Dict[str, object]],
    *,
    dry_run: bool = False,
) -> List[str]:
    ctx = RunContext()
    try:
        require_command("bash")
        order, feature_dirs, feature_opts = resolve_features(features, ctx=ctx)
        if dry_run:
            return order

        for feature_ref in order:
            feature_dir = feature_dirs[feature_ref]
            feature_json = feature_dir / "devcontainer-feature.json"
            install_sh = feature_dir / "install.sh"
            if not feature_json.exists():
                raise FeatureInstallError(
                    "Missing devcontainer-feature.json in "
                    f"{feature_dir} (artifact is not a devcontainer feature, ref/tag is wrong, "
                    "or layer archive could not be unpacked)"
                )
            if not install_sh.exists():
                raise FeatureInstallError(f"Missing install.sh in {feature_dir}")

            defaults = feature_defaults(feature_json)
            opts = feature_opts.get(feature_ref, {})
            merged = {**defaults, **opts}

            print(f"Installing feature: {feature_ref}")
            env = os.environ.copy()
            for key, value in merged.items():
                env[sanitize_var_name(str(key))] = str(value)
            result = subprocess.run(
                ["bash", str(install_sh)],
                env=env,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise FeatureInstallError(f"install.sh failed for {feature_ref} (exit {result.returncode})")
        return order
    finally:
        ctx.cleanup()
