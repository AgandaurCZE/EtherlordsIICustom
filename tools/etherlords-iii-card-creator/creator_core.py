"""Project catalog, validation and deterministic Etherlords II resource builds."""

from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from hashlib import file_digest, sha256
import json
import mmap
from pathlib import Path
import re
import struct
import sys
import tempfile
import xml.etree.ElementTree as ET

from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT / "experiments" / name) for name in ("native-combat-extension", "new-creature")]
sys.path.insert(0, str(HERE.parent / "campaign-ui-research"))
from combat_probe import PINNED_EXE, SOURCE_HASHES
from spell_lab import (
    Archive, RES_HEADER, RES_RECORD, add_sections, add_text, bucket, check_lookup,
    clone_section, field_values, read_reg, write_reg,
)
from testing_rat import TEXTURES_SHA256, remove_flags
from campaign_ui import decode_image, encode_mmp

VERSION = "0.1.0"
FACTIONS = {"Red": "Chaots", "Blue": "Kinets", "Green": "Vitals", "Black": "Synthets"}
RARITIES = ("Cantrip", "Common", "Rare", "Unique")
PORTRAIT_DIR = "Interface\\Encyclopaedia\\"
CARD_ID = re.compile(r"[A-Z0-9]{4}\Z")
STOCK_FILLERS = {"Red": ("STRT", "ZAPP", "LSST", "FRWA"), "Blue": ("AVSC",),
                 "Green": (), "Black": ()}
ASSET_HASHES = {
    "textures.res": TEXTURES_SHA256,
    "textures002.res": "e8861810751a63480fe752180f393bb6ae2ef6c767ed19df4f17259c04597b50",
    "animdb.res": "c2cf9d2b36b7da268775f730d34c453d5d4272b66be9ec078a9dacaaf0adaea9",
    "crfigures.res": "600dc9140770939cd11a9a088523d38dabc27b29046c0e2c58ff5a0355529013",
}


@dataclass(frozen=True)
class Donor:
    name: str
    stock: str
    constructor: int
    vtable: int
    description: str


ABILITIES = {
    "plain": Donor("No activated ability", "STRT", 0x7451B0, 0x8C1A80,
                   "Standard summon. Creature can attack and block."),
    "shaman": Donor("Zap · Kobold Shaman", "KBSH", 0x7451D0, 0x8C1A98,
                    "Activated. Rest to deal 1 damage to a creature or hero. No extra Ether."),
    "brotherhood": Donor("Brotherhood · Doom Rat", "DMRT", 0x745300, 0x8C1B7C,
                         "Activated. Rest and pay 2 Ether to retrieve an owned Rat from the graveyard."),
}
EFFECTS = {
    "greater-unsummoning": Donor("Greater Unsummoning · GRUN", "GRUN", 0x745CA0, 0x8C22B4,
                                "Returns eligible creatures on both sides. Kinets BlueDeath effect. Stock cost adds 1 Ether per creature."),
}


def checksum(path):
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()


def canonical(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def portrait_names(code):
    return [f"{PORTRAIT_DIR}{code.lower()}_{index}.mmp" for index in (1, 2, 3)]


def portrait_tiles(image):
    if image.size == (768, 256):
        return [image.crop((i * 256, 0, (i + 1) * 256, 256)) for i in range(3)]
    if image.size != (384, 512):
        raise ValueError("Use a 384 × 512 portrait or 768 × 256 portrait tile sheet.")
    right = Image.new("RGBA", (256, 256))
    right.paste(image.crop((256, 0, 384, 256)), (0, 0))
    right.paste(image.crop((256, 256, 384, 512)), (128, 0))
    return [image.crop((0, 0, 256, 256)), image.crop((0, 256, 256, 512)), right]


def compose_portrait(tiles):
    top, bottom, right = tiles
    image = Image.new("RGBA", (384, 512))
    image.paste(top, (0, 0))
    image.paste(bottom, (0, 256))
    image.paste(right.crop((0, 0, 128, 256)), (256, 0))
    image.paste(right.crop((128, 0, 256, 256)), (256, 256))
    return image


@contextmanager
def mapped_archive(path):
    with path.open("rb") as handle, mmap.mmap(handle.fileno(), 0, access=mmap.ACCESS_READ) as data:
        yield Archive(data)


class Catalog:
    def __init__(self, game):
        self.game = game.resolve()
        resources = self.game / "Resources"
        for path, expected in {self.game / "Etherlords2.exe": PINNED_EXE,
                               **{resources / name: value for name, value in (SOURCE_HASHES | ASSET_HASHES).items()}}.items():
            if checksum(path) != expected:
                raise ValueError(f"Unsupported source file: {path.name}")
        self.regs = Archive((resources / "regs.res").read_bytes())
        self.text = Archive((resources / "text.res").read_bytes())
        spells = read_reg(self.regs.read("CombatSpells.reg"))
        units = read_reg(self.regs.read("CombatCreatures.reg"))
        self.spells = {key.decode(): field_values(record) for key, record in spells.items()}
        self.units = {key.decode(): field_values(record) for key, record in units.items()}
        self.stock_ids = self.spells.keys() | self.units.keys() | {
            key.decode("ascii", errors="replace") for key in read_reg(self.regs.read("GlobalSpells.reg"))
        }
        self.card_capacity = min(
            32768 - len(spells),
            *((32768 - len(read_reg(self.regs.read(name)))) // 2
              for name in ("ELKIDs.reg", "Texts.reg", "ELKTexts.reg")),
        )
        self.executable = (self.game / "Etherlords2.exe").read_bytes()
        strings = self.text.read("ELKTexts.txt").decode("utf-16")
        self.names = dict(re.findall(r"(?m)^#([A-Z0-9]{4})Nm\r?\n([^\r\n]*)", strings))
        with mapped_archive(resources / "animdb.res") as animations, mapped_archive(
                resources / "crfigures.res") as figures:
            self.models = {code: f"{self.names.get(code, code)} · {code} · {row['Model']}"
                           for code, row in self.units.items()
                           if code in self.spells and f"{row['Model']}.adb" in animations.members
                           and all(f"{row['Model']}.{suffix}" in figures.members for suffix in ("mod", "anm"))}
        self.families = sorted({row["Race"] for row in self.units.values()})
        with mapped_archive(resources / "textures.res") as images:
            self.portraits = {code for code in self.spells if all(n in images.members for n in portrait_names(code))}

    def collides(self, code):
        return code in self.stock_ids or code.encode("ascii") in self.executable

    def preview(self, code):
        if code in self.portraits:
            with mapped_archive(self.game / "Resources" / "textures.res") as images:
                return compose_portrait([decode_image(images.read(n)) for n in portrait_names(code)])
        return None


def new_card(kind, ident):
    card = dict(id=ident, kind=kind, name="New Creature" if kind == "creature" else "New Spell",
                faction="Red", cost=1, rarity="Common", description="", artwork="", portrait_png="")
    if kind == "creature":
        card.update(attack=1, health=1, family="Rat", model="STRT", ability="plain")
    else:
        card.update(effect="greater-unsummoning", flat_cost=True)
    return card


def read_project(path):
    data = json.loads(path.read_text(encoding="utf-8"))
    if (not isinstance(data, dict) or data.get("format") != 1 or not isinstance(data.get("cards"), list)
            or any(not isinstance(card, dict) or card.get("kind") not in ("creature", "spell")
                   or not isinstance(card.get("id"), str) or not isinstance(card.get("name"), str)
                   for card in data["cards"])):
        raise ValueError("Select a Card Creator format 1 project.")
    return data


def artwork_file(card, project_dir):
    path = Path(card["portrait_png"])
    return path if path.is_absolute() else project_dir / path


def validate(project, catalog, project_dir):
    errors = []
    cards = project.get("cards")
    if project.get("format") != 1 or not isinstance(cards, list) or not cards:
        return ["Add at least one card to a format 1 project."]
    if len(cards) > catalog.card_capacity:
        errors.append(f"This project exceeds the signed registry index capacity of {catalog.card_capacity} cards.")
    release = project.get("version")
    if not isinstance(release, str) or not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", release):
        errors.append("Set a release version such as 0.1.0.")
    counts = Counter(c.get("id") for c in cards if isinstance(c, dict) and isinstance(c.get("id"), str))
    for index, card in enumerate(cards, 1):
        if not isinstance(card, dict):
            errors.append(f"Card {index} needs a card definition.")
            continue
        ident = card.get("id")
        prefix = f"Card {index} ({ident or 'no ID'})"

        def issue(message):
            errors.append(f"{prefix}: {message}")

        if not isinstance(ident, str) or not CARD_ID.fullmatch(ident):
            issue("Use exactly four uppercase ASCII letters or digits for ID.")
        elif counts[ident] > 1 or catalog.collides(ident):
            issue("ID collides with a custom or stock card.")
        kind = card.get("kind")
        if kind not in ("creature", "spell"):
            issue("Choose Creature or Spell.")
        common = set(new_card("creature" if kind == "creature" else "spell", "0000"))
        if card.keys() - common:
            issue("Unsupported fields: " + ", ".join(sorted(card.keys() - common)))
        for key, caption, maximum in (("name", "Name", 60), ("description", "Description", 400)):
            value = card.get(key)
            if not isinstance(value, str) or len(value) > maximum or any(c in value for c in "\r\n\0") or (
                    key == "name" and not value.strip()) or value.startswith("#"):
                issue(f"{caption} must be one line, up to {maximum} characters.")
            else:
                try:
                    value.encode("cp1251")
                except UnicodeEncodeError:
                    issue(f"{caption} contains a character the stock fallback text registry cannot encode.")
        if card.get("faction") not in FACTIONS:
            issue("Select one of the four playable factions.")
        if card.get("rarity") not in RARITIES:
            issue("Select a stock rarity.")
        for key, low, high in (("cost", 0, 99),) + (
                (("attack", 0, 99), ("health", 1, 99)) if kind == "creature" else ()):
            if type(card.get(key)) is not int or not low <= card[key] <= high:
                issue(f"{key.capitalize()} must be an integer from {low} to {high}.")
        if kind == "creature":
            if card.get("family") not in catalog.families:
                issue("Select a family present in the stock game.")
            if card.get("model") not in catalog.models:
                issue("Choose a model with verified stock mesh and animation members.")
            if card.get("ability") not in ABILITIES:
                issue("Choose one supported native ability or none.")
        elif kind == "spell" and (card.get("effect") not in EFFECTS or type(card.get("flat_cost")) is not bool):
            issue("Choose a supported native effect and cost policy.")
        ref = card.get("artwork")
        if not isinstance(ref, str) or (ref and ref not in catalog.spells):
            issue("Choose a stock artwork reference or leave it blank.")
        png = card.get("portrait_png")
        if not isinstance(png, str):
            issue("Portrait PNG must be a file path or blank.")
        elif png:
            if kind != "creature":
                issue("Custom portrait PNGs are supported only on the creature detail pane.")
            else:
                try:
                    with Image.open(artwork_file(card, project_dir)) as image:
                        if image.format != "PNG" or image.size not in ((384, 512), (768, 256)):
                            raise ValueError
                        image.verify()
                except (OSError, ValueError):
                    issue("Choose a readable 384 × 512 portrait or 768 × 256 PNG tile sheet.")
    return errors


def verified_registry(archive, member, additions):
    original = read_reg(archive.read(member))
    data = write_reg(original | additions)
    updated = read_reg(data)
    if updated.keys() - original.keys() != additions.keys() or any(updated[k] != v for k, v in original.items()):
        raise ValueError(f"Stock entries changed in {member}")
    return data


def archive_overlay(payloads):
    length = len(payloads)
    if not length:
        raise ValueError("The portrait overlay requires at least one tile.")
    keys = list(payloads)
    output = bytearray(RES_HEADER.size)
    index = {}
    for name, pixels in payloads.items():
        index[name] = len(output), len(pixels)
        output.extend(pixels)
        output.extend(bytes(-len(output) % 16))
    table_start = len(output)
    heads, overflow = {}, []
    for name in keys:
        slot = bucket(name.encode("ascii"), length)
        if slot in heads:
            overflow.append((slot, name))
        else:
            heads[slot] = (-1, name)
    free = iter(i for i in range(length) if i not in heads)
    for slot, name in overflow:
        available = next(free)
        link, original = heads[slot]
        heads[slot] = (available, original)
        heads[available] = (link, name)
    strings = bytearray()
    lookup, rows = [], []
    for slot in range(length):
        link, name = heads[slot]
        encoded = name.encode("ascii")
        offset, size = index[name]
        output.extend(RES_RECORD.pack(link, size, offset, 0, len(encoded), len(strings)))
        strings.extend(encoded)
        lookup.append(encoded)
        rows.append((link, offset))
    check_lookup(lookup, rows)
    output.extend(strings)
    RES_HEADER.pack_into(output, 0, 0x019CE23C, length, table_start, len(strings))
    restored = Archive(output)
    if restored.members.keys() != payloads.keys() or any(restored.read(k) != v for k, v in payloads.items()):
        raise ValueError("Portrait overlay verification failed.")
    return bytes(output)


def build_archives(project, catalog, project_dir):
    regs, text = catalog.regs, catalog.text
    cards, units, pictures, texts, bindings = {}, {}, {}, {}, []
    helpers = read_reg(regs.read("CombatSpells.reg"))
    bodies = read_reg(regs.read("CombatCreatures.reg"))
    with mapped_archive(catalog.game / "Resources" / "textures.res") as images:
        for card in project["cards"]:
            ident = card["id"].encode("ascii")
            creature = card["kind"] == "creature"
            donor = ABILITIES[card["ability"]] if creature else EFFECTS[card["effect"]]
            stock = donor.stock.encode()
            artwork = card["artwork"] or (card["model"] if creature else donor.stock)
            fields = dict(Name=card["id"] + "Nm", ToolTip=card["id"] + "Tt", Color=card["faction"],
                          Cost=card["cost"], OriginalCost=card["cost"], Rarity=card["rarity"],
                          Icon=catalog.spells[artwork]["Icon"])
            fields.update({name: 0 for name in catalog.spells[donor.stock] if name.startswith("Cost") and name != "Cost"})
            cards[ident] = clone_section(helpers[stock], ident, {k.encode(): v for k, v in fields.items()})
            texts[ident + b"Nm"] = (stock + b"Nm", card["name"])
            texts[ident + b"Tt"] = (stock + b"Tt", card["description"] or donor.description)
            if creature:
                body = clone_section(bodies[card["model"].encode()], ident, {
                    b"Power": card["attack"], b"Toughness": card["health"], b"Race": card["family"],
                })
                units[ident] = remove_flags(body, ident, catalog.units[card["model"]].get("Flags")) \
                    if "Flags" in catalog.units[card["model"]] else body
                if card["portrait_png"]:
                    with Image.open(artwork_file(card, project_dir)) as source:
                        art = source.convert("RGBA")
                    for index, (name, tile) in enumerate(zip(portrait_names(card["id"]), portrait_tiles(art), strict=True)):
                        pictures[name] = encode_mmp(images.read(portrait_names("MTPT")[index]), tile)
                elif artwork in catalog.portraits:
                    for name, donor_name in zip(portrait_names(card["id"]), portrait_names(artwork), strict=True):
                        pictures[name] = images.read(donor_name)
            bindings.append({"id": card["id"], "kind": card["kind"],
                             "donor": card["ability"] if creature else card["effect"],
                             "flat_cost": not creature and card["flat_cost"]})
    replacements = {"CombatSpells.reg": verified_registry(regs, "CombatSpells.reg", cards)}
    if units:
        replacements["CombatCreatures.reg"] = verified_registry(regs, "CombatCreatures.reg", units)
    for name in ("ELKIDs.reg", "Texts.reg", "ELKTexts.reg"):
        payload = regs.read(name)
        stock_sections = read_reg(payload)
        additions = []
        for key, (stock, value) in texts.items():
            changes = {}
            if name == "ELKTexts.reg":
                fallback = field_values(stock_sections[stock])["Translate"]
                changes[b"Translate"] = [value] * len(fallback) if isinstance(fallback, list) else value
            additions.append((key, stock, changes))
        new = add_sections(payload, additions)
        new_sections = read_reg(new)
        if new_sections.keys() - stock_sections.keys() != texts.keys() or any(
                new_sections[k] != v for k, v in stock_sections.items()):
            raise ValueError(f"Stock localization changed in {name}")
        replacements[name] = new
    member = "ELKTexts.txt"
    archives = {
        "Resources/regs.res": regs.replace(replacements),
        "Resources/text.res": text.replace({member: add_text(text.read(member), {
            key.decode(): value for key, (_, value) in texts.items()
        })}),
    }
    if pictures:
        archives["Resources/textures001.res"] = archive_overlay(pictures)
    return archives, bindings


def duel_presets(cards, catalog):
    for faction, label in FACTIONS.items():
        ids = [c["id"] for c in cards if c["faction"] == faction]
        pool = STOCK_FILLERS[faction] or tuple(code for code, row in sorted(catalog.spells.items())
                    if row["Color"] == faction and row["Use"] == "+" and row["Class"] == "Creature"
                    and not any(v for k, v in row.items() if k.startswith("Cost") and k != "Cost"))
        for page, start in enumerate(range(0, len(ids), 16), 1):
            selected = ids[start:start + 16]
            stock = list(pool[:4]) or selected
            while len(selected) < 16:
                selected = (selected + selected + stock)[:16]
            root = ET.Element("duel_preset", name=f"Card Creator - {label} {page}", magic=faction,
                              resource_level="3", hero_level="3", specialization="NONE")
            ET.SubElement(root, "skills")
            deck = ET.SubElement(root, "deck")
            for ident in selected:
                ET.SubElement(deck, "spell", code=ident, components="1")
            ET.SubElement(root, "bag_spells")
            ET.indent(root)
            yield f"Duel/card-creator-{faction.lower()}-{page}.prs", ET.tostring(root, encoding="utf-8", xml_declaration=True)


def build(project, catalog, project_dir, output, report=lambda message: None):
    errors = validate(project, catalog, project_dir)
    if errors:
        raise ValueError("\n".join(errors))
    report("Building additive card records, localization and portrait tiles…")
    payloads, bindings = build_archives(project, catalog, project_dir)
    payloads.update(duel_presets(project["cards"], catalog))
    hashes = {name: sha256(data).hexdigest() for name, data in payloads.items()}
    manifest = {"format": 1, "creator": VERSION, "version": project["version"], "executable": PINNED_EXE,
                "bindings": bindings, "files": hashes}
    identity = sha256(canonical(manifest)).hexdigest()[:12]
    output.mkdir(parents=True, exist_ok=True)
    package = output / f"card-creator-{project['version']}-{identity}"
    if package.exists():
        if (package / "manifest.json").read_bytes() != canonical(manifest) or any(
                checksum(package / name) != value for name, value in hashes.items()):
            raise ValueError("The matching package folder contains different files.")
        return package
    with tempfile.TemporaryDirectory(dir=output) as staging:
        stage = Path(staging) / "package"
        stage.mkdir()
        for name, data in payloads.items():
            path = stage / name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(data)
            if checksum(path) != hashes[name]:
                raise ValueError(f"Output checksum mismatch: {name}")
        (stage / "manifest.json").write_bytes(canonical(manifest))
        (stage / "README.txt").write_text("Install and launch this package through Etherlords III — Card Creator.\n"
                                        "Generated game resources are local only.\n", encoding="utf-8")
        stage.rename(package)
    return package
