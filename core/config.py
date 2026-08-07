from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    app_name: str = "Getnet Agent Swarm"
    app_version: str = "1.0.0"
    project_root: Path = Path(__file__).resolve().parent.parent

    @property
    def app_dir(self) -> Path:
        return self.project_root / "app"

    @property
    def data_dir(self) -> Path:
        return self.project_root / "data"


settings = Settings()
