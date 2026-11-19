"""Build a versioned Etherlords III campaign UI package from local archives."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import struct
import tempfile
import zipfile

import campaign_ui as ui


ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / ".campaign-ui-local" / "packages"
ARCHIVES = ("textures.res", "regs.res", "text.res")
MAP_MEMBER = ui.MAP_IMAGE.replace("\\", "/")
PLACES_MEMBER = ui.PLACES.replace("\\", "/")
ROUTE_COUNTS = {f"GlobalMap/Green{stage}.reg": count
                for stage, count in enumerate((1, 12, 8, 6), 1)}
GREEN_TEXT = re.compile(r"T_SC_CAMP_GREEN|MT_E2C_GREEN_(?:NAME|DESC)|MT_E2C_M1[1-4]_(?:NAME|DESC)")


def unique_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key {key!r}")
        result[key] = value
    return result


def read_object(path):
    data = json.loads(path.read_text(encoding="utf-8-sig"), object_pairs_hook=unique_keys)
    if not isinstance(data, dict):
        raise ValueError(f"Expected a JSON object in {path.name}")
    return data


def read_image(project, filename, key, dimensions):
    manifest = read_object(project / filename)
    if set(manifest) != {key}:
        raise ValueError(f"{filename} must contain only {key}")
    value = manifest[key]
    if value is None:
        return {}
    if not isinstance(value, str) or not value:
        raise ValueError(f"{filename} needs a relative PNG path or null")
    image_path = (project / value).resolve()
    if Path(value).is_absolute() or not image_path.is_relative_to(project):
        raise ValueError(f"{filename} image must be inside the project directory")
    from PIL import Image

    with Image.open(image_path) as image:
        if image.format != "PNG" or image.size != dimensions or image.n_frames != 1:
            width, height = dimensions
            raise ValueError(f"{image_path.name} must be a single-frame {width} x {height} PNG")
        image.verify()
    return {key: str(image_path)}


def read_release(project):
    release = read_object(project / "release.json")
    version = release.get("version")
    if not isinstance(version, str) or not re.fullmatch(r"\d{1,4}\.\d{1,4}\.\d{1,4}", version, re.ASCII):
        raise ValueError("release.json version must use MAJOR.MINOR.PATCH")
    hashes = release.get("source_sha256")
    if not isinstance(hashes, dict) or set(hashes) != set(ARCHIVES) or any(
        not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest)
        for digest in hashes.values()
    ):
        raise ValueError("release.json needs lowercase source SHA-256 hashes for all three archives")
    return version, hashes


def read_manifests(project, archives):
    textures = read_image(project, "portrait.json", "green_portrait", (223, 341))
    textures.update(read_image(project, "overview.json", MAP_MEMBER, (736, 444)))

    routes = read_object(project / "mission-routes.json")
    if not routes.keys() <= ROUTE_COUNTS.keys():
        raise ValueError("Only the four Green route members are supported in mission-routes.json")
    for name, points in routes.items():
        count = ROUTE_COUNTS[name]
        archive = archives["regs.res"]
        if len(ui.decode_route(archive.read(archive.get(name)))) != count:
            raise ValueError(f"Unexpected source route count for {name}")
        if not isinstance(points, list) or len(points) != count:
            raise ValueError(f"{name} requires {count} route points")

    locations = read_object(project / "hover-locations.json")
    bounds = locations.get(PLACES_MEMBER, {})
    if locations.keys() - {PLACES_MEMBER} or not isinstance(bounds, dict):
        raise ValueError(f"hover-locations.json accepts an object keyed by {PLACES_MEMBER}")

    localization = read_object(project / "localization.json")
    strings = localization.get(ui.TEXT_BANK, {})
    if localization.keys() - {ui.TEXT_BANK} or not isinstance(strings, dict):
        raise ValueError(f"localization.json accepts an object keyed by {ui.TEXT_BANK}")
    if any(not GREEN_TEXT.fullmatch(key) and not key.startswith("MT_GMAP_TT_") for key in strings):
        raise ValueError("Localization edits must use Green campaign keys or existing map tooltip keys")

    if bounds:
        routes[PLACES_MEMBER] = bounds
    return {
        "textures.res": textures,
        "regs.res": routes,
        "text.res": {ui.TEXT_BANK: strings} if strings else {},
    }


def check_portrait_guard(name, original, replacement):
    header = ui.MMP_HEADER.size
    stride = 256 * 2
    height = 85 if name == ui.PORTRAIT_BOTTOM else 256
    if (len(original) != header + 256 * stride or len(replacement) != len(original)
            or original[:header] != replacement[:header]
            or original[header + height * stride:] != replacement[header + height * stride:]):
        raise ValueError(f"Portrait replacement would change protected bytes in {name}")
    for row in range(height):
        start = header + row * stride + 223 * 2
        end = header + (row + 1) * stride
        if original[start:end] != replacement[start:end]:
            raise ValueError(f"Portrait replacement would change tile padding in {name}")


def verify_archive(source, output, replacements):
    staged = ui.Archive(output)
    if source.names != staged.names or len(source.members) != len(staged.members):
        raise ValueError(f"Archive member names changed in {output.name}")
    expected_table = bytearray(source.table)
    for old, new in zip(source.members, staged.members):
        before = source.read(old)
        after = staged.read(new)
        if after != replacements.get(old, before):
            raise ValueError(f"Unexpected payload for {old.name} in {output.name}")
        if old in replacements and old.name in (ui.PORTRAIT_IMAGE, ui.PORTRAIT_BOTTOM):
            check_portrait_guard(old.name, before, after)
        if len(before) != len(after):
            struct.pack_into("<II", expected_table, old.index * ui.RES_ENTRY.size + 4,
                             len(after), new.offset)
    if staged.table != expected_table:
        raise ValueError(f"Unexpected directory change in {output.name}")


def verify_package(path, instructions, hashes):
    with zipfile.ZipFile(path) as package:
        expected = {"INSTALL.md", *(f"Resources/{name}" for name in hashes)}
        names = package.namelist()
        if set(names) != expected or len(names) != len(expected):
            raise ValueError("Unexpected installation package contents")
        if package.read("INSTALL.md") != instructions:
            raise ValueError("Installation instructions changed in the package")
        for name, digest in hashes.items():
            with package.open(f"Resources/{name}") as stream:
                if hashlib.file_digest(stream, "sha256").hexdigest() != digest:
                    raise ValueError(f"Package checksum mismatch for {name}")


def instructions_for(template, package_id, version, patched_hashes, source_hashes):
    table = "\n".join(f"| `{name}` | `{source_hashes[name]}` | `{digest}` |"
                      for name, digest in patched_hashes.items())
    records = "\n".join(
        f"    '{name}' = @{{ Source = '{source_hashes[name]}'; Patched = '{digest}' }}"
        for name, digest in patched_hashes.items()
    )
    return (template.replace("@VERSION@", version).replace("@PACKAGE_ID@", package_id)
            .replace("@SHA256_TABLE@", table).replace("@ARCHIVE_RECORDS@", records)).encode("utf-8")


def build(project, resources):
    version, source_hashes = read_release(project)
    for name, digest in source_hashes.items():
        if ui.sha256(resources / name) != digest:
            raise ValueError(f"Source SHA-256 mismatch for {resources / name}. Use the pinned baseline.")
    archives = {name: ui.Archive(resources / name) for name in ARCHIVES}
    manifests = read_manifests(project, archives)
    template = (ROOT / "package-install.template.md").read_text(encoding="utf-8")

    OUTPUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="build-", dir=OUTPUT) as temporary:
        work = Path(temporary)
        pending = {}
        for name, manifest in manifests.items():
            if manifest:
                united = work / f"{name}.json"
                united.write_text(json.dumps(manifest), encoding="utf-8")
                updates = ui.replacements_for(archives[name], united, allow_unchanged=True)
                if updates:
                    pending[name] = updates
        if not pending:
            raise ValueError("No archive payload changes to package")
        hashes = {}
        for name, updates in pending.items():
            staged = work / name
            ui.stage_archive(archives[name], staged, updates)
            verify_archive(archives[name], staged, updates)
            hashes[name] = ui.sha256(staged)
            print(f"Verified {name}: {', '.join(member.name for member in updates)}")
        for name, digest in source_hashes.items():
            if ui.sha256(resources / name) != digest:
                raise ValueError(f"Source changed during the build: {name}")

        identity = json.dumps([version, source_hashes, hashes, template], sort_keys=True).encode("utf-8")
        package_id = f"etherlords-iii-campaign-ui-{version}-{hashlib.sha256(identity).hexdigest()[:16]}"
        instructions = instructions_for(template, package_id, version, hashes, source_hashes)
        destination = OUTPUT / f"{package_id}.zip"
        if destination.exists():
            verify_package(destination, instructions, hashes)
            return destination
        candidate = work / destination.name
        with zipfile.ZipFile(candidate, "x", zipfile.ZIP_DEFLATED, compresslevel=1) as package:
            package.writestr("INSTALL.md", instructions)
            for name in hashes:
                package.write(work / name, f"Resources/{name}")
        verify_package(candidate, instructions, hashes)
        try:
            # Windows rename refuses an existing file. POSIX uses a no-replace hard link.
            if os.name == "nt":
                candidate.rename(destination)
            else:
                os.link(candidate, destination)
        except FileExistsError:
            verify_package(destination, instructions, hashes)
        return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=ROOT)
    parser.add_argument("--source-resources", type=Path, required=True,
                        help="Local Resources directory with the pinned source archives")
    args = parser.parse_args()
    try:
        package = build(args.project.resolve(strict=True), args.source_resources.resolve(strict=True))
    except (OSError, ValueError, ImportError, struct.error, zipfile.BadZipFile) as error:
        parser.exit(1, f"Error: {error}\n")
    print(f"Package: {package}")


if __name__ == "__main__":
    main()
