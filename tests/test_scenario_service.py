from __future__ import annotations

from datetime import datetime
import json

import pytest

from src.data.schemas import ScenarioContext
from src.services.monitoring_service import MonitoringService
from src.services.prediction_service import PredictionService
from src.services.scenario_service import ScenarioService
from src.services.simulation_service import SimulationService


def _service(tmp_path):
    return ScenarioService(storage_path=tmp_path / "scenarios.json")


def test_save_and_load_scenario_round_trips_fields(tmp_path):
    service = _service(tmp_path)
    scenario = ScenarioContext(
        scenario_id="shared-001",
        title="Shared Scenario",
        description="Monitoring, Simulation, Prediction 공유 시나리오",
        region="South Korea",
        created_at=datetime(2026, 5, 11, 19, 0),
        created_by="pytest",
    )

    saved = service.save_scenario(scenario)
    loaded = service.load_scenario("shared-001")

    assert saved.scenario_id == "shared-001"
    assert loaded.scenario_id == scenario.scenario_id
    assert loaded.title == scenario.title
    assert loaded.description == scenario.description
    assert loaded.region == scenario.region
    assert loaded.created_at == scenario.created_at
    assert loaded.created_by == scenario.created_by


def test_save_scenario_updates_same_id_without_duplicate(tmp_path):
    service = _service(tmp_path)
    service.save_scenario(
        ScenarioContext(
            scenario_id="same-id",
            title="Before",
            created_at=datetime(2026, 5, 11, 19, 0),
        )
    )
    service.save_scenario(
        ScenarioContext(
            scenario_id="same-id",
            title="After",
            created_at=datetime(2026, 5, 11, 20, 0),
        )
    )

    scenarios = service.list_scenarios()

    assert len(scenarios) == 1
    assert scenarios[0].scenario_id == "same-id"
    assert scenarios[0].title == "After"
    assert scenarios[0].created_at == datetime(2026, 5, 11, 20, 0)


def test_list_scenarios_is_empty_when_storage_file_is_missing(tmp_path):
    service = _service(tmp_path)

    assert service.list_scenarios() == []


def test_list_scenarios_sorts_by_created_at_desc(tmp_path):
    service = _service(tmp_path)
    service.save_scenario(
        ScenarioContext(
            scenario_id="older",
            title="Older",
            created_at=datetime(2026, 5, 10, 12, 0),
        )
    )
    service.save_scenario(
        ScenarioContext(
            scenario_id="newer",
            title="Newer",
            created_at=datetime(2026, 5, 11, 12, 0),
        )
    )

    assert [scenario.scenario_id for scenario in service.list_scenarios()] == [
        "newer",
        "older",
    ]


def test_load_missing_scenario_raises_key_error(tmp_path):
    service = _service(tmp_path)

    with pytest.raises(KeyError, match="missing"):
        service.load_scenario("missing")


def test_save_empty_scenario_id_raises_value_error(tmp_path):
    service = _service(tmp_path)

    with pytest.raises(ValueError, match="scenario_id"):
        service.save_scenario(ScenarioContext(scenario_id="   "))


def test_delete_scenario_removes_saved_record(tmp_path):
    service = _service(tmp_path)
    service.save_scenario(ScenarioContext(scenario_id="delete-me"))

    assert service.delete_scenario("delete-me") is True
    assert service.delete_scenario("delete-me") is False
    with pytest.raises(KeyError):
        service.load_scenario("delete-me")


def test_corrupt_json_store_raises_value_error(tmp_path):
    storage_path = tmp_path / "scenarios.json"
    storage_path.write_text("{not-json", encoding="utf-8")
    service = ScenarioService(storage_path=storage_path)

    with pytest.raises(ValueError, match="JSON"):
        service.list_scenarios()


def test_saved_scenario_context_is_shared_across_core_services(tmp_path):
    service = _service(tmp_path)
    saved = service.save_scenario(
        ScenarioContext(
            scenario_id="shared-integration",
            title="Shared Integration",
            created_at=datetime(2026, 5, 11, 19, 0),
        )
    )
    loaded = service.load_scenario(saved.scenario_id)

    monitoring = MonitoringService().run_dc_power_flow(
        scenario=loaded,
        load_scale=1.0,
    )
    simulation_service = SimulationService()
    simulation = simulation_service.run_simulation(
        simulation_service.build_default_input(
            scenario=loaded,
            load_scale=1.0,
        )
    )
    prediction = PredictionService().run_mock_prediction(
        scenario=loaded,
        load_scale=1.0,
    )

    assert monitoring.scenario.scenario_id == "shared-integration"
    assert simulation.scenario.scenario_id == "shared-integration"
    assert prediction.scenario.scenario_id == "shared-integration"
    assert simulation.source == "astar"
    assert prediction.source == "mock"


def test_saved_file_uses_scenarios_collection(tmp_path):
    storage_path = tmp_path / "scenarios.json"
    service = ScenarioService(storage_path=storage_path)
    service.save_scenario(ScenarioContext(scenario_id="file-check"))

    payload = json.loads(storage_path.read_text(encoding="utf-8"))

    assert list(payload) == ["scenarios"]
    assert payload["scenarios"][0]["scenario_id"] == "file-check"
    assert "updated_at" in payload["scenarios"][0]
