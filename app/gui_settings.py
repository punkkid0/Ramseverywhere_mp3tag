import json
from dataclasses import asdict, dataclass
from pathlib import Path

SETTINGS_FILE = Path.home() / ".ram_mp3tag" / "gui_settings.json"

VALID_APPEARANCES = ("light", "dark", "system")
VALID_ACCENTS = ("gold", "ocean", "slate", "forest", "indigo")


@dataclass
class GuiSettings:
    appearance: str = "dark"
    accent: str = "gold"
    last_folder: str = ""
    last_source_type: str = "folder"

    def normalize(self) -> "GuiSettings":
        if self.appearance not in VALID_APPEARANCES:
            self.appearance = "dark"
        if self.accent not in VALID_ACCENTS:
            self.accent = "gold"
        return self

    @classmethod
    def load(cls) -> "GuiSettings":
        try:
            if SETTINGS_FILE.exists():
                data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
                return cls(
                    appearance=str(data.get("appearance", "dark")),
                    accent=str(data.get("accent", "gold")),
                    last_folder=str(data.get("last_folder", "")),
                    last_source_type=str(data.get("last_source_type", "folder")),
                ).normalize()
        except (OSError, json.JSONDecodeError, TypeError):
            pass
        return cls().normalize()

    def save(self) -> None:
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(
            json.dumps(asdict(self.normalize()), indent=2),
            encoding="utf-8",
        )