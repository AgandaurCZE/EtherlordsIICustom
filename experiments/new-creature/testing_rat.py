"""Build and launch the isolated additive TESTING Rat probe."""

import argparse
import hashlib
import json
import mmap
from pathlib import Path
import shutil
import struct
import sys
import tempfile

HERE = Path(__file__).resolve().parent
LOCAL = HERE / "local"
sys.path.insert(0, str(HERE.parent / "native-combat-extension"))
from combat_probe import (
    INITIALIZER_RETURN, PINNED_EXE, PRODUCER_COUNT, PRODUCER_MAP, SOURCE_HASHES,
    check_hashes, memory, producer, register_producer, registry_node, run, words,
)
from spell_lab import (
    Archive, REG_RECORD, RES_HEADER, RES_RECORD, add_sections, add_text, bucket, clone_section, digest,
    field_values, packed_string, read_fields, read_reg, read_value, write_reg,
)

IDENT = b"E3RT"
SHAMAN = b"KBSH"
MANTIS = b"MTPT"
SHAMAN_PRODUCER = 0x7451D0
PRODUCER_VTABLE = 0x8C1A98
RACE_MAP = 0x9CD91C
STRINGS = {b"E3RTNm": "TESTING Rat", b"E3RTTt": "Deal 1 damage to target creature or hero."}
TEST_HASHES = {
    "regs.res": "006651c76291c40d76b17b5d417764d35f842044f5dc7dba46aff4c1b50d4950",
    "text.res": "f74a61a8a370f895ad0d9f3f1b507289697d40d5a02c183bcd913965f38b66ae",
    "textures001.res": "d11cced416af2de46b8fdbea63ac091fb98a5c9792fa55c269e65280819f149f",
}
TEXTURES_SHA256 = "0b6a82b36aad5f4d1ed819f74bae81cd59ad6f67e7ec80c50a5b7ddf5b077cfb"


def portrait_overlay(resources):
    """Create the optional stock archive slot with only three new portrait names."""
    with (resources / "textures.res").open("rb") as handle:
        if hashlib.file_digest(handle, "sha256").hexdigest() != TEXTURES_SHA256:
            raise ValueError("Unexpected stock textures.res checksum")
        with mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as data:
            source = Archive(data)
            folder = "Interface\\Encyclopaedia\\"
            names = [f"{folder}e3rt_{index}.mmp" for index in (1, 2, 3)]
            existing = {key.casefold() for key in source.members}
            if any(name.casefold() in existing for name in names):
                raise ValueError("An E3RT portrait already exists")
            portraits = {name: source.read(name.replace("e3rt_", "mtpt_")) for name in names}

    output = bytearray(RES_HEADER.size)
    layout = {}
    for name, payload in portraits.items():
        if payload[:12] != b"MMP\0" + struct.pack("<II", 256, 256):
            raise ValueError("Expected a stock 256x256 Encyclopedia tile")
        layout[name] = len(output), len(payload)
        output.extend(payload)
        output.extend(bytes(-len(output) % 16))
    table = len(output)
    slots = [None] * len(portraits)
    if len({bucket(name.encode("ascii"), len(slots)) for name in portraits}) != len(slots):
        raise ValueError("Unexpected hash collision in the fixed portrait names")
    for name in portraits:
        slots[bucket(name.encode("ascii"), len(slots))] = name
    strings = bytearray()
    for name in slots:
        encoded = name.encode("ascii")
        offset, length = layout[name]
        output.extend(RES_RECORD.pack(-1, length, offset, 0, len(encoded), len(strings)))
        strings.extend(encoded)
    output.extend(strings)
    RES_HEADER.pack_into(output, 0, 0x019CE23C, len(slots), table, len(strings))
    verified = Archive(output)
    if verified.members.keys() != portraits.keys() or any(verified.read(k) != v for k, v in portraits.items()):
        raise ValueError("Portrait overlay did not round-trip")
    return output


def remove_flags(section):
    values = {}
    for key, (_, kind, offset) in read_fields(section).items():
        if key != b"Flags":
            _, end = read_value(section, kind, offset)
            values[key] = bytes((kind,)) + packed_string(key) + section[offset:end]
    count = len(values)
    header = struct.pack("<H", count) + packed_string(IDENT)
    slots = [None] * count
    collisions = []
    fields = bytearray()
    for key, record in values.items():
        offset = len(header) + REG_RECORD.size * count + len(fields)
        fields.extend(record)
        slot = bucket(key, count)
        if slots[slot] is None:
            slots[slot] = (-1, offset)
        else:
            collisions.append((slot, offset))
    free = iter(i for i, slot in enumerate(slots) if slot is None)
    for slot, offset in collisions:
        replacement = next(free)
        link, first_offset = slots[slot]
        slots[slot] = (replacement, first_offset)
        slots[replacement] = (link, offset)
    result = header + b"".join(REG_RECORD.pack(*row) for row in slots) + fields
    expected = field_values(section)
    if expected.pop("Flags") != "Lifetap" or field_values(result) != expected:
        raise ValueError("Unexpected Mantis flag or rebuilt creature definition")
    return result


def build(game):
    resources = game / "Resources"
    check_hashes(resources, SOURCE_HASHES)
    if IDENT in (game / "Etherlords2.exe").read_bytes():
        raise ValueError("Experimental ID occurs in the stock executable")
    regs = Archive((resources / "regs.res").read_bytes())
    text = Archive((resources / "text.res").read_bytes())
    spells = "CombatSpells.reg"
    creatures = "CombatCreatures.reg"
    old_creatures = read_reg(regs.read(creatures))
    if IDENT in old_creatures or IDENT in read_reg(regs.read("GlobalSpells.reg")):
        raise ValueError("Creature ID is already present")
    creature = remove_flags(clone_section(old_creatures[MANTIS], IDENT, {
        b"Power": 5, b"Toughness": 5, b"Race": "Rat",
    }))
    replacements = {
        creatures: write_reg(old_creatures | {IDENT: creature}),
        spells: add_sections(regs.read(spells), [(IDENT, SHAMAN, {
            b"Name": "E3RTNm", b"ToolTip": "E3RTTt", b"CostRoot": 0, b"CostRuby": 0,
            b"Icon": 478,
        })]),
    }
    for name in ("ELKIDs.reg", "Texts.reg", "ELKTexts.reg"):
        replacements[name] = add_sections(regs.read(name), [
            (key, SHAMAN + key[-2:], {b"Translate": [value, value]} if name == "ELKTexts.reg" else {})
            for key, value in STRINGS.items()
        ])
    for member, payload in replacements.items():
        original = read_reg(regs.read(member))
        updated = read_reg(payload)
        additions = {IDENT} if member in (creatures, spells) else set(STRINGS)
        if updated.keys() - original.keys() != additions or any(updated[k] != v for k, v in original.items()):
            raise ValueError(f"Original registry entries changed in {member}")
    text_member = "ELKTexts.txt"
    patched = {
        "regs.res": regs.replace(replacements),
        "text.res": text.replace({
            text_member: add_text(text.read(text_member), {k.decode(): v for k, v in STRINGS.items()})
        }),
    }
    for name, data in patched.items():
        (resources / name).write_bytes(data)
    overlay = portrait_overlay(resources)
    with (resources / "textures001.res").open("xb") as target:
        target.write(overlay)
    patched["textures001.res"] = overlay
    return {name: digest(data) for name, data in patched.items()}


def prepare(baseline, name):
    target = LOCAL / name
    if (Path(name).name != name or name in ("", ".", "..") or target.exists()
            or LOCAL.resolve().is_relative_to(baseline)):
        raise ValueError("Use a new directory name under the local probe directory")
    check_hashes(baseline, {"Etherlords2.exe": PINNED_EXE})
    check_hashes(baseline / "Resources", SOURCE_HASHES)
    LOCAL.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=LOCAL) as staging:
        game = Path(staging) / "game"
        shutil.copytree(baseline, game, ignore=shutil.ignore_patterns(
            ".git", ".campaign-ui-local", ".duel-matrix-copy", ".native-combat-test", "local",
            ".spell-probe-backup", ".mechanics-backup", ".etherlords-iii-ui-backup",
            "Save", "Replays", "shot*.bmp",
        ))
        for folder in ("Save", "Replays"):
            (game / folder).mkdir()
        hashes = build(game)
        if hashes != TEST_HASHES:
            raise ValueError("Generated archive hashes differ from the verified build")
        for filename in ("testing-rat.prs", "testing-rat-lifecycle.prs"):
            with (game / "Duel" / filename).open("xb") as handle:
                handle.write((HERE / filename).read_bytes())
        (game / ".native-combat-test").touch(exist_ok=False)
        (game / "testing-rat-hashes.json").write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")
        game.rename(target)
    print(json.dumps(hashes))
    print(target)


class TestingRat:
    local = LOCAL
    archives = TEST_HASHES

    def stage(self, api, process, traces, record):
        register_producer(api, process, record, IDENT, SHAMAN_PRODUCER)
        traces[INITIALIZER_RETURN] = (b"\x68", "rat-registry")
        traces[0x6ED7EB] = (b"\xe8", "shaman-attach")
        traces[0x6ED960] = (b"\x64", "shaman-activate")
        traces[0x6EDBA0] = (b"\xe8", "shaman-hero-damage")
        traces[0x6EDCF0] = (b"\xe8", "shaman-creature-damage")

    def trace(self, api, process, kind, registers):
        if kind == "rat-registry":
            sentinel, count = words(api, process, PRODUCER_MAP, 2)
            entries = [producer(api, process, sentinel, code) for code in (IDENT, SHAMAN)]
            vtables = [words(api, process, pointer, 1)[0] for pointer in entries]
            if count != PRODUCER_COUNT + 1 or entries[0] == entries[1] or vtables != [PRODUCER_VTABLE] * 2:
                raise ValueError("Unexpected registry count or producer ownership")
            return {"entries": count, "E3RT": hex(entries[0]), "KBSH": hex(entries[1]),
                    "producer_vtable": hex(vtables[0])}
        if kind == "shaman-attach":
            spell = registers["edi"]
            owner, = words(api, process, spell + 0x30, 1)
        elif kind == "shaman-activate":
            owner, = words(api, process, registers["ecx"] + 0x28, 1)
        else:
            owner, = words(api, process, registers["esi"] + 0x28, 1)
        code = memory(api, process, owner + 0x20, 4)
        stats, = words(api, process, owner + 0x3C, 1)
        power, toughness = words(api, process, stats, 2)
        fields = {"creature_id": code.decode("ascii", errors="replace"),
                  "power": power, "toughness": toughness}
        if kind == "shaman-attach":
            sentinel, = words(api, process, RACE_MAP, 1)
            node = registry_node(api, process, sentinel, code)
            start, end = words(api, process, node + 0x18, 2)
            if not 0 < end - start < 32:
                raise ValueError("Unexpected live race entry")
            fields["race"] = memory(api, process, start, end - start).decode("ascii")
        elif kind.endswith("-damage"):
            fields["damage"] = words(api, process, registers["esp"] + 4, 1)[0]
        return fields


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare")
    prep.add_argument("baseline", type=Path)
    prep.add_argument("name")
    launch = commands.add_parser("run")
    launch.add_argument("game", type=Path)
    launch.add_argument("log", type=Path)
    args = parser.parse_args()
    try:
        if args.command == "prepare":
            prepare(args.baseline.resolve(strict=True), args.name)
        else:
            run(args.game.resolve(strict=True), "testing-rat", args.log.resolve(), extension=TestingRat())
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
