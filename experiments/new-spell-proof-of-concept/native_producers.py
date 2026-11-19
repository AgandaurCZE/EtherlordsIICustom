"""List native spell producer IDs from the pinned 1.03 executable, read-only."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import struct


PINNED_EXE = "d3ed30f840b3325b1f03c01aa486e7f44328a7d6993964c409950a65e86a158b"
IMAGE_BASE = 0x400000  # Sections in this specific build have matching RVA and raw offsets.


def relative_calls(code, target):
    for match in re.finditer(rb"(?=\xe8(....))", code, re.S):
        address = IMAGE_BASE + match.start()
        if address + 5 + struct.unpack("<i", match[1])[0] == target:
            yield match.start()


def producers(executable):
    if sha256(executable).hexdigest() != PINNED_EXE:
        raise ValueError("Executable checksum differs from the analyzed 1.03 build")
    code = executable[:0x4af000]
    converters = set(relative_calls(code, 0x5246f0))
    result = {}
    for registration in relative_calls(code, 0x746580):
        matches = set()
        for conversion in range(registration - 45, registration):
            if conversion not in converters:
                continue
            for push in range(conversion - 12, conversion):
                if code[push] != 0x68:
                    continue
                offset = struct.unpack_from("<I", code, push + 1)[0] - IMAGE_BASE
                spell = executable[offset:offset + 5]
                if re.fullmatch(rb"[A-Z0-9]{4}\0", spell):
                    matches.add(spell[:4].decode("ascii"))
        if len(matches) != 1:
            raise ValueError(f"Unexpected producer registration at {IMAGE_BASE + registration:#x}")
        ident = matches.pop()
        if ident in result:
            raise ValueError(f"Duplicate native producer {ident}")
        result[ident] = hex(IMAGE_BASE + registration)
    if len(result) != 343:
        raise ValueError("Native producer count differs from the analyzed build")
    return result


def constructors(executable, registrations):
    result = {}
    for ident, address in registrations.items():
        end = int(address, 16) - IMAGE_BASE
        start = end - 62
        # The allocation path calls the producer constructor and saves its result in EDI.
        matches = list(re.finditer(rb"\x8b\xc8\xe8(....)\x8b\xf8", executable[start:end], re.S))
        if len(matches) != 1:
            raise ValueError(f"Unexpected producer constructor sequence for {ident}")
        match = matches[0]
        delta = struct.unpack("<i", match[1])[0]
        result[ident] = hex(IMAGE_BASE + start + match.start() + 7 + delta)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", type=Path)
    parser.add_argument("ids", nargs="*", help="Limit output to these IDs")
    parser.add_argument("--constructors", action="store_true", help="Include native constructor call targets")
    args = parser.parse_args()
    try:
        executable = args.exe.read_bytes()
        found = producers(executable)
        targets = constructors(executable, found) if args.constructors else None
    except (OSError, ValueError) as error:
        parser.exit(1, f"Error: {error}\n")
    result = {ident: found.get(ident) for ident in args.ids} if args.ids else dict(sorted(found.items()))
    report = {"producer_count": len(found), "registration_call_va": result}
    if targets is not None:
        report["distinct_constructor_targets"] = len(set(targets.values()))
        report["constructor_va"] = {ident: targets.get(ident) for ident in result}
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
