import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass
class FileReport:
    filename: str
    status: str
    message: str = ""
    remuxed: bool = False


@dataclass
class ProcessResult:
    """Summary of a batch tagging run."""

    updated: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    failed: list[str] = field(default_factory=list)
    remuxed: list[str] = field(default_factory=list)
    details: list[FileReport] = field(default_factory=list)
    dry_run: bool = False

    @property
    def total(self) -> int:
        return len(self.updated) + len(self.skipped) + len(self.failed)

    def add_detail(
        self,
        filename: str,
        status: str,
        message: str = "",
        remuxed: bool = False,
    ) -> None:
        self.details.append(
            FileReport(
                filename=filename,
                status=status,
                message=message,
                remuxed=remuxed,
            )
        )

    def to_dict(self) -> dict:
        return {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "dry_run": self.dry_run,
            "summary": {
                "updated": len(self.updated),
                "skipped": len(self.skipped),
                "failed": len(self.failed),
                "remuxed": len(self.remuxed),
                "total": self.total,
            },
            "updated": self.updated,
            "skipped": self.skipped,
            "failed": self.failed,
            "remuxed": self.remuxed,
            "details": [asdict(item) for item in self.details],
        }

    def save_json(self, path: str | Path) -> None:
        report_path = Path(path)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as handle:
            json.dump(self.to_dict(), handle, indent=2)