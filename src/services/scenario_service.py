# 사용자 시뮬레이션 시나리오의 저장, 불러오기, 비교를 관리한다.
from __future__ import annotations

from dataclasses import replace
from datetime import datetime
import json
from pathlib import Path
from typing import Any

from src.config.settings import settings
from src.data.schemas import ScenarioContext


class ScenarioService:
    """ScenarioContext를 JSON 파일에 저장하고 조회하는 최소 서비스 계층."""

    def __init__(self, storage_path: Path | str | None = None) -> None:
        self.storage_path = (
            Path(storage_path)
            if storage_path is not None
            else settings.private_data_dir / "scenarios.json"
        )

    def save_scenario(self, scenario: ScenarioContext) -> ScenarioContext:
        """시나리오를 저장한다. 같은 scenario_id가 있으면 덮어쓴다."""
        if not isinstance(scenario, ScenarioContext):
            raise TypeError("scenario는 ScenarioContext여야 합니다.")

        scenario_id = self._validate_scenario_id(scenario.scenario_id)
        resolved_scenario = replace(
            scenario,
            scenario_id=scenario_id,
            created_at=scenario.created_at or _round_to_second(datetime.now()),
        )

        store = self._read_store()
        scenarios = store["scenarios"]
        record = _scenario_to_record(resolved_scenario)

        for index, saved in enumerate(scenarios):
            saved_id = str(saved.get("scenario_id", "")).strip()
            if saved_id == scenario_id:
                scenarios[index] = record
                break
        else:
            scenarios.append(record)

        self._write_store(store)
        return resolved_scenario

    def load_scenario(self, scenario_id: str) -> ScenarioContext:
        """scenario_id에 해당하는 시나리오를 반환한다."""
        resolved_id = self._validate_scenario_id(scenario_id)
        for record in self._read_store()["scenarios"]:
            if str(record.get("scenario_id", "")).strip() == resolved_id:
                return _scenario_from_record(record)
        raise KeyError(f"저장된 시나리오가 없습니다: {resolved_id}")

    def list_scenarios(self) -> list[ScenarioContext]:
        """저장된 시나리오 목록을 created_at 내림차순으로 반환한다."""
        scenarios = [
            _scenario_from_record(record)
            for record in self._read_store()["scenarios"]
        ]
        return sorted(
            scenarios,
            key=lambda scenario: (
                scenario.created_at or datetime.min,
                scenario.scenario_id,
            ),
            reverse=True,
        )

    def delete_scenario(self, scenario_id: str) -> bool:
        """scenario_id에 해당하는 시나리오를 삭제한다."""
        resolved_id = self._validate_scenario_id(scenario_id)
        store = self._read_store()
        original_count = len(store["scenarios"])
        store["scenarios"] = [
            record
            for record in store["scenarios"]
            if str(record.get("scenario_id", "")).strip() != resolved_id
        ]

        if len(store["scenarios"]) == original_count:
            return False

        self._write_store(store)
        return True

    def _read_store(self) -> dict[str, list[dict[str, Any]]]:
        if not self.storage_path.exists():
            return {"scenarios": []}

        try:
            raw_store = json.loads(self.storage_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"시나리오 저장 파일의 JSON 형식이 올바르지 않습니다: {self.storage_path}"
            ) from exc

        if not isinstance(raw_store, dict):
            raise ValueError("시나리오 저장 파일의 최상위 구조는 객체여야 합니다.")

        scenarios = raw_store.get("scenarios", [])
        if not isinstance(scenarios, list):
            raise ValueError("시나리오 저장 파일의 scenarios 필드는 리스트여야 합니다.")

        return {"scenarios": scenarios}

    def _write_store(self, store: dict[str, list[dict[str, Any]]]) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.storage_path.write_text(
            json.dumps(store, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _validate_scenario_id(self, scenario_id: str) -> str:
        if not isinstance(scenario_id, str):
            raise TypeError("scenario_id는 문자열이어야 합니다.")

        resolved_id = scenario_id.strip()
        if not resolved_id:
            raise ValueError("scenario_id는 빈 문자열일 수 없습니다.")
        return resolved_id


def _scenario_to_record(scenario: ScenarioContext) -> dict[str, Any]:
    return {
        "scenario_id": scenario.scenario_id,
        "title": scenario.title,
        "description": scenario.description,
        "region": scenario.region,
        "created_at": (
            scenario.created_at.isoformat()
            if scenario.created_at is not None
            else None
        ),
        "created_by": scenario.created_by,
        "updated_at": _round_to_second(datetime.now()).isoformat(),
    }


def _scenario_from_record(record: dict[str, Any]) -> ScenarioContext:
    if not isinstance(record, dict):
        raise ValueError("시나리오 레코드는 객체여야 합니다.")

    scenario_id = str(record.get("scenario_id", "")).strip()
    if not scenario_id:
        raise ValueError("시나리오 레코드에 scenario_id가 없습니다.")

    return ScenarioContext(
        scenario_id=scenario_id,
        title=str(record.get("title", "") or ""),
        description=str(record.get("description", "") or ""),
        region=str(record.get("region", "") or ""),
        created_at=_parse_datetime(record.get("created_at")),
        created_by=str(record.get("created_by", "") or ""),
    )


def _parse_datetime(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if not isinstance(value, str):
        raise ValueError("created_at은 ISO 문자열이어야 합니다.")
    try:
        return datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"created_at ISO 형식이 올바르지 않습니다: {value}") from exc


def _round_to_second(value: datetime) -> datetime:
    return value.replace(microsecond=0)
