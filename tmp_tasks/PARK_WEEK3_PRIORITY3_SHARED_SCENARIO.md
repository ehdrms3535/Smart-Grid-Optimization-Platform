# 박차오름 3주차 우선순위 3 작업 체크리스트

## 목적
- `pages/02_simulation.py`가 Monitoring, Prediction과 같은 Streamlit session state의 `ScenarioContext`를 공유하게 만든다.
- 박차오름 3주차 범위인 `서비스 간 데이터 전달 구조 정리`, `시뮬레이션-예측-모니터링 연결 포맷 통일`을 완료 상태로 끌어올린다.
- 이 문서는 구현 전에 할 일을 정리하는 임시 작업 목록이다.

## 현재 상태
- `pages/01_monitoring.py`에는 `_get_shared_scenario()`가 있다.
- `pages/03_prediction.py`에도 `_get_shared_scenario()`가 있다.
- 두 페이지는 `st.session_state.sgop_shared_scenario`를 읽고 없으면 새 `ScenarioContext`를 만든다.
- `pages/02_simulation.py`는 현재 `SimulationService.build_default_input()` 호출 시 `scenario`를 넘기지 않는다.
- 따라서 Simulation 페이지는 별도 기본 시나리오를 만들 수 있고, 세 페이지가 같은 `scenario_id`를 쓴다는 보장이 약하다.
- 전수 재확인 결과:
  - `SimulationService.build_default_input()`은 `scenario`를 받으면 같은 `ScenarioContext`를 유지한다.
  - `SimulationService.run_simulation()`은 별도 `created_at`을 받지 않으면 현재 시각으로 결과 시간을 만든다.
  - 이 우선순위의 범위는 session state 기반 공유 시나리오 통합까지이며, `ScenarioService` 저장/불러오기는 구현하지 않는다.

## 작업 0. 선행 조건 확인
- 이 작업은 우선순위 1, 2와 독립적인 통합 작업이다.
- 단, `pages/02_simulation.py` bare-run 검증은 우선순위 1의 `folium` 의존성 정리가 끝난 뒤 실행해야 한다.
- 우선순위 1이 아직 끝나지 않았다면 서비스 단위 검증부터 수행한다.

## 작업 1. Simulation 페이지에 공통 시나리오 import 추가
- 대상 파일: `pages/02_simulation.py`
- 현재 import:

```python
from __future__ import annotations
import streamlit as st
import folium
from streamlit_folium import st_folium
```

- 추가할 import:

```python
from datetime import datetime
from src.data.schemas import ScenarioContext
```

- 주의:
  - `datetime`은 `created_at` 초기화에 사용한다.
  - `ScenarioContext`는 `isinstance()` 검증에 사용한다.

## 작업 2. `_get_shared_scenario()` helper 추가
- 대상 파일: `pages/02_simulation.py`
- 위치 권장:
  - `st.set_page_config(...)` 아래
  - 서비스 초기화 이전 또는 직후
- Monitoring/Prediction과 같은 session key를 사용한다.
  - session key: `sgop_shared_scenario`

- 권장 구현 형태:

```python
def _get_shared_scenario() -> ScenarioContext:
    scenario = st.session_state.get("sgop_shared_scenario")
    if isinstance(scenario, ScenarioContext):
        return scenario

    created_at = datetime.now().replace(minute=0, second=0, microsecond=0)
    scenario = ScenarioContext(
        scenario_id="sgop-demo-scenario",
        title="SGOP Demo Scenario",
        description="Monitoring, Simulation, Prediction이 공유하는 기본 시나리오",
        region="South Korea",
        created_at=created_at,
        created_by="streamlit-session",
    )
    st.session_state.sgop_shared_scenario = scenario
    return scenario
```

## 작업 3. `SimulationInput` 생성 시 shared scenario 전달
- 대상 코드:

```python
sim_input = sim_service.build_default_input(
    start_bus_id=start_bus,
    end_bus_id=end_bus,
    candidate_site_ids=selected_candidates,
    load_scale=load_scale
)
```

- 변경 방향:

```python
shared_scenario = _get_shared_scenario()
shared_created_at = shared_scenario.created_at

sim_input = sim_service.build_default_input(
    scenario=shared_scenario,
    created_at=shared_created_at,
    start_bus_id=start_bus,
    end_bus_id=end_bus,
    candidate_site_ids=selected_candidates,
    load_scale=load_scale,
)
```

- 완료 기준:
  - `sim_result.scenario.scenario_id`가 Monitoring/Prediction의 `sgop-demo-scenario`와 같아진다.
  - 가능하면 `sim_result.created_at`도 shared scenario의 `created_at`와 같은 기준 시각을 사용한다.

## 작업 3-1. `run_simulation()` 호출 시 기준 시각 일관성 유지
- 대상 코드:

```python
sim_result = sim_service.run_simulation(sim_input)
```

- 변경 방향:

```python
sim_result = sim_service.run_simulation(
    sim_input,
    created_at=shared_created_at,
)
```

- 주의:
  - `shared_created_at`이 `None`일 가능성을 고려한다.
  - `ScenarioContext.created_at`이 없으면 `SimulationService`가 기존처럼 현재 시각을 보정하게 둔다.
  - 이 작업은 저장/불러오기 기능을 만들지 않는다.

## 작업 4. 실행 결과의 scenario를 session state에 다시 저장
- `SimulationService`가 scenario의 `created_at`을 보정할 수 있으므로 결과 반환 후 다시 저장한다.
- 대상 위치:
  - `sim_result = sim_service.run_simulation(sim_input)` 직후

- 추가 코드:

```python
st.session_state.sgop_shared_scenario = sim_result.scenario
```

- 완료 기준:
  - Simulation 페이지를 다녀온 뒤 Prediction/Monitoring으로 이동해도 같은 scenario가 유지된다.

## 작업 5. 화면에 scenario metadata 표시
- 입력-결과 연결을 눈으로 확인할 수 있게 제목 아래 또는 오른쪽 패널에 표시한다.
- 표시 항목:
  - `scenario_id`
  - `source`
  - `load_scale`
  - `start_bus_id`
  - `end_bus_id`
  - 후보지 수

- 예시:

```python
st.caption(
    f"시나리오: {sim_result.scenario.scenario_id} | "
    f"소스: {sim_result.source.upper()} | "
    f"부하 배율: {sim_result.simulation_input.load_scale:.2f}x | "
    f"{sim_result.simulation_input.start_bus_id} -> {sim_result.simulation_input.end_bus_id}"
)
```

- 주의:
  - `×` 같은 특수문자 대신 ASCII `x`를 써도 된다.
  - 기존 파일에 이모지가 많지만 새 코드는 가능하면 단순하게 둔다.

## 작업 6. 서비스 단위 통합 검증 추가
- 페이지 import가 `folium` 의존성 때문에 막혀도 서비스 단위로 먼저 검증할 수 있다.

```bash
.venv310/bin/python -c "from src.data.schemas import ScenarioContext; from src.services.monitoring_service import MonitoringService; from src.services.simulation_service import SimulationService; from src.services.prediction_service import PredictionService; scenario=ScenarioContext(scenario_id='shared-week3'); monitoring=MonitoringService().run_dc_power_flow(scenario=scenario, load_scale=1.0); svc=SimulationService(); simulation=svc.run_simulation(svc.build_default_input(scenario=scenario, load_scale=1.0)); prediction=PredictionService().run_mock_prediction(scenario=scenario, load_scale=1.0); print([monitoring.scenario.scenario_id, simulation.scenario.scenario_id, prediction.scenario.scenario_id], simulation.source, simulation.fallback.mode)"
```

- 완료 기준:
  - 출력된 세 scenario id가 모두 `shared-week3`
  - Simulation source가 `astar`

## 작업 7. 페이지 bare-run 검증
- 우선순위 1 완료 후 실행한다.

```bash
.venv310/bin/python -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"
```

- 완료 기준:
  - import 오류 없음
  - `simulation-page-run-ok` 출력

## 작업 8. 전체 정적 검증

```bash
.venv310/bin/python -m compileall app.py pages src
```

- 완료 기준:
  - compile error 없음

## 작업 9. 결과 기록
- 대상 파일: `WORK_TIMELINE.md`
- 기록 내용:
  - `pages/02_simulation.py`가 `sgop_shared_scenario`를 읽고 결과 scenario를 다시 저장하도록 변경
  - 서비스 단위 시나리오 유지 검증 결과
  - 페이지 bare-run 검증 결과
  - compileall 결과

## 최종 완료 기준
- Monitoring, Simulation, Prediction이 같은 `ScenarioContext`를 공유한다.
- Simulation 페이지가 `SimulationInput.scenario`를 별도 생성하지 않고 session state의 공통 scenario를 사용한다.
- `sim_result.scenario.scenario_id`가 화면에 표시된다.
- 서비스 단위 검증에서 세 결과의 scenario id가 모두 같다.
- 이 작업은 시나리오 저장/불러오기 기능을 만들지 않는다. 저장/불러오기는 별도 3주차/후속 작업이다.

## 완료 후 삭제 조건
- 체크리스트의 모든 항목이 구현되고 `WORK_TIMELINE.md`에 검증 결과가 기록되면 이 임시 파일은 삭제해도 된다.
