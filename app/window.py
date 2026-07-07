import logging
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import customtkinter as ctk

from app.models import AppState, SongRow
from app.services import (
    apply_songs,
    default_csv_path,
    load_library,
    save_library,
    sync_library,
)
from app.settings_dialog import SettingsDialog
from core.config import AppConfig
from core.remux import ffmpeg_available

logger = logging.getLogger(__name__)

STATUS_LABELS = {
    "pending": "Pending",
    "updated": "Updated",
    "failed": "Failed",
    "skipped": "Skipped",
    "remuxed": "Remuxed",
}


class Mp3TagApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.config_data = AppConfig.load()
        self.library = AppState()
        self._cancel_requested = False
        self._busy = False
        self._status_filter = "all"
        self._search_text = ""

        self.title("MP3 Tag Editor")
        self.geometry("1180x760")
        self.minsize(960, 640)
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")

        self._build_layout()
        self._show_empty_state()

    def _build_layout(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        top = ctk.CTkFrame(self)
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 8))
        top.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(top, text="Music folder:", width=100, anchor="w").grid(
            row=0, column=0, padx=(12, 8), pady=12, sticky="w"
        )
        self.folder_var = tk.StringVar()
        ctk.CTkEntry(top, textvariable=self.folder_var).grid(
            row=0, column=1, padx=8, pady=12, sticky="ew"
        )
        ctk.CTkButton(top, text="Browse", width=90, command=self._browse_folder).grid(
            row=0, column=2, padx=8, pady=12
        )
        ctk.CTkButton(top, text="Sync folder", width=110, command=self._sync_folder).grid(
            row=0, column=3, padx=8, pady=12
        )
        ctk.CTkButton(top, text="Settings", width=90, command=self._open_settings).grid(
            row=0, column=4, padx=(8, 12), pady=12
        )

        self.status_chip = ctk.CTkLabel(
            top,
            text=self._chip_text(),
            anchor="e",
            text_color="#9cdcfe",
        )
        self.status_chip.grid(row=1, column=0, columnspan=5, sticky="e", padx=12, pady=(0, 10))

        toolbar = ctk.CTkFrame(self)
        toolbar.grid(row=1, column=0, sticky="ew", padx=16, pady=8)
        toolbar.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(toolbar, text="Search:").grid(row=0, column=0, padx=(12, 6), pady=10)
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self._on_search_changed())
        ctk.CTkEntry(toolbar, textvariable=self.search_var, width=220).grid(
            row=0, column=1, padx=6, pady=10, sticky="w"
        )

        ctk.CTkLabel(toolbar, text="Status:").grid(row=0, column=2, padx=(18, 6), pady=10, sticky="e")
        self.filter_menu = ctk.CTkOptionMenu(
            toolbar,
            values=["All", "Pending", "Updated", "Failed", "Skipped"],
            command=self._on_filter_changed,
            width=130,
        )
        self.filter_menu.set("All")
        self.filter_menu.grid(row=0, column=3, padx=6, pady=10, sticky="e")

        self.selection_label = ctk.CTkLabel(toolbar, text="0 selected")
        self.selection_label.grid(row=0, column=4, padx=12, pady=10, sticky="e")

        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=2, column=0, sticky="nsew", padx=16, pady=8)
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
            borderwidth=0,
        )
        style.configure(
            "Songs.Treeview.Heading",
            background="#1f1f1f",
            foreground="#ffffff",
            relief="flat",
        )
        style.map("Songs.Treeview", background=[("selected", "#1f6aa5")])

        columns = ("filename", "title", "artist", "album", "genre", "status", "cover")
        self.tree = ttk.Treeview(
            table_frame,
            columns=columns,
            show="headings",
            selectmode="extended",
            style="Songs.Treeview",
        )
        headings = {
            "filename": ("Filename", 180),
            "title": ("Title", 200),
            "artist": ("Artist", 140),
            "album": ("Album", 120),
            "genre": ("Genre", 100),
            "status": ("Status", 90),
            "cover": ("Cover", 120),
        }
        for key, (label, width) in headings.items():
            self.tree.heading(key, text=label)
            self.tree.column(key, width=width, anchor="w")

        scroll_y = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll_y.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        scroll_y.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        bulk = ctk.CTkFrame(self)
        bulk.grid(row=3, column=0, sticky="ew", padx=16, pady=8)
        for col in range(8):
            bulk.grid_columnconfigure(col, weight=1 if col in (1, 3, 5, 7) else 0)

        ctk.CTkLabel(
            bulk,
            text="Bulk edit (selected rows)",
            font=ctk.CTkFont(weight="bold"),
        ).grid(row=0, column=0, columnspan=8, sticky="w", padx=12, pady=(12, 8))

        self.field_vars = {
            "artist": tk.StringVar(),
            "album": tk.StringVar(),
            "track": tk.StringVar(),
            "genre": tk.StringVar(),
            "comment": tk.StringVar(),
            "cover": tk.StringVar(),
        }
        field_layout = [
            ("Artist", "artist", 0, 1),
            ("Album", "album", 2, 3),
            ("Track", "track", 4, 5),
            ("Genre", "genre", 6, 7),
        ]
        for label, key, label_col, entry_col in field_layout:
            ctk.CTkLabel(bulk, text=f"{label}:").grid(
                row=1, column=label_col, padx=(12, 6), pady=6, sticky="e"
            )
            ctk.CTkEntry(bulk, textvariable=self.field_vars[key]).grid(
                row=1, column=entry_col, padx=6, pady=6, sticky="ew"
            )

        ctk.CTkLabel(bulk, text="Comment:").grid(
            row=2, column=0, padx=(12, 6), pady=6, sticky="e"
        )
        ctk.CTkEntry(bulk, textvariable=self.field_vars["comment"]).grid(
            row=2, column=1, columnspan=3, padx=6, pady=6, sticky="ew"
        )
        ctk.CTkLabel(bulk, text="Cover:").grid(
            row=2, column=4, padx=(12, 6), pady=6, sticky="e"
        )
        ctk.CTkEntry(bulk, textvariable=self.field_vars["cover"]).grid(
            row=2, column=5, columnspan=2, padx=6, pady=6, sticky="ew"
        )
        ctk.CTkButton(bulk, text="Browse", width=80, command=self._browse_cover).grid(
            row=2, column=7, padx=(6, 12), pady=6, sticky="e"
        )

        actions = ctk.CTkFrame(bulk, fg_color="transparent")
        actions.grid(row=3, column=0, columnspan=8, sticky="ew", padx=12, pady=(4, 12))
        actions.grid_columnconfigure(4, weight=1)

        ctk.CTkButton(
            actions, text="Apply to selected", command=self._apply_selected
        ).grid(row=0, column=0, padx=(0, 8))
        ctk.CTkButton(actions, text="Apply to all", command=self._apply_all).grid(
            row=0, column=1, padx=8
        )
        ctk.CTkButton(actions, text="Save CSV", command=self._save_csv).grid(
            row=0, column=2, padx=8
        )
        self.dry_run_var = tk.BooleanVar(value=False)
        ctk.CTkCheckBox(
            actions, text="Dry run", variable=self.dry_run_var
        ).grid(row=0, column=3, padx=12)
        ctk.CTkButton(
            actions, text="Export report", command=self._export_report
        ).grid(row=0, column=5, padx=(8, 0))
        self.cancel_button = ctk.CTkButton(
            actions,
            text="Cancel",
            fg_color="#8b3a3a",
            hover_color="#a84b4b",
            command=self._request_cancel,
            state="disabled",
        )
        self.cancel_button.grid(row=0, column=6, padx=(8, 0))

        bottom = ctk.CTkFrame(self)
        bottom.grid(row=4, column=0, sticky="ew", padx=16, pady=(8, 16))
        bottom.grid_columnconfigure(0, weight=1)

        self.progress = ctk.CTkProgressBar(bottom)
        self.progress.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        self.progress.set(0)

        self.progress_label = ctk.CTkLabel(
            bottom, text="Choose a music folder to get started.", anchor="w"
        )
        self.progress_label.grid(row=1, column=0, sticky="ew", padx=12, pady=(0, 6))

        self.summary_label = ctk.CTkLabel(
            bottom,
            text="Updated: 0   Skipped: 0   Failed: 0   Remuxed: 0",
            anchor="w",
            text_color="#b0b0b0",
        )
        self.summary_label.grid(row=2, column=0, sticky="ew", padx=12, pady=(0, 12))

        self._song_index_by_item: dict[str, int] = {}

    def _chip_text(self) -> str:
        ffmpeg_status = "available" if ffmpeg_available(self.config_data.ffmpeg_path) else "missing"
        return f"ffmpeg: {ffmpeg_status}   |   config loaded"

    def _show_empty_state(self) -> None:
        self.progress_label.configure(text="Choose a music folder to get started.")

    def _browse_folder(self) -> None:
        folder = filedialog.askdirectory(title="Select music folder")
        if not folder:
            return
        self._set_folder(folder)

    def _set_folder(self, folder: str) -> None:
        self.library.folder = folder
        self.library.csv_path = default_csv_path(folder)
        self.folder_var.set(folder)
        self.library.songs = load_library(folder, self.library.csv_path)
        self._refresh_tree()
        self.progress_label.configure(
            text=f"Loaded {len(self.library.songs)} song(s) from {Path(self.library.csv_path).name}"
        )

    def _sync_folder(self) -> None:
        if not self.library.folder:
            messagebox.showwarning("No folder", "Choose a music folder first.")
            return
        try:
            songs, new_files = sync_library(
                self.library.folder,
                self.library.csv_path,
                self.config_data,
            )
        except Exception as exc:
            messagebox.showerror("Sync failed", str(exc))
            return

        self.library.songs = songs
        self._refresh_tree()
        if new_files:
            messagebox.showinfo(
                "Sync complete",
                f"Added {len(new_files)} new file(s).\nEdit tags below, then Apply.",
            )
        else:
            messagebox.showinfo("Sync complete", "CSV is already up to date.")

    def _refresh_tree(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)
        self._song_index_by_item.clear()

        for index, song in enumerate(self.library.songs):
            if not self._matches_filters(song):
                continue
            status = STATUS_LABELS.get(song.status, song.status.title())
            if song.is_new and song.status == "pending":
                status = "NEW"
            values = (
                song.filename,
                song.title,
                song.artist,
                song.album,
                song.genre,
                status,
                song.cover,
            )
            item_id = self.tree.insert("", "end", values=values)
            self._song_index_by_item[item_id] = index
            if song.status == "failed":
                self.tree.item(item_id, tags=("failed",))
            elif song.status == "updated":
                self.tree.item(item_id, tags=("updated",))
            elif song.is_new:
                self.tree.item(item_id, tags=("new",))

        self.tree.tag_configure("failed", foreground="#ff7b7b")
        self.tree.tag_configure("updated", foreground="#7dffb2")
        self.tree.tag_configure("new", foreground="#ffd27d")

    def _matches_filters(self, song: SongRow) -> bool:
        query = self._search_text.strip().lower()
        if query:
            haystack = " ".join(
                [
                    song.filename,
                    song.title,
                    song.artist,
                    song.album,
                    song.genre,
                    song.comment,
                ]
            ).lower()
            if query not in haystack:
                return False

        if self._status_filter == "all":
            return True
        if self._status_filter == "pending":
            return song.status == "pending"
        return song.status == self._status_filter

    def _on_search_changed(self) -> None:
        self._search_text = self.search_var.get()
        self._refresh_tree()

    def _on_filter_changed(self, value: str) -> None:
        self._status_filter = value.lower()
        self._refresh_tree()

    def _selected_indices(self) -> list[int]:
        indices = []
        for item_id in self.tree.selection():
            index = self._song_index_by_item.get(item_id)
            if index is not None:
                indices.append(index)
        return sorted(set(indices))

    def _on_tree_select(self, _event=None) -> None:
        indices = self._selected_indices()
        self.selection_label.configure(text=f"{len(indices)} selected")
        if len(indices) == 1:
            song = self.library.songs[indices[0]]
            self.field_vars["artist"].set(song.artist)
            self.field_vars["album"].set(song.album)
            self.field_vars["track"].set(song.track)
            self.field_vars["genre"].set(song.genre)
            self.field_vars["comment"].set(song.comment)
            self.field_vars["cover"].set(song.cover)

    def _apply_bulk_fields_to_indices(self, indices: list[int]) -> None:
        updates = {key: var.get().strip() for key, var in self.field_vars.items()}
        for index in indices:
            song = self.library.songs[index]
            for key, value in updates.items():
                if value:
                    setattr(song, key, value)

    def _browse_cover(self) -> None:
        if not self.library.folder:
            messagebox.showwarning("No folder", "Choose a music folder first.")
            return
        path = filedialog.askopenfilename(
            title="Select cover image",
            initialdir=self.library.folder,
            filetypes=[
                ("Images", "*.jpg *.jpeg *.png *.webp *.gif *.bmp"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        cover_path = Path(path)
        folder_path = Path(self.library.folder)
        if cover_path.parent == folder_path:
            self.field_vars["cover"].set(cover_path.name)
        else:
            self.field_vars["cover"].set(str(cover_path))

    def _save_csv(self) -> None:
        if not self.library.csv_path:
            messagebox.showwarning("No CSV", "Load a folder first.")
            return
        save_library(self.library.songs, self.library.csv_path)
        messagebox.showinfo("Saved", f"CSV saved to {self.library.csv_path}")

    def _apply_selected(self) -> None:
        indices = self._selected_indices()
        if not indices:
            messagebox.showwarning("No selection", "Select one or more songs first.")
            return
        self._apply_bulk_fields_to_indices(indices)
        self._start_apply(indices)

    def _apply_all(self) -> None:
        if not self.library.songs:
            messagebox.showwarning("No songs", "Sync or load a folder first.")
            return
        indices = list(range(len(self.library.songs)))
        self._apply_bulk_fields_to_indices(indices)
        self._start_apply(indices)

    def _set_busy(self, busy: bool) -> None:
        self._busy = busy
        state = "disabled" if busy else "normal"
        self.cancel_button.configure(state="normal" if busy else "disabled")

    def _request_cancel(self) -> None:
        self._cancel_requested = True
        self.progress_label.configure(text="Cancelling after current file...")

    def _start_apply(self, indices: list[int]) -> None:
        if not self.library.folder:
            messagebox.showwarning("No folder", "Choose a music folder first.")
            return
        if self._busy:
            return

        self._cancel_requested = False
        self._set_busy(True)
        self.library.dry_run = self.dry_run_var.get()
        self.last_result = None

        def worker():
            def on_progress(done, total, filename):
                self.after(0, lambda: self._update_progress(done, total, filename))

            result = apply_songs(
                self.library.folder,
                self.library.songs,
                indices,
                self.config_data,
                dry_run=self.library.dry_run,
                on_progress=on_progress,
                should_cancel=lambda: self._cancel_requested,
            )
            self.after(0, lambda: self._finish_apply(result))

        threading.Thread(target=worker, daemon=True).start()

    def _update_progress(self, done: int, total: int, filename: str) -> None:
        fraction = done / total if total else 0
        self.progress.set(fraction)
        prefix = "[dry-run] " if self.library.dry_run else ""
        self.progress_label.configure(text=f"{prefix}Processing {done}/{total}: {filename}")

    def _finish_apply(self, result) -> None:
        self.last_result = result
        self._set_busy(False)
        self.progress.set(1 if result.total else 0)
        save_library(self.library.songs, self.library.csv_path)
        self._refresh_tree()
        self.summary_label.configure(
            text=(
                f"Updated: {len(result.updated)}   "
                f"Skipped: {len(result.skipped)}   "
                f"Failed: {len(result.failed)}   "
                f"Remuxed: {len(result.remuxed)}"
            )
        )
        mode = "Dry-run complete." if result.dry_run else "Batch tagging complete."
        self.progress_label.configure(text=mode)

    def _export_report(self) -> None:
        if not getattr(self, "last_result", None):
            messagebox.showwarning("No report", "Run Apply first to generate a report.")
            return
        path = filedialog.asksaveasfilename(
            title="Save report",
            defaultextension=".json",
            filetypes=[("JSON", "*.json")],
        )
        if not path:
            return
        self.last_result.save_json(path)
        messagebox.showinfo("Report saved", path)

    def _open_settings(self) -> None:
        summary = (
            "watermark_patterns:\n"
            "  - site watermarks to strip from titles\n\n"
            "ffmpeg:\n"
            f"  path: {self.config_data.ffmpeg_path}\n"
            f"  timeout_seconds: {self.config_data.ffmpeg_timeout}\n\n"
            "backup:\n"
            f"  suffix: {self.config_data.backup_suffix}\n\n"
            "defaults:\n"
            f"  genre: {self.config_data.defaults.get('genre', '')}\n"
            f"  comment: {self.config_data.defaults.get('comment', '')}\n"
        )
        SettingsDialog(self, summary)