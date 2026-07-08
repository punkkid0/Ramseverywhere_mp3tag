import io
import logging
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk
from PIL import Image

from app.models import AppState
from app.services import (
    apply_to_songs,
    build_previews,
    enrich_songs_with_existing,
    list_mp3_items_from_file,
    list_mp3_items_from_folder,
    validate_cover,
)
from app.gui_settings import GuiSettings
from app.settings_dialog import SettingsDialog
from app.theme import ThemeManager
from core.auto_tag import TagJobOptions
from core.config import AppConfig
from core.paths import icon_path
from core.remux import ffmpeg_available

logger = logging.getLogger(__name__)

STATUS_LABELS = {
    "ready": "Current",
    "preview": "Preview",
    "updated": "Updated",
    "failed": "Failed",
    "skipped": "Skipped",
}


class Mp3TagApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.gui_settings = GuiSettings.load()
        self.theme = ThemeManager(self.gui_settings)
        self.theme.apply_global()
        self.palette = self.theme.palette

        self.config_data = AppConfig.load()
        self.app_state = AppState()
        self._cancel_requested = False
        self._busy = False
        self.last_result = None
        self._song_index_by_item: dict[str, int] = {}
        self._cover_path = ""
        self._cover_ctk_image = None
        self._detail_cover_image = None
        self._primary_buttons: list[ctk.CTkButton] = []
        self._panels: list[ctk.CTkFrame] = []
        self._muted_labels: list[ctk.CTkLabel] = []

        self.title("Ramseverywhere MP3 Tag")
        self.geometry("1200x760")
        self.minsize(900, 600)
        self.configure(fg_color=self.palette.bg)

        self._build_layout()
        self._apply_theme()
        self._set_window_icon()
        self._set_status("Choose a music folder or a single MP3 file to get started.")

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # --- Music source ---
        folder_frame = ctk.CTkFrame(self)
        self._panels.append(folder_frame)
        folder_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        folder_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(folder_frame, text="Music:", width=100).grid(
            row=0, column=0, padx=(12, 8), pady=12, sticky="w"
        )
        self.source_var = tk.StringVar()
        ctk.CTkEntry(folder_frame, textvariable=self.source_var).grid(
            row=0, column=1, padx=8, pady=12, sticky="ew"
        )
        browse_folder_btn = ctk.CTkButton(
            folder_frame, text="Browse folder", width=110, command=self._browse_folder
        )
        browse_folder_btn.grid(row=0, column=2, padx=8, pady=12)
        self._primary_buttons.append(browse_folder_btn)
        browse_file_btn = ctk.CTkButton(
            folder_frame, text="Browse file", width=100, command=self._browse_file
        )
        browse_file_btn.grid(row=0, column=3, padx=8, pady=12)
        self._primary_buttons.append(browse_file_btn)
        settings_btn = ctk.CTkButton(
            folder_frame, text="Settings", width=90, command=self._open_settings
        )
        settings_btn.grid(row=0, column=4, padx=(8, 12), pady=12)
        self._primary_buttons.append(settings_btn)
        hint_label = ctk.CTkLabel(
            folder_frame,
            text="Folder = album/bulk  |  File = single song",
            anchor="w",
        )
        hint_label.grid(row=1, column=0, columnspan=2, sticky="w", padx=12, pady=(0, 6))
        self._muted_labels.append(hint_label)
        self.chip_label = ctk.CTkLabel(
            folder_frame, text=self._chip_text(), anchor="e"
        )
        self.chip_label.grid(row=1, column=2, columnspan=3, sticky="e", padx=12, pady=(0, 10))

        # --- Tag options ---
        opts = ctk.CTkFrame(self)
        self._panels.append(opts)
        opts.grid(row=1, column=0, sticky="ew", padx=16, pady=8)
        for col in (1, 3, 5, 7):
            opts.grid_columnconfigure(col, weight=1)

        ctk.CTkLabel(
            opts, text="Tag options", font=ctk.CTkFont(weight="bold")
        ).grid(row=0, column=0, columnspan=8, sticky="w", padx=12, pady=(12, 8))

        self.artist_var = tk.StringVar()
        self.genre_var = tk.StringVar()
        self.year_var = tk.StringVar()
        self.album_var = tk.StringVar()
        self.track_var = tk.StringVar()
        self.cover_display_var = tk.StringVar(value="Keeping existing cover on songs")
        self.mode_var = tk.StringVar(value="auto")

        fields = [
            ("Artist", self.artist_var, 0, 1),
            ("Genre", self.genre_var, 2, 3),
            ("Year", self.year_var, 4, 5),
            ("Mode", self.mode_var, 6, 7),
        ]
        for label, var, label_col, entry_col in fields[:3]:
            ctk.CTkLabel(opts, text=f"{label}:").grid(
                row=1, column=label_col, padx=(12, 6), pady=6, sticky="e"
            )
            placeholder = "Uses file tag if blank" if var is self.artist_var else ""
            ctk.CTkEntry(opts, textvariable=var, placeholder_text=placeholder).grid(
                row=1, column=entry_col, padx=6, pady=6, sticky="ew"
            )

        ctk.CTkLabel(opts, text="Mode:").grid(row=1, column=6, padx=(12, 6), pady=6, sticky="e")
        self.mode_menu = ctk.CTkOptionMenu(
            opts,
            variable=self.mode_var,
            values=["auto", "single", "album"],
            width=120,
        )
        self.mode_menu.grid(row=1, column=7, padx=6, pady=6, sticky="ew")

        ctk.CTkLabel(opts, text="Album:").grid(row=2, column=0, padx=(12, 6), pady=6, sticky="e")
        ctk.CTkEntry(opts, textvariable=self.album_var).grid(
            row=2, column=1, padx=6, pady=6, sticky="ew"
        )
        ctk.CTkLabel(opts, text="Track:").grid(row=2, column=2, padx=(12, 6), pady=6, sticky="e")
        ctk.CTkEntry(opts, textvariable=self.track_var).grid(
            row=2, column=3, padx=6, pady=6, sticky="ew"
        )

        self.use_custom_cover_var = tk.BooleanVar(value=False)

        ctk.CTkLabel(opts, text="Cover art:").grid(
            row=3, column=0, padx=(12, 6), pady=(6, 12), sticky="ne"
        )
        self.cover_thumb = ctk.CTkLabel(
            opts,
            text="♪",
            width=72,
            height=72,
            fg_color="#1a1a1a",
            corner_radius=6,
            text_color="#666666",
        )
        self.cover_thumb.grid(row=3, column=1, padx=6, pady=(6, 12), sticky="nw")

        cover_info = ctk.CTkFrame(opts, fg_color="transparent")
        cover_info.grid(row=3, column=2, columnspan=5, padx=6, pady=(6, 12), sticky="w")
        self.replace_cover_check = ctk.CTkCheckBox(
            cover_info,
            text="Replace cover art (optional)",
            variable=self.use_custom_cover_var,
            command=self._toggle_cover_controls,
        )
        self.replace_cover_check.pack(anchor="w")
        ctk.CTkLabel(
            cover_info,
            textvariable=self.cover_display_var,
            anchor="w",
            font=ctk.CTkFont(weight="bold"),
        ).pack(anchor="w", pady=(4, 0))
        cover_hint = ctk.CTkLabel(
            cover_info,
            text="Off = keep the image already downloaded with each song",
            anchor="w",
        )
        cover_hint.pack(anchor="w", pady=(2, 8))
        self._muted_labels.append(cover_hint)
        cover_buttons = ctk.CTkFrame(cover_info, fg_color="transparent")
        cover_buttons.pack(anchor="w")
        self.select_cover_btn = ctk.CTkButton(
            cover_buttons,
            text="Select image...",
            width=120,
            command=self._browse_cover,
            state="disabled",
        )
        self.select_cover_btn.pack(side="left", padx=(0, 8))
        self._primary_buttons.append(self.select_cover_btn)
        self.clear_cover_btn = ctk.CTkButton(
            cover_buttons,
            text="Clear",
            width=70,
            fg_color="#555555",
            hover_color="#666666",
            command=self._clear_cover,
            state="disabled",
        )
        self.clear_cover_btn.pack(side="left")

        # --- Actions ---
        actions = ctk.CTkFrame(self)
        self._panels.append(actions)
        actions.grid(row=2, column=0, sticky="ew", padx=16, pady=8)
        actions.grid_columnconfigure(4, weight=1)

        preview_btn = ctk.CTkButton(actions, text="Preview changes", command=self._preview)
        preview_btn.grid(row=0, column=0, padx=(12, 8), pady=12)
        self._primary_buttons.append(preview_btn)
        apply_btn = ctk.CTkButton(actions, text="Apply tags", command=self._apply)
        apply_btn.grid(row=0, column=1, padx=8, pady=12)
        self._primary_buttons.append(apply_btn)
        select_all_btn = ctk.CTkButton(actions, text="Select all", width=90, command=self._select_all)
        select_all_btn.grid(row=0, column=2, padx=8, pady=12)
        self._primary_buttons.append(select_all_btn)
        select_none_btn = ctk.CTkButton(actions, text="Select none", width=90, command=self._select_none)
        select_none_btn.grid(row=0, column=3, padx=8, pady=12)
        self._primary_buttons.append(select_none_btn)
        self.selection_label = ctk.CTkLabel(actions, text="0 songs")
        self.selection_label.grid(row=0, column=4, padx=12, pady=12, sticky="e")
        self.cancel_button = ctk.CTkButton(
            actions,
            text="Cancel",
            fg_color="#8b3a3a",
            hover_color="#a84b4b",
            command=self._request_cancel,
            state="disabled",
        )
        self.cancel_button.grid(row=0, column=5, padx=(8, 12), pady=12)

        # --- Song table + detail (layout unchanged — colours applied via theme) ---
        table_frame = ctk.CTkFrame(self)
        self._panels.append(table_frame)
        table_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=8)
        table_frame.grid_columnconfigure(0, weight=3)
        table_frame.grid_columnconfigure(1, weight=0)
        table_frame.grid_rowconfigure(0, weight=1)

        self._tree_style = ttk.Style()

        columns = (
            "filename",
            "title",
            "artist",
            "album",
            "genre",
            "year",
            "mode",
            "cover",
            "status",
        )
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="extended",
            style="Songs.Treeview",
        )
        for key, label, width in [
            ("filename", "Filename", 180),
            ("title", "Title", 140),
            ("artist", "Artist", 100),
            ("album", "Album", 110),
            ("genre", "Genre", 80),
            ("year", "Year", 50),
            ("mode", "Mode", 60),
            ("cover", "Cover", 50),
            ("status", "Status", 80),
        ]:
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, anchor="w")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        detail = ctk.CTkFrame(table_frame, width=260)
        self.detail_panel = detail
        self._panels.append(detail)
        detail.grid(row=0, column=2, sticky="nsew", padx=(10, 0))
        detail.grid_propagate(False)

        ctk.CTkLabel(
            detail, text="Song details", font=ctk.CTkFont(weight="bold")
        ).pack(anchor="w", padx=12, pady=(12, 8))

        self.detail_cover = ctk.CTkLabel(
            detail,
            text="No cover",
            width=140,
            height=140,
            fg_color="#1a1a1a",
            corner_radius=8,
        )
        self.detail_cover.pack(padx=12, pady=(0, 10))

        self.detail_filename = ctk.CTkLabel(
            detail, text="Select a song", anchor="w", wraplength=230
        )
        self.detail_filename.pack(anchor="w", padx=12, pady=(0, 6))

        self.detail_tags = ctk.CTkTextbox(detail, height=220, activate_scrollbars=True)
        self.detail_tags.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.detail_tags.configure(state="disabled")

        # --- Bottom ---
        bottom = ctk.CTkFrame(self)
        self._panels.append(bottom)
        bottom.grid(row=4, column=0, sticky="ew", padx=16, pady=(8, 16))
        bottom.grid_columnconfigure(0, weight=1)

        self.progress = ctk.CTkProgressBar(bottom)
        self.progress.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        self.progress.set(0)

        self.status_label = ctk.CTkLabel(bottom, text="", anchor="w")
        self.status_label.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))

        self.summary_label = ctk.CTkLabel(
            bottom, text="Updated: 0  Failed: 0  Remuxed: 0", anchor="w", text_color="#b0b0b0"
        )
        self.summary_label.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))

    def _set_window_icon(self) -> None:
        path = icon_path()
        if not path:
            return
        try:
            self.iconbitmap(default=str(path))
        except Exception as exc:
            logger.debug("Could not set window icon: %s", exc)

    def _apply_theme(self) -> None:
        self.palette = self.theme.palette
        self.configure(fg_color=self.palette.bg)

        for panel in self._panels:
            panel.configure(fg_color=self.palette.surface, border_color=self.palette.border)

        self.chip_label.configure(text_color=self.palette.text_subtle)
        self.status_label.configure(text_color=self.palette.text)
        self.summary_label.configure(text_color=self.palette.text_subtle)
        self.selection_label.configure(text_color=self.palette.text_muted)

        for label in self._muted_labels:
            label.configure(text_color=self.palette.text_subtle)

        for button in self._primary_buttons:
            button.configure(
                fg_color=self.palette.accent,
                hover_color=self.palette.accent_hover,
                text_color=self.palette.table_select_fg,
            )

        self.cancel_button.configure(
            fg_color=self.palette.danger,
            hover_color=self.palette.danger_hover,
        )
        self.clear_cover_btn.configure(
            fg_color=self.palette.secondary_btn,
            hover_color=self.palette.secondary_btn_hover,
        )

        self.cover_thumb.configure(
            fg_color=self.palette.thumb_bg,
            text_color=self.palette.text_subtle,
        )
        self.detail_cover.configure(
            fg_color=self.palette.thumb_bg,
            text_color=self.palette.text_subtle,
        )
        self.progress.configure(progress_color=self.palette.accent)

        if hasattr(self, "mode_menu"):
            self.mode_menu.configure(
                fg_color=self.palette.accent,
                button_color=self.palette.accent_hover,
                button_hover_color=self.palette.accent_hover,
                text_color=self.palette.table_select_fg,
            )

        self._style_tree()
        if self.app_state.songs:
            self._refresh_tree()

    def _style_tree(self) -> None:
        p = self.palette
        self._tree_style.theme_use("clam")
        self._tree_style.configure(
            "Songs.Treeview",
            background=p.table_bg,
            foreground=p.table_fg,
            fieldbackground=p.table_bg,
            rowheight=30,
        )
        self._tree_style.configure(
            "Songs.Treeview.Heading",
            background=p.table_head_bg,
            foreground=p.table_head_fg,
        )
        self._tree_style.map(
            "Songs.Treeview",
            background=[("selected", p.table_select_bg)],
            foreground=[("selected", p.table_select_fg)],
        )

    def _on_theme_change(self, settings: GuiSettings) -> None:
        self.gui_settings = settings
        self.theme.refresh(settings)
        self.chip_label.configure(text=self._chip_text())
        self._apply_theme()

    def _chip_text(self) -> str:
        ffmpeg_status = "available" if ffmpeg_available(self.config_data.ffmpeg_path) else "missing"
        return (
            f"{self.palette.name}  |  ffmpeg: {ffmpeg_status}  |  "
            f"cover: {self.config_data.cover_size}px"
        )

    def _set_status(self, text: str) -> None:
        self.status_label.configure(text=text)

    def _job_options(self) -> TagJobOptions:
        return TagJobOptions(
            artist=self.artist_var.get().strip(),
            genre=self.genre_var.get().strip(),
            year=self.year_var.get().strip(),
            album=self.album_var.get().strip(),
            track=self.track_var.get().strip(),
            mode=self.mode_var.get().strip(),
            cover=self._cover_path if self.use_custom_cover_var.get() else "",
        )

    def _browse_folder(self) -> None:
        folder = filedialog.askdirectory(parent=self, title="Select music folder")
        if folder:
            self._load_source(folder, "folder")

    def _browse_file(self) -> None:
        initial = self.app_state.folder or str(Path.home())
        file_path = filedialog.askopenfilename(
            parent=self,
            title="Select MP3 file",
            initialdir=initial,
            filetypes=[("MP3 files", "*.mp3"), ("All files", "*.*")],
        )
        if file_path:
            self._load_source(file_path, "file")

    def _load_source(self, path: str, source_type: str) -> None:
        try:
            if source_type == "folder":
                songs = list_mp3_items_from_folder(path)
                label = f"Folder: {path}"
            else:
                songs = list_mp3_items_from_file(path)
                label = f"File: {Path(path).name}"
        except ValueError as exc:
            messagebox.showerror("Could not load", str(exc))
            return

        if not songs:
            messagebox.showwarning("No MP3 files", "No MP3 files found in that location.")
            return

        self.app_state.source_path = path
        self.app_state.source_type = source_type
        self.source_var.set(label)
        self.app_state.songs = songs
        enrich_songs_with_existing(self.app_state.songs)
        for song in self.app_state.songs:
            song.selected = True
        self._refresh_tree(select_first=True)
        count = len(self.app_state.songs)
        kind = "file" if source_type == "file" else "songs"
        self._set_status(f"Loaded {count} {kind}. Preview or Apply tags when ready.")
        self.selection_label.configure(text=f"{count} selected")

    def _toggle_cover_controls(self) -> None:
        enabled = self.use_custom_cover_var.get()
        state = "normal" if enabled else "disabled"
        self.select_cover_btn.configure(state=state)
        self.clear_cover_btn.configure(state=state)
        if not enabled:
            self._clear_cover(keep_checkbox=True)
            self.cover_display_var.set("Keeping existing cover on songs")
            self.cover_thumb.configure(text="♪")

    def _browse_cover(self) -> None:
        if not self.use_custom_cover_var.get():
            return
        initial = self.app_state.folder or str(Path.home())
        path = filedialog.askopenfilename(
            parent=self,
            title="Select cover image",
            initialdir=initial,
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.webp *.gif *.bmp"),
                ("JPEG", "*.jpg *.jpeg"),
                ("PNG", "*.png"),
                ("All files", "*.*"),
            ],
        )
        if path:
            self._set_cover_image(path)

    def _set_cover_image(self, path: str) -> None:
        self.use_custom_cover_var.set(True)
        self._toggle_cover_controls()
        self._cover_path = path
        self.cover_display_var.set(Path(path).name)
        try:
            with Image.open(path) as image:
                thumb = image.copy()
                thumb.thumbnail((72, 72))
                self._cover_ctk_image = ctk.CTkImage(thumb, size=(72, 72))
            self.cover_thumb.configure(image=self._cover_ctk_image, text="")
        except Exception as exc:
            logger.warning("Could not preview cover: %s", exc)
            self.cover_thumb.configure(image=None, text="IMG")

    def _clear_cover(self, keep_checkbox: bool = False) -> None:
        self._cover_path = ""
        self._cover_ctk_image = None
        self.cover_thumb.configure(image=None)
        if self.use_custom_cover_var.get():
            self.cover_display_var.set("No image selected yet")
            self.cover_thumb.configure(text="—")
        else:
            self.cover_display_var.set("Keeping existing cover on songs")
            self.cover_thumb.configure(text="♪")

    def _refresh_tree(self, select_first: bool = False) -> None:
        keep_indices = [] if select_first else self._selected_indices()
        self.tree.delete(*self.tree.get_children())
        self._song_index_by_item.clear()

        for index, song in enumerate(self.app_state.songs):
            values = (
                song.filename,
                song.field("title"),
                song.field("artist"),
                song.field("album"),
                song.field("genre"),
                song.field("year"),
                song.mode,
                "Yes" if song.has_cover else "—",
                STATUS_LABELS.get(song.status, song.status),
            )
            item_id = self.tree.insert("", "end", values=values)
            self._song_index_by_item[item_id] = index
            if not song.selected:
                self.tree.item(item_id, tags=("unselected",))
            elif song.status == "failed":
                self.tree.item(item_id, tags=("failed",))
            elif song.status in {"updated", "preview"}:
                self.tree.item(item_id, tags=("ok",))

        self.tree.tag_configure("failed", foreground=self.palette.danger)
        self.tree.tag_configure("ok", foreground=self.palette.success)
        self.tree.tag_configure("unselected", foreground=self.palette.text_subtle)

        if select_first and self.app_state.songs:
            children = self.tree.get_children()
            if children:
                self.tree.selection_set(children[0])
                self.tree.focus(children[0])
                self._update_detail_panel(self.app_state.songs[0])
        elif keep_indices:
            restore = [
                item_id
                for item_id, idx in self._song_index_by_item.items()
                if idx in keep_indices
            ]
            if restore:
                self.tree.selection_set(restore)
                self._update_detail_panel(self.app_state.songs[keep_indices[0]])
        elif not self.app_state.songs:
            self._clear_detail_panel()

    def _clear_detail_panel(self) -> None:
        self._detail_cover_image = None
        self.detail_cover.configure(image=None, text="No cover")
        self.detail_filename.configure(text="Select a song")
        self.detail_tags.configure(state="normal")
        self.detail_tags.delete("1.0", "end")
        self.detail_tags.configure(state="disabled")

    def _update_detail_panel(self, song) -> None:
        self.detail_filename.configure(text=song.filename)

        if song.cover_bytes:
            try:
                with Image.open(io.BytesIO(song.cover_bytes)) as image:
                    thumb = image.copy()
                    thumb.thumbnail((140, 140))
                    self._detail_cover_image = ctk.CTkImage(thumb, size=(140, 140))
                self.detail_cover.configure(image=self._detail_cover_image, text="")
            except Exception as exc:
                logger.warning("Could not show embedded cover: %s", exc)
                self._detail_cover_image = None
                self.detail_cover.configure(image=None, text="Cover")
        else:
            self._detail_cover_image = None
            self.detail_cover.configure(image=None, text="No cover")

        lines = [f"Status: {STATUS_LABELS.get(song.status, song.status)}"]
        if song.message:
            lines.append(f"Note: {song.message}")
        lines.append("")

        field_labels = [
            ("title", "Title"),
            ("artist", "Artist"),
            ("album", "Album"),
            ("album_artist", "Album artist"),
            ("track", "Track"),
            ("genre", "Genre"),
            ("year", "Year"),
            ("comment", "Comment"),
        ]
        display = song.display
        for key, label in field_labels:
            value = display.get(key, "")
            lines.append(f"{label}: {value or '—'}")

        if song.preview and song.existing:
            changes = []
            for key, label in field_labels:
                before = song.existing.get(key, "")
                after = song.preview.after.get(key, "")
                if before != after:
                    changes.append(f"{label}: {before or '—'} → {after or '—'}")
            if changes:
                lines.append("")
                lines.append("Changes from current:")
                lines.extend(changes)

        self.detail_tags.configure(state="normal")
        self.detail_tags.delete("1.0", "end")
        self.detail_tags.insert("1.0", "\n".join(lines))
        self.detail_tags.configure(state="disabled")

    def _selected_indices(self) -> list[int]:
        indices = []
        for item_id in self.tree.selection():
            index = self._song_index_by_item.get(item_id)
            if index is not None:
                indices.append(index)
        return sorted(set(indices))

    def _on_select(self, _event=None) -> None:
        indices = self._selected_indices()
        selected = set(indices)
        for index, song in enumerate(self.app_state.songs):
            song.selected = index in selected
        count = sum(1 for song in self.app_state.songs if song.selected)
        self.selection_label.configure(text=f"{count} selected")
        if indices:
            self._update_detail_panel(self.app_state.songs[indices[0]])
        else:
            self._clear_detail_panel()

    def _select_all(self) -> None:
        self.tree.selection_set(self.tree.get_children())
        for song in self.app_state.songs:
            song.selected = True
        self.selection_label.configure(text=f"{len(self.app_state.songs)} selected")

    def _select_none(self) -> None:
        self.tree.selection_remove(self.tree.get_children())
        for song in self.app_state.songs:
            song.selected = False
        self.selection_label.configure(text="0 selected")

    def _validate_form(self) -> bool:
        if not self.app_state.songs:
            messagebox.showwarning(
                "No music selected",
                "Choose a folder (album/bulk) or a single MP3 file first.",
            )
            return False
        if self.use_custom_cover_var.get():
            if not self._cover_path:
                messagebox.showwarning(
                    "Cover optional",
                    "Select an image, or uncheck 'Replace cover art' to keep "
                    "the covers already on the songs.",
                )
                return False
            cover_error = validate_cover(self.app_state.songs, self._cover_path)
            if cover_error:
                messagebox.showerror("Cover not found", cover_error)
                return False
        return True

    def _preview(self) -> None:
        if not self._validate_form():
            return
        options = self._job_options()
        build_previews(self.app_state.songs, options, self.config_data)
        self._refresh_tree()
        indices = self._selected_indices()
        if indices:
            self._update_detail_panel(self.app_state.songs[indices[0]])
        self._set_status("Preview ready — no files were modified. Click Apply tags to write.")

    def _sync_selection_from_tree(self) -> None:
        selected = set(self._selected_indices())
        if selected:
            for index, song in enumerate(self.app_state.songs):
                song.selected = index in selected

    def _apply(self) -> None:
        if not self._validate_form():
            return
        self._sync_selection_from_tree()
        selected_count = sum(1 for s in self.app_state.songs if s.selected)
        if selected_count == 0:
            messagebox.showwarning("No selection", "Select at least one song.")
            return
        if not messagebox.askyesno(
            "Apply tags",
            f"Apply tags to {selected_count} song(s)?\n\nBackups (.bak) will be created.",
        ):
            return
        self._start_job(dry_run=False)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        self.cancel_button.configure(state="normal" if busy else "disabled")

    def _request_cancel(self) -> None:
        self._cancel_requested = True
        self._set_status("Cancelling after current file...")

    def _start_job(self, dry_run: bool) -> None:
        if self._busy:
            return
        self._cancel_requested = False
        self._set_busy(True)
        options = self._job_options()

        def worker():
            try:
                def on_progress(done, total, filename):
                    self.after(0, lambda: self._update_progress(done, total, filename))

                result = apply_to_songs(
                    self.app_state.songs,
                    options,
                    self.config_data,
                    dry_run=dry_run,
                    on_progress=on_progress,
                    should_cancel=lambda: self._cancel_requested,
                )
                self.after(0, lambda: self._finish_job(result))
            except Exception as exc:
                self.after(0, lambda: self._finish_error(str(exc)))

        threading.Thread(target=worker, daemon=True).start()

    def _update_progress(self, done: int, total: int, filename: str) -> None:
        self.progress.set(done / total if total else 0)
        self._set_status(f"Processing {done}/{total}: {filename}")

    def _finish_job(self, result) -> None:
        self.last_result = result
        self._set_busy(False)
        self.progress.set(1 if result.updated else 0)
        self._refresh_tree()
        indices = self._selected_indices()
        if indices:
            self._update_detail_panel(self.app_state.songs[indices[0]])
        self.summary_label.configure(
            text=(
                f"Updated: {len(result.updated)}  "
                f"Skipped: {len(result.skipped)}  "
                f"Failed: {len(result.failed)}  "
                f"Remuxed: {len(result.remuxed)}"
            )
        )
        self._set_status(
            "Tags applied successfully." if not result.failed else "Finished with some errors."
        )

    def _finish_error(self, message: str) -> None:
        self._set_busy(False)
        messagebox.showerror("Error", message)
        self._set_status(message)

    def _open_settings(self) -> None:
        summary = (
            f"site_names: (edit in config.yaml)\n"
            f"comment: {self.config_data.default_comment}\n"
            f"cover.size: {self.config_data.cover_size}\n"
            f"cover.quality: {self.config_data.cover_quality}\n"
            f"ffmpeg.path: {self.config_data.ffmpeg_path}\n"
        )
        SettingsDialog(
            self,
            summary,
            self.gui_settings,
            on_theme_change=self._on_theme_change,
        )