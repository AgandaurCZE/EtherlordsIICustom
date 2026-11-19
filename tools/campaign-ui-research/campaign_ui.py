"""Inspect Etherlords II resources and stage campaign UI archive replacements."""

import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import struct
import tempfile
from dataclasses import dataclass


RES_HEADER = struct.Struct("<4I")
RES_ENTRY = struct.Struct("<iIIIHI")
RES_MAGIC = 0x019CE23C
MMP_HEADER = struct.Struct("<4s18I")
MAP_IMAGE = r"Interface\GlobalMap\GlobalMap.mmp"
SYMBOL_IMAGE = r"Interface\world_symbols_map.mmp"
PORTRAIT_IMAGE = r"Interface\compain_panel_01.mmp"
PORTRAIT_BOTTOM = r"Interface\compain_panel_012.mmp"
PLACES = r"GlobalMap\GlobalMap.reg"
TEXT_BANK = "ELKTexts.txt"
ROUTE = re.compile(r"GlobalMap\\(Black|Blue|Green|Red|White)[1-5][ab]?\.reg", re.I)
TEXT_KEY = re.compile(r"(?m)^#([^\r\n]+)\r?\n")
IMAGE_TARGETS = {
    "textures.res": {MAP_IMAGE, PORTRAIT_IMAGE, PORTRAIT_BOTTOM, SYMBOL_IMAGE},
    "textures002.res": {SYMBOL_IMAGE},
}
CAMPAIGN_KEYS = re.compile(r"(?:T_SC_CAMP_|MT_E2C_|MT_GMAP_TT_)[A-Z0-9_]+")


@dataclass(frozen=True)
class Member:
    index: int
    name: str
    offset: int
    size: int


class Archive:
    def __init__(self, path):
        self.path = Path(path)
        length = self.path.stat().st_size
        with self.path.open("rb") as source:
            header = source.read(RES_HEADER.size)
            if len(header) != RES_HEADER.size:
                raise ValueError("Truncated RES header")
            magic, count, self.table_offset, names_size = RES_HEADER.unpack(header)
            if magic != RES_MAGIC or not RES_HEADER.size <= self.table_offset <= length:
                raise ValueError("Invalid Nival RES header")
            table_size = count * RES_ENTRY.size
            if self.table_offset + table_size + names_size != length:
                raise ValueError("Invalid RES directory bounds")
            source.seek(self.table_offset)
            self.table = source.read(table_size)
            self.names = source.read(names_size)
        self.members = []
        self.by_name = {}
        for index, (link, size, offset, _, name_size, name_offset) in enumerate(
            RES_ENTRY.iter_unpack(self.table)
        ):
            if not -1 <= link < count or not RES_HEADER.size <= offset <= offset + size <= self.table_offset:
                raise ValueError(f"Invalid RES entry {index}")
            if not name_size or name_offset + name_size > names_size:
                raise ValueError(f"Invalid RES name bounds for entry {index}")
            name = self.names[name_offset:name_offset + name_size].decode("cp1251")
            member = Member(index, name, offset, size)
            self.members.append(member)
            self.by_name.setdefault(name.casefold(), []).append(member)

    def get(self, name):
        matches = self.by_name.get(name.replace("/", "\\").casefold(), [])
        if len(matches) != 1:
            raise ValueError(f"Expected one RES member named {name!r}, found {len(matches)}")
        return matches[0]

    def read(self, member):
        with self.path.open("rb") as source:
            source.seek(member.offset)
            payload = source.read(member.size)
        if len(payload) != member.size:
            raise ValueError(f"Truncated payload for {member.name}")
        return payload


def sha256(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def copy_exact(source, output, size):
    while size:
        block = source.read(min(size, 1024 * 1024))
        if not block:
            raise ValueError("Source changed while copying")
        output.write(block)
        size -= len(block)


def stage_archive(archive, output_path, replacements):
    """Keep names, hash-chain rows and timestamps. Relocate only resized members."""
    output_path = output_path.resolve()
    if output_path.exists() or output_path.name.casefold() != archive.path.name.casefold():
        raise ValueError("Output must be a new file with the original archive basename")
    if (output_path.parent.name.casefold() == "resources"
            and (output_path.parent.parent / "Etherlords2.exe").exists()):
        raise ValueError("Use a staging directory outside the game's Resources directory")

    fixed = sorted(
        ((member, payload) for member, payload in replacements.items() if len(payload) == member.size),
        key=lambda replacement: replacement[0].offset,
    )
    for member, _ in fixed:
        if any(
            other != member and other.size and member.offset < other.offset + other.size
            and other.offset < member.offset + member.size for other in archive.members
        ):
            raise ValueError(f"Overlapping payload for {member.name}")
    directory = bytearray(archive.table)
    source_hash = sha256(archive.path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output_path.parent) as temporary:
        staged = Path(temporary) / output_path.name
        with archive.path.open("rb") as source, staged.open("wb") as output:
            for member, payload in fixed:
                copy_exact(source, output, member.offset - source.tell())
                output.write(payload)
                source.seek(member.size, io.SEEK_CUR)
            copy_exact(source, output, archive.table_offset - source.tell())
            for member, payload in replacements.items():
                if len(payload) != member.size:
                    output.write(bytes(-output.tell() % 16))
                    struct.pack_into("<II", directory, member.index * RES_ENTRY.size + 4,
                                     len(payload), output.tell())
                    output.write(payload)
            output.write(bytes(-output.tell() % 16))
            table_offset = output.tell()
            output.write(directory)
            output.write(archive.names)
            output.seek(8)
            output.write(struct.pack("<I", table_offset))
        verified = Archive(staged)
        for member, payload in replacements.items():
            if verified.read(verified.get(member.name)) != payload:
                raise ValueError(f"Read-back failed for {member.name}")
        if sha256(archive.path) != source_hash:
            raise ValueError("Source changed during staging")
        patched_hash = sha256(staged)
        # Publish the completed file without replacing an existing file.
        if os.name == "nt":
            staged.rename(output_path)
        else:
            os.link(staged, output_path)
    print(f"Original SHA-256 {source_hash}")
    print(f"Staged   SHA-256 {patched_hash}")
    print(output_path)


def mmp_fields(payload):
    if len(payload) < MMP_HEADER.size:
        raise ValueError("Truncated MMP header")
    magic, width, height, levels, fmt, bits, *channels = MMP_HEADER.unpack_from(payload)
    if magic != b"MMP\0" or fmt not in (0x5650, 0x5551, 0x4444, 0x8888):
        raise ValueError("Expected a supported packed RGB(A) MMP")
    if bits not in (16, 32) or not (1 <= width <= 8192 and 1 <= height <= 8192):
        raise ValueError("Invalid MMP pixel layout")
    masks = [tuple(channels[index:index + 3]) for index in (3, 6, 9, 0)]
    occupied = 0
    for mask, shift, depth in masks:
        if (shift + depth > bits or depth > 8 or mask != ((1 << depth) - 1) << shift
                or mask & occupied):
            raise ValueError("Invalid MMP channel masks")
        occupied |= mask
    if any(depth == 0 for _, _, depth in masks[:3]):
        raise ValueError("Missing MMP color channel")
    words = struct.Struct("<H" if bits == 16 else "<I")
    size = width * height * words.size
    if len(payload) < MMP_HEADER.size + size:
        raise ValueError("Truncated MMP pixels")
    return width, height, levels, words, masks


def decode_image(payload):
    from PIL import Image

    if payload.startswith((b"BM", b"\xff\xd8\xff", b"\x89PNG\r\n\x1a\n", b"DDS ")):
        with Image.open(io.BytesIO(payload)) as image:
            return image.convert("RGBA")
    if len(payload) >= MMP_HEADER.size and payload[:4] == b"MMP\0" and payload[16:20] == b"DXT1":
        width, height = struct.unpack_from("<II", payload, 4)
        if not (1 <= width <= 8192 and 1 <= height <= 8192):
            raise ValueError("Invalid DXT1 dimensions")
        size = ((width + 3) // 4) * ((height + 3) // 4) * 8
        pixels = payload[MMP_HEADER.size:MMP_HEADER.size + size]
        if len(pixels) != size:
            raise ValueError("Truncated DXT1 blocks")
        header = struct.pack("<31I", 124, 0x81007, height, width, size, 0, 0, *([0] * 11),
                             32, 4, int.from_bytes(b"DXT1", "little"), 0, 0, 0, 0, 0,
                             0x1000, 0, 0, 0, 0)
        with Image.open(io.BytesIO(b"DDS " + header + pixels)) as image:
            return image.convert("RGBA")
    width, height, _, word, masks = mmp_fields(payload)
    start = MMP_HEADER.size
    pixels = payload[start:start + width * height * word.size]
    if word.size == 4 and masks[:3] == [(0xff0000, 16, 8), (0xff00, 8, 8), (0xff, 0, 8)]:
        if masks[3] == (0xff000000, 24, 8):
            return Image.frombytes("RGBA", (width, height), pixels, "raw", "BGRA")
        if not masks[3][0]:
            return Image.frombytes("RGB", (width, height), pixels, "raw", "BGRX").convert("RGBA")
    rgba = bytes(
        ((value & mask) >> shift) * 255 // ((1 << depth) - 1) if depth else 255
        for (value,) in word.iter_unpack(pixels)
        for mask, shift, depth in masks
    )
    return Image.frombytes("RGBA", (width, height), rgba)


def encode_image(template, filename):
    from PIL import Image

    with Image.open(filename) as source:
        image = source.convert("RGBA")
    if template.startswith(b"BM"):
        size, pixel_offset, dib, width, height, planes, bits, codec = struct.unpack_from(
            "<I4xIIiiHHI", template, 2
        )
        if (size, pixel_offset, dib, width, height, planes, bits, codec) != (
            len(template), 54, 40, 736, 444, 1, 24, 0
        ) or len(template) < 54 + width * height * 3:
            raise ValueError("Expected the observed uncompressed 736 x 444 overview BMP")
        if image.size != (width, height):
            raise ValueError(f"Image must be {width} x {height}")
        pixels = image.convert("RGB").tobytes("raw", "BGR", width * 3, -1)
        return template[:54] + pixels + template[54 + len(pixels):]
    width, height, _, _, _ = mmp_fields(template)
    if image.size != (width, height):
        raise ValueError(f"Image must be {width} x {height}")
    return encode_mmp(template, image)


def encode_mmp(template, image):
    width, height, levels, word, masks = mmp_fields(template)
    if levels != 1 or len(template) != MMP_HEADER.size + width * height * word.size:
        raise ValueError("Replacement supports only single-level packed MMP textures")
    if image.width > width or image.height > height:
        raise ValueError("Replacement region exceeds the texture dimensions")
    output = bytearray(template)
    for index, rgba in enumerate(image.getdata()):
        value = 0
        for channel, (_, shift, depth) in zip(rgba, masks):
            value |= ((channel * ((1 << depth) - 1) + 127) // 255) << shift
        row, column = divmod(index, image.width)
        word.pack_into(output, MMP_HEADER.size + (row * width + column) * word.size, value)
    return bytes(output)


def decode_route(payload):
    if len(payload) < 4 or (len(payload) - 4) % 8:
        raise ValueError("Invalid route length")
    points = list(struct.iter_unpack("<ii", payload[4:]))
    if len(points) != struct.unpack_from("<I", payload)[0]:
        raise ValueError("Route point count disagrees with payload length")
    return points


def decode_places(payload):
    if len(payload) < 4:
        raise ValueError("Truncated GlobalMap.reg")
    count = struct.unpack_from("<I", payload)[0]
    cursor = 4
    places = []
    for _ in range(count):
        if cursor + 16 >= len(payload):
            raise ValueError("Truncated place record")
        bounds = struct.unpack_from("<4i", payload, cursor)
        end = payload.index(0, cursor + 16)
        key = payload[cursor + 16:end].decode("ascii")
        places.append({"bounds": bounds, "key": key})
        cursor = end + 1
    if cursor != len(payload):
        raise ValueError("Unexpected bytes after place records")
    return places


def text_values(payload):
    original = payload.decode("utf-16")
    matches = list(TEXT_KEY.finditer(original))
    return original, {
        match[1]: (match.end(), matches[index + 1].start() if index + 1 < len(matches) else len(original))
        for index, match in enumerate(matches)
    }


def replace_text(payload, values):
    original, spans = text_values(payload)
    edits = []
    for key, value in values.items():
        if not CAMPAIGN_KEYS.fullmatch(key) or key not in spans:
            raise ValueError(f"Unknown campaign localization key {key!r}")
        if not isinstance(value, str) or not value.strip() or "\0" in value or any(
            line.startswith("#") for line in value.splitlines()
        ):
            raise ValueError(f"Invalid text for {key}")
        start, end = spans[key]
        suffix = re.search(r"(?:\r?\n)+\Z", original[start:end])
        if suffix:
            end = start + suffix.start()
        newline = "\r\n" if "\r\n" in original else "\n"
        edits.append((start, end, newline.join(value.splitlines())))
    for start, end, value in sorted(edits, reverse=True):
        original = original[:start] + value + original[end:]
    return payload[:2] + original.encode("utf-16-le" if payload[:2] == b"\xff\xfe" else "utf-16-be")


def checked_coordinates(bounds, count):
    size = (736, 444)
    if not isinstance(bounds, list) or len(bounds) != count or any(
        type(value) is not int or not 0 <= value < size[index % len(size)]
        for index, value in enumerate(bounds)
    ):
        raise ValueError(f"Invalid map coordinates {bounds!r}")
    return bounds


def replacements_for(archive, manifest_path, *, allow_unchanged=False):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
    if not isinstance(manifest, dict) or not manifest:
        raise ValueError("Expected a nonempty JSON object keyed by RES member name")
    replacements = {}
    filename = archive.path.name.casefold()
    if "green_portrait" in manifest:
        from PIL import Image

        path = manifest.pop("green_portrait")
        if filename != "textures.res" or not isinstance(path, str):
            raise ValueError("green_portrait requires an image path and textures.res")
        with Image.open(manifest_path.parent / path) as source:
            if source.size != (223, 341):
                raise ValueError("The complete Green portrait must be 223 x 341")
            portrait = source.convert("RGBA")
        for name, bounds in [
            (PORTRAIT_IMAGE, (0, 0, 223, 256)),
            (PORTRAIT_BOTTOM, (0, 256, 223, 341)),
        ]:
            member = archive.get(name)
            template = archive.read(member)
            if mmp_fields(template)[:3] != (256, 256, 1):
                raise ValueError(f"Unexpected Green portrait tile layout for {name}")
            replacements[member] = encode_mmp(template, portrait.crop(bounds))
    for name, value in manifest.items():
        member = archive.get(name)
        if member in replacements:
            raise ValueError(f"Duplicate replacement for {member.name}")
        old = archive.read(member)
        if member.name in IMAGE_TARGETS.get(filename, ()) and isinstance(value, str):
            payload = encode_image(old, manifest_path.parent / value)
        elif filename == "regs.res" and ROUTE.fullmatch(member.name) and isinstance(value, list):
            if len(value) != len(decode_route(old)):
                raise ValueError("Keep the original number of route points for each stage")
            payload = struct.pack("<I", len(value)) + b"".join(
                struct.pack("<ii", *checked_coordinates(point, 2)) for point in value
            )
        elif filename == "regs.res" and member.name == PLACES and isinstance(value, dict):
            places = decode_places(old)
            if not value.keys() <= {place["key"] for place in places}:
                raise ValueError("Unknown place key")
            records = []
            for place in places:
                key = place["key"]
                bounds = checked_coordinates(value[key], 4) if key in value else place["bounds"]
                if bounds[0] >= bounds[2] or bounds[1] >= bounds[3]:
                    raise ValueError(f"Inverted or empty bounds for {key}")
                records.append(struct.pack("<4i", *bounds) + key.encode("ascii") + b"\0")
            payload = struct.pack("<I", len(places)) + b"".join(records)
        elif filename == "text.res" and member.name == TEXT_BANK and isinstance(value, dict):
            payload = replace_text(old, value)
        else:
            raise ValueError(f"Unsupported archive, member or replacement value for {name}")
        replacements[member] = payload
    replacements = {member: data for member, data in replacements.items()
                    if archive.read(member) != data}
    if not replacements and not allow_unchanged:
        raise ValueError("Manifest makes no changes")
    return replacements


def inspect_member(archive, member):
    payload = archive.read(member)
    if ROUTE.fullmatch(member.name):
        return decode_route(payload)
    if member.name == PLACES:
        return decode_places(payload)
    if member.name == TEXT_BANK:
        original, spans = text_values(payload)
        return {key: original[start:end].rstrip("\r\n") for key, (start, end) in spans.items()
                if CAMPAIGN_KEYS.fullmatch(key)}
    raise ValueError("No structured decoder for this member. Use list, extract or preview.")


def show_members(archive, pattern):
    for member in archive.members:
        if not pattern.search(member.name):
            continue
        print(f"{member.index:4}  0x{member.offset:08x}  {member.size:10}  {member.name}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list", help="List RES directory rows")
    listing.add_argument("--match", default="", help="Case-insensitive regular expression")
    for command in ("extract", "preview", "inspect"):
        child = commands.add_parser(command)
        child.add_argument("member", help="Exact archive name, with backslashes or slashes")
        if command != "inspect":
            child.add_argument("output", type=Path)
    stage = commands.add_parser("stage", help="Build a new archive from a JSON manifest")
    stage.add_argument("manifest", type=Path)
    stage.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        archive = Archive(args.archive)
        if args.command == "list":
            show_members(archive, re.compile(args.match, re.I))
        elif args.command == "stage":
            stage_archive(archive, args.output, replacements_for(archive, args.manifest))
        else:
            member = archive.get(args.member)
            if args.command == "inspect":
                print(json.dumps({member.name: inspect_member(archive, member)}, indent=2))
            else:
                payload = archive.read(member)
                if args.command == "preview":
                    image = decode_image(payload)
                    with args.output.open("xb") as output:
                        image.save(output, format="PNG")
                else:
                    with args.output.open("xb") as output:
                        output.write(payload)
    except (OSError, ValueError, re.error, struct.error, ImportError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
