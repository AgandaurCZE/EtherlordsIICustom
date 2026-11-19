"""Install a verified creator package and restore any changes by checksum."""

import ctypes as ct
from ctypes import wintypes as wt
import json
from pathlib import Path
import re
import shutil
import tempfile
import uuid

from creator_core import ABILITIES, ASSET_HASHES, CARD_ID, EFFECTS, PINNED_EXE, SOURCE_HASHES, canonical, checksum

BACKUP = ".card-creator-backup"
MARKER = ".native-combat-test"
ORIGINALS = {f"Resources/{name}": digest for name, digest in SOURCE_HASHES.items()}
FILES = re.compile(r"Resources/(?:regs|text|textures001)\.res|Duel/card-creator-(?:red|blue|green|black)-[1-9][0-9]*\.prs")
HASH = re.compile(r"[a-f0-9]{64}")


def game_closed():
    class ProcessEntry(ct.Structure):
        _fields_ = [(name, wt.DWORD) for name in ("size", "usage", "pid")] + [
            ("heap", ct.c_size_t), ("module", wt.DWORD), ("threads", wt.DWORD),
            ("parent", wt.DWORD), ("priority", wt.LONG), ("flags", wt.DWORD),
            ("name", wt.WCHAR * 260),
        ]

    api = ct.WinDLL("kernel32", use_last_error=True)
    api.CreateToolhelp32Snapshot.argtypes = (wt.DWORD, wt.DWORD)
    api.CreateToolhelp32Snapshot.restype = wt.HANDLE
    api.CloseHandle.argtypes = (wt.HANDLE,)
    for function in (api.Process32FirstW, api.Process32NextW):
        function.argtypes = (wt.HANDLE, ct.POINTER(ProcessEntry))
        function.restype = wt.BOOL
    handle = api.CreateToolhelp32Snapshot(2, 0)
    if handle == ct.c_void_p(-1).value:
        raise ct.WinError(ct.get_last_error())
    try:
        entry = ProcessEntry(size=ct.sizeof(ProcessEntry))
        present = api.Process32FirstW(handle, ct.byref(entry))
        while present:
            if entry.name.casefold() == "etherlords2.exe":
                raise ValueError("Close Etherlords II before installing or rolling back.")
            present = api.Process32NextW(handle, ct.byref(entry))
        if ct.get_last_error() != 18:  # ERROR_NO_MORE_FILES
            raise ct.WinError(ct.get_last_error())
    finally:
        api.CloseHandle(handle)


def safe_path(root, name):
    path = root / name
    if path.resolve() != path:
        raise ValueError(f"Linked or redirected path is unsupported: {name}")
    return path


def load_manifest(folder):
    profile = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    rows, files = profile.get("bindings"), profile.get("files")
    if profile.get("format") != 1 or profile.get("executable") != PINNED_EXE:
        raise ValueError("This package targets a different executable or format.")
    if not isinstance(files, dict) or not ORIGINALS.keys() <= files.keys() or any(
            not FILES.fullmatch(name) or not isinstance(digest, str) or not HASH.fullmatch(digest)
            for name, digest in files.items()):
        raise ValueError("The package file list is invalid.")
    if not isinstance(rows, list) or not rows:
        raise ValueError("The native configuration is empty.")
    seen = set()
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"id", "kind", "donor", "flat_cost"}:
            raise ValueError("Invalid native registration.")
        ident, kind = row["id"], row["kind"]
        donors = ABILITIES if kind == "creature" else EFFECTS
        if (not isinstance(ident, str) or not CARD_ID.fullmatch(ident) or ident in seen
                or kind not in ("creature", "spell") or row["donor"] not in donors
                or type(row["flat_cost"]) is not bool or (kind == "creature" and row["flat_cost"])):
            raise ValueError("Unsupported or duplicate native registration.")
        seen.add(ident)
    return profile


def verified_stock(game):
    if checksum(safe_path(game, "Etherlords2.exe")) != PINNED_EXE:
        raise ValueError("This folder does not match the supported Etherlords II 1.03 build.")
    for name, expected in ORIGINALS.items():
        if checksum(safe_path(game, name)) != expected:
            raise ValueError(f"Target has incompatible or already modified {name}.")
    for name, expected in ASSET_HASHES.items():
        if checksum(safe_path(game, f"Resources/{name}")) != expected:
            raise ValueError(f"Target has incompatible stock artwork or models: {name}.")


def atomic_copy(source, target):
    with tempfile.NamedTemporaryFile(dir=target.parent, delete=False) as handle:
        temporary = Path(handle.name)
    try:
        shutil.copyfile(source, temporary)
        temporary.replace(target)
    finally:
        temporary.unlink(missing_ok=True)


def install(game, package, report=lambda message: None):
    game, package = game.resolve(strict=True), package.resolve(strict=True)
    game_closed()
    verified_stock(game)
    if any(safe_path(game, name).exists() for name in (BACKUP, MARKER, "Resources/textures001.res")):
        raise ValueError("This copy contains a previous install, test marker, or an occupied artwork archive.")
    manifest = load_manifest(package)
    for name, expected in manifest["files"].items():
        target = safe_path(game, name)
        if not target.parent.is_dir() or (name not in ORIGINALS and target.exists()):
            raise ValueError(f"Refusing to overwrite {name} or use a missing directory.")
        if checksum(safe_path(package, name)) != expected:
            raise ValueError(f"Package verification failed: {name}")
    backup = game / BACKUP
    with tempfile.TemporaryDirectory(dir=game) as temporary:
        stage = Path(temporary) / "backup"
        stage.mkdir()
        for name, expected in ORIGINALS.items():
            destination = stage / name
            destination.parent.mkdir(exist_ok=True)
            shutil.copyfile(game / name, destination)
            if checksum(destination) != expected:
                raise ValueError(f"Backup verification failed: {name}")
        (stage / "manifest.json").write_bytes(canonical(manifest))
        stage.rename(backup)
    report("Backups verified. Installing the card resources and Duel decks…")
    try:
        for name, expected in manifest["files"].items():
            path = safe_path(game, name)
            atomic_copy(safe_path(package, name), path)
            if checksum(path) != expected:
                raise ValueError(f"Installation verification failed: {name}")
        (game / MARKER).touch(exist_ok=False)
    except Exception:
        rollback(game)
        raise
    return game


def rollback(game):
    game = game.resolve(strict=True)
    game_closed()
    backup = safe_path(game, BACKUP)
    manifest = load_manifest(backup)
    for name, installed in manifest["files"].items():
        target = safe_path(game, name)
        if name in ORIGINALS and checksum(safe_path(backup, name)) != ORIGINALS[name]:
            raise ValueError(f"Backup checksum differs: {name}")
        if target.exists() and checksum(target) not in (installed, ORIGINALS.get(name)):
            raise ValueError(f"File changed since install: {name}. Verified backups are in {backup}.")
    for name in manifest["files"]:
        target = safe_path(game, name)
        if name in ORIGINALS:
            atomic_copy(backup / name, target)
            if checksum(target) != ORIGINALS[name]:
                raise ValueError(f"Restored checksum differs: {name}")
        else:
            target.unlink(missing_ok=True)
    safe_path(game, MARKER).unlink(missing_ok=True)
    # Remove only the known files inside the verified backup directory.
    for name in ORIGINALS:
        (backup / name).unlink()
    (backup / "Resources").rmdir()
    (backup / "manifest.json").unlink()
    backup.rmdir()


def disposable(source, package, directory, report=lambda message: None):
    source, directory = source.resolve(strict=True), directory.resolve()
    game_closed()
    verified_stock(source)
    if directory.is_relative_to(source):
        raise ValueError("Choose a test workspace outside the source game.")
    directory.mkdir(parents=True, exist_ok=True)
    game = directory / ("Duel-" + uuid.uuid4().hex[:10])
    report(f"Copying the verified game to {game}…")
    with tempfile.TemporaryDirectory(dir=directory) as staging:
        copy = Path(staging) / "game"
        shutil.copytree(source, copy, ignore=shutil.ignore_patterns(
            ".git", ".campaign-ui-local", "local", BACKUP, MARKER, ".duel-matrix-copy",
            "Save", "Replays", "shot*.bmp",
        ))
        for folder in ("Save", "Replays"):
            (copy / folder).mkdir()
        install(copy, package, report)
        copy.rename(game)
    return game
