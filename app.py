import json
import math
import os
import secrets
import subprocess
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
import webbrowser
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox

from PIL import Image, ImageTk
from pypresence import ActivityType, Presence
from pypresence.types import StatusDisplayType


DEFAULT_CONFIG = {
    "client_id": "",
    "large_image_key": "chibi_cloud",
    "large_image_text": "PresenceCast by Cloud",
    "small_image_key": "chibi_cloud",
    "small_image_text": "PresenceCast by Cloud",
    "playing_image_key": "chibi_cloud_playing",
    "playing_image_text": "PresenceCast | Playing",
    "listening_image_key": "chibi_cloud_listening",
    "listening_image_text": "PresenceCast | Listening",
    "watching_image_key": "chibi_cloud_watching",
    "watching_image_text": "PresenceCast | Watching",
    "competing_image_key": "",
    "competing_image_text": "PresenceCast | Competing",
    "emoji_asset_override": True,
}
APP_NAME = "PresenceCast 2.0"
TOOL_LABEL = "Presence Studio"
APP_VERSION = "2.0.1"
GITHUB_REPOSITORY = "CloudyCodez/PresenceCast"
RELEASE_ASSET_NAME = "PresenceCast.exe"
LATEST_RELEASE_API = f"https://api.github.com/repos/{GITHUB_REPOSITORY}/releases/latest"
RELEASES_URL = f"https://github.com/{GITHUB_REPOSITORY}/releases"

PALETTE = {
    "window": "#07111A",
    "header": "#0A1622",
    "surface": "#112130",
    "panel": "#152638",
    "panel_alt": "#1B3046",
    "panel_soft": "#203B56",
    "input": "#0E1B28",
    "line": "#2F4F6B",
    "text": "#F7F2E8",
    "muted": "#A5B7C8",
    "soft": "#72879A",
    "aqua": "#66E7FF",
    "sky": "#52B8FF",
    "mint": "#57F1B4",
    "gold": "#FFD36F",
    "coral": "#FF8E6A",
    "rose": "#FF6B7E",
    "ink": "#091018",
}

ACTIVITY_ACCENTS = {
    "Playing": PALETTE["coral"],
    "Listening": PALETTE["aqua"],
    "Watching": PALETTE["gold"],
    "Competing": PALETTE["rose"],
}

ACTIVITY_VERBS = {
    "Playing": "Playing",
    "Listening": "Listening to",
    "Watching": "Watching",
    "Competing": "Competing in",
}

DISPLAY_MODE_OPTIONS = {
    "Show activity name": StatusDisplayType.NAME,
    "Show details": StatusDisplayType.DETAILS,
    "Show state": StatusDisplayType.STATE,
}

ACTIVITY_TYPE_OPTIONS = {
    "Playing": ActivityType.PLAYING,
    "Listening": ActivityType.LISTENING,
    "Watching": ActivityType.WATCHING,
    "Competing": ActivityType.COMPETING,
}

ACTIVITY_ASSET_FIELDS = {
    "Playing": ("playing_image_key", "playing_image_text"),
    "Listening": ("listening_image_key", "listening_image_text"),
    "Watching": ("watching_image_key", "watching_image_text"),
    "Competing": ("competing_image_key", "competing_image_text"),
}

EMOJI_ASSET_HINTS = {
    "Playing": ("\U0001F3AE", "\U0001F579\ufe0f", "\U0001F47E", "\u2694\ufe0f", "\U0001F3C6"),
    "Listening": ("\U0001F3A7", "\U0001F3B5", "\U0001F3B6", "\U0001F3BC", "\U0001F3A4"),
    "Watching": ("\U0001F4FA", "\U0001F3AC", "\U0001F37F", "\U0001F440", "\U0001F4F9"),
}

TIMER_MODES = ("Static", "Elapsed", "Countdown")

PRESETS = [
    {
        "label": "Deep Focus",
        "note": "Quiet maker energy",
        "name": "Deep Focus",
        "details": "Shipping a polished build",
        "state": "Heads-down sprint",
        "type": "Playing",
        "display_mode": "Show details",
        "timer_mode": "Elapsed",
    },
    {
        "label": "Night Shift",
        "note": "Late-hours creator mode",
        "name": "Night Shift",
        "details": "Refining the final pass",
        "state": "After-hours momentum",
        "type": "Playing",
        "display_mode": "Show state",
        "timer_mode": "Elapsed",
    },
    {
        "label": "Listening Lounge",
        "note": "Audio-first atmosphere",
        "name": "Listening Lounge",
        "details": "Curating the perfect loop",
        "state": "Low-distraction mode",
        "type": "Listening",
        "display_mode": "Show details",
        "timer_mode": "Elapsed",
    },
    {
        "label": "Movie Night",
        "note": "Cinematic social vibe",
        "name": "Movie Night",
        "details": "Director's cut in progress",
        "state": "Popcorn and commentary",
        "type": "Watching",
        "display_mode": "Show activity name",
        "timer_mode": "Countdown",
        "duration": "120",
    },
    {
        "label": "Ranked Push",
        "note": "Clear and actionable",
        "name": "Ranked Push",
        "details": "Climbing the ladder",
        "state": "Queueing with the squad",
        "type": "Competing",
        "display_mode": "Show details",
        "timer_mode": "Elapsed",
        "party_enabled": True,
        "party_current": "2",
        "party_max": "5",
    },
    {
        "label": "Collab Sprint",
        "note": "Share the build state",
        "name": "Collab Sprint",
        "details": "Polishing the release candidate",
        "state": "Reviewing with the team",
        "type": "Playing",
        "display_mode": "Show state",
        "timer_mode": "Elapsed",
        "party_enabled": True,
        "party_current": "3",
        "party_max": "6",
    },
]

BRAND_THEMES = [
    {
        "label": "Aurora Operator",
        "note": "Cool, focused, quietly premium",
        "payload": {
            "name": "Aurora Operator",
            "details": "Designing the calmest powerful workflow",
            "state": "Polish pass with motion and glass",
            "activity_type": "Playing",
            "display_mode": "Show details",
            "timer_mode": "Elapsed",
            "emoji_asset_override": True,
            "manual_large_text": "PresenceCast | Aurora",
            "manual_small_text": "Aurora badge",
            "primary_button_label": "Studio",
            "primary_button_url": "https://example.com/studio",
        },
    },
    {
        "label": "Signal Room",
        "note": "Community-first social energy",
        "payload": {
            "name": "Signal Room",
            "details": "Hosting a live creative session",
            "state": "Drop in and build with us",
            "activity_type": "Watching",
            "display_mode": "Show state",
            "timer_mode": "Elapsed",
            "party_enabled": True,
            "party_current": "4",
            "party_max": "12",
            "manual_large_text": "PresenceCast | Signal Room",
            "primary_button_label": "Join Hub",
            "primary_button_url": "https://discord.gg/example",
            "secondary_button_label": "Project",
            "secondary_button_url": "https://example.com/project",
        },
    },
    {
        "label": "Afterglow Arcade",
        "note": "Loud, playful, late-night",
        "payload": {
            "name": "Afterglow Arcade",
            "details": "Queueing into something chaotic",
            "state": "Neon momentum only",
            "activity_type": "Competing",
            "display_mode": "Show details",
            "timer_mode": "Countdown",
            "duration": "90",
            "party_enabled": True,
            "party_current": "2",
            "party_max": "5",
            "manual_large_text": "PresenceCast | Afterglow",
            "manual_small_text": "Arcade badge",
        },
    },
    {
        "label": "Midnight Broadcast",
        "note": "Minimal copy, maximum atmosphere",
        "payload": {
            "name": "Midnight Broadcast",
            "details": "Curating the final scene",
            "state": "Nocturne cut in progress",
            "activity_type": "Listening",
            "display_mode": "Show activity name",
            "timer_mode": "Elapsed",
            "details_url": "https://example.com/mixtape",
            "state_url": "https://example.com/notes",
            "manual_large_text": "PresenceCast | Midnight",
            "manual_small_text": "Broadcast seal",
        },
    },
]


def get_runtime_dirs() -> tuple[Path, Path]:
    exe_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    bundle_dir = Path(getattr(sys, "_MEIPASS", exe_dir))
    return exe_dir, bundle_dir


APP_DIR, BUNDLE_DIR = get_runtime_dirs()
PROFILES_PATH = APP_DIR / "profiles.json"
HISTORY_PATH = APP_DIR / "history.json"
THEME_EXPORTS_DIR = APP_DIR / "theme_bundles"
CONFIG_PATH = APP_DIR / "config.json"
BUNDLED_CONFIG_PATH = BUNDLE_DIR / "config.json"


def pick_path(filename: str) -> Path:
    app_path = APP_DIR / filename
    if app_path.exists():
        return app_path
    return BUNDLE_DIR / filename


ICON_PATH = pick_path("presencecast.ico")
LOGO_PATH = pick_path("presencecast.png")
MASCOT_PATH = pick_path("chibi_cloud.png")
ACTIVITY_PREVIEW_PATHS = {
    "Playing": pick_path("Chibi Cloud Playing.png"),
    "Listening": pick_path("Chibi Cloud Listening.png"),
    "Watching": pick_path("Chibi Cloud Watching.png"),
}


class PresenceApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("1440x940")
        self.root.minsize(1240, 860)
        self.root.configure(bg=PALETTE["window"])

        self.rpc: Presence | None = None
        self.connected_client_id: str | None = None
        self.config = self._load_config()
        self.client_id = str(self.config.get("client_id", "")).strip()
        self.large_image_key = str(self.config.get("large_image_key", DEFAULT_CONFIG["large_image_key"])).strip()
        self.large_image_text = str(self.config.get("large_image_text", DEFAULT_CONFIG["large_image_text"])).strip()
        self.small_image_key = str(self.config.get("small_image_key", DEFAULT_CONFIG["small_image_key"])).strip()
        self.small_image_text = str(self.config.get("small_image_text", DEFAULT_CONFIG["small_image_text"])).strip()
        self.activity_image_keys = {
            label: str(self.config.get(key_field, DEFAULT_CONFIG[key_field])).strip()
            for label, (key_field, _text_field) in ACTIVITY_ASSET_FIELDS.items()
        }
        self.activity_image_texts = {
            label: str(self.config.get(text_field, DEFAULT_CONFIG[text_field])).strip()
            for label, (_key_field, text_field) in ACTIVITY_ASSET_FIELDS.items()
        }

        self.profiles = self._load_profiles()
        self.history = self._load_history()
        self.segmented_groups: list[tuple[tk.StringVar, dict[str, tk.Button], dict[str, str] | None]] = []
        self.workspace_tab_buttons: dict[str, tk.Button] = {}
        self.image_cache: dict[tuple[str, int, int], ImageTk.PhotoImage] = {}

        self.logo_photo: ImageTk.PhotoImage | None = None
        self.header_logo_photo: ImageTk.PhotoImage | None = None
        self.mascot_photo: ImageTk.PhotoImage | None = None
        self.preview_asset_photo: ImageTk.PhotoImage | None = None
        self.preview_badge_photo: ImageTk.PhotoImage | None = None
        self.theme_name_var = tk.StringVar(value="Custom Studio")

        self.name_var = tk.StringVar()
        self.details_var = tk.StringVar()
        self.state_var = tk.StringVar()
        self.primary_button_label_var = tk.StringVar()
        self.primary_button_url_var = tk.StringVar()
        self.secondary_button_label_var = tk.StringVar()
        self.secondary_button_url_var = tk.StringVar()
        self.details_url_var = tk.StringVar()
        self.state_url_var = tk.StringVar()
        self.large_url_var = tk.StringVar()
        self.small_url_var = tk.StringVar()
        self.profile_name_var = tk.StringVar()
        self.profile_var = tk.StringVar()
        self.status_var = tk.StringVar(value="PresenceCast 2.0 is ready to shape a richer Discord profile.")
        self.update_status_var = tk.StringVar(value=f"Version {APP_VERSION}")
        self.active_workspace_tab = tk.StringVar(value="main")
        self.display_mode_var = tk.StringVar(value="Show activity name")
        self.activity_type_var = tk.StringVar(value="Playing")
        self.timer_mode_var = tk.StringVar(value="Elapsed")
        self.duration_var = tk.StringVar(value="45")
        self.party_enabled_var = tk.BooleanVar(value=False)
        self.party_current_var = tk.StringVar(value="1")
        self.party_max_var = tk.StringVar(value="4")
        self.party_id_var = tk.StringVar()
        self.join_secret_var = tk.StringVar()
        self.spectate_secret_var = tk.StringVar()
        self.match_secret_var = tk.StringVar()
        self.instance_var = tk.BooleanVar(value=True)
        self.show_advanced_var = tk.BooleanVar(value=False)
        self.manual_large_image_var = tk.StringVar()
        self.manual_large_text_var = tk.StringVar()
        self.manual_small_image_var = tk.StringVar()
        self.manual_small_text_var = tk.StringVar()
        self.emoji_asset_override_var = tk.BooleanVar(
            value=bool(self.config.get("emoji_asset_override", DEFAULT_CONFIG["emoji_asset_override"]))
        )

        self.animation_phase = 0.0
        self.status_after_id: str | None = None
        self.motion_phase = 0.0
        self.motion_after_id: str | None = None
        self._mousewheel_bound = False
        self.update_info: dict[str, str] | None = None
        self.update_check_in_progress = False

        self._apply_icon()
        self._build_ui()
        self._wire_live_updates()
        self._refresh_profile_menu()
        self._refresh_history_panel()
        self._refresh_preview()
        self._start_status_animation()
        self._start_surface_motion()
        self.root.after(1800, self.check_for_updates)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _apply_icon(self) -> None:
        png_loaded = False
        if LOGO_PATH.exists():
            try:
                logo = tk.PhotoImage(file=str(LOGO_PATH))
                self.root.iconphoto(True, logo)
                png_loaded = True
            except Exception:
                pass

        if ICON_PATH.exists() and not png_loaded:
            try:
                self.root.iconbitmap(default=str(ICON_PATH))
            except Exception:
                pass

    def _load_image(self, path: Path, width: int, height: int) -> ImageTk.PhotoImage | None:
        if not path.exists():
            return None
        cache_key = (str(path), width, height)
        if cache_key in self.image_cache:
            return self.image_cache[cache_key]
        try:
            image = Image.open(path).convert("RGBA")
            image.thumbnail((width, height), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))
            offset_x = max(0, (width - image.width) // 2)
            offset_y = max(0, (height - image.height) // 2)
            canvas.paste(image, (offset_x, offset_y), image)
            photo = ImageTk.PhotoImage(canvas)
            self.image_cache[cache_key] = photo
            return photo
        except Exception:
            return None

    def _build_ui(self) -> None:
        self.header = tk.Frame(self.root, bg=PALETTE["header"], height=184)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)
        self._build_header()

        self.content_shell = tk.Frame(self.root, bg=PALETTE["window"])
        self.content_shell.pack(fill="both", expand=True, padx=18, pady=(14, 10))

        self.content_canvas = tk.Canvas(
            self.content_shell,
            bg=PALETTE["window"],
            bd=0,
            highlightthickness=0,
            yscrollincrement=24,
        )
        self.content_canvas.pack(side="left", fill="both", expand=True)
        self.content_canvas.bind("<Configure>", self._on_canvas_resize)
        self.content_canvas.bind("<Enter>", self._bind_mousewheel)
        self.content_canvas.bind("<Leave>", self._unbind_mousewheel)

        self.content_scrollbar = tk.Scrollbar(
            self.content_shell,
            orient="vertical",
            command=self.content_canvas.yview,
            troughcolor=PALETTE["window"],
            bg=PALETTE["panel"],
            activebackground=PALETTE["sky"],
        )
        self.content_scrollbar.pack(side="right", fill="y")
        self.content_canvas.configure(yscrollcommand=self.content_scrollbar.set)

        self.content = tk.Frame(self.content_canvas, bg=PALETTE["window"])
        self.content_window = self.content_canvas.create_window(0, 0, window=self.content, anchor="nw")
        self.content.bind("<Configure>", self._on_content_configure)

        self._build_scroll_content()

        self.footer = tk.Frame(self.root, bg=PALETTE["header"], height=42)
        self.footer.pack(fill="x", side="bottom")
        self.footer.pack_propagate(False)
        self.footer_label = tk.Label(
            self.footer,
            text="made with \u2665 by Cloud | Discord desktop client required for live RPC",
            font=("Segoe UI", 10, "italic"),
            fg=PALETTE["muted"],
            bg=PALETTE["header"],
        )
        self.footer_label.pack(side="right", padx=18, pady=10)

    def _build_header(self) -> None:
        left = tk.Frame(self.header, bg=PALETTE["header"])
        left.pack(side="left", fill="both", expand=True, padx=22, pady=18)

        self.header_logo_photo = self._load_image(LOGO_PATH, 96, 96)
        if self.header_logo_photo is not None:
            tk.Label(left, image=self.header_logo_photo, bg=PALETTE["header"]).pack(side="left", padx=(0, 18))

        text_shell = tk.Frame(left, bg=PALETTE["header"])
        text_shell.pack(side="left", fill="both", expand=True)

        chips = tk.Frame(text_shell, bg=PALETTE["header"])
        chips.pack(anchor="w", pady=(2, 10))
        self._chip(chips, "PresenceCast 2.0", PALETTE["gold"], PALETTE["ink"]).pack(side="left")
        self._chip(chips, "Studio Workflow", PALETTE["panel_soft"], PALETTE["text"]).pack(side="left", padx=(8, 0))
        self._chip(chips, "Discord Rich Presence", PALETTE["panel_soft"], PALETTE["text"]).pack(side="left", padx=(8, 0))

        tk.Label(
            text_shell,
            text="Set a Discord presence fast.",
            font=("Bahnschrift SemiBold", 31),
            fg=PALETTE["text"],
            bg=PALETTE["header"],
        ).pack(anchor="w")

        tk.Label(
            text_shell,
            text="PresenceCast now focuses on the core flow first: write the three main lines, preview the card, and cast. Advanced options stay available, but out of the way.",
            font=("Segoe UI", 11),
            fg=PALETTE["muted"],
            bg=PALETTE["header"],
            wraplength=720,
            justify="left",
        ).pack(anchor="w", pady=(8, 0))

        right = tk.Frame(self.header, bg=PALETTE["header"])
        right.pack(side="right", padx=22, pady=18)

        hero_stack = tk.Frame(right, bg=PALETTE["header"])
        hero_stack.pack(anchor="e")

        top_cards = tk.Frame(hero_stack, bg=PALETTE["header"])
        top_cards.pack(anchor="e")
        self.header_card_primary = self._header_card(
            top_cards,
            "Client",
            "Loaded" if self.client_id.isdigit() else "Missing ID",
            self.client_id if self.client_id else "config.json",
            PALETTE["mint"] if self.client_id.isdigit() else PALETTE["gold"],
        )
        self.header_card_primary.pack(side="left")
        self.header_card_secondary = self._header_card(
            top_cards,
            "Surface Rule",
            "Buttons visible to others",
            "Use a second account to verify",
            PALETTE["aqua"],
        )
        self.header_card_secondary.pack(side="left", padx=(10, 0))

        lower_row = tk.Frame(hero_stack, bg=PALETTE["header"])
        lower_row.pack(anchor="e", pady=(10, 0))

        mascot_frame = tk.Frame(
            lower_row,
            bg=PALETTE["surface"],
            highlightbackground=PALETTE["line"],
            highlightthickness=1,
            padx=10,
            pady=10,
        )
        mascot_frame.pack(side="right")
        self.mascot_photo = self._load_image(MASCOT_PATH, 122, 94)
        if self.mascot_photo is not None:
            tk.Label(mascot_frame, image=self.mascot_photo, bg=PALETTE["surface"]).pack()
        else:
            tk.Label(
                mascot_frame,
                text="Presence\nArt",
                font=("Bahnschrift SemiBold", 17),
                fg=PALETTE["text"],
                bg=PALETTE["surface"],
                justify="center",
            ).pack()

    def _build_scroll_content(self) -> None:
        self.templates_panel = self._make_panel(self.content, bg=PALETTE["panel_alt"])
        self.templates_panel.pack(fill="x", padx=8, pady=(0, 16))
        self._section_heading(self.templates_panel, "Quick Starts").pack(anchor="w", padx=20, pady=(18, 6))
        tk.Label(
            self.templates_panel,
            text="Pick a starting point, adjust the three main lines, then cast. Everything else is tucked into Advanced.",
            font=("Segoe UI", 10),
            fg=PALETTE["muted"],
            bg=PALETTE["panel_alt"],
            wraplength=1080,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 12))
        self._build_preset_strip(self.templates_panel)

        self.workspace = tk.Frame(self.content, bg=PALETTE["window"])
        self.workspace.pack(fill="both", expand=True, padx=8, pady=(0, 12))
        self.workspace.grid_columnconfigure(0, weight=5)
        self.workspace.grid_columnconfigure(1, weight=3)

        left_column = tk.Frame(self.workspace, bg=PALETTE["window"])
        right_column = tk.Frame(self.workspace, bg=PALETTE["window"])
        left_column.grid(row=0, column=0, sticky="nsew", padx=(0, 14))
        right_column.grid(row=0, column=1, sticky="nsew")

        self._build_workspace_tabs(left_column)
        self._build_preview_panel(right_column)
        self._build_action_panel(right_column)

    def _build_preset_strip(self, parent: tk.Widget) -> None:
        row = tk.Frame(parent, bg=parent.cget("bg"))
        row.pack(fill="x", padx=18, pady=(0, 18))
        for index, preset in enumerate(PRESETS):
            button = tk.Button(
                row,
                text=preset["label"],
                command=lambda payload=preset: self.apply_preset(payload),
                font=("Segoe UI Semibold", 10),
                fg=PALETTE["text"],
                bg=PALETTE["panel"],
                activeforeground=PALETTE["ink"],
                activebackground=ACTIVITY_ACCENTS[preset["type"]],
                relief="flat",
                bd=0,
                padx=14,
                pady=10,
                cursor="hand2",
            )
            button.grid(row=index // 3, column=index % 3, sticky="ew", padx=(0, 10), pady=(0, 10))
            row.grid_columnconfigure(index % 3, weight=1)

    def _build_workspace_tabs(self, parent: tk.Widget) -> None:
        self.workspace_tabs_shell = self._make_panel(parent)
        self.workspace_tabs_shell.pack(fill="x")

        header = tk.Frame(self.workspace_tabs_shell, bg=PALETTE["panel"])
        header.pack(fill="x", padx=20, pady=(18, 12))

        tk.Label(
            header,
            text="Workspace",
            font=("Bahnschrift SemiBold", 18),
            fg=PALETTE["text"],
            bg=PALETTE["panel"],
        ).pack(side="left")

        tabs_row = tk.Frame(header, bg=PALETTE["panel"])
        tabs_row.pack(side="right")

        self.workspace_tab_buttons["main"] = self._action_button(
            tabs_row,
            "Main",
            lambda: self._switch_workspace_tab("main"),
            PALETTE["gold"],
            PALETTE["ink"],
        )
        self.workspace_tab_buttons["main"].pack(side="left")

        self.workspace_tab_buttons["advanced"] = self._action_button(
            tabs_row,
            "Advanced",
            lambda: self._switch_workspace_tab("advanced"),
            PALETTE["panel_soft"],
            PALETTE["text"],
        )
        self.workspace_tab_buttons["advanced"].pack(side="left", padx=(10, 0))

        tk.Label(
            self.workspace_tabs_shell,
            text="Main keeps the everyday flow clean. Advanced holds the power-user options without crowding the first screen.",
            font=("Segoe UI", 10),
            fg=PALETTE["muted"],
            bg=PALETTE["panel"],
            wraplength=620,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self.workspace_page_container = tk.Frame(self.workspace_tabs_shell, bg=PALETTE["panel"])
        self.workspace_page_container.pack(fill="x", padx=0, pady=(0, 0))

        self.main_workspace_page = tk.Frame(self.workspace_page_container, bg=PALETTE["panel"])
        self.advanced_workspace_page = tk.Frame(self.workspace_page_container, bg=PALETTE["panel"])

        self._build_main_workspace_page(self.main_workspace_page)
        self._build_advanced_workspace_page(self.advanced_workspace_page)
        self._switch_workspace_tab("main")

    def _build_main_workspace_page(self, parent: tk.Widget) -> None:
        self._build_beginner_intro(parent)
        self._build_story_panel(parent)
        self._build_profiles_panel(parent)

    def _build_advanced_workspace_page(self, parent: tk.Widget) -> None:
        self._build_mechanics_panel(parent)
        self._build_links_panel(parent)
        self._build_art_panel(parent)
        self._build_theme_panel(parent)

    def _build_beginner_intro(self, parent: tk.Widget) -> None:
        panel = self._make_panel(parent, bg=PALETTE["panel_alt"])
        panel.pack(fill="x", pady=(0, 16))
        self._section_heading(panel, "Begin Here").pack(anchor="w", padx=20, pady=(18, 6))
        tk.Label(
            panel,
            text="If you are new to Rich Presence, keep it simple: pick a preset, write what you are doing, add short context, then click Cast Presence.",
            font=("Segoe UI", 10),
            fg=PALETTE["muted"],
            bg=PALETTE["panel_alt"],
            wraplength=620,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 14))

        steps = tk.Frame(panel, bg=PALETTE["panel_alt"])
        steps.pack(fill="x", padx=18, pady=(0, 18))
        step_text = [
            ("1", "Pick a vibe", "Use Quick Starts above for a strong default."),
            ("2", "Write three short lines", "Name, details, and state should read in one glance."),
            ("3", "Cast and check Discord", "The desktop app must be open on your PC."),
        ]
        for index, (number, title, body) in enumerate(step_text):
            card = tk.Frame(
                steps,
                bg=PALETTE["panel"],
                highlightbackground=PALETTE["line"],
                highlightthickness=1,
                padx=12,
                pady=12,
            )
            card.grid(row=0, column=index, sticky="nsew", padx=(0, 10 if index < len(step_text) - 1 else 0))
            steps.grid_columnconfigure(index, weight=1)
            tk.Label(
                card,
                text=number,
                font=("Bahnschrift SemiBold", 22),
                fg=PALETTE["gold"],
                bg=PALETTE["panel"],
            ).pack(anchor="w")
            tk.Label(
                card,
                text=title,
                font=("Segoe UI Semibold", 11),
                fg=PALETTE["text"],
                bg=PALETTE["panel"],
            ).pack(anchor="w", pady=(4, 2))
            tk.Label(
                card,
                text=body,
                font=("Segoe UI", 9),
                fg=PALETTE["muted"],
                bg=PALETTE["panel"],
                wraplength=180,
                justify="left",
            ).pack(anchor="w")

    def _switch_workspace_tab(self, tab_name: str) -> None:
        self.active_workspace_tab.set(tab_name)
        self.main_workspace_page.pack_forget()
        self.advanced_workspace_page.pack_forget()

        active_button_bg = PALETTE["gold"]
        active_button_fg = PALETTE["ink"]
        inactive_bg = PALETTE["panel_soft"]
        inactive_fg = PALETTE["text"]

        for name, button in self.workspace_tab_buttons.items():
            if name == tab_name:
                button.configure(bg=active_button_bg, fg=active_button_fg, activebackground=PALETTE["aqua"])
            else:
                button.configure(bg=inactive_bg, fg=inactive_fg, activebackground=PALETTE["sky"])

        if tab_name == "advanced":
            self.advanced_workspace_page.pack(fill="x")
        else:
            self.main_workspace_page.pack(fill="x")

    def _build_advanced_panel(self, parent: tk.Widget) -> None:
        self.advanced_panel = self._make_panel(parent)
        self.advanced_panel.pack(fill="x", pady=(16, 0))
        top = tk.Frame(self.advanced_panel, bg=PALETTE["panel"])
        top.pack(fill="x", padx=20, pady=(18, 10))
        tk.Label(
            top,
            text="Advanced",
            font=("Bahnschrift SemiBold", 18),
            fg=PALETTE["text"],
            bg=PALETTE["panel"],
        ).pack(side="left")
        self.advanced_toggle_button = self._action_button(
            top,
            "Show",
            self._toggle_advanced_panel,
            PALETTE["panel_soft"],
            PALETTE["text"],
        )
        self.advanced_toggle_button.pack(side="right")

        tk.Label(
            self.advanced_panel,
            text="Optional controls for buttons, art, timing, and party data.",
            font=("Segoe UI", 10),
            fg=PALETTE["muted"],
            bg=PALETTE["panel"],
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self.advanced_content = tk.Frame(self.advanced_panel, bg=PALETTE["panel"])

        self._segmented_control(
            self.advanced_content,
            "Activity type",
            self.activity_type_var,
            list(ACTIVITY_TYPE_OPTIONS.keys()),
            "Choose the verb Discord shows for this presence.",
            accent_map=ACTIVITY_ACCENTS,
        )
        self._segmented_control(
            self.advanced_content,
            "Status display mode",
            self.display_mode_var,
            list(DISPLAY_MODE_OPTIONS.keys()),
            "Controls the compact line in Discord's status strip.",
        )
        self._segmented_control(
            self.advanced_content,
            "Timing mode",
            self.timer_mode_var,
            list(TIMER_MODES),
            "Use elapsed for 'started at', countdown for an end time, or static for no timer.",
        )

        timing_row = tk.Frame(self.advanced_content, bg=PALETTE["panel"])
        timing_row.pack(fill="x", padx=20, pady=(0, 10))
        self._compact_field(timing_row, "Countdown duration (minutes)", self.duration_var, "45").pack(fill="x")

        buttons_grid = tk.Frame(self.advanced_content, bg=PALETTE["panel"])
        buttons_grid.pack(fill="x", padx=20, pady=(0, 8))
        buttons_grid.grid_columnconfigure(0, weight=1)
        buttons_grid.grid_columnconfigure(1, weight=1)
        self._compact_field(buttons_grid, "Primary button label", self.primary_button_label_var, "Project").grid(
            row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 10)
        )
        self._compact_field(
            buttons_grid, "Primary button URL", self.primary_button_url_var, "https://example.com/project"
        ).grid(row=0, column=1, sticky="ew", pady=(0, 10))
        self._compact_field(buttons_grid, "Secondary button label", self.secondary_button_label_var, "Community").grid(
            row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 10)
        )
        self._compact_field(
            buttons_grid, "Secondary button URL", self.secondary_button_url_var, "https://discord.gg/your-room"
        ).grid(row=1, column=1, sticky="ew", pady=(0, 10))

        self.party_toggle = tk.Checkbutton(
            self.advanced_content,
            text="Enable party information",
            variable=self.party_enabled_var,
            font=("Segoe UI", 10),
            fg=PALETTE["text"],
            bg=PALETTE["panel"],
            activeforeground=PALETTE["text"],
            activebackground=PALETTE["panel"],
            selectcolor=PALETTE["input"],
            highlightthickness=0,
        )
        self.party_toggle.pack(anchor="w", padx=20, pady=(0, 10))

        party_grid = tk.Frame(self.advanced_content, bg=PALETTE["panel"])
        party_grid.pack(fill="x", padx=20, pady=(0, 8))
        party_grid.grid_columnconfigure(0, weight=1)
        party_grid.grid_columnconfigure(1, weight=1)
        self._compact_field(party_grid, "Party current", self.party_current_var, "1").grid(
            row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 10)
        )
        self._compact_field(party_grid, "Party max", self.party_max_var, "4").grid(
            row=0, column=1, sticky="ew", pady=(0, 10)
        )

        art_grid = tk.Frame(self.advanced_content, bg=PALETTE["panel"])
        art_grid.pack(fill="x", padx=20, pady=(0, 18))
        art_grid.grid_columnconfigure(0, weight=1)
        art_grid.grid_columnconfigure(1, weight=1)
        self._compact_field(
            art_grid, "Large image key or URL", self.manual_large_image_var, "chibi_cloud_playing"
        ).grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))
        self._compact_field(art_grid, "Large image tooltip", self.manual_large_text_var, "PresenceCast highlight").grid(
            row=0, column=1, sticky="ew", pady=(0, 10)
        )
        self._compact_field(art_grid, "Badge image key or URL", self.manual_small_image_var, "chibi_cloud").grid(
            row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 10)
        )
        self._compact_field(art_grid, "Badge tooltip", self.manual_small_text_var, "PresenceCast badge").grid(
            row=1, column=1, sticky="ew", pady=(0, 10)
        )

        self.emoji_asset_toggle = tk.Checkbutton(
            self.advanced_content,
            text="Auto-match art from emoji cues",
            variable=self.emoji_asset_override_var,
            font=("Segoe UI", 10),
            fg=PALETTE["text"],
            bg=PALETTE["panel"],
            activeforeground=PALETTE["text"],
            activebackground=PALETTE["panel"],
            selectcolor=PALETTE["input"],
            highlightthickness=0,
        )
        self.emoji_asset_toggle.pack(anchor="w", padx=20, pady=(0, 18))

        self._toggle_advanced_panel(force=False)

    def _toggle_advanced_panel(self, force: bool | None = None) -> None:
        visible = self.show_advanced_var.get() if force is None else force
        if force is None:
            visible = not visible
        self.show_advanced_var.set(visible)
        if visible:
            self.advanced_content.pack(fill="x")
            self.advanced_toggle_button.configure(text="Hide")
        else:
            self.advanced_content.pack_forget()
            self.advanced_toggle_button.configure(text="Show")

    def _build_story_panel(self, parent: tk.Widget) -> None:
        self.story_panel = self._make_panel(parent)
        self.story_panel.pack(fill="x")
        self._section_heading(self.story_panel, "Quick Cast").pack(anchor="w", padx=20, pady=(18, 6))
        tk.Label(
            self.story_panel,
            text="This is the main flow: name, details, state, then cast. Keep each line short enough to read in one glance.",
            font=("Segoe UI", 10),
            fg=PALETTE["muted"],
            bg=PALETTE["panel"],
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 14))

        self.name_entry = self._add_field(
            self.story_panel,
            "Activity name",
            self.name_var,
            ("Bahnschrift SemiBold", 20),
            "Deep Focus",
        )
        self.details_entry = self._add_field(
            self.story_panel,
            "Details",
            self.details_var,
            ("Segoe UI", 13),
            "Shipping PresenceCast 2.0",
        )
        self.state_entry = self._add_field(
            self.story_panel,
            "State",
            self.state_var,
            ("Segoe UI", 13),
            "Review pass in motion",
        )

        counts_row = tk.Frame(self.story_panel, bg=PALETTE["panel"])
        counts_row.pack(fill="x", padx=20, pady=(2, 14))
        self.name_count = self._metric_label(counts_row, "Name 0 / 128")
        self.details_count = self._metric_label(counts_row, "Details 0 / 128")
        self.state_count = self._metric_label(counts_row, "State 0 / 128")
        self.name_count.pack(side="left")
        self.details_count.pack(side="left", padx=(14, 0))
        self.state_count.pack(side="left", padx=(14, 0))

        self._segmented_control(
            self.story_panel,
            "Activity type",
            self.activity_type_var,
            list(ACTIVITY_TYPE_OPTIONS.keys()),
            "This decides whether Discord says Playing, Listening, Watching, or Competing.",
            accent_map=ACTIVITY_ACCENTS,
        )

    def _build_links_panel(self, parent: tk.Widget) -> None:
        self.links_panel = self._make_panel(parent)
        self.links_panel.pack(fill="x", pady=(16, 0))
        self._section_heading(self.links_panel, "Action Layer").pack(anchor="w", padx=20, pady=(18, 6))
        tk.Label(
            self.links_panel,
            text="Buttons and field URLs make presence more actionable. Discord still limits custom buttons to two, and you cannot see them on your own account.",
            font=("Segoe UI", 10),
            fg=PALETTE["muted"],
            bg=PALETTE["panel"],
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 14))

        links_grid = tk.Frame(self.links_panel, bg=PALETTE["panel"])
        links_grid.pack(fill="x", padx=20)
        links_grid.grid_columnconfigure(0, weight=1)
        links_grid.grid_columnconfigure(1, weight=1)

        self._compact_field(links_grid, "Primary button label", self.primary_button_label_var, "Project").grid(
            row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 10)
        )
        self._compact_field(
            links_grid, "Primary button URL", self.primary_button_url_var, "https://example.com/project"
        ).grid(row=0, column=1, sticky="ew", pady=(0, 10))
        self._compact_field(links_grid, "Secondary button label", self.secondary_button_label_var, "Community").grid(
            row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 10)
        )
        self._compact_field(
            links_grid, "Secondary button URL", self.secondary_button_url_var, "https://discord.gg/your-room"
        ).grid(row=1, column=1, sticky="ew", pady=(0, 10))
        self._compact_field(
            links_grid, "Details click URL", self.details_url_var, "https://example.com/session"
        ).grid(row=2, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))
        self._compact_field(links_grid, "State click URL", self.state_url_var, "https://example.com/context").grid(
            row=2, column=1, sticky="ew", pady=(0, 10)
        )
        self._compact_field(links_grid, "Large art click URL", self.large_url_var, "https://example.com/hero").grid(
            row=3, column=0, sticky="ew", padx=(0, 10), pady=(0, 18)
        )
        self._compact_field(links_grid, "Badge click URL", self.small_url_var, "https://example.com/badge").grid(
            row=3, column=1, sticky="ew", pady=(0, 18)
        )

    def _build_profiles_panel(self, parent: tk.Widget) -> None:
        self.profiles_panel = self._make_panel(parent)
        self.profiles_panel.pack(fill="x", pady=(16, 0))
        self._section_heading(self.profiles_panel, "Profiles").pack(anchor="w", padx=20, pady=(18, 6))
        tk.Label(
            self.profiles_panel,
            text="Save complete studio states so your favorite setups stay one click away.",
            font=("Segoe UI", 10),
            fg=PALETTE["muted"],
            bg=PALETTE["panel"],
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self.profile_menu = tk.OptionMenu(self.profiles_panel, self.profile_var, "")
        self.profile_menu.configure(
            font=("Segoe UI", 10),
            fg=PALETTE["text"],
            bg=PALETTE["panel_alt"],
            activeforeground=PALETTE["ink"],
            activebackground=PALETTE["sky"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            anchor="w",
            padx=12,
        )
        self.profile_menu["menu"].configure(
            font=("Segoe UI", 10),
            fg=PALETTE["text"],
            bg=PALETTE["panel_alt"],
            activeforeground=PALETTE["ink"],
            activebackground=PALETTE["sky"],
            bd=0,
        )
        self.profile_menu.pack(fill="x", padx=20, pady=(0, 10))

        name_wrap = self._compact_field(self.profiles_panel, "Profile name", self.profile_name_var, "After-hours polish")
        name_wrap.pack(fill="x", padx=20, pady=(0, 12))

        row = tk.Frame(self.profiles_panel, bg=PALETTE["panel"])
        row.pack(fill="x", padx=20, pady=(0, 18))
        self._action_button(row, "Save", self.save_profile, PALETTE["gold"], PALETTE["ink"]).pack(side="left")
        self._action_button(row, "Load", self.load_selected_profile, PALETTE["panel_soft"], PALETTE["text"]).pack(
            side="left", padx=(10, 0)
        )
        self._action_button(row, "Delete", self.delete_selected_profile, PALETTE["panel_soft"], PALETTE["text"]).pack(
            side="left", padx=(10, 0)
        )

    def _build_theme_panel(self, parent: tk.Widget) -> None:
        self.theme_panel = self._make_panel(parent, bg=PALETTE["panel_alt"])
        self.theme_panel.pack(fill="x", pady=(16, 0))
        self._section_heading(self.theme_panel, "Theme Bundles").pack(anchor="w", padx=20, pady=(18, 6))
        tk.Label(
            self.theme_panel,
            text="Turn a studio setup into a reusable branded bundle. Load one of the built-in art directions or import and export your own JSON theme packs.",
            font=("Segoe UI", 10),
            fg=PALETTE["muted"],
            bg=PALETTE["panel_alt"],
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self.active_theme_chip = tk.Label(
            self.theme_panel,
            textvariable=self.theme_name_var,
            font=("Segoe UI Semibold", 10),
            fg=PALETTE["ink"],
            bg=PALETTE["gold"],
            padx=12,
            pady=7,
        )
        self.active_theme_chip.pack(anchor="w", padx=20, pady=(0, 12))

        self.theme_cards = tk.Frame(self.theme_panel, bg=PALETTE["panel_alt"])
        self.theme_cards.pack(fill="x", padx=20)

        for index, theme in enumerate(BRAND_THEMES):
            card = tk.Frame(
                self.theme_cards,
                bg=PALETTE["panel"],
                highlightbackground=PALETTE["line"],
                highlightthickness=1,
                padx=12,
                pady=12,
            )
            card.grid(row=index // 2, column=index % 2, sticky="nsew", padx=(0, 10), pady=(0, 10))
            self.theme_cards.grid_columnconfigure(index % 2, weight=1)
            tk.Label(
                card,
                text=theme["label"],
                font=("Bahnschrift SemiBold", 15),
                fg=PALETTE["text"],
                bg=PALETTE["panel"],
            ).pack(anchor="w")
            tk.Label(
                card,
                text=theme["note"],
                font=("Segoe UI", 9),
                fg=PALETTE["muted"],
                bg=PALETTE["panel"],
            ).pack(anchor="w", pady=(4, 10))
            self._action_button(
                card,
                "Load Theme",
                lambda payload=theme: self.apply_brand_theme(payload),
                PALETTE["panel_soft"],
                PALETTE["text"],
            ).pack(anchor="w")

        row = tk.Frame(self.theme_panel, bg=PALETTE["panel_alt"])
        row.pack(fill="x", padx=20, pady=(6, 18))
        self._action_button(row, "Export Theme", self.export_theme_bundle, PALETTE["gold"], PALETTE["ink"]).pack(
            side="left"
        )
        self._action_button(row, "Import Theme", self.import_theme_bundle, PALETTE["panel_soft"], PALETTE["text"]).pack(
            side="left", padx=(10, 0)
        )

    def _build_mechanics_panel(self, parent: tk.Widget) -> None:
        self.mechanics_panel = self._make_panel(parent)
        self.mechanics_panel.pack(fill="x")
        self._section_heading(self.mechanics_panel, "Session Dynamics").pack(anchor="w", padx=20, pady=(18, 6))
        tk.Label(
            self.mechanics_panel,
            text="Current Discord docs emphasize actionable presence: timings, party state, and join context make profiles dramatically more useful.",
            font=("Segoe UI", 10),
            fg=PALETTE["muted"],
            bg=PALETTE["panel"],
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 14))

        self._segmented_control(
            self.mechanics_panel,
            "Timing mode",
            self.timer_mode_var,
            list(TIMER_MODES),
            "Elapsed starts now. Countdown ends after the duration you set.",
        )

        duration_wrap = self._compact_field(self.mechanics_panel, "Countdown duration (minutes)", self.duration_var, "45")
        duration_wrap.pack(fill="x", padx=20, pady=(0, 10))

        self.party_toggle = tk.Checkbutton(
            self.mechanics_panel,
            text="Enable party context",
            variable=self.party_enabled_var,
            font=("Segoe UI", 10),
            fg=PALETTE["text"],
            bg=PALETTE["panel"],
            activeforeground=PALETTE["text"],
            activebackground=PALETTE["panel"],
            selectcolor=PALETTE["input"],
            highlightthickness=0,
        )
        self.party_toggle.pack(anchor="w", padx=20, pady=(2, 10))

        party_grid = tk.Frame(self.mechanics_panel, bg=PALETTE["panel"])
        party_grid.pack(fill="x", padx=20)
        party_grid.grid_columnconfigure(0, weight=1)
        party_grid.grid_columnconfigure(1, weight=1)
        self._compact_field(party_grid, "Party current", self.party_current_var, "1").grid(
            row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 10)
        )
        self._compact_field(party_grid, "Party max", self.party_max_var, "4").grid(
            row=0, column=1, sticky="ew", pady=(0, 10)
        )
        self._compact_field(party_grid, "Party ID", self.party_id_var, "session-alpha").grid(
            row=1, column=0, sticky="ew", columnspan=2, pady=(0, 10)
        )
        self._compact_field(party_grid, "Join secret", self.join_secret_var, "join-token").grid(
            row=2, column=0, sticky="ew", padx=(0, 10), pady=(0, 10)
        )
        self._compact_field(party_grid, "Spectate secret", self.spectate_secret_var, "spectate-token").grid(
            row=2, column=1, sticky="ew", pady=(0, 10)
        )
        self._compact_field(party_grid, "Match secret", self.match_secret_var, "match-token").grid(
            row=3, column=0, sticky="ew", columnspan=2, pady=(0, 10)
        )

        self.instance_toggle = tk.Checkbutton(
            self.mechanics_panel,
            text="Mark as a live session instance",
            variable=self.instance_var,
            font=("Segoe UI", 10),
            fg=PALETTE["text"],
            bg=PALETTE["panel"],
            activeforeground=PALETTE["text"],
            activebackground=PALETTE["panel"],
            selectcolor=PALETTE["input"],
            highlightthickness=0,
        )
        self.instance_toggle.pack(anchor="w", padx=20, pady=(0, 12))

        row = tk.Frame(self.mechanics_panel, bg=PALETTE["panel"])
        row.pack(fill="x", padx=20, pady=(0, 18))
        self._action_button(row, "Shuffle IDs", self.shuffle_session_ids, PALETTE["panel_soft"], PALETTE["text"]).pack(
            side="left"
        )

    def _build_art_panel(self, parent: tk.Widget) -> None:
        self.art_panel = self._make_panel(parent)
        self.art_panel.pack(fill="x", pady=(16, 0))
        self._section_heading(self.art_panel, "Art Direction").pack(anchor="w", padx=20, pady=(18, 6))
        tk.Label(
            self.art_panel,
            text="Discord recommends expressive 1024x1024 art and consistent large imagery across a party. You can keep the smart defaults, override them with asset keys, or point at external image URLs.",
            font=("Segoe UI", 10),
            fg=PALETTE["muted"],
            bg=PALETTE["panel"],
            wraplength=560,
            justify="left",
        ).pack(anchor="w", padx=20, pady=(0, 14))

        self.emoji_asset_toggle = tk.Checkbutton(
            self.art_panel,
            text="Auto-match art from emoji cues in your text",
            variable=self.emoji_asset_override_var,
            font=("Segoe UI", 10),
            fg=PALETTE["text"],
            bg=PALETTE["panel"],
            activeforeground=PALETTE["text"],
            activebackground=PALETTE["panel"],
            selectcolor=PALETTE["input"],
            highlightthickness=0,
        )
        self.emoji_asset_toggle.pack(anchor="w", padx=20, pady=(0, 10))

        art_grid = tk.Frame(self.art_panel, bg=PALETTE["panel"])
        art_grid.pack(fill="x", padx=20)
        art_grid.grid_columnconfigure(0, weight=1)
        art_grid.grid_columnconfigure(1, weight=1)
        self._compact_field(
            art_grid, "Large image key or URL", self.manual_large_image_var, "chibi_cloud_playing"
        ).grid(row=0, column=0, sticky="ew", padx=(0, 10), pady=(0, 10))
        self._compact_field(art_grid, "Large image tooltip", self.manual_large_text_var, "Studio spotlight").grid(
            row=0, column=1, sticky="ew", pady=(0, 10)
        )
        self._compact_field(art_grid, "Badge image key or URL", self.manual_small_image_var, "chibi_cloud").grid(
            row=1, column=0, sticky="ew", padx=(0, 10), pady=(0, 10)
        )
        self._compact_field(art_grid, "Badge tooltip", self.manual_small_text_var, "PresenceCast badge").grid(
            row=1, column=1, sticky="ew", pady=(0, 18)
        )

    def _build_history_panel(self, parent: tk.Widget) -> None:
        self.history_panel = self._make_panel(parent)
        self.history_panel.pack(fill="x", pady=(16, 0))
        self._section_heading(self.history_panel, "Recent Casts").pack(anchor="w", padx=20, pady=(18, 6))
        tk.Label(
            self.history_panel,
            text="Successful casts are remembered automatically so you can revisit a working look fast.",
            font=("Segoe UI", 10),
            fg=PALETTE["muted"],
            bg=PALETTE["panel"],
        ).pack(anchor="w", padx=20, pady=(0, 12))

        self.history_list = tk.Frame(self.history_panel, bg=PALETTE["panel"])
        self.history_list.pack(fill="x", padx=20)

        row = tk.Frame(self.history_panel, bg=PALETTE["panel"])
        row.pack(fill="x", padx=20, pady=(12, 18))
        self._action_button(row, "Clear History", self.clear_history, PALETTE["panel_soft"], PALETTE["text"]).pack(
            side="left"
        )

    def _build_preview_panel(self, parent: tk.Widget) -> None:
        self.preview_panel = self._make_panel(parent, bg=PALETTE["panel_alt"])
        self.preview_panel.pack(fill="x")
        self._section_heading(self.preview_panel, "Discord Surface Preview").pack(anchor="w", padx=18, pady=(18, 6))
        tk.Label(
            self.preview_panel,
            text="A stylized approximation of the card your friends will see.",
            font=("Segoe UI", 10),
            fg=PALETTE["muted"],
            bg=PALETTE["panel_alt"],
        ).pack(anchor="w", padx=18, pady=(0, 12))

        self.preview_card = tk.Frame(
            self.preview_panel,
            bg=PALETTE["ink"],
            highlightbackground=PALETTE["line"],
            highlightthickness=1,
            padx=14,
            pady=14,
        )
        self.preview_card.pack(fill="x", padx=18, pady=(0, 18))

        top = tk.Frame(self.preview_card, bg=PALETTE["ink"])
        top.pack(fill="x")

        self.preview_art_shell = tk.Frame(
            top,
            bg=PALETTE["panel_soft"],
            width=124,
            height=124,
            highlightbackground=PALETTE["line"],
            highlightthickness=1,
        )
        self.preview_art_shell.pack(side="left")
        self.preview_art_shell.pack_propagate(False)
        self.preview_art_label = tk.Label(
            self.preview_art_shell,
            text="Art",
            font=("Bahnschrift SemiBold", 18),
            fg=PALETTE["text"],
            bg=PALETTE["panel_soft"],
            justify="center",
        )
        self.preview_art_label.pack(fill="both", expand=True)

        self.preview_badge_shell = tk.Frame(
            self.preview_art_shell,
            bg=PALETTE["panel"],
            width=42,
            height=42,
            highlightbackground=PALETTE["line"],
            highlightthickness=1,
        )
        self.preview_badge_shell.place(relx=1.0, rely=1.0, x=-8, y=-8, anchor="se")
        self.preview_badge_shell.pack_propagate(False)
        self.preview_badge_label = tk.Label(
            self.preview_badge_shell,
            text="Badge",
            font=("Segoe UI", 8),
            fg=PALETTE["text"],
            bg=PALETTE["panel"],
            justify="center",
        )
        self.preview_badge_label.pack(fill="both", expand=True)

        text = tk.Frame(top, bg=PALETTE["ink"])
        text.pack(side="left", fill="both", expand=True, padx=(14, 0))

        self.preview_title = tk.Label(
            text,
            text="Playing Deep Focus",
            font=("Bahnschrift SemiBold", 18),
            fg=PALETTE["text"],
            bg=PALETTE["ink"],
            anchor="w",
            justify="left",
            wraplength=260,
        )
        self.preview_title.pack(fill="x")

        self.preview_details = tk.Label(
            text,
            text="Shipping a polished build",
            font=("Segoe UI", 10),
            fg=PALETTE["muted"],
            bg=PALETTE["ink"],
            anchor="w",
            justify="left",
            wraplength=260,
        )
        self.preview_details.pack(fill="x", pady=(10, 0))

        self.preview_state = tk.Label(
            text,
            text="Heads-down sprint",
            font=("Segoe UI", 10),
            fg=PALETTE["mint"],
            bg=PALETTE["ink"],
            anchor="w",
            justify="left",
            wraplength=260,
        )
        self.preview_state.pack(fill="x", pady=(4, 0))

        self.preview_meta = tk.Label(
            text,
            text="Elapsed now",
            font=("Cascadia Code", 9),
            fg=PALETTE["soft"],
            bg=PALETTE["ink"],
            anchor="w",
            justify="left",
        )
        self.preview_meta.pack(fill="x", pady=(8, 0))

        self.preview_surface = tk.Label(
            text,
            text="Buttons only render for other accounts",
            font=("Segoe UI", 9),
            fg=PALETTE["gold"],
            bg=PALETTE["ink"],
            anchor="w",
            justify="left",
            wraplength=260,
        )
        self.preview_surface.pack(fill="x", pady=(8, 0))

        self.preview_button_row = tk.Frame(self.preview_card, bg=PALETTE["ink"])
        self.preview_button_row.pack(fill="x", pady=(14, 0))

    def _build_insights_panel(self, parent: tk.Widget) -> None:
        self.insights_panel = self._make_panel(parent)
        self.insights_panel.pack(fill="x", pady=(16, 0))
        self._section_heading(self.insights_panel, "Launch Readiness").pack(anchor="w", padx=18, pady=(18, 6))

        self.readiness_score = tk.Label(
            self.insights_panel,
            text="82",
            font=("Bahnschrift SemiBold", 40),
            fg=PALETTE["gold"],
            bg=PALETTE["panel"],
        )
        self.readiness_score.pack(anchor="w", padx=18, pady=(0, 2))

        self.readiness_caption = tk.Label(
            self.insights_panel,
            text="Strong surface story",
            font=("Segoe UI Semibold", 11),
            fg=PALETTE["text"],
            bg=PALETTE["panel"],
        )
        self.readiness_caption.pack(anchor="w", padx=18)

        self.insight_lines = []
        for index in range(3):
            label = tk.Label(
                self.insights_panel,
                text="",
                font=("Segoe UI", 10),
                fg=PALETTE["muted"],
                bg=PALETTE["panel"],
                wraplength=280,
                justify="left",
                anchor="w",
            )
            label.pack(fill="x", padx=18, pady=(10 if index == 0 else 8, 0))
            self.insight_lines.append(label)

        tk.Label(
            self.insights_panel,
            text="Driven by current Discord Rich Presence guidance: short copy, actionable state, useful timing, and expressive art.",
            font=("Segoe UI", 9),
            fg=PALETTE["soft"],
            bg=PALETTE["panel"],
            wraplength=280,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(14, 18))

    def _build_action_panel(self, parent: tk.Widget) -> None:
        self.action_panel = self._make_panel(parent, bg=PALETTE["panel_alt"])
        self.action_panel.pack(fill="x", pady=(16, 0))
        self._section_heading(self.action_panel, "Broadcast").pack(anchor="w", padx=18, pady=(18, 6))
        tk.Label(
            self.action_panel,
            text="Cast immediately, then let the app keep itself current from GitHub releases.",
            font=("Segoe UI", 10),
            fg=PALETTE["muted"],
            bg=PALETTE["panel_alt"],
            wraplength=280,
            justify="left",
        ).pack(anchor="w", padx=18, pady=(0, 10))

        tk.Button(
            self.action_panel,
            text="Cast Presence",
            command=self.generate_presence,
            font=("Bahnschrift SemiBold", 15),
            fg=PALETTE["ink"],
            bg=PALETTE["gold"],
            activeforeground=PALETTE["ink"],
            activebackground=PALETTE["aqua"],
            relief="flat",
            bd=0,
            padx=20,
            pady=13,
            cursor="hand2",
        ).pack(fill="x", padx=18, pady=(6, 10))

        secondary = tk.Frame(self.action_panel, bg=PALETTE["panel_alt"])
        secondary.pack(fill="x", padx=18)
        self._action_button(secondary, "Clear", self.clear_presence, PALETTE["panel_soft"], PALETTE["text"]).pack(
            side="left", fill="x", expand=True
        )
        self._action_button(
            secondary, "Recall Latest", self.load_latest_history_entry, PALETTE["panel_soft"], PALETTE["text"]
        ).pack(side="left", fill="x", expand=True, padx=(10, 0))

        self.status_title = tk.Label(
            self.action_panel,
            text="Studio status",
            font=("Segoe UI Semibold", 10),
            fg=PALETTE["aqua"],
            bg=PALETTE["panel_alt"],
        )
        self.status_title.pack(anchor="w", padx=18, pady=(18, 4))

        self.status_chip = tk.Label(
            self.action_panel,
            textvariable=self.status_var,
            font=("Segoe UI", 11),
            fg=PALETTE["mint"],
            bg=PALETTE["panel_alt"],
            wraplength=280,
            justify="left",
        )
        self.status_chip.pack(anchor="w", padx=18, pady=(0, 10))

        update_row = tk.Frame(self.action_panel, bg=PALETTE["panel_alt"])
        update_row.pack(fill="x", padx=18, pady=(4, 8))
        tk.Label(
            update_row,
            textvariable=self.update_status_var,
            font=("Segoe UI", 9),
            fg=PALETTE["muted"],
            bg=PALETTE["panel_alt"],
            justify="left",
            wraplength=180,
        ).pack(side="left", fill="x", expand=True)
        self.check_updates_button = self._action_button(
            update_row,
            "Check Updates",
            lambda: self.check_for_updates(manual=True),
            PALETTE["panel_soft"],
            PALETTE["text"],
        )
        self.check_updates_button.pack(side="right", padx=(10, 0))

        tk.Label(
            self.action_panel,
            text="Current Discord behaviors worth remembering:\n• Rich Presence via RPC needs the desktop client\n• Buttons are for other users, not yourself\n• Discord surfaces reward concise text and consistent art",
            font=("Segoe UI", 9),
            fg=PALETTE["soft"],
            bg=PALETTE["panel_alt"],
            justify="left",
            wraplength=280,
        ).pack(anchor="w", padx=18, pady=(0, 18))

    def _make_panel(self, parent: tk.Widget, bg: str | None = None) -> tk.Frame:
        color = bg or PALETTE["panel"]
        return tk.Frame(parent, bg=color, highlightbackground=PALETTE["line"], highlightthickness=1)

    def _chip(self, parent: tk.Widget, text: str, bg: str, fg: str) -> tk.Label:
        return tk.Label(parent, text=text, font=("Segoe UI Semibold", 9), fg=fg, bg=bg, padx=10, pady=6)

    def _header_card(self, parent: tk.Widget, title: str, headline: str, caption: str, accent: str) -> tk.Frame:
        card = tk.Frame(parent, bg=PALETTE["surface"], highlightbackground=PALETTE["line"], highlightthickness=1)
        tk.Label(card, text=title.upper(), font=("Segoe UI", 8), fg=accent, bg=PALETTE["surface"]).pack(
            anchor="w", padx=12, pady=(10, 3)
        )
        tk.Label(
            card,
            text=headline,
            font=("Bahnschrift SemiBold", 15),
            fg=PALETTE["text"],
            bg=PALETTE["surface"],
        ).pack(anchor="w", padx=12)
        tk.Label(
            card,
            text=caption,
            font=("Segoe UI", 9),
            fg=PALETTE["muted"],
            bg=PALETTE["surface"],
        ).pack(anchor="w", padx=12, pady=(4, 10))
        return card

    def _summary_card(self, parent: tk.Widget, title: str) -> dict[str, tk.Widget]:
        frame = tk.Frame(parent, bg=PALETTE["panel"], highlightbackground=PALETTE["line"], highlightthickness=1)
        title_label = tk.Label(frame, text=title, font=("Segoe UI Semibold", 10), fg=PALETTE["muted"], bg=PALETTE["panel"])
        title_label.pack(anchor="w", padx=16, pady=(14, 4))
        value = tk.Label(frame, text="Ready", font=("Bahnschrift SemiBold", 20), fg=PALETTE["text"], bg=PALETTE["panel"])
        value.pack(anchor="w", padx=16)
        caption = tk.Label(
            frame,
            text="",
            font=("Segoe UI", 10),
            fg=PALETTE["soft"],
            bg=PALETTE["panel"],
            wraplength=330,
            justify="left",
        )
        caption.pack(anchor="w", padx=16, pady=(4, 14))
        return {"frame": frame, "title": title_label, "value": value, "caption": caption}

    def _section_heading(self, parent: tk.Widget, text: str) -> tk.Label:
        return tk.Label(parent, text=text, font=("Bahnschrift SemiBold", 18), fg=PALETTE["text"], bg=parent.cget("bg"))

    def _metric_label(self, parent: tk.Widget, text: str) -> tk.Label:
        return tk.Label(parent, text=text, font=("Cascadia Code", 9), fg=PALETTE["soft"], bg=parent.cget("bg"))

    def _add_field(
        self,
        parent: tk.Widget,
        label: str,
        variable: tk.StringVar,
        font: tuple[str, int] | tuple[str, int, str],
        placeholder: str,
    ) -> tk.Entry:
        frame = tk.Frame(parent, bg=parent.cget("bg"))
        frame.pack(fill="x", padx=20, pady=(0, 12))
        tk.Label(frame, text=label, font=("Segoe UI Semibold", 11), fg=PALETTE["text"], bg=parent.cget("bg")).pack(
            anchor="w", pady=(0, 6)
        )
        tk.Label(frame, text=placeholder, font=("Segoe UI", 9), fg=PALETTE["soft"], bg=parent.cget("bg")).pack(
            anchor="w", pady=(0, 6)
        )
        entry = tk.Entry(
            frame,
            textvariable=variable,
            font=font,
            fg=PALETTE["text"],
            bg=PALETTE["input"],
            insertbackground=PALETTE["text"],
            relief="flat",
            bd=0,
        )
        entry.pack(fill="x", ipady=13)
        entry.bind("<Return>", lambda _event: self.generate_presence())
        return entry

    def _compact_field(self, parent: tk.Widget, label: str, variable: tk.StringVar, placeholder: str) -> tk.Frame:
        frame = tk.Frame(parent, bg=parent.cget("bg"))
        tk.Label(frame, text=label, font=("Segoe UI", 9), fg=PALETTE["soft"], bg=parent.cget("bg")).pack(
            anchor="w", pady=(0, 5)
        )
        tk.Entry(
            frame,
            textvariable=variable,
            font=("Segoe UI", 10),
            fg=PALETTE["text"],
            bg=PALETTE["input"],
            insertbackground=PALETTE["text"],
            relief="flat",
            bd=0,
        ).pack(fill="x", ipady=8)
        tk.Label(frame, text=placeholder, font=("Segoe UI", 8), fg=PALETTE["soft"], bg=parent.cget("bg")).pack(
            anchor="w", pady=(5, 0)
        )
        return frame

    def _action_button(self, parent: tk.Widget, text: str, command: object, bg: str, fg: str) -> tk.Button:
        return tk.Button(
            parent,
            text=text,
            command=command,
            font=("Segoe UI Semibold", 10),
            fg=fg,
            bg=bg,
            activeforeground=PALETTE["ink"] if bg != PALETTE["panel_soft"] else PALETTE["text"],
            activebackground=PALETTE["gold"] if bg != PALETTE["panel_soft"] else PALETTE["sky"],
            relief="flat",
            bd=0,
            padx=14,
            pady=9,
            cursor="hand2",
        )

    def _segmented_control(
        self,
        parent: tk.Widget,
        label: str,
        variable: tk.StringVar,
        options: list[str],
        description: str,
        accent_map: dict[str, str] | None = None,
    ) -> None:
        shell = tk.Frame(parent, bg=parent.cget("bg"))
        shell.pack(fill="x", padx=20, pady=(0, 14))
        tk.Label(shell, text=label, font=("Segoe UI Semibold", 11), fg=PALETTE["text"], bg=parent.cget("bg")).pack(
            anchor="w"
        )
        tk.Label(shell, text=description, font=("Segoe UI", 9), fg=PALETTE["soft"], bg=parent.cget("bg")).pack(
            anchor="w", pady=(4, 8)
        )
        row = tk.Frame(shell, bg=parent.cget("bg"))
        row.pack(fill="x")
        buttons: dict[str, tk.Button] = {}
        for index, option in enumerate(options):
            button = tk.Button(
                row,
                text=option,
                command=lambda value=option: variable.set(value),
                font=("Segoe UI Semibold", 10),
                fg=PALETTE["text"],
                bg=PALETTE["panel_alt"],
                activeforeground=PALETTE["ink"],
                activebackground=PALETTE["gold"],
                relief="flat",
                bd=0,
                padx=12,
                pady=10,
                cursor="hand2",
            )
            button.pack(side="left", fill="x", expand=True, padx=(0, 8 if index < len(options) - 1 else 0))
            buttons[option] = button
        self.segmented_groups.append((variable, buttons, accent_map))

    def _wire_live_updates(self) -> None:
        observed = [
            self.name_var,
            self.details_var,
            self.state_var,
            self.primary_button_label_var,
            self.primary_button_url_var,
            self.secondary_button_label_var,
            self.secondary_button_url_var,
            self.details_url_var,
            self.state_url_var,
            self.large_url_var,
            self.small_url_var,
            self.display_mode_var,
            self.activity_type_var,
            self.timer_mode_var,
            self.duration_var,
            self.party_current_var,
            self.party_max_var,
            self.party_id_var,
            self.join_secret_var,
            self.spectate_secret_var,
            self.match_secret_var,
            self.manual_large_image_var,
            self.manual_large_text_var,
            self.manual_small_image_var,
            self.manual_small_text_var,
        ]
        for variable in observed:
            variable.trace_add("write", self._update_counts)

        self.party_enabled_var.trace_add("write", self._refresh_preview)
        self.instance_var.trace_add("write", self._refresh_preview)
        self.emoji_asset_override_var.trace_add("write", self._refresh_preview)

        self.name_entry.focus_set()
        self._refresh_segmented_controls()
        self._update_counts()

    def _update_counts(self, *_args: object) -> None:
        self.name_count.configure(text=f"Name {min(len(self.name_var.get()), 128)} / 128")
        self.details_count.configure(text=f"Details {min(len(self.details_var.get()), 128)} / 128")
        self.state_count.configure(text=f"State {min(len(self.state_var.get()), 128)} / 128")
        self._refresh_preview()

    def _refresh_segmented_controls(self) -> None:
        for variable, buttons, accent_map in self.segmented_groups:
            selected = variable.get()
            for option, button in buttons.items():
                if option == selected:
                    accent = accent_map.get(option, PALETTE["gold"]) if accent_map else PALETTE["gold"]
                    button.configure(bg=accent, fg=PALETTE["ink"], activebackground=accent)
                else:
                    button.configure(bg=PALETTE["panel_alt"], fg=PALETTE["text"], activebackground=PALETTE["sky"])

    def _refresh_preview(self, *_args: object) -> None:
        self._refresh_segmented_controls()
        accent = ACTIVITY_ACCENTS[self.activity_type_var.get()]
        self.preview_state.configure(fg=accent)

        activity_name = self.name_var.get().strip() or "PresenceCast"
        details = self.details_var.get().strip() or "Details line"
        state = self.state_var.get().strip() or "State line"
        verb = ACTIVITY_VERBS[self.activity_type_var.get()]

        self.preview_title.configure(text=f"{verb} {activity_name[:42]}")
        self.preview_details.configure(text=details[:72])

        party_text = self._party_preview_text()
        state_line = state[:52]
        if party_text:
            state_line = f"{state_line} ({party_text})" if state_line else party_text
        self.preview_state.configure(text=state_line or "State line")
        self.preview_meta.configure(text=self._timer_preview_text())

        surface_bits = []
        if self._collect_buttons(strict=False):
            surface_bits.append("Buttons")
        if self.party_enabled_var.get() and party_text:
            surface_bits.append(f"Party {party_text}")
        if not surface_bits:
            surface_bits.append("Simple profile card")
        self.preview_surface.configure(text=" | ".join(surface_bits))

        self._refresh_preview_art()
        self._refresh_preview_buttons()

        self.header_card_primary.configure(highlightbackground=accent)
        self.preview_panel.configure(highlightbackground=accent)
        self.action_panel.configure(highlightbackground=accent)
        self.preview_badge_shell.configure(highlightbackground=accent)
        self.preview_art_shell.configure(highlightbackground=accent)
        self.status_title.configure(fg=accent)

    def _refresh_preview_art(self) -> None:
        large_path, large_placeholder = self._resolve_preview_art()
        if large_path is not None:
            self.preview_asset_photo = self._load_image(large_path, 124, 124)
            if self.preview_asset_photo is not None:
                self.preview_art_label.configure(image=self.preview_asset_photo, text="")
            else:
                self.preview_art_label.configure(image="", text=large_placeholder)
        else:
            self.preview_art_label.configure(image="", text=large_placeholder)

        badge_path, badge_placeholder = self._resolve_preview_badge()
        if badge_path is not None:
            self.preview_badge_photo = self._load_image(badge_path, 40, 40)
            if self.preview_badge_photo is not None:
                self.preview_badge_label.configure(image=self.preview_badge_photo, text="")
            else:
                self.preview_badge_label.configure(image="", text=badge_placeholder)
        else:
            self.preview_badge_label.configure(image="", text=badge_placeholder)

    def _refresh_preview_buttons(self) -> None:
        for child in self.preview_button_row.winfo_children():
            child.destroy()
        buttons = self._collect_buttons(strict=False)
        if not buttons:
            tk.Label(
                self.preview_button_row,
                text="No custom buttons on this cast.",
                font=("Segoe UI", 9),
                fg=PALETTE["soft"],
                bg=PALETTE["ink"],
            ).pack(anchor="w")
            return
        for index, button in enumerate(buttons):
            tk.Label(
                self.preview_button_row,
                text=button["label"],
                font=("Segoe UI Semibold", 9),
                fg=PALETTE["ink"],
                bg=PALETTE["gold"] if index == 0 else PALETTE["panel_soft"],
                padx=10,
                pady=7,
            ).pack(side="left", padx=(0, 8))

    def _refresh_summary_cards(self) -> None:
        score, headline, insights = self._analyze_presence()
        self.summary_cards["readiness"]["value"].configure(text=f"{score}/100")
        self.summary_cards["readiness"]["caption"].configure(text=headline)

        party_text = self._party_preview_text()
        social_value = "Joinable" if self.join_secret_var.get().strip() else "Solo"
        social_caption = "No party state yet."
        if party_text:
            social_value = f"{party_text} party"
            social_caption = "Party context makes the card more actionable."
        elif self.party_enabled_var.get():
            social_value = "Party draft"
            social_caption = "Current/max sizing still needs to validate cleanly."
        self.summary_cards["social"]["value"].configure(text=social_value)
        self.summary_cards["social"]["caption"].configure(text=social_caption)

        buttons = self._collect_buttons(strict=False)
        urls = self._collect_urls(strict=False)
        surface_value = "Profile Story"
        surface_caption = "A clean static card focused on text and art."
        if buttons and urls:
            surface_value = "Clickable"
            surface_caption = "Buttons plus field links create multiple paths into your world."
        elif buttons:
            surface_value = "Call To Action"
            surface_caption = "Custom buttons are in place; remember you need another viewer to see them."
        elif urls:
            surface_value = "Linkable"
            surface_caption = "Field URLs add interaction without spending both button slots."
        self.summary_cards["surface"]["value"].configure(text=surface_value)
        self.summary_cards["surface"]["caption"].configure(text=surface_caption)

        for widget in self.summary_cards.values():
            widget["frame"].configure(highlightbackground=ACTIVITY_ACCENTS[self.activity_type_var.get()])

        self.readiness_caption.configure(text=headline)
        for label, text in zip(self.insight_lines, insights):
            label.configure(text=text)

    def _refresh_insights(self) -> None:
        score, headline, insights = self._analyze_presence()
        self.readiness_score.configure(text=str(score))
        self.readiness_caption.configure(text=headline)
        for label, text in zip(self.insight_lines, insights):
            label.configure(text=text)

    def _analyze_presence(self) -> tuple[int, str, list[str]]:
        name = self.name_var.get().strip()
        details = self.details_var.get().strip()
        state = self.state_var.get().strip()
        buttons = self._collect_buttons(strict=False)
        urls = self._collect_urls(strict=False)
        art_is_present = bool(self._resolved_large_asset()[0] or self.manual_large_image_var.get().strip())

        score = 10
        notes = []
        if name:
            score += 18
        else:
            notes.append("Add an activity name first. Discord still needs a strong top-line identity.")
        if details:
            score += 12
        else:
            notes.append("Details are the clearest place to explain what you are actually doing.")
        if state:
            score += 12
        else:
            notes.append("State is perfect for context like queue, focus mode, or party status.")
        if details and len(details) <= 42:
            score += 8
        else:
            notes.append("Shorter details travel better across profile popouts and friend lists.")
        if state and len(state) <= 42:
            score += 8
        else:
            notes.append("Trim state into a quick phrase, not a full sentence.")
        if self.timer_mode_var.get() != "Static":
            score += 8
        else:
            notes.append("A timer often makes the activity feel more alive and current.")
        if self.party_enabled_var.get():
            try:
                current, maximum = self._validated_party_numbers()
                if maximum >= current:
                    score += 12
            except ValueError:
                notes.append("Party context is enabled, but the current/max values still need to validate.")
        if buttons:
            score += 7
        if urls:
            score += 6
        if art_is_present:
            score += 9
        score = min(100, score)

        if score >= 88:
            headline = "High-signal presence with strong Discord fit"
        elif score >= 72:
            headline = "Strong surface story"
        elif score >= 56:
            headline = "Solid foundation, but it can get sharper"
        else:
            headline = "Needs a little more context before it shines"

        if len(notes) < 3:
            if not buttons and not urls:
                notes.append("Add a button or field URL if you want a stronger call to action.")
            if not self.party_enabled_var.get():
                notes.append("Party metadata is optional, but it is one of Discord's clearest social signals.")
            if not self.manual_large_image_var.get().strip() and not self.emoji_asset_override_var.get():
                notes.append("Emoji auto-art or a manual asset key can give each cast more personality.")

        return score, headline, notes[:3]

    def _resolved_large_asset(self) -> tuple[str, str]:
        manual_key = self.manual_large_image_var.get().strip()
        manual_text = self.manual_large_text_var.get().strip()
        if manual_key:
            return manual_key[:128], (manual_text or self.large_image_text)[:128]
        activity_label = self._resolve_art_activity_label()
        key = self.activity_image_keys.get(activity_label, "").strip() or self.large_image_key
        text = self.activity_image_texts.get(activity_label, "").strip() or self.large_image_text
        return key[:128], text[:128]

    def _resolved_small_asset(self) -> tuple[str | None, str | None]:
        manual_key = self.manual_small_image_var.get().strip()
        manual_text = self.manual_small_text_var.get().strip()
        key = manual_key or self.small_image_key
        text = manual_text or self.small_image_text
        return (key[:128] if key else None), (text[:128] if key and text else None)

    def _resolve_preview_art(self) -> tuple[Path | None, str]:
        manual = self.manual_large_image_var.get().strip()
        if manual.lower().startswith(("https://", "http://")):
            return None, "URL\nArt"
        if manual:
            return None, manual[:20]
        activity_label = self._resolve_art_activity_label()
        preview_path = ACTIVITY_PREVIEW_PATHS.get(activity_label)
        if preview_path is not None and preview_path.exists():
            return preview_path, "Art"
        if MASCOT_PATH.exists():
            return MASCOT_PATH, "Art"
        return None, "Art"

    def _resolve_preview_badge(self) -> tuple[Path | None, str]:
        manual = self.manual_small_image_var.get().strip()
        if manual.lower().startswith(("https://", "http://")):
            return None, "URL"
        if MASCOT_PATH.exists():
            return MASCOT_PATH, "Badge"
        if manual:
            return None, manual[:10]
        return None, "Badge"

    def _resolve_art_activity_label(self) -> str:
        if self.emoji_asset_override_var.get():
            emoji_match = self._match_activity_from_emoji()
            if emoji_match:
                return emoji_match
        return self.activity_type_var.get()

    def _match_activity_from_emoji(self) -> str | None:
        combined = " ".join((self.name_var.get().strip(), self.details_var.get().strip(), self.state_var.get().strip()))
        for activity_label, emoji_group in EMOJI_ASSET_HINTS.items():
            if any(emoji in combined for emoji in emoji_group):
                return activity_label
        return None

    def _timer_preview_text(self) -> str:
        mode = self.timer_mode_var.get()
        if mode == "Static":
            return "Static presence"
        if mode == "Elapsed":
            return "Elapsed from now"
        duration = self._safe_positive_int(self.duration_var.get().strip(), default=45, minimum=1, maximum=1440)
        return f"Countdown {duration}m"

    def _party_preview_text(self) -> str:
        if not self.party_enabled_var.get():
            return ""
        try:
            current, maximum = self._validated_party_numbers()
        except ValueError:
            return ""
        return f"{current} of {maximum}"

    def apply_preset(self, preset: dict[str, object]) -> None:
        self.theme_name_var.set(str(preset.get("label", "Custom Studio")))
        self.name_var.set(str(preset.get("name", "")))
        self.details_var.set(str(preset.get("details", "")))
        self.state_var.set(str(preset.get("state", "")))
        self.activity_type_var.set(str(preset.get("type", "Playing")))
        self.display_mode_var.set(str(preset.get("display_mode", "Show activity name")))
        self.timer_mode_var.set(str(preset.get("timer_mode", "Elapsed")))
        self.duration_var.set(str(preset.get("duration", "45")))
        self.party_enabled_var.set(bool(preset.get("party_enabled", False)))
        self.party_current_var.set(str(preset.get("party_current", "1")))
        self.party_max_var.set(str(preset.get("party_max", "4")))
        self.status_var.set(f'Loaded scene "{preset["label"]}".')
        self.name_entry.focus_set()
        self.name_entry.icursor("end")
        self._refresh_preview()

    def apply_brand_theme(self, theme: dict[str, object]) -> None:
        payload = theme.get("payload", {})
        if not isinstance(payload, dict):
            return
        merged_payload = self._snapshot_payload()
        merged_payload.update(payload)
        self._apply_snapshot(merged_payload)
        self.theme_name_var.set(str(theme.get("label", "Custom Studio")))
        self._flash_status(PALETTE["mint"], f'Loaded theme bundle "{self.theme_name_var.get()}".')

    def export_theme_bundle(self) -> None:
        try:
            THEME_EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        suggested_name = (self.profile_name_var.get().strip() or self.name_var.get().strip() or "presence-theme").replace(
            " ", "_"
        )
        path = filedialog.asksaveasfilename(
            title="Export Presence Theme",
            initialdir=str(THEME_EXPORTS_DIR),
            initialfile=f"{suggested_name}.json",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        bundle = {
            "format": "presencecast-theme-v1",
            "name": self.theme_name_var.get().strip() or suggested_name,
            "exported_at": int(time.time()),
            "payload": self._snapshot_payload(),
        }
        try:
            with Path(path).open("w", encoding="utf-8") as file:
                json.dump(bundle, file, indent=2)
            self._flash_status(PALETTE["gold"], f'Exported theme bundle to "{Path(path).name}".')
        except OSError as exc:
            messagebox.showerror("Export Error", f"Could not export theme bundle.\n\nError: {exc}")

    def import_theme_bundle(self) -> None:
        path = filedialog.askopenfilename(
            title="Import Presence Theme",
            initialdir=str(THEME_EXPORTS_DIR if THEME_EXPORTS_DIR.exists() else APP_DIR),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
        )
        if not path:
            return
        try:
            with Path(path).open("r", encoding="utf-8") as file:
                bundle = json.load(file)
        except (OSError, json.JSONDecodeError) as exc:
            messagebox.showerror("Import Error", f"Could not read that theme bundle.\n\nError: {exc}")
            return

        if not isinstance(bundle, dict):
            messagebox.showerror("Import Error", "That file is not a valid PresenceCast theme bundle.")
            return
        payload = bundle.get("payload", {})
        if not isinstance(payload, dict):
            messagebox.showerror("Import Error", "That theme bundle is missing its payload.")
            return

        self._apply_snapshot(payload)
        self.theme_name_var.set(str(bundle.get("name", Path(path).stem)))
        self._flash_status(PALETTE["mint"], f'Imported theme bundle "{self.theme_name_var.get()}".')

    def _snapshot_payload(self) -> dict[str, object]:
        return {
            "theme_name": self.theme_name_var.get().strip(),
            "name": self.name_var.get().strip(),
            "details": self.details_var.get().strip(),
            "state": self.state_var.get().strip(),
            "display_mode": self.display_mode_var.get(),
            "activity_type": self.activity_type_var.get(),
            "timer_mode": self.timer_mode_var.get(),
            "duration": self.duration_var.get().strip(),
            "party_enabled": self.party_enabled_var.get(),
            "party_current": self.party_current_var.get().strip(),
            "party_max": self.party_max_var.get().strip(),
            "party_id": self.party_id_var.get().strip(),
            "join_secret": self.join_secret_var.get().strip(),
            "spectate_secret": self.spectate_secret_var.get().strip(),
            "match_secret": self.match_secret_var.get().strip(),
            "instance": self.instance_var.get(),
            "emoji_asset_override": self.emoji_asset_override_var.get(),
            "manual_large_image": self.manual_large_image_var.get().strip(),
            "manual_large_text": self.manual_large_text_var.get().strip(),
            "manual_small_image": self.manual_small_image_var.get().strip(),
            "manual_small_text": self.manual_small_text_var.get().strip(),
            "primary_button_label": self.primary_button_label_var.get().strip(),
            "primary_button_url": self.primary_button_url_var.get().strip(),
            "secondary_button_label": self.secondary_button_label_var.get().strip(),
            "secondary_button_url": self.secondary_button_url_var.get().strip(),
            "details_url": self.details_url_var.get().strip(),
            "state_url": self.state_url_var.get().strip(),
            "large_url": self.large_url_var.get().strip(),
            "small_url": self.small_url_var.get().strip(),
        }

    def _apply_snapshot(self, payload: dict[str, object]) -> None:
        self.theme_name_var.set(str(payload.get("theme_name", self.theme_name_var.get() or "Custom Studio")))
        self.name_var.set(str(payload.get("name", "")))
        self.details_var.set(str(payload.get("details", "")))
        self.state_var.set(str(payload.get("state", "")))
        self.display_mode_var.set(str(payload.get("display_mode", "Show activity name")))
        self.activity_type_var.set(str(payload.get("activity_type", "Playing")))
        self.timer_mode_var.set(str(payload.get("timer_mode", "Elapsed")))
        self.duration_var.set(str(payload.get("duration", "45")))
        self.party_enabled_var.set(bool(payload.get("party_enabled", False)))
        self.party_current_var.set(str(payload.get("party_current", "1")))
        self.party_max_var.set(str(payload.get("party_max", "4")))
        self.party_id_var.set(str(payload.get("party_id", "")))
        self.join_secret_var.set(str(payload.get("join_secret", "")))
        self.spectate_secret_var.set(str(payload.get("spectate_secret", "")))
        self.match_secret_var.set(str(payload.get("match_secret", "")))
        self.instance_var.set(bool(payload.get("instance", True)))
        self.emoji_asset_override_var.set(bool(payload.get("emoji_asset_override", True)))
        self.manual_large_image_var.set(str(payload.get("manual_large_image", "")))
        self.manual_large_text_var.set(str(payload.get("manual_large_text", "")))
        self.manual_small_image_var.set(str(payload.get("manual_small_image", "")))
        self.manual_small_text_var.set(str(payload.get("manual_small_text", "")))
        self.primary_button_label_var.set(str(payload.get("primary_button_label", "")))
        self.primary_button_url_var.set(str(payload.get("primary_button_url", "")))
        self.secondary_button_label_var.set(str(payload.get("secondary_button_label", "")))
        self.secondary_button_url_var.set(str(payload.get("secondary_button_url", "")))
        self.details_url_var.set(str(payload.get("details_url", "")))
        self.state_url_var.set(str(payload.get("state_url", "")))
        self.large_url_var.set(str(payload.get("large_url", "")))
        self.small_url_var.set(str(payload.get("small_url", "")))
        self._refresh_preview()

    def _load_profiles(self) -> dict[str, dict[str, object]]:
        if not PROFILES_PATH.exists():
            return {}
        try:
            with PROFILES_PATH.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, dict):
                return {str(key): value for key, value in data.items() if isinstance(value, dict)}
        except (OSError, json.JSONDecodeError):
            pass
        return {}

    def _save_profiles(self) -> None:
        with PROFILES_PATH.open("w", encoding="utf-8") as file:
            json.dump(self.profiles, file, indent=2, sort_keys=True)

    def _load_history(self) -> list[dict[str, object]]:
        if not HISTORY_PATH.exists():
            return []
        try:
            with HISTORY_PATH.open("r", encoding="utf-8") as file:
                data = json.load(file)
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
        except (OSError, json.JSONDecodeError):
            pass
        return []

    def _save_history(self) -> None:
        with HISTORY_PATH.open("w", encoding="utf-8") as file:
            json.dump(self.history[:10], file, indent=2)

    def _refresh_profile_menu(self) -> None:
        menu = self.profile_menu["menu"]
        menu.delete(0, "end")
        names = sorted(self.profiles)
        if not names:
            self.profile_var.set("")
            menu.add_command(label="No saved profiles yet", command=lambda: None)
            return
        if self.profile_var.get() not in names:
            self.profile_var.set(names[0])
        for name in names:
            menu.add_command(label=name, command=lambda value=name: self.profile_var.set(value))

    def save_profile(self) -> None:
        profile_name = self.profile_name_var.get().strip() or self.name_var.get().strip()
        if not profile_name:
            messagebox.showerror("Missing Profile Name", "Add a profile name before saving.")
            return
        self.profiles[profile_name] = self._snapshot_payload()
        self._save_profiles()
        self.profile_var.set(profile_name)
        self._refresh_profile_menu()
        self._flash_status(PALETTE["gold"], f'Saved profile "{profile_name}".')

    def load_selected_profile(self) -> None:
        profile_name = self.profile_var.get().strip()
        payload = self.profiles.get(profile_name)
        if not profile_name or payload is None:
            self._flash_status(PALETTE["gold"], "Choose a saved profile first.")
            return
        self.profile_name_var.set(profile_name)
        self._apply_snapshot(payload)
        self._flash_status(PALETTE["mint"], f'Loaded profile "{profile_name}".')

    def delete_selected_profile(self) -> None:
        profile_name = self.profile_var.get().strip()
        if not profile_name or profile_name not in self.profiles:
            self._flash_status(PALETTE["gold"], "Choose a saved profile first.")
            return
        del self.profiles[profile_name]
        self._save_profiles()
        self.profile_name_var.set("")
        self._refresh_profile_menu()
        self._flash_status(PALETTE["rose"], f'Deleted profile "{profile_name}".')

    def _refresh_history_panel(self) -> None:
        if not hasattr(self, "history_list"):
            return
        for child in self.history_list.winfo_children():
            child.destroy()

        if not self.history:
            tk.Label(
                self.history_list,
                text="No casts yet. Your successful broadcasts will appear here.",
                font=("Segoe UI", 9),
                fg=PALETTE["soft"],
                bg=PALETTE["panel"],
                justify="left",
            ).pack(anchor="w")
            return

        for entry in self.history[:6]:
            snapshot = entry.get("payload", {})
            if not isinstance(snapshot, dict):
                continue
            title = str(snapshot.get("name", "")) or "Untitled cast"
            activity_type = str(snapshot.get("activity_type", "Playing"))
            stamp = time.strftime("%b %d %I:%M %p", time.localtime(int(entry.get("timestamp", time.time()))))
            tk.Button(
                self.history_list,
                text=f"{stamp} | {activity_type} | {title[:26]}",
                command=lambda payload=snapshot: self._apply_snapshot(payload),
                font=("Segoe UI", 9),
                fg=PALETTE["text"],
                bg=PALETTE["panel_alt"],
                activeforeground=PALETTE["ink"],
                activebackground=PALETTE["sky"],
                relief="flat",
                bd=0,
                anchor="w",
                justify="left",
                padx=12,
                pady=9,
                cursor="hand2",
            ).pack(fill="x", pady=(0, 8))

    def load_latest_history_entry(self) -> None:
        if not self.history:
            self._flash_status(PALETTE["gold"], "No saved cast history yet.")
            return
        payload = self.history[0].get("payload")
        if isinstance(payload, dict):
            self._apply_snapshot(payload)
            self._flash_status(PALETTE["mint"], "Loaded the latest cast into the studio.")

    def clear_history(self) -> None:
        self.history = []
        self._save_history()
        self._refresh_history_panel()
        self._flash_status(PALETTE["gold"], "Recent cast history cleared.")

    def _on_content_configure(self, _event: tk.Event) -> None:
        self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))

    def _on_canvas_resize(self, event: tk.Event) -> None:
        self.content_canvas.itemconfigure(self.content_window, width=event.width)
        self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all"))

    def _bind_mousewheel(self, _event: tk.Event) -> None:
        if self._mousewheel_bound:
            return
        self.root.bind_all("<MouseWheel>", self._on_mousewheel)
        self._mousewheel_bound = True

    def _unbind_mousewheel(self, _event: tk.Event | None) -> None:
        if not self._mousewheel_bound:
            return
        self.root.unbind_all("<MouseWheel>")
        self._mousewheel_bound = False

    def _on_mousewheel(self, event: tk.Event) -> None:
        self.content_canvas.yview_scroll(int(-event.delta / 120), "units")

    def _load_config(self) -> dict[str, str]:
        for path in (CONFIG_PATH, BUNDLED_CONFIG_PATH):
            if not path.exists():
                continue
            try:
                with path.open("r", encoding="utf-8") as file:
                    data = json.load(file)
                if isinstance(data, dict):
                    return {
                        "client_id": str(data.get("client_id", DEFAULT_CONFIG["client_id"])).strip(),
                        "large_image_key": str(data.get("large_image_key", DEFAULT_CONFIG["large_image_key"])).strip(),
                        "large_image_text": str(data.get("large_image_text", DEFAULT_CONFIG["large_image_text"])).strip(),
                        "small_image_key": str(data.get("small_image_key", DEFAULT_CONFIG["small_image_key"])).strip(),
                        "small_image_text": str(data.get("small_image_text", DEFAULT_CONFIG["small_image_text"])).strip(),
                        "playing_image_key": str(data.get("playing_image_key", DEFAULT_CONFIG["playing_image_key"])).strip(),
                        "playing_image_text": str(data.get("playing_image_text", DEFAULT_CONFIG["playing_image_text"])).strip(),
                        "listening_image_key": str(data.get("listening_image_key", DEFAULT_CONFIG["listening_image_key"])).strip(),
                        "listening_image_text": str(data.get("listening_image_text", DEFAULT_CONFIG["listening_image_text"])).strip(),
                        "watching_image_key": str(data.get("watching_image_key", DEFAULT_CONFIG["watching_image_key"])).strip(),
                        "watching_image_text": str(data.get("watching_image_text", DEFAULT_CONFIG["watching_image_text"])).strip(),
                        "competing_image_key": str(data.get("competing_image_key", DEFAULT_CONFIG["competing_image_key"])).strip(),
                        "competing_image_text": str(data.get("competing_image_text", DEFAULT_CONFIG["competing_image_text"])).strip(),
                        "emoji_asset_override": bool(data.get("emoji_asset_override", DEFAULT_CONFIG["emoji_asset_override"])),
                    }
            except (OSError, json.JSONDecodeError):
                continue
        return DEFAULT_CONFIG.copy()

    def _validate_url(self, value: str, field_name: str) -> str:
        url = value.strip()
        if not url:
            return ""
        if not url.lower().startswith(("https://", "http://")):
            raise ValueError(f"{field_name} must start with https:// or http://.")
        return url[:512]

    def _collect_buttons(self, strict: bool = True) -> list[dict[str, str]]:
        buttons = []
        for label_var, url_var in (
            (self.primary_button_label_var, self.primary_button_url_var),
            (self.secondary_button_label_var, self.secondary_button_url_var),
        ):
            label = label_var.get().strip()
            url = url_var.get().strip()
            if not label and not url:
                continue
            if not label or not url:
                if strict:
                    raise ValueError("Each button needs both a label and a URL.")
                return []
            if not url.lower().startswith(("https://", "http://")):
                if strict:
                    raise ValueError("Button URLs must start with https:// or http://.")
                return []
            buttons.append({"label": label[:32], "url": url[:512]})
        return buttons

    def _collect_urls(self, strict: bool = True) -> dict[str, str]:
        values = {}
        for key, variable, label in (
            ("details_url", self.details_url_var, "Details URL"),
            ("state_url", self.state_url_var, "State URL"),
            ("large_url", self.large_url_var, "Large art URL"),
            ("small_url", self.small_url_var, "Badge URL"),
        ):
            value = variable.get().strip()
            if not value:
                continue
            try:
                values[key] = self._validate_url(value, label)
            except ValueError:
                if strict:
                    raise
                return {}
        return values

    def _safe_positive_int(self, raw: str, default: int, minimum: int, maximum: int) -> int:
        try:
            value = int(raw)
        except (TypeError, ValueError):
            return default
        return max(minimum, min(maximum, value))

    def _validated_party_numbers(self) -> tuple[int, int]:
        current = int(self.party_current_var.get().strip())
        maximum = int(self.party_max_var.get().strip())
        if current < 1 or maximum < 1:
            raise ValueError("Party values must be positive numbers.")
        if current > maximum:
            raise ValueError("Party current size cannot be larger than party max.")
        return current, maximum

    def _parse_version_tuple(self, raw: str) -> tuple[int, int, int]:
        cleaned = raw.strip().lstrip("vV")
        values = []
        for part in cleaned.split("."):
            digits = "".join(character for character in part if character.isdigit())
            values.append(int(digits or "0"))
        while len(values) < 3:
            values.append(0)
        return tuple(values[:3])

    def _is_packaged_build(self) -> bool:
        return bool(getattr(sys, "frozen", False) and Path(sys.executable).suffix.lower() == ".exe")

    def _set_update_busy(self, busy: bool) -> None:
        self.update_check_in_progress = busy
        if hasattr(self, "check_updates_button"):
            self.check_updates_button.configure(state="disabled" if busy else "normal")

    def _fetch_latest_release_info(self) -> dict[str, str]:
        request = urllib.request.Request(
            LATEST_RELEASE_API,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": f"PresenceCast/{APP_VERSION}",
            },
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))

        tag_name = str(payload.get("tag_name", "")).strip()
        version = tag_name.lstrip("vV")
        asset_url = ""
        for asset in payload.get("assets", []):
            if str(asset.get("name", "")).strip() == RELEASE_ASSET_NAME:
                asset_url = str(asset.get("browser_download_url", "")).strip()
                break

        return {
            "tag_name": tag_name,
            "version": version,
            "html_url": str(payload.get("html_url", RELEASES_URL)).strip() or RELEASES_URL,
            "asset_url": asset_url,
            "published_at": str(payload.get("published_at", "")).strip(),
        }

    def check_for_updates(self, manual: bool = False) -> None:
        if self.update_check_in_progress:
            return
        self._set_update_busy(True)
        self.update_status_var.set("Checking for updates...")

        def worker() -> None:
            try:
                info = self._fetch_latest_release_info()
                self.root.after(0, lambda: self._handle_update_check_result(info, manual, None))
            except Exception as exc:
                self.root.after(0, lambda: self._handle_update_check_result(None, manual, exc))

        threading.Thread(target=worker, daemon=True).start()

    def _handle_update_check_result(
        self,
        info: dict[str, str] | None,
        manual: bool,
        error: Exception | None,
    ) -> None:
        self._set_update_busy(False)
        if error is not None:
            self.update_status_var.set(f"Version {APP_VERSION}")
            if manual:
                messagebox.showerror("Update Check Failed", f"Could not check for updates.\n\nError: {error}")
            return

        assert info is not None
        self.update_info = info
        current_version = self._parse_version_tuple(APP_VERSION)
        latest_version = self._parse_version_tuple(info["version"])

        if latest_version > current_version:
            self.update_status_var.set(f"Update {info['version']} available")
            prompt = (
                f"PresenceCast {info['version']} is available.\n\n"
                f"You are on {APP_VERSION}."
            )
            if self._is_packaged_build() and info.get("asset_url"):
                prompt += "\n\nDownload and install it now?"
                if manual or True:
                    if messagebox.askyesno("Update Available", prompt):
                        self.download_and_install_update(info)
            else:
                prompt += "\n\nThis build cannot self-install updates. Open the releases page instead?"
                if manual and messagebox.askyesno("Update Available", prompt):
                    webbrowser.open(info["html_url"])
        else:
            self.update_status_var.set(f"Version {APP_VERSION} is current")
            if manual:
                messagebox.showinfo("Up To Date", f"PresenceCast {APP_VERSION} is already the latest release.")

    def download_and_install_update(self, info: dict[str, str]) -> None:
        if not self._is_packaged_build():
            webbrowser.open(info.get("html_url", RELEASES_URL))
            return
        asset_url = info.get("asset_url", "").strip()
        if not asset_url:
            messagebox.showinfo("Release Found", "The latest release is available, but no Windows asset was found.")
            webbrowser.open(info.get("html_url", RELEASES_URL))
            return

        self._set_update_busy(True)
        self.update_status_var.set(f"Downloading {info['version']}...")

        def worker() -> None:
            target_path = Path(tempfile.gettempdir()) / f"PresenceCast-{info['version']}.exe"
            request = urllib.request.Request(
                asset_url,
                headers={"User-Agent": f"PresenceCast/{APP_VERSION}"},
            )
            try:
                with urllib.request.urlopen(request, timeout=60) as response, target_path.open("wb") as file:
                    while True:
                        chunk = response.read(1024 * 256)
                        if not chunk:
                            break
                        file.write(chunk)
                self.root.after(0, lambda: self._finish_update_download(info, target_path, None))
            except Exception as exc:
                self.root.after(0, lambda: self._finish_update_download(info, target_path, exc))

        threading.Thread(target=worker, daemon=True).start()

    def _finish_update_download(self, info: dict[str, str], target_path: Path, error: Exception | None) -> None:
        self._set_update_busy(False)
        if error is not None:
            self.update_status_var.set(f"Version {APP_VERSION}")
            messagebox.showerror("Update Download Failed", f"Could not download the update.\n\nError: {error}")
            return
        self.update_status_var.set(f"Installing {info['version']}...")
        self._launch_self_update(target_path)

    def _launch_self_update(self, downloaded_exe: Path) -> None:
        current_exe = Path(sys.executable).resolve()
        backup_exe = current_exe.with_suffix(".old.exe")
        script_path = Path(tempfile.gettempdir()) / f"presencecast-updater-{int(time.time())}.ps1"
        script_path.write_text(
            "\n".join(
                [
                    "param(",
                    "  [string]$TargetExe,",
                    "  [string]$DownloadedExe,",
                    "  [string]$BackupExe,",
                    "  [int]$ProcessIdToWaitFor",
                    ")",
                    "$ErrorActionPreference = 'Stop'",
                    "for ($i = 0; $i -lt 180; $i++) {",
                    "  if (-not (Get-Process -Id $ProcessIdToWaitFor -ErrorAction SilentlyContinue)) { break }",
                    "  Start-Sleep -Milliseconds 500",
                    "}",
                    "for ($i = 0; $i -lt 20; $i++) {",
                    "  try {",
                    "    if (Test-Path -LiteralPath $BackupExe) { Remove-Item -LiteralPath $BackupExe -Force }",
                    "    if (Test-Path -LiteralPath $TargetExe) { Move-Item -LiteralPath $TargetExe -Destination $BackupExe -Force }",
                    "    Move-Item -LiteralPath $DownloadedExe -Destination $TargetExe -Force",
                    "    Start-Process -FilePath $TargetExe",
                    "    exit 0",
                    "  } catch {",
                    "    Start-Sleep -Seconds 1",
                    "  }",
                    "}",
                    "exit 1",
                ]
            ),
            encoding="utf-8",
        )

        creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        subprocess.Popen(
            [
                "powershell",
                "-NoProfile",
                "-ExecutionPolicy",
                "Bypass",
                "-File",
                str(script_path),
                str(current_exe),
                str(downloaded_exe),
                str(backup_exe),
                str(os.getpid()),
            ],
            creationflags=creation_flags,
        )
        self._flash_status(PALETTE["gold"], "Installing update and restarting PresenceCast...")
        self.on_close()

    def _ensure_connection(self) -> None:
        if self.rpc is not None and self.connected_client_id == self.client_id:
            return
        self._disconnect()
        self.rpc = Presence(self.client_id)
        self.rpc.connect()
        self.connected_client_id = self.client_id

    def _disconnect(self) -> None:
        if self.rpc is None:
            return
        try:
            self.rpc.clear()
        except Exception:
            pass
        try:
            self.rpc.close()
        except Exception:
            pass
        self.rpc = None
        self.connected_client_id = None

    def _flash_status(self, color: str, message: str) -> None:
        self.status_var.set(message)
        self.status_chip.configure(fg=color)

    def _start_status_animation(self) -> None:
        self.animation_phase += 0.16
        pulse = int(165 + 42 * math.sin(self.animation_phase))
        if self.status_chip.cget("fg") not in {PALETTE["rose"], PALETTE["gold"]}:
            self.status_chip.configure(fg=f"#{pulse:02x}{241:02x}{180:02x}")
        self.status_after_id = self.root.after(100, self._start_status_animation)

    def _blend_hex(self, left: str, right: str, ratio: float) -> str:
        ratio = max(0.0, min(1.0, ratio))
        left = left.lstrip("#")
        right = right.lstrip("#")
        left_rgb = [int(left[index : index + 2], 16) for index in (0, 2, 4)]
        right_rgb = [int(right[index : index + 2], 16) for index in (0, 2, 4)]
        blended = [
            int(channel_left + (channel_right - channel_left) * ratio)
            for channel_left, channel_right in zip(left_rgb, right_rgb)
        ]
        return "#" + "".join(f"{value:02x}" for value in blended)

    def _start_surface_motion(self) -> None:
        self.motion_phase += 0.11
        accent = ACTIVITY_ACCENTS[self.activity_type_var.get()]
        ratio = (math.sin(self.motion_phase) + 1) / 2
        border = self._blend_hex(PALETTE["line"], accent, 0.25 + ratio * 0.55)
        glow = self._blend_hex(PALETTE["soft"], PALETTE["text"], 0.2 + ratio * 0.35)

        for widget in (
            self.preview_card,
            self.preview_art_shell,
            self.preview_badge_shell,
            self.header_card_primary,
            self.header_card_secondary,
        ):
            widget.configure(highlightbackground=border)

        if hasattr(self, "active_theme_chip"):
            self.active_theme_chip.configure(bg=border, fg=PALETTE["ink"])
        self.preview_meta.configure(fg=glow)
        self.preview_surface.configure(fg=self._blend_hex(PALETTE["gold"], PALETTE["text"], ratio * 0.25))

        self.motion_after_id = self.root.after(90, self._start_surface_motion)

    def shuffle_session_ids(self) -> None:
        self.party_id_var.set(self.party_id_var.get().strip() or f"party-{self._random_token(8)}")
        self.join_secret_var.set(self._random_token(18))
        self.spectate_secret_var.set(self._random_token(18))
        self.match_secret_var.set(self._random_token(18))
        self._flash_status(PALETTE["mint"], "Fresh session identifiers generated.")

    def _random_token(self, size: int) -> str:
        return secrets.token_urlsafe(size)[: max(10, size + 4)]

    def _build_payload(self) -> dict[str, object]:
        activity_name = self.name_var.get().strip()
        details = self.details_var.get().strip()
        state = self.state_var.get().strip()

        if not self.client_id.isdigit():
            raise ValueError("config.json must contain a valid numeric Discord Application ID.")
        if not activity_name:
            raise ValueError("Type an activity name before casting presence.")

        display_mode = DISPLAY_MODE_OPTIONS[self.display_mode_var.get()]
        activity_type = ACTIVITY_TYPE_OPTIONS[self.activity_type_var.get()]
        large_image, large_text = self._resolved_large_asset()
        small_image, small_text = self._resolved_small_asset()
        buttons = self._collect_buttons(strict=True)

        start_time = None
        end_time = None
        timer_mode = self.timer_mode_var.get()
        if timer_mode == "Elapsed":
            start_time = int(time.time())
        elif timer_mode == "Countdown":
            minutes = self._safe_positive_int(self.duration_var.get().strip(), default=45, minimum=1, maximum=1440)
            end_time = int(time.time()) + minutes * 60

        party_id = None
        party_size = None
        if self.party_enabled_var.get():
            current, maximum = self._validated_party_numbers()
            if not self.party_id_var.get().strip():
                self.party_id_var.set(f"party-{self._random_token(8)}")
            party_id = self.party_id_var.get().strip()[:128]
            party_size = [current, maximum]

        return {
            "name": activity_name[:128],
            "details": details[:128] if details else None,
            "state": state[:128] if state else None,
            "activity_type": activity_type,
            "status_display_type": display_mode,
            "start": start_time,
            "end": end_time,
            "large_image": large_image or None,
            "large_text": large_text if large_image and large_text else None,
            "small_image": small_image,
            "small_text": small_text,
            "party_id": party_id,
            "party_size": party_size,
            "join": self.join_secret_var.get().strip()[:128] or None,
            "spectate": self.spectate_secret_var.get().strip()[:128] or None,
            "match": self.match_secret_var.get().strip()[:128] or None,
            "buttons": buttons or None,
            "instance": self.instance_var.get(),
        }

    def generate_presence(self) -> None:
        try:
            payload = self._build_payload()
            self._ensure_connection()
            assert self.rpc is not None
            self.rpc.update(**payload)
            self._remember_cast()
            activity_name = self.name_var.get().strip()
            message = f'Broadcasting "{activity_name[:44]}".'
            if payload.get("buttons"):
                message += " Buttons are visible to other users."
            self._flash_status(PALETTE["mint"], message)
            self._refresh_preview()
        except ValueError as exc:
            self._flash_status(PALETTE["gold"], str(exc))
            messagebox.showerror("PresenceCast Input Error", str(exc))
        except Exception as exc:
            self._flash_status(PALETTE["rose"], "Discord connection failed.")
            messagebox.showerror(
                "Discord RPC Error",
                "Discord must be open on your PC, and your Application ID in config.json must be valid.\n\n"
                f"Error: {exc}",
            )

    def _remember_cast(self) -> None:
        snapshot = self._snapshot_payload()
        entry = {"timestamp": int(time.time()), "payload": snapshot}
        self.history = [entry] + [
            item for item in self.history if isinstance(item, dict) and item.get("payload") != snapshot
        ]
        self.history = self.history[:10]
        self._save_history()
        self._refresh_history_panel()

    def clear_presence(self) -> None:
        if self.rpc is None:
            self._flash_status(PALETTE["gold"], "Nothing active to clear.")
            return
        try:
            self.rpc.clear()
            self._flash_status(PALETTE["gold"], "Presence cleared.")
        except Exception as exc:
            self._flash_status(PALETTE["rose"], "Could not clear Discord presence.")
            messagebox.showerror("Discord RPC Error", str(exc))

    def on_close(self) -> None:
        if self.status_after_id is not None:
            self.root.after_cancel(self.status_after_id)
        if self.motion_after_id is not None:
            self.root.after_cancel(self.motion_after_id)
        self._unbind_mousewheel(None)

        def shutdown() -> None:
            self._disconnect()

        thread = threading.Thread(target=shutdown, daemon=True)
        thread.start()
        self.root.destroy()


def main() -> None:
    root = tk.Tk()
    PresenceApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
