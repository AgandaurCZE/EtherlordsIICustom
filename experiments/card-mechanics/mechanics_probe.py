"""Build isolated, local Etherlords II 1.03 card mechanics probes."""

import argparse
import json
from pathlib import Path
import re
import struct
import sys
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "new-spell-proof-of-concept"))
from spell_lab import Archive, bucket, digest, field_values, read_fields, read_reg, REG_RECORD, write_reg
from prepare_duel_matrix import SOURCE_HASHES


def apply_rat_stats(data):
    archive = Archive(data)
    member = "CombatCreatures.reg"
    _, offset, _ = archive.members[member]
    registry = archive.read(member)
    rows = read_reg(registry)
    rat = rows[b"STRT"]
    start = registry.index(rat)
    fields = read_fields(rat)
    result = bytearray(data)
    for name in (b"Power", b"Toughness"):
        _, kind, position = fields[name]
        if kind != 0 or struct.unpack_from("<i", rat, position)[0] != 1:
            raise ValueError("Unexpected stock Stink Rat statistics")
        struct.pack_into("<i", result, offset + start + position, 3)
    verified = read_reg(Archive(result).read(member))
    expected = field_values(rat) | {"Power": 3, "Toughness": 3}
    if (field_values(verified[b"STRT"]) != expected
            or any(verified[key] != section for key, section in rows.items() if key != b"STRT")
            or sum(before != after for before, after in zip(data, result, strict=True)) != 2):
        raise ValueError("Rat stat probe verification failed")
    return result


def field_records(section):
    # Values need not be physically ordered like their hash slots.
    positions = sorted((position - len(key) - 3, key)
                       for key, (_, _, position) in read_fields(section).items())
    ends = [position for position, _ in positions[1:]] + [len(section)]
    return {key: section[position:end] for (position, key), end in zip(positions, ends, strict=True)}


def copy_rat_ability(data):
    archive = Archive(data)
    member = "CombatSpells.reg"
    sections = read_reg(archive.read(member))
    rat, donor = (sections[key] for key in (b"STRT", b"DMRT"))
    copied_keys = (b"Ability", b"AbilityIcon", b"AbilityText")
    original = field_records(rat)
    donor_records = field_records(donor)
    if any(key in original for key in copied_keys):
        raise ValueError("Unexpected stock Stink Rat ability fields")
    records = original | {key: donor_records[key] for key in copied_keys}
    header = struct.pack("<HH4s", len(records), 4, b"STRT")
    # Field keys follow the same hash rules as section names.
    slots = [None] * len(records)
    data_area = bytearray()
    pending = []
    for key, record in records.items():
        start = len(header) + len(records) * REG_RECORD.size + len(data_area)
        data_area.extend(record)
        head = bucket(key, len(records))
        if slots[head] is None:
            slots[head] = (-1, start)
        else:
            pending.append((head, start))
    free = iter(index for index, slot in enumerate(slots) if slot is None)
    for head, start in pending:
        index = next(free)
        link, pointer = slots[head]
        slots[index] = (link, start)
        slots[head] = (index, pointer)
    changed = header + b"".join(REG_RECORD.pack(*slot) for slot in slots) + data_area
    expected = field_values(rat) | {key.decode(): field_values(donor)[key.decode()] for key in copied_keys}
    if field_values(changed) != expected:
        raise ValueError("Rat ability fields did not round-trip")
    sections[b"STRT"] = changed
    result = archive.replace({member: write_reg(sections)})
    if read_reg(Archive(result).read(member)) != sections:
        raise ValueError("Rat ability probe changed another spell record")
    return result


def zap_label(data):
    archive = Archive(data)
    member = "ELKTexts.txt"
    original = archive.read(member).decode("utf-16")
    pattern = r"(?m)(^#ZAPPTt\r?\n)Deals 1 damage to target creature or hero(?=\r?$)"
    changed, count = re.subn(pattern, r"\1UI-only test: 3 damage to target creature or hero", original)
    if count != 1:
        raise ValueError("Expected exactly one stock Zap tooltip")
    return archive.replace({member: b"\xff\xfe" + changed.encode("utf-16-le")})


def build(resources, phase, output):
    if not output.is_relative_to(HERE / "local") or output.exists():
        raise ValueError("Choose a new output directory below this experiment's local/ directory")
    archive_name = "text.res" if phase == "zap-ui-control" else "regs.res"
    data = (resources / archive_name).read_bytes()
    original_hash = digest(data)
    if original_hash != SOURCE_HASHES[archive_name]:
        raise ValueError(f"Wrong stock SHA-256 for {archive_name}")
    if phase == "zap-ui-control":
        changed = zap_label(data)
    else:
        changed = apply_rat_stats(data)
        if phase == "rat-ability":
            changed = copy_rat_ability(changed)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as scratch:
        package = Path(scratch) / "output"
        package.mkdir()
        hashes = {"archive": archive_name, "original": original_hash, "modified": digest(changed)}
        (package / archive_name).write_bytes(changed)
        (package / "checksums.json").write_text(json.dumps(hashes, indent=2) + "\n", encoding="utf-8")
        if phase == "rat-stats":
            with zipfile.ZipFile(package / "rat-3x3-local.zip", "x", zipfile.ZIP_DEFLATED) as bundle:
                bundle.write(package / archive_name, f"Resources/{archive_name}")
                bundle.write(package / "checksums.json", "checksums.json")
                bundle.write(HERE / "INSTALL.md", "INSTALL.md")
        package.rename(output)
    print(json.dumps(hashes, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resources", type=Path, required=True)
    parser.add_argument("phase", choices=("rat-stats", "rat-ability", "zap-ui-control"))
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    output = (args.output or HERE / "local" / args.phase).resolve()
    try:
        build(args.resources, args.phase, output)
    except (OSError, ValueError, KeyError, struct.error) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
