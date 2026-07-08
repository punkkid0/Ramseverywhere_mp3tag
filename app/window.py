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
    list_mp3_items,
    validate_cover,
)
from app.settings_dialog import SettingsDialog
from core.auto_tag import TagJobOptions
from core.config import AppConfig
from core.remux import ffmpeg_available

logger = logging.getLogger(__name__)


class Mp3TagApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config_data = AppConfig.load()
        self.app_state = AppState()
        self._cancel_requested = False
        self._busy = False
        self.last_result = None
        self._song_index_by_item: dict[str, int] = {}
        self._cover_path = ""
        self._cover_ctk_image = None

        self.title("Ramseverywhere MP3 Tag")
        self.geometry("1100x720")
        self.minsize(900, 600)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self._build_layout()
        self._set_status("Choose a music folder to get started.")

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(3, weight=1)

        # --- Folder row ---
        folder_frame = ctk.CTkFrame(self)
        folder_frame.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        folder_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(folder_frame, text="Music folder:", width=100).grid(
            row=0, column=0, padx=(12, 8), pady=12, sticky="w"
        )
        self.folder_var = tk.StringVar()
        ctk.CTkEntry(folder_frame, textvariable=self.folder_var).grid(
            row=0, column=1, padx=8, pady=12, sticky="ew"
        )
        ctk.CTkButton(folder_frame, text="Browse", width=90, command=self._browse_folder).grid(
            row=0, column=2, padx=8, pady=12
        )
        ctk.CTkButton(folder_frame, text="Settings", width=90, command=self._open_settings).grid(
            row=0, column=3, padx=(8, 12), pady=12
        )
        self.chip_label = ctk.CTkLabel(
            folder_frame, text=self._chip_text(), anchor="e", text_color="#9cdcfe"
        )
        self.chip_label.grid(row=1, column=0, columnspan=4, sticky="e", padx=12, pady=(0, 10))

        # --- Tag options ---
        opts = ctk.CTkFrame(self)
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
            ("Artist *", self.artist_var, 0, 1),
            ("Genre", self.genre_var, 2, 3),
            ("Year", self.year_var, 4, 5),
            ("Mode", self.mode_var, 6, 7),
        ]
        for label, var, label_col, entry_col in fields[:3]:
            ctk.CTkLabel(opts, text=f"{label}:").grid(
                row=1, column=label_col, padx=(12, 6), pady=6, sticky="e"
            )
            ctk.CTkEntry(opts, textvariable=var).grid(
                row=1, column=entry_col, padx=6, pady=6, sticky="ew"
            )

        ctk.CTkLabel(opts, text="Mode:").grid(row=1, column=6, padx=(12, 6), pady=6, sticky="e")
        ctk.CTkOptionMenu(
            opts,
            variable=self.mode_var,
            values=["auto", "single", "album"],
            width=120,
        ).grid(row=1, column=7, padx=6, pady=6, sticky="ew")

        ctk.CTkLabel(opts, text="Album:").grid(row=2, column=0, padx=(12, 6), pady=6, sticky="e")
        ctk.CTkEntry(opts, textvariable=self.album_var).grid(
            row=2, column=1, padx=6, pady=6, sticky="ew"
        )
        ctk.CTkLabel(opts, text="Track:").grid(row=2, column=2, padx=(12, 6), pady=6, sticky="e")
        ctk.CTkEntry(opts, textvariable=self.track_var).grid(
            row=2, column=3, padx=6, pady=6, sticky="ew"
        )

        self.use_custom_cover_var = tk.BooleanVar(value=False)
        self.cover_display_var.set("Keeping existing cover on songs")

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
        ctk.CTkLabel(
            cover_info,
            text="Off = keep the image already downloaded with each song",
            text_color="#888888",
            anchor="w",
        ).pack(anchor="w", pady=(2, 8))
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
        actions.grid(row=2, column=0, sticky="ew", padx=16, pady=8)
        actions.grid_columnconfigure(4, weight=1)

        ctk.CTkButton(actions, text="Preview changes", command=self._preview).grid(
            row=0, column=0, padx=(12, 8), pady=12
        )
        ctk.CTkButton(actions, text="Apply tags", command=self._apply).grid(
            row=0, column=1, padx=8, pady=12
        )
        ctk.CTkButton(actions, text="Select all", width=90, command=self._select_all).grid(
            row=0, column=2, padx=8, pady=12
        )
        ctk.CTkButton(actions, text="Select none", width=90, command=self._select_none).grid(
            row=0, column=3, padx=8, pady=12
        )
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

        # --- Song table ---
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=3, column=0, sticky="nsew", padx=16, pady=8)
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Songs.Treeview",
            background="#2b2b2b",
            foreground="#f2f2f2",
            fieldbackground="#2b2b2b",
            rowheight=28,
        )
        style.configure("Songs.Treeview.Heading", background="#1f1f1f", foreground="#ffffff")
        style.map("Songs.Treeview", background=[("selected", "#1f6aa5")])

        columns = ("filename", "title", "artist", "album", "mode", "status")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="extended",
            style="Songs.Treeview",
        )
        for key, label, width in [
            ("filename", "Filename", 220),
            ("title", "Title", 180),
            ("artist", "Artist", 120),
            ("album", "Album", 140),
            ("mode", "Mode", 70),
            ("status", "Status", 100),
        ]:
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, anchor="w")

        scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self._on_select)

        # --- Bottom ---
        bottom = ctk.CTkFrame(self)
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

    def _chip_text(self) -> str:
        ffmpeg_status = "available" if ffmpeg_available(self.config_data.ffmpeg_path) else "missing"
        return f"ffmpeg: {ffmpeg_status}  |  cover size: {self.config_data.cover_size}px"

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
        folder = filedialog.askdirectory(title="Select music folder")
        if folder:
            self._load_folder(folder)

    def _load_folder(self, folder: str) -> None:
        self.app_state.folder = folder
        self.folder_var.set(folder)
        self.app_state.songs = list_mp3_items(folder)
        for song in self.app_state.songs:
            song.selected = True
        self._refresh_tree()
        self._set_status(f"Loaded {len(self.app_state.songs)} song(s). Fill artist, then Preview or Apply.")
        self.selection_label.configure(text=f"{len(self.app_state.songs)} songs")

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

    def _refresh_tree(self) -> None:
        self.tree.delete(*self.tree.get_children())
        self._song_index_by_item.clear()

        for index, song in enumerate(self.app_state.songs):
            preview = song.preview
            values = (
                song.filename,
                song.title_after,
                song.artist_after,
                preview.after.get("album", "") if preview else "",
                song.mode,
                song.status,
            )
            item_id = self.tree.insert("", "end", values=values)
            self._song_index_by_item[item_id] = index
            if not song.selected:
                self.tree.item(item_id, tags=("unselected",))
            elif song.status == "failed":
                self.tree.item(item_id, tags=("failed",))
            elif song.status in {"updated", "preview"}:
                self.tree.item(item_id, tags=("ok",))

        self.tree.tag_configure("failed", foreground="#ff7b7b")
        self.tree.tag_configure("ok", foreground="#7dffb2")
        self.tree.tag_configure("unselected", foreground="#888888")

    def _selected_indices(self) -> list[int]:
        indices = []
        for item_id in self.tree.selection():
            index = self._song_index_by_item.get(item_id)
            if index is not None:
                indices.append(index)
        return sorted(set(indices))

    def _on_select(self, _event=None) -> None:
        selected = set(self._selected_indices())
        for index, song in enumerate(self.app_state.songs):
            song.selected = index in selected
        count = sum(1 for song in self.app_state.songs if song.selected)
        self.selection_label.configure(text=f"{count} selected")

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
        if not self.app_state.folder:
            messagebox.showwarning("No folder", "Choose a music folder first.")
            return False
        if not self.artist_var.get().strip():
            messagebox.showwarning("Artist required", "Enter an artist name.")
            return False
        if not self.app_state.songs:
            messagebox.showwarning("No songs", "No MP3 files found in that folder.")
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
        self.summary_label.configure(
            text=(
                f"Updated: {len(result.updated)}  "
                f"Skipped: {len(result.skipped)}  "
                f"Failed: {len(result.failed)}  "
                f"Remuxed: {len(result.remuxed)}"
            )
        )
        self._set_status("Tags applied successfully." if not result.failed else "Finished with some errors.")

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
        SettingsDialog(self, summary)