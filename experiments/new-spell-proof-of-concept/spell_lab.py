"""Inspect spell metadata or generate a local additive Encyclopedia probe."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import tempfile


RES_HEADER = struct.Struct("<4I")
RES_RECORD = struct.Struct("<iIIIHI")
REG_RECORD = struct.Struct("<hI")
REG_MAGIC = b"\xfb\x3e\xab\x45"
HERE = Path(__file__).resolve().parent


def digest(data):
    return hashlib.sha256(data).hexdigest()


class Archive:
    def __init__(self, data):
        self.data = data
        magic, count, self.directory, names_size = RES_HEADER.unpack_from(data)
        self.names_at = self.directory + count * RES_RECORD.size
        if magic != 0x019CE23C or self.directory < 16 or self.names_at + names_size != len(data):
            raise ValueError("Invalid Nival RES directory")
        self.members = {}
        for row in range(count):
            position = self.directory + row * RES_RECORD.size
            _, size, offset, _, length, name_at = RES_RECORD.unpack_from(data, position)
            if name_at + length > names_size or not 16 <= offset <= offset + size <= self.directory:
                raise ValueError("RES entry out of bounds")
            start = self.names_at + name_at
            name = data[start:start + length].decode("cp1251")
            if name in self.members:
                raise ValueError(f"Duplicate RES member {name}")
            self.members[name] = (position, offset, size)

    def read(self, name):
        _, offset, size = self.members[name]
        return self.data[offset:offset + size]

    def replace(self, replacements):
        directory = bytearray(self.data[self.directory:])
        output = bytearray(self.data[:self.directory])
        for name, payload in replacements.items():
            position, _, _ = self.members[name]
            output.extend(bytes(-len(output) % 16))
            struct.pack_into("<II", directory, position - self.directory + 4, len(payload), len(output))
            output.extend(payload)
        output.extend(bytes(-len(output) % 16))
        struct.pack_into("<I", output, 8, len(output))
        output.extend(directory)
        verified = Archive(output)
        if verified.members.keys() != self.members.keys() or any(
            verified.read(key) != replacements.get(key, self.read(key)) for key in self.members
        ):
            raise ValueError("Archive verification failed")
        return output


def read_string(data, offset):
    length = struct.unpack_from("<H", data, offset)[0]
    start = offset + 2
    end = start + length
    if end > len(data):
        raise ValueError("REG string out of bounds")
    return bytes(data[start:end]), end


def bucket(name, count):
    value = sum(byte if byte < 128 else byte - 256 for byte in name.lower())
    return (value & 0xffffffff) % count


def check_lookup(names, rows):
    for index, name in enumerate(names):
        slot = bucket(name, len(names))
        seen = set()
        while slot != index:
            if not 0 <= slot < len(rows) or slot in seen:
                raise ValueError(f"Broken REG hash chain for {name!r}")
            seen.add(slot)
            slot = rows[slot][0]


def read_reg(data):
    if data[:4] != REG_MAGIC:
        raise ValueError("Expected hashed Nival REG")
    count = struct.unpack_from("<H", data, 4)[0]
    rows = list(REG_RECORD.iter_unpack(data[6:6 + count * 6]))
    offsets = sorted(offset for _, offset in rows)
    if len(rows) != count or len(set(offsets)) != count or any(
        not 6 + count * 6 <= offset < len(data) for offset in offsets
    ):
        raise ValueError("Invalid REG section offsets")
    ends = dict(zip(offsets, offsets[1:] + [len(data)]))
    names = [read_string(data, offset + 2)[0] for _, offset in rows]
    check_lookup(names, rows)
    if len({name.lower() for name in names}) != len(names):
        raise ValueError("Duplicate REG section")
    return {name: bytes(data[offset:ends[offset]]) for name, (_, offset) in zip(names, rows)}


def write_reg(sections):
    count = len(sections)
    rows = [None] * count
    pending = []
    body = bytearray()
    for name, section in sections.items():
        offset = 6 + count * 6 + len(body)
        body.extend(section)
        head = bucket(name, count)
        if rows[head] is None:
            rows[head] = (-1, offset)
        else:
            pending.append((head, offset))
    free = iter(index for index, row in enumerate(rows) if row is None)
    for head, offset in pending:
        slot = next(free)
        link, original_offset = rows[head]
        rows[slot] = (link, offset)
        rows[head] = (slot, original_offset)
    result = REG_MAGIC + struct.pack("<H", count) + b"".join(REG_RECORD.pack(*row) for row in rows) + body
    if read_reg(result) != sections:
        raise ValueError("REG verification failed")
    return result


def read_fields(section):
    count = struct.unpack_from("<H", section)[0]
    _, start = read_string(section, 2)
    rows = list(REG_RECORD.iter_unpack(section[start:start + count * 6]))
    fields = {}
    for link, offset in rows:
        kind = section[offset]
        name, pos = read_string(section, offset + 1)
        fields[name] = (link, kind, pos)
    check_lookup(list(fields), rows)
    if len(fields) != count:
        raise ValueError("Invalid REG keys")
    return fields


def read_value(section, kind, pos):
    count = 1
    if kind & 128:
        count = struct.unpack_from("<H", section, pos)[0]
        pos += 2
    values = []
    for _ in range(count):
        if kind & 127 == 2:
            value, pos = read_string(section, pos)
            values.append(value.decode("cp1251"))
        elif kind & 127 in (0, 1):
            values.append(struct.unpack_from("<i" if kind & 127 == 0 else "<f", section, pos)[0])
            pos += 4
        else:
            raise ValueError(f"Unsupported REG field type {kind}")
    return (values if kind & 128 else values[0]), pos


def field_values(section):
    return {key.decode("cp1251"): read_value(section, kind, pos)[0]
            for key, (_, kind, pos) in read_fields(section).items()}


def packed_string(value):
    return struct.pack("<H", len(value)) + value


def clone_section(template, name, changes):
    fields = read_fields(template)
    if not changes.keys() <= fields.keys():
        raise ValueError("A replacement key is absent from the original section")
    header = struct.pack("<H", len(fields)) + packed_string(name)
    index = bytearray()
    data = bytearray()
    for key, (link, kind, pos) in fields.items():
        _, end = read_value(template, kind, pos)
        if key not in changes:
            value = template[pos:end]
        elif kind == 2:
            value = packed_string(changes[key].encode("cp1251"))
        elif kind == 0:
            value = struct.pack("<i", changes[key])
        elif kind == 130:
            strings = changes[key]
            value = struct.pack("<H", len(strings)) + b"".join(
                packed_string(string.encode("cp1251")) for string in strings
            )
        else:
            raise ValueError(f"Cannot replace {key!r} with REG type {kind}")
        index.extend(REG_RECORD.pack(link, len(header) + 6 * len(fields) + len(data)))
        data.extend(bytes([kind]) + packed_string(key) + value)
    result = header + index + data
    expected = field_values(template)
    expected.update({key.decode("ascii"): value for key, value in changes.items()})
    if field_values(result) != expected:
        raise ValueError("Cloned fields did not round-trip")
    return result


def add_sections(payload, additions):
    sections = read_reg(payload)
    originals = set(name.lower() for name in sections)
    for name, model, changes in additions:
        if name.lower() in originals:
            raise ValueError(f"Existing REG section would be overwritten: {name!r}")
        originals.add(name.lower())
        sections[name] = clone_section(sections[model], name, changes)
    return write_reg(sections)


def add_text(payload, records):
    if not payload.startswith(b"\xff\xfe"):
        raise ValueError("Expected a UTF-16LE text bank")
    text = payload.decode("utf-16")
    keys = {key.casefold() for key in re.findall(r"(?m)^#([^\r\n]+)", text)}
    if any(key.casefold() in keys for key in records):
        raise ValueError("Existing localization key would be overwritten")
    newline = "\r\n" if "\r\n" in text else "\n"
    suffix = "" if text.endswith("\n") else newline
    for key, value in records.items():
        if not value or any(character in value for character in "\r\n\0"):
            raise ValueError("Probe labels must be nonempty single lines")
        suffix += f"#{key}{newline}{value}{newline}"
    return payload + suffix.encode("utf-16-le")


def inspect(resources, names):
    regs = Archive((resources / "regs.res").read_bytes())
    spells = read_reg(regs.read("CombatSpells.reg"))
    text = Archive((resources / "text.res").read_bytes()).read("ELKTexts.txt").decode("utf-16")
    blocks = dict(re.findall(r"(?m)^#([^\r\n]+)\r?\n(.*?)(?=^#|\Z)", text, re.S | re.M))
    for name in names:
        fields = field_values(spells[name.encode("ascii")])
        print(json.dumps({"id": name, "fields": fields,
                          "name": blocks.get(fields["Name"], "").strip(),
                          "description": blocks.get(fields["ToolTip"], "").strip()}, indent=2))


def build(resources, output, profile_path):
    profile = json.loads(profile_path.read_text(encoding="utf-8"))
    code, model = (profile[key].encode("ascii") for key in ("id", "model"))
    if not re.fullmatch(rb"[A-Z0-9]{4}", code):
        raise ValueError("Probe ID must be four uppercase ASCII letters or digits")
    if not output.is_relative_to(HERE / "local") or output.exists():
        raise ValueError("Build into a new directory under this experiment's ignored local/ folder")
    pinned = profile["source_sha256"]
    if set(pinned) != {"regs.res", "text.res"}:
        raise ValueError("Expected pinned hashes for regs.res and text.res")
    archives = {}
    for name, expected in pinned.items():
        data = (resources / name).read_bytes()
        if digest(data) != expected:
            raise ValueError(f"Source checksum mismatch for {name}")
        archives[name] = Archive(data)
    keys = {code + b"Nm": profile["name"], code + b"Tt": profile["description"]}
    fields = {name.encode("ascii"): value for name, value in profile["fields"].items()}
    fields.update({b"Name": (code + b"Nm").decode("ascii"), b"ToolTip": (code + b"Tt").decode("ascii")})
    regs = archives["regs.res"]
    replacement = {
        "CombatSpells.reg": add_sections(regs.read("CombatSpells.reg"), [(code, model, fields)]),
    }
    metadata = [(key, model + key[-2:], {}) for key in keys]
    for name in ("ELKIDs.reg", "Texts.reg"):
        replacement[name] = add_sections(regs.read(name), metadata)
    fallback = [(key, model + key[-2:], {b"Translate": [value, value]}) for key, value in keys.items()]
    replacement["ELKTexts.reg"] = add_sections(regs.read("ELKTexts.reg"), fallback)
    text = archives["text.res"]
    strings = {key.decode("ascii"): value for key, value in keys.items()}
    patched = {
        "regs.res": regs.replace(replacement),
        "text.res": text.replace({"ELKTexts.txt": add_text(text.read("ELKTexts.txt"), strings)}),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=output.parent) as workspace:
        staged = Path(workspace) / "probe"
        staged.mkdir()
        report = {}
        for name, data in patched.items():
            (staged / name).write_bytes(data)
            report[name] = {"source_sha256": pinned[name], "probe_sha256": digest(data)}
        (staged / "checksums.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        staged.rename(output)
    print(json.dumps(report, indent=2))
    print(f"Local metadata probe: {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--resources", type=Path, required=True)
    sub = parser.add_subparsers(dest="command", required=True)
    inspection = sub.add_parser("inspect")
    inspection.add_argument("ids", nargs="+")
    probe = sub.add_parser("build")
    probe.add_argument("--profile", type=Path, default=HERE / "spell-probe.json")
    probe.add_argument("--output", type=Path, default=HERE / "local" / "metadata-probe")
    args = parser.parse_args()
    try:
        if args.command == "inspect":
            inspect(args.resources, args.ids)
        else:
            build(args.resources, args.output.resolve(), args.profile)
    except (OSError, ValueError, KeyError, TypeError, struct.error) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
