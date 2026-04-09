import json
import math
import sys
import threading
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from pypresence import ActivityType, Presence
from pypresence.types import StatusDisplayType


DEFAULT_CONFIG = {
    "client_id": "",
    "large_image_key": "chibi_cloud",
    "large_image_text": "PresenceCast by Cloud",
}
APP_NAME = "PresenceCast"
TOOL_LABEL = "Cloud's RPC Tool"

PALETTE = {
    "window": "#050505",
    "header": "#0a0a0a",
    "surface": "#101010",
    "panel": "#151515",
    "panel_soft": "#1b1b1b",
    "input": "#080808",
    "border": "#2f2f2f",
    "text": "#f5f5f5",
    "muted": "#b2b2b2",
    "soft": "#848484",
    "blue": "#22a7ff",
    "cyan": "#7fe7ff",
    "mint": "#3dd7ae",
    "amber": "#ffb347",
    "rose": "#ff7a90",
    "gold": "#ffd166",
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

PRESETS = [
    {
        "label": "Deep work",
        "name": "Deep work",
        "details": "Heads down",
        "state": "Focusing on a priority task",
        "type": "Playing",
    },
    {
        "label": "Building",
        "name": "Building",
        "details": "Creating something new",
        "state": "In the middle of a session",
        "type": "Playing",
    },
    {
        "label": "In a meeting",
        "name": "In a meeting",
        "details": "Slower replies for a bit",
        "state": "Wrapping up a conversation",
        "type": "Watching",
    },
    {
        "label": "Study mode",
        "name": "Study mode",
        "details": "Deep focus",
        "state": "Quiet concentration",
        "type": "Listening",
    },
    {
        "label": "Away briefly",
        "name": "Away briefly",
        "details": "Back soon",
        "state": "Taking a short break",
        "type": "Watching",
    },
]


def get_runtime_dirs() -> tuple[Path, Path]:
    exe_dir = Path(sys.executable).resolve().parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
    bundle_dir = Path(getattr(sys, "_MEIPASS", exe_dir))
    return exe_dir, bundle_dir


APP_DIR, BUNDLE_DIR = get_runtime_dirs()


def pick_path(filename: str) -> Path:
    app_path = APP_DIR / filename
    if app_path.exists():
        return app_path
    return BUNDLE_DIR / filename


CONFIG_PATH = APP_DIR / "config.json"
BUNDLED_CONFIG_PATH = BUNDLE_DIR / "config.json"
ICON_PATH = pick_path("presencecast.ico")
LOGO_PATH = pick_path("presencecast.png")
MASCOT_PATH = pick_path("chibi-cloud-watermark.png")


class PresenceApp:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_NAME)
        self.root.geometry("980x760")
        self.root.minsize(920, 700)
        self.root.configure(bg=PALETTE["window"])

        self.rpc: Presence | None = None
        self.connected_client_id: str | None = None
        self.config = self._load_config()
        self.client_id = str(self.config.get("client_id", "")).strip()
        self.large_image_key = str(self.config.get("large_image_key", DEFAULT_CONFIG["large_image_key"])).strip()
        self.large_image_text = str(self.config.get("large_image_text", DEFAULT_CONFIG["large_image_text"])).strip()

        self.logo_photo: tk.PhotoImage | None = None
        self.small_logo_photo: tk.PhotoImage | None = None
        self.mascot_photo: tk.PhotoImage | None = None

        self.name_var = tk.StringVar()
        self.details_var = tk.StringVar()
        self.state_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Ready to cast your activity into Discord.")
        self.display_mode_var = tk.StringVar(value="Show activity name")
        self.activity_type_var = tk.StringVar(value="Playing")
        self.timer_enabled_var = tk.BooleanVar(value=True)

        self.animation_phase = 0.0
        self.status_after_id: str | None = None
        self._mousewheel_bound = False

        self._apply_icon()
        self._build_ui()
        self._start_status_animation()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def _apply_icon(self) -> None:
        png_loaded = False
        if LOGO_PATH.exists():
            try:
                self.logo_photo = tk.PhotoImage(file=str(LOGO_PATH))
                self.root.iconphoto(True, self.logo_photo)
                png_loaded = True
            except Exception:
                self.logo_photo = None

        if ICON_PATH.exists() and not png_loaded:
            try:
                self.root.iconbitmap(default=str(ICON_PATH))
            except Exception:
                pass

    def _build_ui(self) -> None:
        self.header = tk.Frame(self.root, bg=PALETTE["header"], height=134)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        self._build_header()

        self.content_shell = tk.Frame(self.root, bg=PALETTE["window"])
        self.content_shell.pack(fill="both", expand=True, padx=18, pady=(14, 8))

        self.content_canvas = tk.Canvas(
            self.content_shell,
            bg=PALETTE["window"],
            bd=0,
            highlightthickness=0,
            yscrollincrement=22,
        )
        self.content_canvas.pack(side="left", fill="both", expand=True)

        self.content_scrollbar = tk.Scrollbar(
            self.content_shell,
            orient="vertical",
            command=self.content_canvas.yview,
            troughcolor=PALETTE["window"],
            bg=PALETTE["panel"],
            activebackground=PALETTE["blue"],
        )
        self.content_scrollbar.pack(side="right", fill="y")
        self.content_canvas.configure(yscrollcommand=self.content_scrollbar.set)
        self.content_canvas.bind("<Configure>", self._on_canvas_resize)
        self.content_canvas.bind("<Enter>", self._bind_mousewheel)
        self.content_canvas.bind("<Leave>", self._unbind_mousewheel)

        self.content = tk.Frame(self.content_canvas, bg=PALETTE["window"])
        self.content_window = self.content_canvas.create_window(0, 0, window=self.content, anchor="nw")
        self.content.bind("<Configure>", self._on_content_configure)

        self._build_scroll_content()

        self.footer = tk.Frame(self.root, bg=PALETTE["header"], height=40)
        self.footer.pack(fill="x", side="bottom")
        self.footer.pack_propagate(False)

        self.footer_label = tk.Label(
            self.footer,
            text="made with \u2665 by Cloud",
            font=("Segoe UI", 10, "italic"),
            fg=PALETTE["muted"],
            bg=PALETTE["header"],
        )
        self.footer_label.pack(side="right", padx=18, pady=10)

        self.name_var.trace_add("write", self._update_counts)
        self.details_var.trace_add("write", self._update_counts)
        self.state_var.trace_add("write", self._update_counts)
        self.display_mode_var.trace_add("write", self._update_preview)
        self.activity_type_var.trace_add("write", self._update_preview)

        self.name_entry.focus_set()
        self._update_counts()
        self._update_preview()

    def _build_header(self) -> None:
        left = tk.Frame(self.header, bg=PALETTE["header"])
        left.pack(side="left", fill="both", expand=True, padx=22, pady=18)

        if LOGO_PATH.exists():
            try:
                logo = tk.PhotoImage(file=str(LOGO_PATH))
                factor = max(1, math.ceil(max(logo.width(), logo.height()) / 72))
                self.small_logo_photo = logo.subsample(factor, factor)
            except Exception:
                self.small_logo_photo = None

        if self.small_logo_photo is not None:
            tk.Label(left, image=self.small_logo_photo, bg=PALETTE["header"]).pack(side="left", padx=(0, 14))

        title_block = tk.Frame(left, bg=PALETTE["header"])
        title_block.pack(side="left", fill="y")

        tk.Label(
            title_block,
            text=TOOL_LABEL,
            font=("Segoe UI Semibold", 10),
            fg=PALETTE["cyan"],
            bg=PALETTE["header"],
        ).pack(anchor="w")

        tk.Label(
            title_block,
            text="Broadcast presence with clarity.",
            font=("Bahnschrift SemiBold", 28),
            fg=PALETTE["text"],
            bg=PALETTE["header"],
        ).pack(anchor="w", pady=(4, 2))

        tk.Label(
            title_block,
            text="Craft a polished Discord activity without the clutter.",
            font=("Segoe UI", 12),
            fg=PALETTE["muted"],
            bg=PALETTE["header"],
        ).pack(anchor="w")

        right = tk.Frame(self.header, bg=PALETTE["header"])
        right.pack(side="right", padx=22, pady=24)

        if MASCOT_PATH.exists():
            try:
                mascot = tk.PhotoImage(file=str(MASCOT_PATH))
                factor = max(1, math.ceil(max(mascot.width() / 132, mascot.height() / 92)))
                self.mascot_photo = mascot.subsample(factor, factor)
            except Exception:
                self.mascot_photo = None

        if self.mascot_photo is not None:
            mascot_frame = tk.Frame(
                right,
                bg=PALETTE["surface"],
                highlightbackground=PALETTE["border"],
                highlightthickness=1,
                padx=10,
                pady=10,
            )
            mascot_frame.pack(anchor="e")
            tk.Label(mascot_frame, image=self.mascot_photo, bg=PALETTE["surface"]).pack(anchor="e")

        tk.Label(
            right,
            text="RPC",
            font=("Segoe UI Semibold", 9),
            fg=PALETTE["window"],
            bg=PALETTE["amber"],
            padx=12,
            pady=7,
        ).pack(anchor="e", pady=(10, 0))

    def _build_scroll_content(self) -> None:
        self.templates_shell = tk.Frame(self.content, bg=PALETTE["window"])
        self.templates_shell.pack(fill="x", pady=(0, 14))

        tk.Label(
            self.templates_shell,
            text="Templates",
            font=("Segoe UI Semibold", 11),
            fg=PALETTE["text"],
            bg=PALETTE["window"],
        ).pack(anchor="w", padx=14, pady=(0, 10))

        self.templates_row = tk.Frame(self.templates_shell, bg=PALETTE["window"])
        self.templates_row.pack(fill="x", padx=14)

        for index, preset in enumerate(PRESETS):
            button = tk.Button(
                self.templates_row,
                text=preset["label"],
                command=lambda payload=preset: self.apply_preset(payload),
                font=("Segoe UI", 10),
                fg=PALETTE["text"],
                bg=PALETTE["panel_soft"],
                activeforeground=PALETTE["window"],
                activebackground=PALETTE["blue"],
                relief="flat",
                bd=0,
                padx=16,
                pady=9,
                cursor="hand2",
            )
            button.grid(row=index // 3, column=index % 3, sticky="w", padx=(0, 10), pady=(0, 10))

        self.workspace = tk.Frame(self.content, bg=PALETTE["window"])
        self.workspace.pack(fill="both", expand=True, padx=14, pady=(2, 0))

        self.left_column = tk.Frame(self.workspace, bg=PALETTE["window"])
        self.left_column.pack(side="left", fill="both", expand=True)

        self.right_column = tk.Frame(self.workspace, bg=PALETTE["window"], width=292)
        self.right_column.pack(side="left", fill="y", padx=(18, 0))
        self.right_column.pack_propagate(False)

        self.composer_panel = self._make_panel(self.left_column)
        self.composer_panel.pack(fill="x")
        self._section_heading(self.composer_panel, "Presence Composer").pack(anchor="w", padx=22, pady=(18, 6))

        self.name_entry = self._add_field(self.composer_panel, "Activity name", self.name_var, ("Segoe UI", 20), top_padding=8)
        self.details_entry = self._add_field(self.composer_panel, "Details", self.details_var, ("Segoe UI", 14))
        self.state_entry = self._add_field(self.composer_panel, "State", self.state_var, ("Segoe UI", 14), bottom_padding=12)

        for entry in (self.name_entry, self.details_entry, self.state_entry):
            entry.bind("<Return>", lambda _event: self.generate_presence())

        self.metrics_row = tk.Frame(self.composer_panel, bg=PALETTE["panel"])
        self.metrics_row.pack(fill="x", padx=22, pady=(0, 18))
        self.name_count = self._metric_label(self.metrics_row, "Activity name: 0 / 128")
        self.name_count.pack(side="left")
        self.details_count = self._metric_label(self.metrics_row, "Details: 0 / 128")
        self.details_count.pack(side="left", padx=(16, 0))
        self.state_count = self._metric_label(self.metrics_row, "State: 0 / 128")
        self.state_count.pack(side="left", padx=(16, 0))

        self.side_panel = self._make_panel(self.right_column)
        self.side_panel.pack(fill="x")
        self._section_heading(self.side_panel, "Broadcast").pack(anchor="w", padx=18, pady=(18, 6))

        self.preview_card = tk.Frame(self.side_panel, bg=PALETTE["input"])
        self.preview_card.pack(fill="x", padx=18, pady=(2, 16))

        self.preview_name = tk.Label(
            self.preview_card,
            text="Activity name appears here",
            font=("Segoe UI Semibold", 12),
            fg=PALETTE["text"],
            bg=PALETTE["input"],
            anchor="w",
        )
        self.preview_name.pack(fill="x", padx=14, pady=(14, 0))

        self.preview_details = tk.Label(
            self.preview_card,
            text="Details line",
            font=("Segoe UI", 10),
            fg=PALETTE["muted"],
            bg=PALETTE["input"],
            anchor="w",
        )
        self.preview_details.pack(fill="x", padx=14, pady=(10, 0))

        self.preview_state = tk.Label(
            self.preview_card,
            text="State line",
            font=("Segoe UI", 10),
            fg=PALETTE["mint"],
            bg=PALETTE["input"],
            anchor="w",
        )
        self.preview_state.pack(fill="x", padx=14, pady=(4, 14))

        self.options_grid = tk.Frame(self.side_panel, bg=PALETTE["panel"])
        self.options_grid.pack(fill="x", padx=18)

        self._labeled_option(self.options_grid, "Display mode", self.display_mode_var, list(DISPLAY_MODE_OPTIONS.keys()), 0)
        self._labeled_option(self.options_grid, "Activity type", self.activity_type_var, list(ACTIVITY_TYPE_OPTIONS.keys()), 1)

        self.timer_toggle = tk.Checkbutton(
            self.side_panel,
            text="Show elapsed timer",
            variable=self.timer_enabled_var,
            font=("Segoe UI", 10),
            fg=PALETTE["text"],
            bg=PALETTE["panel"],
            activeforeground=PALETTE["text"],
            activebackground=PALETTE["panel"],
            selectcolor=PALETTE["input"],
            highlightthickness=0,
        )
        self.timer_toggle.pack(anchor="w", padx=18, pady=(14, 6))

        self.button_row = tk.Frame(self.side_panel, bg=PALETTE["panel"])
        self.button_row.pack(fill="x", padx=18, pady=(10, 0))

        self.generate_button = tk.Button(
            self.button_row,
            text="Cast Presence",
            command=self.generate_presence,
            font=("Segoe UI Semibold", 12),
            fg=PALETTE["window"],
            bg=PALETTE["text"],
            activeforeground=PALETTE["window"],
            activebackground=PALETTE["amber"],
            relief="flat",
            bd=0,
            padx=26,
            pady=12,
            cursor="hand2",
        )
        self.generate_button.pack(side="left")
        self.generate_button.bind("<Enter>", lambda _event: self.generate_button.configure(bg=PALETTE["amber"]))
        self.generate_button.bind("<Leave>", lambda _event: self.generate_button.configure(bg=PALETTE["text"]))

        self.clear_button = tk.Button(
            self.button_row,
            text="Clear",
            command=self.clear_presence,
            font=("Segoe UI Semibold", 12),
            fg=PALETTE["text"],
            bg=PALETTE["panel_soft"],
            activeforeground=PALETTE["window"],
            activebackground=PALETTE["mint"],
            relief="flat",
            bd=0,
            padx=24,
            pady=12,
            cursor="hand2",
        )
        self.clear_button.pack(side="left", padx=(10, 0))

        self.status_title = tk.Label(
            self.side_panel,
            text="Status",
            font=("Segoe UI Semibold", 10),
            fg=PALETTE["cyan"],
            bg=PALETTE["panel"],
        )
        self.status_title.pack(anchor="w", padx=18, pady=(18, 4))

        self.status_chip = tk.Label(
            self.side_panel,
            textvariable=self.status_var,
            font=("Segoe UI", 11),
            fg=PALETTE["mint"],
            bg=PALETTE["panel"],
            wraplength=246,
            justify="left",
        )
        self.status_chip.pack(anchor="w", padx=18, pady=(0, 18))

    def _make_panel(self, parent: tk.Widget) -> tk.Frame:
        return tk.Frame(parent, bg=PALETTE["panel"], highlightbackground=PALETTE["border"], highlightthickness=1)

    def _section_heading(self, parent: tk.Widget, text: str) -> tk.Label:
        return tk.Label(parent, text=text, font=("Segoe UI Semibold", 11), fg=PALETTE["blue"], bg=parent.cget("bg"))

    def _metric_label(self, parent: tk.Widget, text: str) -> tk.Label:
        return tk.Label(parent, text=text, font=("Segoe UI", 10), fg=PALETTE["soft"], bg=parent.cget("bg"))

    def _add_field(
        self,
        parent: tk.Widget,
        label: str,
        variable: tk.StringVar,
        font: tuple[str, int] | tuple[str, int, str],
        top_padding: int = 0,
        bottom_padding: int = 0,
    ) -> tk.Entry:
        frame = tk.Frame(parent, bg=parent.cget("bg"))
        frame.pack(fill="x", padx=22, pady=(top_padding, bottom_padding))

        tk.Label(
            frame,
            text=label,
            font=("Segoe UI Semibold", 12),
            fg=PALETTE["text"],
            bg=parent.cget("bg"),
        ).pack(anchor="w", pady=(0, 8))

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
        return entry

    def _labeled_option(self, parent: tk.Widget, label: str, variable: tk.StringVar, options: list[str], row: int) -> None:
        frame = tk.Frame(parent, bg=PALETTE["panel"])
        frame.grid(row=row, column=0, sticky="ew", pady=(0, 12))
        parent.grid_columnconfigure(0, weight=1)

        tk.Label(
            frame,
            text=label,
            font=("Segoe UI Semibold", 10),
            fg=PALETTE["text"],
            bg=PALETTE["panel"],
        ).pack(anchor="w", pady=(0, 6))

        menu = tk.OptionMenu(frame, variable, *options)
        menu.configure(
            font=("Segoe UI", 10),
            fg=PALETTE["text"],
            bg=PALETTE["panel_soft"],
            activeforeground=PALETTE["window"],
            activebackground=PALETTE["blue"],
            relief="flat",
            bd=0,
            highlightthickness=0,
            anchor="w",
            padx=10,
        )
        menu["menu"].configure(
            font=("Segoe UI", 10),
            fg=PALETTE["text"],
            bg=PALETTE["panel_soft"],
            activeforeground=PALETTE["window"],
            activebackground=PALETTE["blue"],
            bd=0,
        )
        menu.pack(fill="x")

    def _update_counts(self, *_args: object) -> None:
        self.name_count.configure(text=f"Activity name: {min(len(self.name_var.get()), 128)} / 128")
        self.details_count.configure(text=f"Details: {min(len(self.details_var.get()), 128)} / 128")
        self.state_count.configure(text=f"State: {min(len(self.state_var.get()), 128)} / 128")
        self._update_preview()

    def _update_preview(self, *_args: object) -> None:
        name = self.name_var.get().strip() or "Activity name appears here"
        details = self.details_var.get().strip() or "Details line"
        state = self.state_var.get().strip() or "State line"
        self.preview_name.configure(text=name[:32])
        self.preview_details.configure(text=details[:48])
        self.preview_state.configure(text=state[:48])

    def apply_preset(self, preset: dict[str, str]) -> None:
        self.name_var.set(preset["name"])
        self.details_var.set(preset["details"])
        self.state_var.set(preset["state"])
        self.activity_type_var.set(preset["type"])
        self.display_mode_var.set("Show activity name")
        self.status_var.set(f'Loaded "{preset["label"]}".')
        self.name_entry.focus_set()
        self.name_entry.icursor("end")
        self._update_preview()

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
                    }
            except (OSError, json.JSONDecodeError):
                continue

        return DEFAULT_CONFIG.copy()

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
        pulse = int(170 + 35 * math.sin(self.animation_phase))
        if self.status_chip.cget("fg") not in {PALETTE["rose"], PALETTE["gold"]}:
            self.status_chip.configure(fg=f"#{pulse:02x}{255:02x}{215:02x}")
        self.status_after_id = self.root.after(100, self._start_status_animation)

    def generate_presence(self) -> None:
        activity_name = self.name_var.get().strip()
        details = self.details_var.get().strip()
        state = self.state_var.get().strip()

        if not self.client_id.isdigit():
            messagebox.showerror("Missing Application ID", "config.json does not contain a valid numeric Discord Application ID.")
            return

        if not activity_name:
            messagebox.showerror("Missing Activity Name", "Type the activity name you want PresenceCast to send.")
            return

        try:
            self._ensure_connection()
            display_mode = DISPLAY_MODE_OPTIONS[self.display_mode_var.get()]
            activity_type = ACTIVITY_TYPE_OPTIONS[self.activity_type_var.get()]
            start_time = int(time.time()) if self.timer_enabled_var.get() else None
            self.rpc.update(
                name=activity_name[:128],
                details=details[:128] if details else None,
                state=state[:128] if state else None,
                activity_type=activity_type,
                status_display_type=display_mode,
                start=start_time,
                large_image=self.large_image_key or None,
                large_text=self.large_image_text[:128] if self.large_image_key and self.large_image_text else None,
            )
            self._flash_status(PALETTE["mint"], f'Casting "{activity_name[:44]}".')
            self._update_preview()
        except Exception as exc:
            self._flash_status(PALETTE["rose"], "Discord connection failed.")
            messagebox.showerror(
                "Discord RPC Error",
                "Discord must be open on your PC, and your Application ID in config.json must be valid.\n\n"
                f"Error: {exc}",
            )

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
