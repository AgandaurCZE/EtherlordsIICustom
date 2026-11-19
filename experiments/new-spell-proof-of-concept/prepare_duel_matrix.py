"""Prepare two disposable copies and three named single-player Duel controls."""

import argparse
from collections import Counter
from pathlib import Path
import re
import shutil
import xml.etree.ElementTree as ET

from native_producers import PINNED_EXE
from spell_lab import Archive, HERE, digest, field_values, read_reg


SOURCE_HASHES = {
    "regs.res": "e38ed76d8fcde2aeee1e22a89771e9eb05d95f3364e122a3024db929975970d7",
    "text.res": "0360ed75214fc2565fef1e3bb67b096323d6a9d5a4e17a87a72b38b7d6f9af6b",
}
PROBE_HASHES = {
    "regs.res": "26592e61ae3b78b372deadd15546af63cf743ae41eb7168567c233cee3ed69e3",
    "text.res": "ff90849e81172c47505b7be90e5f5aa31f390bf713d7196296b66ebcce8f185f",
}


def check_hashes(directory, expected):
    for name, checksum in expected.items():
        if digest((directory / name).read_bytes()) != checksum:
            raise ValueError(f"Hash mismatch for {directory / name}")


def write_presets(probe_game):
    regs = Archive((probe_game / "Resources" / "regs.res").read_bytes())
    spells = read_reg(regs.read("CombatSpells.reg"))
    native_decks = read_reg(regs.read("CombatDecks.reg"))
    blue_deck = field_values(native_decks[b"STU1"])["Spells"]
    blue_ids = []
    for slot in blue_deck:
        match = re.fullmatch(r"([A-Z0-9]{4})\(\d+:\d+\)", slot)
        if match is None:
            raise ValueError(f"Unexpected stock deck slot {slot!r}")
        blue_ids.append(match[1])

    paths = []
    for number, name, count in (
        (3, "Matrix 03 - One E3TC", 1),
        (4, "Matrix 04 - Three E3TC", 3),
        (5, "Matrix 05 - GRUN Control", 3),
    ):
        preset = ET.parse(HERE / "duel-testing-card.prs")
        root = preset.getroot()
        root.set("name", name)
        slots = root.findall("deck/spell")
        if number == 5:
            root.set("magic", "Blue")
            for node, ident in zip(slots, blue_ids[:-count] + ["GRUN"] * count, strict=True):
                node.set("code", ident)
        else:
            matching = [node for node in slots if node.get("code") == "E3TC"]
            for node in matching[count:]:
                node.set("code", "FRWA")
        ids = Counter(node.get("code") for node in slots)
        expected = "GRUN" if number == 5 else "E3TC"
        if len(slots) != 16 or ids[expected] != count:
            raise ValueError(f"Unexpected card count for {name}")
        for ident in ids:
            if field_values(spells[ident.encode("ascii")])["Color"] != root.get("magic"):
                raise ValueError(f"Unexpected faction for {ident} in {name}")
        path = probe_game / "Duel" / f"matrix-{number:02}.prs"
        ET.indent(preset)
        with path.open("xb") as output:
            preset.write(output, encoding="utf-8", xml_declaration=True)
        paths.append(path)
    return paths


def prepare(baseline, resources, output):
    if (not output.is_relative_to(HERE / "local") or output.exists()
            or output.is_relative_to(baseline)):
        raise ValueError("Use a new directory under local/ outside the baseline game")
    check_hashes(baseline, {"Etherlords2.exe": PINNED_EXE})
    check_hashes(baseline / "Resources", SOURCE_HASHES)
    check_hashes(resources, PROBE_HASHES)
    output.mkdir(parents=True)
    ignore = shutil.ignore_patterns(".git", ".campaign-ui-local", "local", ".spell-probe-backup",
                                    ".etherlords-iii-ui-backup", "shot*.bmp")
    for name in ("stock", "probe"):
        game = output / name
        shutil.copytree(baseline, game, ignore=ignore)
        if name == "probe":
            for archive in PROBE_HASHES:
                shutil.copyfile(resources / archive, game / "Resources" / archive)
            check_hashes(game / "Resources", PROBE_HASHES)
            write_presets(game)
        else:
            check_hashes(game / "Resources", SOURCE_HASHES)
        (game / ".duel-matrix-copy").touch(exist_ok=False)
    (output / "logs").mkdir()
    print(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("--probe", type=Path, default=HERE / "local" / "metadata-probe")
    parser.add_argument("--output", type=Path, default=HERE / "local" / "duel-matrix")
    args = parser.parse_args()
    try:
        prepare(args.baseline.resolve(strict=True), args.probe.resolve(strict=True), args.output.resolve())
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
