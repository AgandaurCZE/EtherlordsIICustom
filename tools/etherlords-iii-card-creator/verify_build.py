"""Optional read-only-source checks for the Card Creator builder."""

import argparse
from copy import deepcopy
from pathlib import Path
import tempfile

from PIL import Image

from creator_core import (
    Archive, Catalog, HERE, build, checksum, compose_portrait, read_project,
    portrait_names, portrait_tiles, read_reg, validate,
)


def verify(source):
    catalog = Catalog(source)
    example = read_project(HERE / "example-project.json")
    extended = read_project(HERE / "five-card-test-project.json")
    duplicate = deepcopy(extended)
    duplicate["cards"][1]["id"] = duplicate["cards"][0]["id"]
    duplicate["cards"][2]["id"] = "STRT"
    duplicate["cards"][3]["health"] = 0
    assert len(validate(duplicate, catalog, HERE)) >= 4
    with tempfile.TemporaryDirectory() as work:
        output = Path(work)
        packages = [build(project, catalog, HERE, output) for project in (example, extended)]
        package = packages[1]
        assert build(extended, catalog, HERE, output) == package
        expected = {card["id"].encode("ascii") for card in extended["cards"]}
        archive = Archive((package / "Resources/regs.res").read_bytes())
        cards = read_reg(archive.read("CombatSpells.reg"))
        originals = read_reg(catalog.regs.read("CombatSpells.reg"))
        assert cards.keys() - originals.keys() == expected
        assert all(cards[key] == value for key, value in originals.items())
        portrait = Image.new("RGBA", (384, 512))
        for x, y, color in ((5, 5, "red"), (300, 300, "blue"), (300, 5, "green")):
            portrait.putpixel((x, y), Image.new("RGBA", (1, 1), color).getpixel((0, 0)))
        assert compose_portrait(portrait_tiles(portrait)).tobytes() == portrait.tobytes()
        portrait.save(output / "test.png")
        art_project = deepcopy(extended)
        art_project["cards"][0]["portrait_png"] = "test.png"
        art_package = build(art_project, catalog, output, output)
        art = Archive((art_package / "Resources/textures001.res").read_bytes())
        for name in portrait_names("E3RT"):
            assert art.read(name)[:4] == b"MMP\0"
        assert checksum(package / "Resources/regs.res") == checksum(art_package / "Resources/regs.res")
        print("Two-card and five-card packages verified, including deterministic rebuild and PNG conversion.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    verify(parser.parse_args().source)
