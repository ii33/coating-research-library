"""Durable, immutable research artifacts and verifiable publication manifests.

Paths passed to this module are POSIX-style paths relative to a caller-supplied
existing root. The store assumes no hostile process changes directory symlinks
concurrently. It performs no network access or publication.
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import tempfile


def canonical_json(value):
    """Return deterministic UTF-8 JSON bytes; reject non-finite floats."""
    return (json.dumps(value, ensure_ascii=False, sort_keys=True,
                       separators=(",", ":"), allow_nan=False) + "\n").encode("utf-8")


def _relative(value):
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValueError("path must be a nonempty POSIX relative path")
    p = PurePosixPath(value)
    if p.is_absolute() or PureWindowsPath(value).is_absolute() or PureWindowsPath(value).drive:
        raise ValueError("absolute paths are not allowed")
    if any(part in (".", "..", "") for part in value.split("/")):
        raise ValueError("path must not contain empty, . or .. components")
    return p


def _target(root, relative):
    root = Path(root).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("root must be a directory")
    path = root.joinpath(*_relative(relative).parts)
    # Reject symlinks even if they currently resolve inside the root. This also
    # rejects a symlink at the target itself, including a dangling one.
    current = root
    for component in path.relative_to(root).parts:
        current = current / component
        if current.is_symlink():
            raise ValueError("symlinks are not allowed in artifact paths")
    return path


def _sync_dir(directory):
    # fsync on directories is not available on Windows. On POSIX, do not hide
    # failure: callers must know when directory-entry durability is uncertain.
    if os.name == "nt":
        return
    fd = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def _ensure_parent(root, target):
    root = Path(root).resolve(strict=True)
    current = root
    for part in target.parent.relative_to(root).parts:
        current = current / part
        try:
            current.mkdir()
        except FileExistsError:
            if current.is_symlink() or not current.is_dir():
                raise ValueError("artifact parent is not a real directory")
        else:
            _sync_dir(current.parent)


def _write_temp(parent, data):
    fd, name = tempfile.mkstemp(prefix=".artifact-", suffix=".tmp", dir=parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        return Path(name)
    except BaseException:
        # fdopen takes ownership on success. Close explicitly if it failed.
        try:
            os.close(fd)
        except OSError:
            pass
        try:
            os.unlink(name)
        except FileNotFoundError:
            pass
        raise


def write_immutable_bytes(root, relative, data):
    """Atomically publish bytes without ever overwriting different content.

    Existing equal bytes are accepted idempotently; conflicting bytes raise
    FileExistsError. An atomic hard-link publication avoids the check/replace
    race between concurrent writers. The filesystem must support hard links.
    """
    if not isinstance(data, bytes):
        raise TypeError("data must be bytes")
    target = _target(root, relative)
    _ensure_parent(root, target)
    if target.exists():
        if target.read_bytes() == data:
            return target
        raise FileExistsError("immutable artifact differs: " + relative)
    temp = _write_temp(target.parent, data)
    try:
        try:
            os.link(temp, target)
        except FileExistsError:
            # Another writer may have published during our write.
            if target.is_symlink() or target.read_bytes() != data:
                raise FileExistsError("immutable artifact differs: " + relative)
        _sync_dir(target.parent)
    finally:
        temp.unlink(missing_ok=True)
        _sync_dir(target.parent)
    return target


def write_immutable_json(root, relative, value):
    """Canonicalize and save a JSON object as an immutable artifact."""
    return write_immutable_bytes(root, relative, canonical_json(value))


def _replace_bytes(root, relative, data):
    target = _target(root, relative)
    _ensure_parent(root, target)
    temp = _write_temp(target.parent, data)
    try:
        os.replace(temp, target)
        _sync_dir(target.parent)
    finally:
        if temp.exists():
            temp.unlink()
            _sync_dir(target.parent)
    return target


def _excluded(rel, manifest):
    p = PurePosixPath(rel)
    return (rel == manifest or any(part in ("__pycache__", "tmp", ".tmp", "logs", ".logs") for part in p.parts)
            or (p.name.endswith((".tmp", ".temp", ".log", ".pyc", "~")) or ".log." in p.name)
            or p.name.startswith(".artifact-"))


def _inventory(root, directory, manifest):
    root = Path(root).resolve(strict=True)
    directory = root if directory == "." else _target(root, directory)
    if not directory.is_dir():
        raise ValueError("inventory directory must exist")
    entries = []
    for base, dirs, files in os.walk(directory, followlinks=False):
        base = Path(base)
        dirs.sort()
        files.sort()
        dirs[:] = [d for d in dirs if d not in ("__pycache__", "tmp", ".tmp", "logs", ".logs")]
        for name in dirs:
            if (base / name).is_symlink():
                raise ValueError("symlink directory in inventory")
        for name in files:
            path = base / name
            rel = path.relative_to(root).as_posix()
            if _excluded(rel, manifest):
                continue
            if path.is_symlink() or not path.is_file():
                raise ValueError("non-regular file in inventory: " + rel)
            data = path.read_bytes()
            entries.append({"path": rel, "bytes": len(data),
                            "sha256": hashlib.sha256(data).hexdigest()})
    return sorted(entries, key=lambda e: e["path"])


def write_manifest(root, directory, manifest="manifest.json"):
    """Inventory a relative directory and atomically replace its manifest.

    Entry paths are relative to root, not to directory. Logs, temporary files,
    caches and the manifest itself are excluded.
    """
    if directory != ".":
        _relative(directory)
    _relative(manifest)
    entries = _inventory(root, directory, manifest)
    value = {"version": 1, "directory": directory, "files": entries}
    _replace_bytes(root, manifest, canonical_json(value))
    return value


def verify_manifest(root, manifest="manifest.json"):
    """Read a manifest and verify its inventory, sizes and hashes; raise on error."""
    path = _target(root, manifest)
    with path.open("r", encoding="utf-8") as stream:
        value = json.load(stream, parse_constant=lambda x: (_ for _ in ()).throw(ValueError("non-finite JSON")))
    if not isinstance(value, dict) or value.get("version") != 1 or not isinstance(value.get("files"), list):
        raise ValueError("invalid manifest")
    directory = value.get("directory")
    if directory != ".":
        _relative(directory)
    for entry in value["files"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "bytes", "sha256"}:
            raise ValueError("invalid manifest entry")
        _relative(entry["path"])
    actual = _inventory(root, directory, manifest)
    if value["files"] != actual:
        raise ValueError("manifest inventory, size, or SHA-256 mismatch")
    return True
