from collections.abc import Callable

import customtkinter as ctk

from app.gui_settings import GuiSettings
from app.theme import ACCENT_CHOICES


class SettingsDialog(ctk.CTkToplevel):
    def __init__(
        self,
        master,
        config_summary: str,
        gui_settings: GuiSettings,
        on_theme_change: Callable[[GuiSettings], None] | None = None,
    ):
        super().__init__(master)
        self.gui_settings = gui_settings.normalize()
        self.on_theme_change = on_theme_change

        self.title("Settings")
        self.geometry("520x460")
        self.resizable(False, False)
        self.transient(master)
        self.grab_set()

        ctk.CTkLabel(
            self,
            text="Appearance",
            font=ctk.CTkFont(size=18, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(20, 8))

        appearance_row = ctk.CTkFrame(self, fg_color="transparent")
        appearance_row.pack(fill="x", padx=20, pady=(0, 6))
        ctk.CTkLabel(appearance_row, text="Theme:", width=90, anchor="w").pack(side="left")
        self.appearance_var = ctk.StringVar(value=self.gui_settings.appearance.title())
        ctk.CTkOptionMenu(
            appearance_row,
            variable=self.appearance_var,
            values=["Light", "Dark", "System"],
            command=self._on_appearance_change,
            width=180,
        ).pack(side="left", padx=(8, 0))

        accent_row = ctk.CTkFrame(self, fg_color="transparent")
        accent_row.pack(fill="x", padx=20, pady=(0, 12))
        ctk.CTkLabel(accent_row, text="Accent:", width=90, anchor="w").pack(side="left")
        self.accent_var = ctk.StringVar(
            value=ACCENT_CHOICES.get(self.gui_settings.accent, "Black & Gold")
        )
        ctk.CTkOptionMenu(
            accent_row,
            variable=self.accent_var,
            values=list(ACCENT_CHOICES.values()),
            command=self._on_accent_change,
            width=180,
        ).pack(side="left", padx=(8, 0))

        ctk.CTkLabel(
            self,
            text="Dark + Black & Gold is the default. System follows Windows.",
            text_color="#64748B",
            anchor="w",
        ).pack(anchor="w", padx=20, pady=(0, 16))

        ctk.CTkLabel(
            self,
            text="Tagging configuration",
            font=ctk.CTkFont(size=16, weight="bold"),
        ).pack(anchor="w", padx=20, pady=(0, 8))

        ctk.CTkLabel(
            self,
            text="Edit config.yaml in your project or music folder to change:",
            anchor="w",
            justify="left",
        ).pack(anchor="w", padx=20)

        textbox = ctk.CTkTextbox(self, height=140)
        textbox.pack(fill="both", expand=True, padx=20, pady=12)
        textbox.insert("1.0", config_summary)
        textbox.configure(state="disabled")

        ctk.CTkButton(self, text="Close", command=self.destroy).pack(pady=(0, 20))

    def _appearance_key(self, label: str) -> str:
        return label.strip().lower()

    def _accent_key(self, label: str) -> str:
        for key, name in ACCENT_CHOICES.items():
            if name == label:
                return key
        return "gold"

    def _emit_change(self) -> None:
        self.gui_settings.appearance = self._appearance_key(self.appearance_var.get())
        self.gui_settings.accent = self._accent_key(self.accent_var.get())
        self.gui_settings.save()
        if self.on_theme_change:
            self.on_theme_change(self.gui_settings)

    def _on_appearance_change(self, _value: str) -> None:
        self._emit_change()

    def _on_accent_change(self, _value: str) -> None:
        self._emit_change()