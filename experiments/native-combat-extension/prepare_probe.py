"""Make an isolated test game and stage only the selected combat profile."""

import argparse
from pathlib import Path
import shutil
import tempfile

from combat_probe import HERE, PINNED_EXE, PROBE_HASHES, PROFILE_ARCHIVES, SOURCE_HASHES, check_hashes
from prepare_duel_matrix import write_presets


def prepare(baseline, profile, name, metadata):
    local = (HERE / "local").resolve()
    target = local / name
    if Path(name).name != name or name in ("", ".", "..") or target.exists():
        raise ValueError("Choose a new directory name directly below local/")
    if local.is_relative_to(baseline):
        raise ValueError("The test output must be outside the supplied baseline game")
    check_hashes(baseline, {"Etherlords2.exe": PINNED_EXE})
    check_hashes(baseline / "Resources", SOURCE_HASHES)
    additive = profile in ("alias", "alias-flat")
    if additive:
        check_hashes(metadata, PROBE_HASHES)
    local.mkdir(exist_ok=True)
    ignore = shutil.ignore_patterns(".git", ".campaign-ui-local", ".duel-matrix-copy", "local",
                                    ".spell-probe-backup", ".mechanics-backup",
                                    ".etherlords-iii-ui-backup", "Save", "Replays", "shot*.bmp")
    with tempfile.TemporaryDirectory(prefix="prepare-", dir=local) as scratch:
        game = Path(scratch) / "game"
        shutil.copytree(baseline, game, ignore=ignore)
        for directory in ("Save", "Replays"):
            (game / directory).mkdir(exist_ok=True)
        if additive:
            for archive in PROBE_HASHES:
                shutil.copyfile(metadata / archive, game / "Resources" / archive)
            write_presets(game)
        elif profile == "rat-brotherhood":
            import sys
            sys.path.insert(0, str(HERE.parent / "card-mechanics"))
            from mechanics_probe import apply_rat_stats, copy_rat_ability
            regs = game / "Resources" / "regs.res"
            regs.write_bytes(copy_rat_ability(apply_rat_stats(regs.read_bytes())))
        if not additive:
            preset_dir = HERE.parent / "card-mechanics" / "duel-presets"
            names = ("mechanics-rat-ability",) if profile == "rat-brotherhood" else (
                "mechanics-zap", "mechanics-wall-target",
            )
            for preset in names:
                filename = preset + ".prs"
                with (game / "Duel" / filename).open("xb") as handle:
                    handle.write((preset_dir / filename).read_bytes())
        check_hashes(game, {"Etherlords2.exe": PINNED_EXE})
        check_hashes(game / "Resources", PROFILE_ARCHIVES[profile])
        (game / ".native-combat-test").touch(exist_ok=False)
        game.rename(target)
    print(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("profile", choices=PROFILE_ARCHIVES)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("name", help="New disposable directory name under local/")
    parser.add_argument("--metadata", type=Path,
                        default=HERE.parent / "new-spell-proof-of-concept" / "local" / "metadata-probe")
    args = parser.parse_args()
    try:
        prepare(args.baseline.resolve(strict=True), args.profile, args.name, args.metadata)
    except (OSError, ValueError, KeyError) as error:
        parser.exit(1, f"Error: {error}\n")


if __name__ == "__main__":
    main()
