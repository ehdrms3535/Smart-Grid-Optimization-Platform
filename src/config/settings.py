# 실행 설정과 환경 변수 기반 구성 값을 관리한다.
from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path


def _strip_quotes(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        return value[1:-1]
    return value


def _read_dotenv(env_file: Path) -> dict[str, str]:
    if not env_file.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = _strip_quotes(value.strip())

        if key:
            values[key] = value

    return values


@dataclass(frozen=True, slots=True)
class Settings:
    root_dir: Path
    src_dir: Path
    data_dir: Path
    raw_data_dir: Path
    processed_data_dir: Path
    mock_data_dir: Path
    private_data_dir: Path
    models_dir: Path
    secrets_dir: Path
    env_file: Path
    sgop_env: str
    vworld_api_key: str | None
    public_data_api_key: str | None
    openai_api_key: str | None

    def require(self, value: str | None, name: str) -> str:
        if value:
            return value
        raise ValueError(f"Required setting is missing: {name}")

    @property
    def required_vworld_api_key(self) -> str:
        return self.require(self.vworld_api_key, "VWORLD_API_KEY")

    @property
    def required_public_data_api_key(self) -> str:
        return self.require(self.public_data_api_key, "PUBLIC_DATA_API_KEY")

    @property
    def required_openai_api_key(self) -> str:
        return self.require(self.openai_api_key, "OPENAI_API_KEY")


def load_settings(env_file: str | Path | None = None) -> Settings:
    root_dir = Path(__file__).resolve().parents[2]
    resolved_env_file = Path(env_file) if env_file else root_dir / ".env"

    dotenv_values = _read_dotenv(resolved_env_file)
    merged = {**dotenv_values, **os.environ}

    data_dir = root_dir / "data"

    return Settings(
        root_dir=root_dir,
        src_dir=root_dir / "src",
        data_dir=data_dir,
        raw_data_dir=data_dir / "raw",
        processed_data_dir=data_dir / "processed",
        mock_data_dir=data_dir / "mock",
        private_data_dir=data_dir / "private",
        models_dir=root_dir / "models",
        secrets_dir=root_dir / "secrets",
        env_file=resolved_env_file,
        sgop_env=merged.get("SGOP_ENV", "local"),
        vworld_api_key=merged.get("VWORLD_API_KEY") or None,
        public_data_api_key=merged.get("PUBLIC_DATA_API_KEY") or None,
        openai_api_key=merged.get("OPENAI_API_KEY") or None,
    )


settings = load_settings()
