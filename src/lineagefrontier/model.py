"""Strict local manifest and interoperable in-toto/SLSA SHA-256 subset."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PureWindowsPath
from types import MappingProxyType
from typing import Mapping
import hashlib
import json
import re

STATEMENT = "https://in-toto.io/Statement/v1"
PREDICATE = "https://slsa.dev/provenance/v1"
MAX_MANIFEST_BYTES = 2 * 1024 * 1024
MAX_ARTIFACTS = 1000
MAX_ACTIONS = 1000
MAX_EDGES = 10000
MAX_FILE_BYTES = 64 * 1024 * 1024


class LineageError(ValueError):
    """An actionable input, safety or resource-bound error."""


def _obj(value, label):
    if not isinstance(value, dict):
        raise LineageError(f"{label}: expected object")
    return value


def _array(value, label):
    if not isinstance(value, list):
        raise LineageError(f"{label}: expected array")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise LineageError(f"{label}: expected nonempty string of <=2048 characters")
    return value


def _id(value, label):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", value):
        raise LineageError(f"{label}: expected portable ID (1..64 ASCII characters)")
    return value


def _digest(resource, label):
    resource = _obj(resource, label)
    digest = _obj(resource.get("digest"), f"{label}.digest")
    value = digest.get("sha256")
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", value):
        raise LineageError(f"{label}: supported subset requires a SHA-256 hex digest")
    return value.lower()


def _relative(value, label):
    value = _text(value, label)
    path = Path(value)
    windows = PureWindowsPath(value)
    if path.is_absolute() or windows.drive or windows.root or "\\" in value or any(p in ("..", ".") for p in value.split("/")):
        raise LineageError(f"{label}: use a root-relative path with / and no traversal")
    return value


@dataclass(frozen=True)
class Artifact:
    id: str
    digest: str
    path: str
    kind: str


@dataclass(frozen=True)
class Action:
    id: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    cost: int
    instruction: str


@dataclass(frozen=True)
class Manifest:
    artifacts: Mapping[str, Artifact]
    dependencies: Mapping[str, tuple[str, ...]]
    builders: Mapping[str, str]
    actions: Mapping[str, Action]
    topological: tuple[str, ...]

    def provenance_fingerprint(self) -> str:
        """Bind a snapshot to inventory/recorded lineage, independent of recipes."""
        records = [{"id": a.id, "digest": a.digest, "path": a.path, "kind": a.kind,
                    "dependencies": self.dependencies[a.id], "builder": self.builders.get(a.id)}
                   for a in self.artifacts.values()]
        return hashlib.sha256(json.dumps(records, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

    @classmethod
    def from_dict(cls, raw: dict) -> "Manifest":
        raw = _obj(raw, "manifest")
        if type(raw.get("schema_version")) is not int or raw["schema_version"] != 1:
            raise LineageError("schema_version: only 1 is supported")
        entries = _array(raw.get("artifacts"), "artifacts")
        if not entries or len(entries) > MAX_ARTIFACTS:
            raise LineageError(f"artifacts: require 1..{MAX_ARTIFACTS} entries")
        artifacts, by_digest = {}, {}
        for entry in entries:
            entry = _obj(entry, "artifact")
            aid = _id(entry.get("id"), "artifact.id")
            if aid in artifacts:
                raise LineageError(f"duplicate artifact ID: {aid}")
            digest = _digest(entry, f"artifact {aid}")
            if digest in by_digest:
                raise LineageError(f"ambiguous duplicate content digest: {aid} and {by_digest[digest]}; use one logical slot")
            kind = entry.get("kind")
            if kind not in ("input", "output"):
                raise LineageError(f"artifact {aid}: kind must be input or output")
            artifacts[aid] = Artifact(aid, digest, _relative(entry.get("path"), f"artifact {aid}.path"), kind)
            by_digest[digest] = aid
        dependencies = {aid: () for aid in artifacts}
        builders = {}
        statements = _array(raw.get("statements"), "statements")
        if len(statements) > MAX_ARTIFACTS:
            raise LineageError("too many statements")
        for i, statement in enumerate(statements):
            statement = _obj(statement, f"statement[{i}]")
            if statement.get("_type") != STATEMENT or statement.get("predicateType") != PREDICATE:
                raise LineageError(f"statement[{i}]: only bare in-toto Statement v1 / SLSA provenance v1 supported; DSSE is not verified")
            pred = _obj(statement.get("predicate"), "predicate")
            build = _obj(pred.get("buildDefinition"), "buildDefinition")
            _text(build.get("buildType"), "buildType")
            external = build.get("externalParameters")
            if external is None:
                external = {}
            _obj(external, "externalParameters")
            run = _obj(pred.get("runDetails"), "runDetails")
            builder = _obj(run.get("builder"), "builder")
            builder_id = _text(builder.get("id"), "builder.id")
            dep_ids = set()
            resources = build.get("resolvedDependencies")
            if resources is None:
                resources = []
            for resource in _array(resources, "resolvedDependencies"):
                digest = _digest(resource, "resolvedDependency")
                if digest not in by_digest:
                    raise LineageError(f"missing dependency digest: {digest}")
                dep_ids.add(by_digest[digest])
            subjects = _array(statement.get("subject"), "subject")
            if not subjects:
                raise LineageError("subject: require at least one output")
            for subject in subjects:
                digest = _digest(subject, "subject")
                if digest not in by_digest:
                    raise LineageError(f"unknown subject digest: {digest}")
                aid = by_digest[digest]
                if artifacts[aid].kind != "output":
                    raise LineageError(f"input {aid} cannot have build provenance")
                if aid in builders:
                    raise LineageError(f"duplicate provenance subject: {aid}")
                builders[aid] = builder_id
                dependencies[aid] = tuple(sorted(dep_ids))
        missing = sorted(aid for aid, a in artifacts.items() if a.kind == "output" and aid not in builders)
        if missing:
            raise LineageError(f"missing output provenance: {', '.join(missing)}")
        if sum(map(len, dependencies.values())) > MAX_EDGES:
            raise LineageError("too many provenance edges")
        topological = _topological(dependencies)
        actions = {}
        raw_actions = _array(raw.get("actions"), "actions")
        if len(raw_actions) > MAX_ACTIONS:
            raise LineageError("too many actions")
        for entry in raw_actions:
            entry = _obj(entry, "action")
            aid = _id(entry.get("id"), "action.id")
            if aid in actions:
                raise LineageError(f"duplicate action ID: {aid}")
            inputs = _refs(entry.get("inputs"), artifacts, f"action {aid}.inputs")
            outputs = _refs(entry.get("outputs"), artifacts, f"action {aid}.outputs")
            if not outputs or set(inputs) & set(outputs):
                raise LineageError(f"action {aid}: outputs must be nonempty and disjoint from inputs")
            if any(artifacts[x].kind != "output" for x in outputs):
                raise LineageError(f"action {aid}: cannot manufacture input slots")
            cost = entry.get("cost")
            if type(cost) is not int or not 0 <= cost <= 10**12:
                raise LineageError(f"action {aid}: cost must be integer units in 0..10^12")
            instruction = _text(entry.get("instruction"), f"action {aid}.instruction")
            actions[aid] = Action(aid, inputs, outputs, cost, instruction)
        if sum(len(a.inputs) + len(a.outputs) for a in actions.values()) > MAX_EDGES:
            raise LineageError("too many action edges")
        return cls(*(MappingProxyType(dict(sorted(m.items()))) for m in (artifacts, dependencies, builders, actions)), topological)


def _refs(value, artifacts, label):
    values = _array(value, label)
    refs = [_id(v, label) for v in values]
    if len(refs) != len(set(refs)):
        raise LineageError(f"{label}: duplicate reference")
    unknown = sorted(set(refs) - artifacts.keys())
    if unknown:
        raise LineageError(f"{label}: missing artifacts {unknown}")
    return tuple(sorted(refs))


def _topological(dependencies):
    import heapq
    children = {a: [] for a in dependencies}
    remaining = {}
    for aid, deps in dependencies.items():
        remaining[aid] = len(deps)
        for dep in deps:
            children[dep].append(aid)
    ready = [a for a, n in remaining.items() if not n]
    heapq.heapify(ready)
    order = []
    while ready:
        aid = heapq.heappop(ready)
        order.append(aid)
        for child in sorted(children[aid]):
            remaining[child] -= 1
            if not remaining[child]:
                heapq.heappush(ready, child)
    if len(order) != len(dependencies):
        raise LineageError(f"provenance cycle involving: {', '.join(sorted(a for a, n in remaining.items() if n))}")
    return tuple(order)


def load_manifest(path: str | Path) -> Manifest:
    path = Path(path)
    # Bound the actual read rather than trusting a pre-read stat on mutable files.
    with path.open("rb") as stream:
        payload = stream.read(MAX_MANIFEST_BYTES + 1)
    if len(payload) > MAX_MANIFEST_BYTES:
        raise LineageError("manifest exceeds 2 MiB")
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise LineageError(f"duplicate JSON key: {key}")
            result[key] = value
        return result
    def reject_nonfinite(value):
        raise LineageError(f"nonfinite JSON constant: {value}")
    try:
        raw = json.loads(payload.decode("utf-8"), object_pairs_hook=unique_object, parse_constant=reject_nonfinite)
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise LineageError(f"invalid manifest JSON: {exc}") from exc
    return Manifest.from_dict(raw)


def hash_file(root: Path, relative: str, max_bytes: int = MAX_FILE_BYTES) -> str:
    """Read only regular local files beneath root; reject escaping symlinks."""
    root = root.resolve(strict=True)
    path = root / relative
    resolved = path.resolve(strict=True)
    if not resolved.is_relative_to(root):
        raise LineageError(f"path escapes root: {relative}")
    if not resolved.is_file():
        raise LineageError(f"not a regular file: {relative}")
    before = resolved.stat()
    if before.st_size > max_bytes:
        raise LineageError(f"file exceeds {max_bytes} bytes: {relative}")
    digest = hashlib.sha256()
    total = 0
    with resolved.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            total += len(chunk)
            if total > max_bytes:
                raise LineageError(f"file grew beyond byte limit: {relative}")
            digest.update(chunk)
    after = resolved.stat()
    if (before.st_ino, before.st_size, before.st_mtime_ns) != (after.st_ino, after.st_size, after.st_mtime_ns):
        raise LineageError(f"file changed during verification: {relative}; retry from a stable snapshot")
    return digest.hexdigest()
