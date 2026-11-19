"""Etherlords III — Card Creator desktop application."""

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import json
import os
from pathlib import Path
import queue
import subprocess
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageOps, ImageTk

from creator_core import (
    ABILITIES, EFFECTS, FACTIONS, HERE, RARITIES, VERSION, Catalog, artwork_file,
    build, canonical, compose_portrait, new_card, portrait_tiles, read_project, validate,
)
from install_game import disposable, install, load_manifest, rollback

TITLE = "Etherlords III — Card Creator"
BG, NAV, PANEL, LINE = "#171b20", "#11151a", "#20262d", "#35414a"
INK, MUTED, GOLD, TEAL = "#f1eee5", "#aebabc", "#efbc72", "#81d2be"
PALETTE = {"Red": "#dd795e", "Blue": "#7fadf1", "Green": "#9fc487", "Black": "#c29ecc"}

# The right panel gives the purpose, engine scope and an example for each input.
HELP = {
    "name": ("Required", "Name", "Appears in the game’s card list, hand and Encyclopedia. Enter one line, up to 60 characters.", "TESTING Rat"),
    "id": ("Required", "Native card ID", "The game uses this four-character key in decks and combat. Use letters A–Z and digits 0–9. Editing it breaks references in existing decks and saves.", "E3RT"),
    "faction": ("Required", "Faction", "Determines which faction can include the card in its deck and where the Encyclopedia lists it. The model can come from another faction.", "Chaots"),
    "rarity": ("Required", "Rarity", "Sets the stock rarity field. The generated Duel fixture uses zero purchase resources for custom cards.", "Common"),
    "cost": ("Required", "Ether cost", "The amount paid to cast the card. Enter 0–99. Greater Unsummoning can also apply a per-creature surcharge.", "1"),
    "description": ("Optional", "Description", "Displays one line of help text, up to 400 characters. Changing the text leaves combat behavior unchanged. Blank uses the selected donor’s explanation.", "Rest to deal 1 damage."),
    "attack": ("Required", "Attack", "Starting damage in ordinary combat. Enter a whole number from 0 to 99.", "5"),
    "health": ("Required", "Health", "Starting toughness. Enter a whole number from 1 to 99.", "5"),
    "family": ("Required", "Creature family", "Sets the family read by native interactions. Rat has been verified with Brotherhood. Other family effects may also require a stock class or specialization.", "Rat"),
    "model": ("Required · Experimental combinations", "Stock model and animations", "Select a creature model with its original mesh and animation set. The selection provides appearance and sounds. The family, stats and ability are separate.", "Mantis Patriarch · MTPT · cr309"),
    "ability": ("Required", "Native creature ability", "Assign one native summon implementation. The catalog shows the donor, targeting and activation requirements. Multiple attached abilities are unsupported.", "Zap · Kobold Shaman"),
    "effect": ("Required", "Native spell effect", "The selected donor supplies targeting, effects and animation. Greater Unsummoning is the proven additive spell donor.", "Greater Unsummoning · GRUN"),
    "flat_cost": ("Optional", "Flat Ether cost", "When selected, only the base cost is paid. Leave it clear to use the donor’s extra charge of 1 Ether per eligible creature.", "Select for TESTING CARD."),
    "artwork": ("Optional", "Stock illustration", "Select a stock small card illustration. A compatible creature portrait is also reused unless you choose a PNG tile sheet.", "Mantis Patriarch · MTPT"),
    "portrait_png": ("Optional", "Encyclopedia PNG", "Use a 384 × 512 portrait. The creator converts it to the three game textures. A 768 × 256 sheet of prepared tiles also works. The small icon uses the stock illustration.", "mantis-portrait.png"),
    "ordered": ("Unsupported", "Ordered effect combinations", "The Zap chain experiment changed stock Zap. Generalized damage, target overrides and ordered effects are unavailable for additive cards in this release.", "Damage → Unsummon is listed for reference."),
    "game": ("Required for build", "Stock game directory", "Choose an untouched English 1.03 directory containing Etherlords2.exe and Resources. The executable and source archives are verified by checksum.", "A stock backup copy is suitable."),
    "version": ("Required", "Package version", "Use three numbers separated by periods. The version and content checksum are included in the package folder name.", "0.1.0"),
    "test": ("Optional", "Disposable game copy", "Copies the verified source game without saves or replays, installs the current package there, and keeps its backup. This is the default installation path.", "Use for a new Duel."),
    "install": ("Optional", "Selected game copy", "Installs into a separate folder you choose, after confirmation, a closed-game check and verified backups. Select a dedicated copy rather than your campaign installation.", "E:/Games/Etherlords-Test"),
    "rollback": ("Optional", "Rollback", "Restores stock archives and removes generated assets after verifying checksums. Close the game first. Edited or unrelated files are preserved.", "Roll back the disposable copy after a test."),
    "library": ("Project", "Card library", "Search by name or four-character ID. Filter by faction or card type, or double-click a row to edit it.", "Search “Rat”."),
    "build": ("Build only", "Build mod", "Verifies the project and creates a local versioned package. The source game stays untouched. Multiple IDs are registered together when the test game launches.", "Build before creating a disposable copy."),
    "launch": ("Experimental", "Launch a test Duel", "Starts the selected copy through the pinned native extension and records a local diagnostic log. Use the Card Creator Duel preset for your faction.", "Card Creator - Chaots 1"),
}


class CardCreator:
    def __init__(self, root, workspace, start_project=None, start_game=None):
        self.root, self.workspace = root, workspace
        workspace.mkdir(parents=True, exist_ok=True)
        self.settings_file = workspace / "settings.json"
        try:
            settings = json.loads(self.settings_file.read_text(encoding="utf-8"))
            saved_game = settings.get("game", "")
        except (OSError, ValueError, AttributeError):
            saved_game = ""
        self.game = Path(start_game or saved_game).resolve() if start_game or saved_game else None
        self.project_path = start_project
        self.project = read_project(start_project) if start_project else read_project(HERE / "example-project.json")
        self.selected = 0 if self.project["cards"] else None
        self.catalog = self.package = self.installed = self.log_path = None
        self.fields = {}
        self.view = "Card Library"
        self.busy = False
        self.running = None
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.events = queue.Queue()
        self.validation = []
        self.query, self.type_filter, self.faction_filter = (tk.StringVar(value=x) for x in ("", "All types", "All factions"))
        root.title(TITLE)
        root.geometry("1320x820")
        root.minsize(1080, 710)
        root.configure(bg=BG)
        self.theme()
        self.shell()
        self.go("Card Library")
        self.root.after(130, self.poll)
        if self.game:
            self.load_game(self.game)

    def theme(self):
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=BG, foreground=INK, fieldbackground=PANEL, font=("Segoe UI", 10))
        style.configure("TEntry", padding=7, insertcolor=INK, bordercolor=LINE, lightcolor=LINE, darkcolor=LINE)
        style.configure("TCombobox", padding=7, arrowsize=15, bordercolor=LINE, lightcolor=LINE, darkcolor=LINE,
                        insertcolor=INK)
        style.map("TCombobox", fieldbackground=[("readonly", PANEL)], foreground=[("readonly", INK)],
                  selectbackground=[("readonly", PANEL)], selectforeground=[("readonly", INK)])
        style.configure("TButton", background=PANEL, bordercolor=LINE, lightcolor=PANEL, darkcolor=PANEL, padding=(12, 8))
        style.map("TButton", background=[("active", LINE), ("disabled", NAV)], foreground=[("disabled", MUTED)])
        style.configure("Accent.TButton", background=GOLD, foreground=NAV, bordercolor=GOLD,
                        lightcolor=GOLD, darkcolor=GOLD)
        style.map("Accent.TButton", background=[("active", "#ffcf89"), ("disabled", LINE)])
        style.configure("Treeview", background=PANEL, fieldbackground=PANEL, rowheight=42, bordercolor=LINE)
        style.map("Treeview", background=[("selected", "#38565a")])
        style.configure("Treeview.Heading", background=NAV, foreground=MUTED, padding=9)
        self.root.option_add("*TCombobox*Listbox.background", PANEL)
        self.root.option_add("*TCombobox*Listbox.foreground", INK)
        self.root.option_add("*TCombobox*Listbox.selectBackground", "#38565a")

    def label(self, parent, text, size=10, *, color=INK, bold=False, bg=BG, **options):
        return tk.Label(parent, text=text, font=("Segoe UI", size, "bold" if bold else "normal"),
                        fg=color, bg=bg, anchor="w", **options)

    def help(self, key, detail=""):
        status, title, body, example = HELP[key]
        self.help_status.configure(text=status)
        self.help_title.configure(text=title)
        self.help_body.configure(text=body + ("\n\n" + detail if detail else ""))
        self.help_example.configure(text="Example\n" + example)

    def context(self, widget, key, detail=lambda: ""):
        for signal in ("<FocusIn>", "<Button-1>"):
            widget.bind(signal, lambda _event: self.help(key, detail()), add="+")

    def button(self, parent, text, command, *, primary=False, key=None):
        control = ttk.Button(parent, text=text, command=command, style="Accent.TButton" if primary else "TButton")
        if key:
            self.context(control, key)
        return control

    def shell(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)
        self.nav = tk.Frame(self.root, bg=NAV, width=208)
        self.nav.grid(row=0, column=0, sticky="nsew")
        self.nav.grid_propagate(False)
        self.label(self.nav, "ETHERLORDS III", 17, color=GOLD, bold=True, bg=NAV).pack(anchor="w", padx=21, pady=(24, 0))
        self.label(self.nav, "Card Creator", 12, bg=NAV).pack(anchor="w", padx=22, pady=(3, 24))
        self.nav_buttons = {}
        for name in ("Card Library", "Creature Editor", "Spell Editor", "Artwork and Models",
                     "Build & Install", "Testing & Diagnostics", "Settings"):
            control = tk.Button(self.nav, text=name, command=lambda item=name: self.navigate(item),
                                bg=NAV, fg=MUTED, activebackground=PANEL, activeforeground=INK, anchor="w",
                                relief="flat", bd=0, padx=21, pady=10, font=("Segoe UI", 10), cursor="hand2")
            control.pack(fill="x", padx=7, pady=2)
            self.nav_buttons[name] = control
        tk.Frame(self.nav, bg=LINE, height=1).pack(fill="x", padx=20, pady=(22, 8))
        self.label(self.nav, f"Creator {VERSION}  ·  Game 1.03", 9, color=MUTED, bg=NAV).pack(anchor="w", padx=20)
        self.center = tk.Frame(self.root, bg=BG)
        self.center.grid(row=0, column=1, sticky="nsew", padx=23, pady=20)
        self.right = tk.Frame(self.root, bg=PANEL, width=286)
        self.right.grid(row=0, column=2, sticky="nsew")
        self.right.grid_propagate(False)
        self.label(self.right, "CONTEXTUAL HELP", 9, color=TEAL, bold=True, bg=PANEL).pack(fill="x", padx=19, pady=(26, 16))
        self.help_status = self.label(self.right, "", 9, color=GOLD, bold=True, bg=PANEL)
        self.help_status.pack(fill="x", padx=19)
        self.help_title = self.label(self.right, "", 16, bold=True, bg=PANEL, wraplength=240, justify="left")
        self.help_title.pack(fill="x", padx=19, pady=(4, 9))
        self.help_body = self.label(self.right, "", 10, bg=PANEL, wraplength=240, justify="left")
        self.help_body.pack(fill="x", padx=19)
        self.help_example = self.label(self.right, "", 9, color=MUTED, bg=PANEL, wraplength=240, justify="left")
        self.help_example.pack(fill="x", padx=19, pady=(13, 14))
        tk.Frame(self.right, bg=LINE, height=1).pack(fill="x", padx=19, pady=9)
        self.label(self.right, "CARD PREVIEW", 9, color=TEAL, bold=True, bg=PANEL).pack(anchor="w", padx=19, pady=(7, 8))
        self.canvas = tk.Canvas(self.right, width=247, height=280, bg=PANEL, highlightthickness=0)
        self.canvas.pack(anchor="n")
        self.label(self.right, "Editor preview", 9, color=MUTED, bg=PANEL).pack(anchor="w", padx=24)
        self.status = tk.StringVar(value="Open Settings to select a stock game copy.")
        bar = self.label(self.root, "", 9, color=MUTED, bg=NAV)
        bar.configure(textvariable=self.status, padx=16, pady=8)
        bar.grid(row=1, column=0, columnspan=3, sticky="ew")

    def title(self, heading, description):
        self.label(self.center, heading, 28, bold=True).pack(anchor="w")
        self.label(self.center, description, 10, color=MUTED, wraplength=620, justify="left").pack(anchor="w", pady=(4, 18))

    def go(self, name):
        self.view = name
        self.fields.clear()
        for child in self.center.winfo_children():
            child.destroy()
        for label, control in self.nav_buttons.items():
            control.configure(bg=PANEL if label == name else NAV, fg=GOLD if label == name else MUTED)
        if name == "Card Library":
            self.library()
        elif name in ("Creature Editor", "Spell Editor", "Artwork and Models"):
            self.editor(name)
        elif name == "Build & Install":
            self.build_page()
        elif name == "Testing & Diagnostics":
            self.testing_page()
        else:
            self.settings_page()
        self.preview()

    def navigate(self, name):
        self.capture()
        kind = {"Creature Editor": "creature", "Spell Editor": "spell"}.get(name)
        if kind and (self.card is None or self.card["kind"] != kind):
            self.selected = next((i for i, card in enumerate(self.project["cards"]) if card["kind"] == kind), None)
        self.go(name)

    @property
    def card(self):
        cards = self.project["cards"]
        return cards[self.selected] if self.selected is not None and self.selected < len(cards) else None

    def fresh_id(self):
        used = {c["id"] for c in self.project["cards"]}
        digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
        for number in range(36 ** 3):
            candidate = "E" + digits[number // 1296] + digits[number // 36 % 36] + digits[number % 36]
            if candidate not in used and (not self.catalog or not self.catalog.collides(candidate)):
                return candidate
        raise ValueError("The automatic ID range is full. Enter a four-character ID manually.")

    def create(self, kind, clone=False):
        self.capture()
        card = dict(self.card, id=self.fresh_id(), name=(self.card["name"][:54] + " copy")) if clone and self.card else new_card(
            kind, self.fresh_id()
        )
        self.project["cards"].append(card)
        self.selected = len(self.project["cards"]) - 1
        self.go("Creature Editor" if kind == "creature" else "Spell Editor")

    def delete(self):
        if self.card and messagebox.askyesno("Delete custom card", f"Delete {self.card['name']} from this project?"):
            self.project["cards"].pop(self.selected)
            self.selected = None
            self.go("Card Library")

    def open_project(self):
        path = filedialog.askopenfilename(filetypes=[("Card Creator project", "*.json")])
        if path:
            try:
                self.project = read_project(Path(path))
                self.project_path, self.selected, self.package = Path(path), None, None
                self.validation = []
                self.go("Card Library")
            except (ValueError, OSError) as error:
                self.error(error)

    def blank_project(self):
        if messagebox.askyesno("Start a new project?", "Replace the current view with a blank project? Save any edits you want to keep first."):
            self.project = {"format": 1, "name": "Untitled project", "version": VERSION, "cards": []}
            self.project_path = self.selected = self.package = None
            self.go("Card Library")

    def save(self):
        self.capture()
        path = self.project_path or filedialog.asksaveasfilename(defaultextension=".json",
                                                                filetypes=[("Card Creator project", "*.json")])
        if path:
            try:
                self.project_path = Path(path)
                self.project_path.write_bytes(canonical(self.project))
                self.status.set(f"Saved {self.project_path}")
            except OSError as error:
                self.error(error)

    def library(self):
        self.title("Card Library", f"{self.project.get('name', 'Untitled project')}  /  {len(self.project['cards'])} custom cards")
        actions = tk.Frame(self.center, bg=BG)
        actions.pack(fill="x", pady=(0, 13))
        for label, command, primary in (
            ("New Creature", lambda: self.create("creature"), True), ("New Spell", lambda: self.create("spell"), False),
            ("Open", self.open_project, False), ("Save", self.save, False), ("New Project", self.blank_project, False),
        ):
            self.button(actions, label, command, primary=primary).pack(side="left", padx=(0, 7))
        filters = tk.Frame(self.center, bg=BG)
        filters.pack(fill="x", pady=(0, 10))
        search = ttk.Entry(filters, textvariable=self.query)
        search.pack(side="left", fill="x", expand=True, padx=(0, 6))
        search.bind("<KeyRelease>", lambda _event: self.refresh_library())
        self.context(search, "library")
        for variable, choices in ((self.type_filter, ("All types", "Creature", "Spell")),
                                  (self.faction_filter, ("All factions", *FACTIONS.values()))):
            combo = ttk.Combobox(filters, textvariable=variable, values=choices, state="readonly", width=12)
            combo.pack(side="left", padx=(0, 6))
            combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_library())
            self.context(combo, "library")
        list_frame = tk.Frame(self.center, bg=BG)
        list_frame.pack(fill="both", expand=True)
        self.tree = ttk.Treeview(list_frame, columns=("name", "id", "type", "faction", "status"), show="headings",
                                selectmode="browse")
        for key, heading, width in (("name", "NAME", 170), ("id", "ID", 64), ("type", "TYPE", 77),
                                    ("faction", "FACTION", 88), ("status", "VALIDATION", 110)):
            self.tree.heading(key, text=heading, anchor="w")
            self.tree.column(key, width=width, minwidth=48, stretch=key in ("name", "status"))
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        scroll.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self.select)
        self.tree.bind("<Double-1>", lambda _event: self.edit_card())
        bottom = tk.Frame(self.center, bg=BG)
        bottom.pack(fill="x", pady=(13, 0))
        for label, command in (("Edit", self.edit_card), ("Duplicate", lambda: self.create(self.card["kind"], True) if self.card else None),
                               ("Delete", self.delete), ("Validate project", self.validate_action)):
            self.button(bottom, label, command).pack(side="left", padx=(0, 7))
        self.help("library")
        self.refresh_library()

    def refresh_library(self):
        query = self.query.get().casefold()
        selected = self.selected
        self.tree.delete(*self.tree.get_children())
        errors = validate(self.project, self.catalog, self.project_dir) if self.catalog else []
        for index, card in enumerate(self.project["cards"]):
            name, ident = str(card.get("name", "")), str(card.get("id", ""))
            kind, faction = card.get("kind", "").capitalize(), FACTIONS.get(card.get("faction"), "Unknown")
            if query not in f"{name} {ident}".casefold() or self.type_filter.get() not in ("All types", kind) or (
                    self.faction_filter.get() not in ("All factions", faction)):
                continue
            status = "Review" if any(e.startswith(f"Card {index + 1} (") for e in errors) else (
                "Ready to build" if self.catalog else "Source needed")
            self.tree.insert("", "end", iid=str(index), values=(name, ident, kind, faction, status))
        if selected is not None and self.tree.exists(str(selected)):
            self.tree.selection_set(str(selected))

    def select(self, _event):
        rows = self.tree.selection()
        if rows:
            self.selected = int(rows[0])
            self.preview()

    def edit_card(self):
        if self.card:
            self.go("Creature Editor" if self.card["kind"] == "creature" else "Spell Editor")

    @property
    def project_dir(self):
        return self.project_path.parent if self.project_path else self.workspace

    def editor(self, page):
        if not self.card:
            self.title(page, "Select a card in the library or create one.")
            if page != "Artwork and Models":
                kind = "creature" if page == "Creature Editor" else "spell"
                self.button(self.center, f"New {kind.title()}", lambda: self.create(kind), primary=True).pack(anchor="w")
            return
        card = self.card
        self.title(page, f"{card['name']}  /  {card['id']}")
        form = tk.Frame(self.center, bg=BG)
        form.pack(fill="both")
        form.grid_columnconfigure((0, 1), weight=1, uniform="field")
        models = self.catalog.models if self.catalog else {"STRT": "Stink Rat · STRT", "MTPT": "Mantis Patriarch · MTPT"}
        images = {"": "Use default artwork", **(
            {key: f"{self.catalog.names.get(key, key)} · {key}" for key in self.catalog.spells} if self.catalog else
            {"MTPT": "Mantis Patriarch · MTPT", "GRUN": "Greater Unsummoning · GRUN"}
        )}
        if page == "Artwork and Models":
            self.field(form, 0, 0, "Stock illustration", "artwork", images, search=True)
            if card["kind"] == "creature":
                self.field(form, 0, 1, "Stock model", "model", models, search=True)
                self.field(form, 1, 0, "Portrait PNG · optional", "portrait_png", width=2)
                self.button(self.center, "Browse PNG…", self.choose_artwork).pack(anchor="w", pady=7)
                self.label(self.center, "384 × 512 PNG · converted to three creature Encyclopedia tiles",
                           color=MUTED, wraplength=600).pack(anchor="w", pady=(3, 12))
            self.help("artwork")
        else:
            self.field(form, 0, 0, "Card name *", "name")
            self.field(form, 0, 1, "Native ID *", "id")
            self.field(form, 1, 0, "Faction *", "faction", FACTIONS)
            self.field(form, 1, 1, "Ether cost *", "cost")
            self.field(form, 2, 0, "Rarity *", "rarity", RARITIES)
            self.field(form, 2, 1, "Description · optional", "description")
            if card["kind"] == "creature":
                self.field(form, 3, 0, "Attack *", "attack")
                self.field(form, 3, 1, "Health *", "health")
                self.field(form, 4, 0, "Creature family *", "family", tuple(self.catalog.families) if self.catalog else ("Rat",))
                self.field(form, 4, 1, "Stock model *", "model", models, search=True)
                self.field(form, 5, 0, "Native ability *", "ability", {k: v.name for k, v in ABILITIES.items()}, width=2,
                           search=True, descriptions={v.name: v.description for v in ABILITIES.values()})
            else:
                self.field(form, 3, 0, "Native effect *", "effect", {k: v.name for k, v in EFFECTS.items()}, width=2,
                           search=True, descriptions={v.name: v.description for v in EFFECTS.values()})
                value = tk.BooleanVar(value=card.get("flat_cost", False))
                self.fields["flat_cost"] = (value, {})
                control = ttk.Checkbutton(form, text="Flat Ether cost", variable=value, command=self.changed)
                control.grid(row=4, column=0, columnspan=2, sticky="w", pady=8)
                self.context(control, "flat_cost")
                unsupported = self.label(form, "Ordered effects and custom targeting · unavailable", color=MUTED)
                unsupported.grid(row=5, column=0, columnspan=2, sticky="w", pady=8)
                self.context(unsupported, "ordered")
            self.help("name")
        actions = tk.Frame(self.center, bg=BG)
        actions.pack(fill="x", pady=15)
        self.button(actions, "Save Project", self.save, primary=True).pack(side="left", padx=(0, 8))
        self.button(actions, "Back to Library", lambda: self.navigate("Card Library")).pack(side="left")

    def field(self, form, row, column, label, key, choices=(), *, width=1, search=False, descriptions=None):
        cell = tk.Frame(form, bg=BG)
        cell.grid(row=row, column=column, columnspan=width, sticky="ew", padx=(0, 11), pady=(0, 10))
        caption = self.label(cell, label, 9, bold=True)
        caption.pack(anchor="w", pady=(0, 4))
        mapping = choices if isinstance(choices, dict) else {option: option for option in choices}
        current = self.card.get(key, "")
        var = tk.StringVar(value=mapping.get(current, current))
        self.fields[key] = (var, {label: ident for ident, label in mapping.items()})
        if mapping:
            labels = tuple(sorted(mapping.values(), key=str.casefold))
            control = ttk.Combobox(cell, textvariable=var, values=labels, state="normal" if search else "readonly")
            if search:
                def filter_values(event):
                    if event.keysym not in ("Up", "Down", "Tab", "Return", "Escape"):
                        tokens = var.get().casefold().split()
                        matches = tuple(x for x in labels if all(term in x.casefold() for term in tokens))
                        control.configure(values=labels if var.get() in labels else matches)
                control.bind("<KeyRelease>", filter_values)
                control.configure(postcommand=lambda: control.configure(values=labels) if var.get() in labels else None)
            control.bind("<<ComboboxSelected>>", lambda _event: (self.changed(), self.help(
                key, (descriptions or {}).get(var.get(), ""))))
        elif key in ("cost", "attack", "health"):
            control = ttk.Spinbox(cell, textvariable=var, from_=1 if key == "health" else 0, to=99,
                                  command=self.changed)
        else:
            control = ttk.Entry(cell, textvariable=var)
        control.pack(fill="x")
        control.bind("<FocusOut>", lambda _event: self.changed(), add="+")
        self.context(control, key, lambda: (descriptions or {}).get(var.get(), ""))
        self.context(caption, key)

    def changed(self):
        self.capture()
        self.preview()

    def capture(self):
        if not self.card:
            return
        for key, (var, lookup) in self.fields.items():
            raw = var.get()
            value = lookup.get(raw, raw)
            if key in ("cost", "attack", "health"):
                try:
                    value = int(value)
                except ValueError:
                    pass
            self.card[key] = value

    def choose_artwork(self):
        path = filedialog.askopenfilename(filetypes=[("PNG images", "*.png")])
        if path:
            self.fields["portrait_png"][0].set(path)
            self.changed()
            self.help("portrait_png")

    def preview(self):
        box, card = self.canvas, self.card
        box.delete("all")
        if not card:
            box.create_text(123, 130, text="Select a card", fill=MUTED, font=("Segoe UI", 11))
            return
        accent = PALETTE.get(card.get("faction"), GOLD)
        box.create_rectangle(6, 5, 240, 274, fill=NAV, outline=accent, width=2)
        box.create_text(17, 18, text=str(card.get("name", "")), anchor="nw", width=168,
                        font=("Segoe UI", 13, "bold"), fill=INK)
        box.create_oval(202, 13, 231, 42, fill=accent, outline="")
        box.create_text(217, 27, text=str(card.get("cost", "")), font=("Segoe UI", 10, "bold"), fill=NAV)
        illustrated = None
        try:
            if card.get("portrait_png"):
                with Image.open(artwork_file(card, self.project_dir)) as source:
                    illustrated = compose_portrait(portrait_tiles(source.convert("RGBA")))
            elif self.catalog:
                code = card.get("artwork") or card.get("model") or "GRUN"
                illustrated = self.catalog.preview(code)
        except (OSError, ValueError):
            pass
        if illustrated is not None:
            self.preview_photo = ImageTk.PhotoImage(ImageOps.fit(illustrated, (208, 120), centering=(0.5, 0.68)))
            box.create_image(123, 106, image=self.preview_photo)
        else:
            box.create_rectangle(18, 48, 228, 166, fill=PANEL, outline=LINE)
            box.create_polygon(123, 62, 159, 106, 123, 150, 87, 106, outline=accent, fill=NAV, width=2)
            box.create_text(123, 107, text=card.get("id", ""), fill=accent, font=("Segoe UI", 13, "bold"))
        label = f"{FACTIONS.get(card.get('faction'), '')}  /  {card.get('kind', '').title()}"
        box.create_text(17, 175, text=label, font=("Segoe UI", 9, "bold"), fill=accent, anchor="nw")
        box.create_text(17, 198, text=str(card.get("description", ""))[:140], anchor="nw", width=206,
                        font=("Segoe UI", 9), fill=INK)
        if card.get("kind") == "creature":
            box.create_text(224, 253, text=f"{card.get('attack', '')} / {card.get('health', '')}",
                            font=("Segoe UI", 12, "bold"), fill=accent, anchor="e")

    def settings_page(self):
        self.title("Settings", "Select the pinned stock game used to read the catalog and build local packages.")
        self.label(self.center, "Stock game directory *", bold=True).pack(anchor="w")
        field = ttk.Entry(self.center)
        field.insert(0, str(self.game or ""))
        field.configure(state="readonly")
        field.pack(fill="x", pady=(6, 9))
        self.context(field, "game")
        self.button(self.center, "Choose Game Folder…", self.choose_game, primary=True, key="game").pack(anchor="w")
        self.label(self.center, "Local workspace", bold=True).pack(anchor="w", pady=(21, 5))
        self.label(self.center, str(self.workspace), color=MUTED, wraplength=620, justify="left").pack(anchor="w")
        self.help("game")

    def choose_game(self):
        path = filedialog.askdirectory(title="Choose a stock Etherlords II game folder")
        if path:
            self.load_game(Path(path))

    def load_game(self, game):
        def ready(catalog):
            self.catalog, self.game = catalog, catalog.game
            self.settings_file.write_bytes(canonical({"game": str(self.game)}))
            self.status.set(f"Verified stock game · {len(catalog.models)} model rows · {len(catalog.families)} families")
            self.go(self.view)
        self.task("Verifying the stock game and catalog…", lambda _report: Catalog(game), ready)

    def validate_action(self):
        self.capture()
        if not self.catalog:
            self.error("Select a verified stock game in Settings first.")
            return
        self.validation = validate(self.project, self.catalog, self.project_dir)
        if self.validation:
            self.error("\n".join(self.validation))
        else:
            self.status.set("All cards passed validation.")

    def build_page(self):
        self.title("Build & Install", "Generate a local package, then choose where to test it.")
        self.label(self.center, "Package version *", bold=True).pack(anchor="w")
        version = tk.StringVar(value=self.project.get("version", "0.1.0"))
        field = ttk.Entry(self.center, textvariable=version, width=17)
        field.pack(anchor="w", pady=(5, 13))
        self.context(field, "version")
        version.trace_add("write", lambda *_: self.project.update(version=version.get()))
        actions = tk.Frame(self.center, bg=BG)
        actions.pack(fill="x")
        self.button(actions, "Build Mod", self.build_action, primary=True, key="build").pack(side="left", padx=(0, 8))
        self.button(actions, "Open Package…", self.open_package).pack(side="left")
        self.label(self.center, str(self.package or "No package selected"), color=MUTED, justify="left", wraplength=620).pack(
            anchor="w", pady=(12, 21))
        self.label(self.center, "Installation target", 15, bold=True).pack(anchor="w", pady=(0, 8))
        for label, explanation, callback, key in (
            ("Create Disposable Copy", "Recommended for testing. The stock source stays untouched.", self.disposable_action, "test"),
            ("Install into a Game Copy…", "Choose a separate, compatible copy. Verified backups are created first.", self.install_action, "install"),
            ("Roll Back a Game Copy…", "Restore backed-up resources and remove the generated files.", self.rollback_action, "rollback"),
        ):
            self.button(self.center, label, callback, key=key).pack(anchor="w", pady=(0, 4))
            self.label(self.center, explanation, 9, color=MUTED, wraplength=610).pack(anchor="w", pady=(0, 13))
        self.help("build")

    def build_action(self):
        self.capture()
        if not self.catalog:
            self.error("Choose a verified stock game folder in Settings first.")
            return
        project = json.loads(canonical(self.project))
        catalog, project_dir = self.catalog, self.project_dir
        def ready(path):
            self.package = path
            self.status.set(f"Package verified · {path.name}")
            self.go("Build & Install")
        self.task("Validating project…", lambda report: build(
            project, catalog, project_dir, self.workspace / "builds", report
        ), ready)

    def open_package(self):
        folder = filedialog.askdirectory(title="Open a built package folder")
        if folder:
            try:
                load_manifest(Path(folder))
                self.package = Path(folder)
                self.go("Build & Install")
            except (OSError, ValueError, KeyError) as error:
                self.error(error)

    def installed_ready(self, game):
        self.installed = game
        self.status.set(f"Installed into {game}")
        self.go("Testing & Diagnostics")

    def disposable_action(self):
        if not self.package or not self.game:
            self.error("Select a stock game and build a package first.")
            return
        game, package = self.game, self.package
        self.task("Preparing a disposable copy…", lambda report: disposable(
            game, package, self.workspace / "games", report
        ), self.installed_ready)

    def install_action(self):
        if not self.package:
            self.error("Build or open a package first.")
            return
        folder = filedialog.askdirectory(title="Choose a separate game copy")
        if folder:
            target = Path(folder).resolve()
            if target == self.game:
                self.error("Choose a different copy. The stock source is reserved for builds.")
            elif messagebox.askyesno("Install into this copy?", f"Install the current package into:\n{target}\n\n"
                                    "The creator verifies and backs up stock files before replacing them."):
                package = self.package
                self.task("Checking installation target…", lambda report: install(target, package, report),
                          self.installed_ready)

    def rollback_action(self):
        folder = filedialog.askdirectory(title="Choose an installed game copy", initialdir=self.installed or self.workspace)
        if folder and messagebox.askyesno("Roll back this copy?", f"Restore the original files in\n{folder}?"):
            def ready(_result):
                if self.installed == Path(folder).resolve():
                    self.installed = None
                self.status.set("Rollback completed. Original archive checksums verified.")
            self.task("Verifying backup and rolling back…", lambda _report: rollback(Path(folder)), ready)

    def testing_page(self):
        self.title("Testing & Diagnostics", "Launch a disposable Duel with its native registrations and keep a local log.")
        row = tk.Frame(self.center, bg=BG)
        row.pack(fill="x", pady=(0, 9))
        self.button(row, "Launch Test Game", self.launch, primary=True, key="launch").pack(side="left", padx=(0, 8))
        self.button(row, "Select Installed Copy…", self.select_installed).pack(side="left", padx=(0, 8))
        self.button(row, "Open Log Folder", self.open_log_folder).pack(side="left")
        self.label(self.center, str(self.installed or "No installed copy selected"), color=MUTED, wraplength=620).pack(
            anchor="w", pady=(2, 10))
        self.diagnostics = tk.Text(self.center, bg=NAV, fg=INK, height=15, wrap="word", font=("Consolas", 10),
                                   relief="flat", padx=12, pady=10)
        self.diagnostics.pack(fill="both", expand=True)
        self.diagnostics.configure(state="disabled")
        self.show_log()
        self.help("launch")

    def select_installed(self):
        path = filedialog.askdirectory(title="Choose a Card Creator installation")
        if path:
            self.installed = Path(path).resolve()
            self.go("Testing & Diagnostics")

    def launch(self):
        if self.running is not None and self.running.poll() is None:
            self.error("The current test game is still running.")
            return
        if not self.installed:
            self.error("Create or select an installed game copy first.")
            return
        try:
            target = self.installed.parent / ".card-creator-logs"
            target.mkdir(exist_ok=True)
            self.log_path = target / (datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".jsonl")
            console = self.log_path.with_suffix(".console.txt")
            executable = Path(sys.executable)
            if executable.name.casefold() == "pythonw.exe":
                executable = executable.with_name("python.exe")
            with console.open("wb") as stream:
                self.running = subprocess.Popen([str(executable), str(HERE / "native_project.py"), str(self.installed),
                                                 str(self.log_path)], stdout=stream, stderr=stream,
                                                creationflags=0x08000000)
            self.status.set(f"Launching native test · {self.log_path.name}")
        except OSError as error:
            self.error(error)

    def open_log_folder(self):
        if self.log_path:
            os.startfile(self.log_path.parent)
        else:
            self.error("Launch a test game to create its log.")

    def show_log(self):
        if self.view == "Testing & Diagnostics" and self.log_path:
            file = self.log_path if self.log_path.exists() else self.log_path.with_suffix(".console.txt")
            if file.exists():
                output = self.format_log(file.read_text(encoding="utf-8", errors="replace"))
                if self.diagnostics.get("1.0", "end-1c") != output:
                    self.diagnostics.configure(state="normal")
                    self.diagnostics.delete("1.0", "end")
                    self.diagnostics.insert("1.0", output)
                    self.diagnostics.see("end")
                    self.diagnostics.configure(state="disabled")

    def format_log(self, text):
        lines = []
        for raw in text.splitlines():
            try:
                event = json.loads(raw)
            except ValueError:
                lines.append(raw)
                continue
            kind = event.get("event")
            if kind == "launch":
                line = "Verified executable and installed package. Starting the game."
            elif kind == "project-producers":
                line = f"Registered {len(event['created'])} custom IDs: {', '.join(event['created'])}."
            elif kind == "shaman-summon":
                line = f"{event['card']} summoned as {event['attack']}/{event['health']}."
            elif kind == "shaman-activate":
                line = f"{event['card']} entered the Shaman ability routine."
            elif kind == "unsummoning-debit":
                line = f"{event['card']} entered Unsummoning with {event['creatures']} eligible creatures."
            elif kind == "exit":
                line = f"Game exited with code {event['code']}."
            elif kind == "exception" and (not event.get("first_chance") or event["code"] == "0xc0000005"):
                line = f"Game exception {event['code']} at {event['address']}. See the full log for details."
            else:
                continue
            lines.append(line)
        return "\n".join(lines[-35:])

    def task(self, message, job, ready):
        if self.busy:
            self.error("Wait for the current operation to finish.")
            return
        self.busy = True
        self.status.set(message)
        future = self.executor.submit(job, lambda progress: self.events.put(("progress", progress)))
        future.add_done_callback(lambda result: self.events.put(("result", (result, ready))))

    def error(self, error):
        self.status.set(str(error).splitlines()[0])
        messagebox.showerror(TITLE, str(error))

    def poll(self):
        while not self.events.empty():
            event, value = self.events.get_nowait()
            if event == "progress":
                self.status.set(value)
            else:
                self.busy = False
                future, ready = value
                try:
                    ready(future.result())
                except Exception as error:
                    self.error(error)
        if self.running is not None and self.running.poll() is not None:
            self.status.set(f"Test launcher ended · exit {self.running.returncode}")
            self.running = None
        self.show_log()
        self.root.after(250, self.poll)


def main():
    parser = argparse.ArgumentParser(description=TITLE)
    parser.add_argument("--project", type=Path)
    parser.add_argument("--game", type=Path)
    parser.add_argument("--workspace", type=Path, default=Path(os.environ.get("LOCALAPPDATA", Path.home())) /
                        "Etherlords III Card Creator")
    args = parser.parse_args()
    root = tk.Tk()
    CardCreator(root, args.workspace, args.project, args.game)
    root.mainloop()


if __name__ == "__main__":
    main()
