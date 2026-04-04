# AGENTS.md

## 목적
- 이 저장소는 SGOP MVP를 위한 Streamlit 기반 멀티페이지 앱이다.
- 현재 기준 계획 문서는 `2026-03-30` 회의안과 개발 흐름도다.
- 작업 순서는 항상 `계약 정의 -> mock -> 최소 구현 -> 실제 연결 -> 안정화`를 따른다.

## 작업 시작 전 필수 확인
- 먼저 `git status --short`를 확인한다.
- 현재 워크트리는 더럽혀져 있을 수 있다. 내가 만들지 않은 변경은 되돌리지 않는다.
- `Monitoring`, `Simulation`, `A*` 관련 모듈은 아직 대부분 스텁이다.
- 현재 구현 기준점은 `Prediction` 쪽이다. 새 기능은 이 흐름을 참고하되, 페이지별 하드코딩을 늘리지 않는다.
- 외부 API, 실제 데이터, 모델 파일이 없어도 mock 기준으로 동작해야 한다.

## 반드시 먼저 읽을 파일
1. `meeting_plan/MEETING_PLAN_2026-03-30.md`
2. `DEVELOPMENT_FLOW_2026-03-30.md`
3. `src/data/schemas.py`
4. `app.py`
5. `pages/03_prediction.py`
6. `src/services/prediction_service.py`
7. `pages/01_monitoring.py`
8. `pages/02_simulation.py`
9. `src/services/monitoring_service.py`
10. `src/services/simulation_service.py`
11. `src/engine/search/astar_router.py`
12. `src/engine/search/score_function.py`
13. `src/engine/forecast/feature_builder.py`
14. `src/config/settings.py`

## 현재 저장소 상태
- `pages/03_prediction.py`와 `src/services/prediction_service.py`만 목업 수준 구현이 있다.
- `src/data/schemas.py`가 페이지/서비스 간 공통 계약의 기준 파일이다.
- `data/mock`에는 아직 실제 fixture 파일이 없다.
- `src/domain`, `src/services`, `src/engine/search`, `src/engine/powerflow`의 다수 파일은 한 줄 스텁이다.

## 공통 계약 규칙
- 페이지와 서비스 사이의 입출력은 `src/data/schemas.py`의 dataclass를 우선 사용한다.
- ad hoc `dict`를 페이지마다 새로 정의하지 않는다.
- `scenario_id`는 페이지별로 따로 만들지 말고 같은 시나리오 맥락을 공유한다.
- 서비스가 실제 계산을 못 해도 스키마 형식은 유지하고, 필요하면 `warnings`와 `fallback`에 이유를 남긴다.
- 새 결과 타입이 필요하면 먼저 `src/data/schemas.py`에 추가하고 나서 서비스/페이지를 수정한다.

## 현재까지 진행된 작업
- `1순위` 작업으로 공통 계약 스키마를 `src/data/schemas.py`에 추가했다.
- 추가된 핵심 타입:
  - `FallbackInfo`
  - `ScenarioContext`
  - `MonitoringResult`
  - `SimulationInput`
  - `SimulationResult`
  - `RouteResult`
  - `ScoreBreakdown`
  - 보조 타입 (`MonitoringKpi`, `LineStatusSnapshot`, `RoutePoint`, `RecommendationResult`, `SimulationDelta`, `TimeSeriesPoint`)
- 기존 `PredictionResult`는 깨지지 않도록 `scenario`, `warnings`, `fallback` 필드를 기본값과 함께 확장했다.

## 앞으로 작업할 때 우선순위
1. `src/data/schemas.py` 기준으로 서비스 반환 형식을 통일한다.
2. `Monitoring`과 `Simulation` 서비스에 mock 반환 뼈대를 만든다.
3. 각 페이지가 서비스만 호출하도록 정리한다.
4. 그다음에 `A*`, 점수화, power flow 같은 엔진 구현으로 내려간다.

## 검증 규칙
- 코드 수정 후 최소한 `python3 -m compileall app.py pages src`는 실행한다.
- 가능하면 수정한 스키마를 import 하는 경로가 깨지지 않는지 확인한다.
- 테스트가 없으면 없다고 명시하고 끝내지 말고, 최소 정적 검증은 수행한다.
