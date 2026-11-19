"""Run a Card Creator package through the existing pinned x86 debug launcher."""

import argparse
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

from creator_core import ABILITIES, EFFECTS, PINNED_EXE, checksum
from install_game import BACKUP, load_manifest
from combat_probe import (
    INITIALIZER_BYTES, INITIALIZER_RETURN, INITIALIZER_TAIL, PRODUCER_COUNT, PRODUCER_MAP,
    SURCHARGE_CHECK, SURCHARGE_DEBIT, branch, executable_buffer, memory, p32,
    producer, producer_instructions, replace, run, words,
)
from spell_lab import Archive, field_values, read_reg


def jcc(opcode, address, destination):
    return bytes((0x0F, opcode)) + p32((destination - address - 6) & 0xFFFFFFFF)


def project_initializer(address, bindings):
    code = bytearray.fromhex("89 38 81 7e 04") + p32(PRODUCER_COUNT)
    tail = len(code)
    code.extend(bytes(6))
    for ident, donor in bindings:
        code.extend(producer_instructions(address + len(code), ident, donor.constructor))
    code[tail:tail + 6] = jcc(0x85, address + tail, address + len(code))
    code.extend(INITIALIZER_BYTES[:4])
    code.extend(branch(0xE9, address + len(code), INITIALIZER_TAIL + len(INITIALIZER_BYTES)))
    return bytes(code)


def surcharge_stub(address, ids, debit=False):
    code = bytearray() if debit else bytearray.fromhex("8b 57 14")
    checks = []
    for ident in ids:
        code.extend(b"\x81\x7f\x04" + ident)
        checks.append(len(code))
        code.extend(bytes(6))
    if debit:
        code.extend(bytes.fromhex("55 eb 02"))
        flat = address + len(code)
        code.extend(bytes.fromhex("6a 00 50"))
        call_site = address + len(code)
        code.extend(branch(0xE8, call_site, 0x7542B0))
        code.extend(branch(0xE9, address + len(code), 0x6CCCDE))
    else:
        code.extend(bytes.fromhex("39 6a 20"))
        code.extend(jcc(0x8C, address + len(code), 0x6CCCB9))
        flat = address + len(code)
        code.extend(branch(0xE9, flat, 0x6CCCC0))
        call_site = None
    for offset in checks:
        code[offset:offset + 6] = jcc(0x84, address + offset, flat)
    return bytes(code), call_site


class CreatorExtension:
    def __init__(self, game):
        self.local = game.parent
        manifest = load_manifest(game / BACKUP)
        self.archives = {Path(name).name: expected for name, expected in manifest["files"].items()
                         if name.startswith("Resources/")}
        exe = game / "Etherlords2.exe"
        if checksum(exe) != PINNED_EXE:
            raise ValueError("The game executable does not match this package.")
        binary = exe.read_bytes()
        regs = Archive((game / "Resources/regs.res").read_bytes())
        rows = read_reg(regs.read("CombatSpells.reg"))
        creatures = read_reg(regs.read("CombatCreatures.reg"))
        stock = Archive((game / BACKUP / "Resources/regs.res").read_bytes())
        stock_rows = read_reg(stock.read("CombatSpells.reg"))
        stock_creatures = read_reg(stock.read("CombatCreatures.reg"))
        if any(rows.get(code) != row for code, row in stock_rows.items()) or any(
                creatures.get(code) != row for code, row in stock_creatures.items()):
            raise ValueError("The installed package changed a stock combat record.")
        self.bindings = []
        self.flat = []
        custom_creatures = set()
        for row in manifest["bindings"]:
            ident = row["id"].encode("ascii")
            creature = row["kind"] == "creature"
            if (ident in binary or ident in stock_rows or ident not in rows or
                    field_values(rows[ident])["Class"] != ("Creature" if creature else "Sorcery")):
                raise ValueError(f"Missing or incompatible metadata for {row['id']}.")
            donor = (ABILITIES if creature else EFFECTS)[row["donor"]]
            self.bindings.append((ident, donor))
            if creature:
                custom_creatures.add(ident)
            if row["flat_cost"]:
                self.flat.append(ident)
        if rows.keys() - stock_rows.keys() != {code for code, _ in self.bindings} or (
                creatures.keys() - stock_creatures.keys() != custom_creatures):
            raise ValueError("Metadata and native configuration list different card IDs.")
        known = {code.decode("ascii", errors="replace") for code in rows}
        for preset in (game / "Duel").glob("*.prs"):
            try:
                root = ET.parse(preset).getroot()
            except ET.ParseError as error:
                raise ValueError(f"Invalid Duel preset {preset.name}: {error}") from error
            referenced = {spell.get("code", "") for spell in root.findall(".//spell")}
            if missing := referenced - known:
                raise ValueError(f"{preset.name} requires missing card IDs: {', '.join(sorted(missing))}.")

    def stage(self, api, process, traces, record):
        address = executable_buffer(api, process, lambda target: project_initializer(target, self.bindings))
        jump = branch(0xE9, INITIALIZER_TAIL, address) + b"\x90"
        replace(api, process, INITIALIZER_TAIL, INITIALIZER_BYTES, jump)
        traces[INITIALIZER_RETURN] = (b"\x68", "project-producers")
        if self.flat:
            for site, original, debit in (
                (SURCHARGE_CHECK, bytes.fromhex("8b 57 14 39 6a 20 7d 07"), False),
                (SURCHARGE_DEBIT, bytes.fromhex("55 50 e8 d2 75 08 00"), True),
            ):
                address = executable_buffer(api, process, lambda target: surcharge_stub(target, self.flat, debit)[0])
                jump = branch(0xE9, site, address) + b"\x90" * (len(original) - 5)
                replace(api, process, site, original, jump)
                if debit:
                    traces[surcharge_stub(address, self.flat, True)[1]] = (b"\xe8", "unsummoning-debit")
        if any(donor.stock == "KBSH" for _, donor in self.bindings):
            traces[0x6ED7EB] = (b"\xe8", "shaman-summon")
            traces[0x6ED960] = (b"\x64", "shaman-activate")
        record("configured", cards=[code.decode() for code, _ in self.bindings])

    def trace(self, api, process, kind, registers):
        if kind == "project-producers":
            sentinel, total = words(api, process, PRODUCER_MAP, 2)
            if total != PRODUCER_COUNT + len(self.bindings):
                raise ValueError(f"Expected {PRODUCER_COUNT + len(self.bindings)} producers, found {total}.")
            result, addresses = {}, set()
            for code, donor in self.bindings:
                instance = producer(api, process, sentinel, code)
                original = producer(api, process, sentinel, donor.stock.encode())
                if instance in addresses or instance == original or words(api, process, instance, 1)[0] != donor.vtable:
                    raise ValueError("Producer ownership or native class is inconsistent.")
                result[code.decode()] = hex(instance)
                addresses.add(instance)
            return {"total": total, "created": result}
        if kind == "unsummoning-debit":
            spell = registers["edi"]
            return {"card": memory(api, process, spell + 4, 4).decode("ascii"),
                    "creatures": registers["ebp"], "surcharge": words(api, process, registers["esp"] + 4, 1)[0]}
        if kind == "shaman-summon":
            owner = words(api, process, registers["edi"] + 0x30, 1)[0]
        else:
            owner = words(api, process, registers["ecx"] + 0x28, 1)[0]
        stats = words(api, process, owner + 0x3C, 1)[0]
        attack, health = words(api, process, stats, 2)
        return {"card": memory(api, process, owner + 0x20, 4).decode("ascii"),
                "attack": attack, "health": health}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("game", type=Path)
    parser.add_argument("log", type=Path)
    args = parser.parse_args()
    try:
        game = args.game.resolve(strict=True)
        run(game, "card-creator", args.log.resolve(), extension=CreatorExtension(game))
    except (OSError, ValueError, KeyError) as error:
        print(f"Could not launch: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
