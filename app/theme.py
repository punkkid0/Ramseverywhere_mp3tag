from __future__ import annotations

from dataclasses import dataclass

import customtkinter as ctk

from app.gui_settings import GuiSettings

ACCENT_CHOICES = {
    "gold": "Black & Gold",
    "ocean": "Ocean Blue",
    "slate": "Slate Gray",
    "forest": "Forest Green",
    "indigo": "Indigo",
}


@dataclass(frozen=True)
class ThemePalette:
    name: str
    accent: str
    accent_hover: str
    accent_soft: str
    bg: str
    surface: str
    surface_alt: str
    border: str
    text: str
    text_muted: str
    text_subtle: str
    danger: str
    danger_hover: str
    success: str
    warning: str
    table_bg: str
    table_fg: str
    table_head_bg: str
    table_head_fg: str
    table_select_bg: str
    table_select_fg: str
    table_alt_bg: str
    thumb_bg: str
    secondary_btn: str
    secondary_btn_hover: str


PALETTES: dict[str, dict[str, ThemePalette]] = {
    "gold": {
        "light": ThemePalette(
            name="Black & Gold",
            accent="#EAB308",
            accent_hover="#CA8A04",
            accent_soft="#FEF9C3",
            bg="#F5F5F5",
            surface="#FFFFFF",
            surface_alt="#FAFAFA",
            border="#D4D4D4",
            text="#0A0A0A",
            text_muted="#262626",
            text_subtle="#525252",
            danger="#DC2626",
            danger_hover="#B91C1C",
            success="#16A34A",
            warning="#CA8A04",
            table_bg="#FFFFFF",
            table_fg="#0A0A0A",
            table_head_bg="#0A0A0A",
            table_head_fg="#EAB308",
            table_select_bg="#EAB308",
            table_select_fg="#0A0A0A",
            table_alt_bg="#F5F5F5",
            thumb_bg="#E5E5E5",
            secondary_btn="#737373",
            secondary_btn_hover="#525252",
        ),
        "dark": ThemePalette(
            name="Black & Gold",
            accent="#FACC15",
            accent_hover="#EAB308",
            accent_soft="#3F3500",
            bg="#0A0A0A",
            surface="#141414",
            surface_alt="#1C1C1C",
            border="#2E2E2E",
            text="#F5F5F5",
            text_muted="#D4D4D4",
            text_subtle="#A3A3A3",
            danger="#F87171",
            danger_hover="#EF4444",
            success="#4ADE80",
            warning="#FACC15",
            table_bg="#1A1A1A",
            table_fg="#F0F0F0",
            table_head_bg="#0A0A0A",
            table_head_fg="#FACC15",
            table_select_bg="#FACC15",
            table_select_fg="#0A0A0A",
            table_alt_bg="#242424",
            thumb_bg="#262626",
            secondary_btn="#404040",
            secondary_btn_hover="#525252",
        ),
    },
    "ocean": {
        "light": ThemePalette(
            name="Ocean",
            accent="#0284C7",
            accent_hover="#0369A1",
            accent_soft="#E0F2FE",
            bg="#F1F5F9",
            surface="#FFFFFF",
            surface_alt="#F8FAFC",
            border="#CBD5E1",
            text="#0F172A",
            text_muted="#475569",
            text_subtle="#64748B",
            danger="#DC2626",
            danger_hover="#B91C1C",
            success="#059669",
            warning="#D97706",
            table_bg="#FFFFFF",
            table_fg="#0F172A",
            table_head_bg="#E2E8F0",
            table_head_fg="#1E293B",
            table_select_bg="#0284C7",
            table_select_fg="#FFFFFF",
            table_alt_bg="#F8FAFC",
            thumb_bg="#E2E8F0",
            secondary_btn="#94A3B8",
            secondary_btn_hover="#64748B",
        ),
        "dark": ThemePalette(
            name="Ocean",
            accent="#38BDF8",
            accent_hover="#0EA5E9",
            accent_soft="#0C4A6E",
            bg="#0F172A",
            surface="#1E293B",
            surface_alt="#111827",
            border="#334155",
            text="#F8FAFC",
            text_muted="#CBD5E1",
            text_subtle="#94A3B8",
            danger="#F87171",
            danger_hover="#EF4444",
            success="#34D399",
            warning="#FBBF24",
            table_bg="#1E293B",
            table_fg="#F1F5F9",
            table_head_bg="#0F172A",
            table_head_fg="#E2E8F0",
            table_select_bg="#0284C7",
            table_select_fg="#FFFFFF",
            table_alt_bg="#111827",
            thumb_bg="#0F172A",
            secondary_btn="#475569",
            secondary_btn_hover="#64748B",
        ),
    },
    "slate": {
        "light": ThemePalette(
            name="Slate",
            accent="#475569",
            accent_hover="#334155",
            accent_soft="#E2E8F0",
            bg="#F8FAFC",
            surface="#FFFFFF",
            surface_alt="#F1F5F9",
            border="#CBD5E1",
            text="#0F172A",
            text_muted="#475569",
            text_subtle="#64748B",
            danger="#DC2626",
            danger_hover="#B91C1C",
            success="#047857",
            warning="#B45309",
            table_bg="#FFFFFF",
            table_fg="#0F172A",
            table_head_bg="#E2E8F0",
            table_head_fg="#334155",
            table_select_bg="#475569",
            table_select_fg="#FFFFFF",
            table_alt_bg="#F8FAFC",
            thumb_bg="#E2E8F0",
            secondary_btn="#94A3B8",
            secondary_btn_hover="#64748B",
        ),
        "dark": ThemePalette(
            name="Slate",
            accent="#94A3B8",
            accent_hover="#CBD5E1",
            accent_soft="#334155",
            bg="#111827",
            surface="#1F2937",
            surface_alt="#111827",
            border="#374151",
            text="#F9FAFB",
            text_muted="#D1D5DB",
            text_subtle="#9CA3AF",
            danger="#F87171",
            danger_hover="#EF4444",
            success="#34D399",
            warning="#FBBF24",
            table_bg="#1F2937",
            table_fg="#F3F4F6",
            table_head_bg="#111827",
            table_head_fg="#E5E7EB",
            table_select_bg="#475569",
            table_select_fg="#FFFFFF",
            table_alt_bg="#111827",
            thumb_bg="#111827",
            secondary_btn="#4B5563",
            secondary_btn_hover="#6B7280",
        ),
    },
    "forest": {
        "light": ThemePalette(
            name="Forest",
            accent="#059669",
            accent_hover="#047857",
            accent_soft="#D1FAE5",
            bg="#F6FAF8",
            surface="#FFFFFF",
            surface_alt="#F0FDF4",
            border="#BBF7D0",
            text="#14532D",
            text_muted="#166534",
            text_subtle="#4B5563",
            danger="#DC2626",
            danger_hover="#B91C1C",
            success="#059669",
            warning="#CA8A04",
            table_bg="#FFFFFF",
            table_fg="#14532D",
            table_head_bg="#DCFCE7",
            table_head_fg="#166534",
            table_select_bg="#059669",
            table_select_fg="#FFFFFF",
            table_alt_bg="#F0FDF4",
            thumb_bg="#DCFCE7",
            secondary_btn="#86EFAC",
            secondary_btn_hover="#4ADE80",
        ),
        "dark": ThemePalette(
            name="Forest",
            accent="#34D399",
            accent_hover="#10B981",
            accent_soft="#064E3B",
            bg="#052E16",
            surface="#14532D",
            surface_alt="#052E16",
            border="#166534",
            text="#ECFDF5",
            text_muted="#A7F3D0",
            text_subtle="#6EE7B7",
            danger="#F87171",
            danger_hover="#EF4444",
            success="#34D399",
            warning="#FBBF24",
            table_bg="#14532D",
            table_fg="#ECFDF5",
            table_head_bg="#052E16",
            table_head_fg="#D1FAE5",
            table_select_bg="#059669",
            table_select_fg="#FFFFFF",
            table_alt_bg="#052E16",
            thumb_bg="#052E16",
            secondary_btn="#166534",
            secondary_btn_hover="#15803D",
        ),
    },
    "indigo": {
        "light": ThemePalette(
            name="Indigo",
            accent="#4F46E5",
            accent_hover="#4338CA",
            accent_soft="#E0E7FF",
            bg="#FAFAFE",
            surface="#FFFFFF",
            surface_alt="#F5F3FF",
            border="#C7D2FE",
            text="#1E1B4B",
            text_muted="#4338CA",
            text_subtle="#6366F1",
            danger="#DC2626",
            danger_hover="#B91C1C",
            success="#059669",
            warning="#D97706",
            table_bg="#FFFFFF",
            table_fg="#1E1B4B",
            table_head_bg="#EEF2FF",
            table_head_fg="#3730A3",
            table_select_bg="#4F46E5",
            table_select_fg="#FFFFFF",
            table_alt_bg="#F5F3FF",
            thumb_bg="#EEF2FF",
            secondary_btn="#A5B4FC",
            secondary_btn_hover="#818CF8",
        ),
        "dark": ThemePalette(
            name="Indigo",
            accent="#818CF8",
            accent_hover="#6366F1",
            accent_soft="#312E81",
            bg="#1E1B4B",
            surface="#312E81",
            surface_alt="#1E1B4B",
            border="#4338CA",
            text="#EEF2FF",
            text_muted="#C7D2FE",
            text_subtle="#A5B4FC",
            danger="#F87171",
            danger_hover="#EF4444",
            success="#34D399",
            warning="#FBBF24",
            table_bg="#312E81",
            table_fg="#EEF2FF",
            table_head_bg="#1E1B4B",
            table_head_fg="#E0E7FF",
            table_select_bg="#4F46E5",
            table_select_fg="#FFFFFF",
            table_alt_bg="#1E1B4B",
            thumb_bg="#1E1B4B",
            secondary_btn="#4338CA",
            secondary_btn_hover="#4F46E5",
        ),
    },
}


class ThemeManager:
    def __init__(self, settings: GuiSettings):
        self.settings = settings.normalize()
        self.palette = self._resolve_palette()

    def _mode_key(self) -> str:
        appearance = self.settings.appearance
        if appearance == "system":
            mode = ctk.get_appearance_mode()
            return "dark" if str(mode).lower() == "dark" else "light"
        return appearance

    def _resolve_palette(self) -> ThemePalette:
        accent = self.settings.accent
        mode = self._mode_key()
        return PALETTES.get(accent, PALETTES["gold"])[mode]

    def apply_global(self) -> None:
        ctk.set_appearance_mode(self.settings.appearance)
        ctk.set_default_color_theme("blue")
        self.palette = self._resolve_palette()

    def refresh(self, settings: GuiSettings | None = None) -> ThemePalette:
        if settings is not None:
            self.settings = settings.normalize()
        self.apply_global()
        return self.palette