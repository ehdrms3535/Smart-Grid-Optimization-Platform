# WORK_TIMELINE.md

## 목적
- 이 파일은 SGOP 저장소의 작업 타임라인과 최근 변경 맥락을 기록한다.
- 새 작업을 시작할 때는 최신 항목부터 읽고, 작업이 끝나면 결과를 추가한다.
- `AGENTS.md`를 읽었다면 이 파일도 같이 읽는 것이 기본 규칙이다.

## 기록 규칙
- 항목 순서는 최신 작업이 아래에 오도록 시간순으로 쌓는다.
- 각 항목에는 최소한 `날짜`, `작업`, `수정 파일`, `검증`, `다음 작업`을 남긴다.
- 구현이 아니라 조사만 했더라도 다음 사람이나 다음 세션이 바로 이어받을 수 있을 만큼 구체적으로 적는다.

## 타임라인

### 2026-03-30
- 작업: MVP 범위, fallback, 역할 분담, 개발 흐름을 문서 기준으로 고정했다.
- 수정 파일: `meeting_plan/MEETING_PLAN_2026-03-30.md`, `DEVELOPMENT_FLOW_2026-03-30.md`
- 검증: 문서 기준 합의안 작성
- 다음 작업: 공통 계약 스키마 정의

### 2026-04-04 1순위 완료
- 작업: 공통 계약 스키마를 `src/data/schemas.py`에 정리했다.
- 수정 파일: `src/data/schemas.py`
- 검증: 서비스/페이지 공통 계약 타입 추가 완료
- 다음 작업: `Monitoring`, `Simulation` 서비스 mock 반환 뼈대 구현

### 2026-04-04 Streamlit 실행 안정화
- 작업: WSL/로컬 환경에서 Streamlit 첫 실행과 파일 감시 문제를 줄이기 위한 로컬 설정을 추가했다.
- 수정 파일: `.streamlit/config.toml`
- 검증: Streamlit HTML/정적 자산 응답 확인
- 다음 작업: 서비스와 페이지 mock 연결 계속 진행

### 2026-04-04 2순위 완료
- 작업: `MonitoringService`, `SimulationService`에 공통 계약 기준 mock 반환 뼈대를 구현했다.
- 수정 파일: `src/services/monitoring_service.py`, `src/services/simulation_service.py`
- 검증:
  - `python3 -c "from src.services.monitoring_service import MonitoringService; result = MonitoringService().get_monitoring_result(load_scale=1.05); print(result.source, result.scenario.scenario_id, len(result.kpis), len(result.line_statuses), len(result.trend_points), result.fallback.mode)"`
  - `python3 -c "from src.services.simulation_service import SimulationService; svc = SimulationService(); result = svc.run_mock_simulation(svc.build_default_input(load_scale=1.1)); print(result.source, result.scenario.scenario_id, len(result.recommendations), len(result.deltas), result.selected_route.route_id, result.fallback.mode)"`
  - `python3 -c "from src.data.schemas import ScenarioContext; from src.services.monitoring_service import MonitoringService; from src.services.simulation_service import SimulationService; scenario = ScenarioContext(scenario_id='shared-001'); monitoring = MonitoringService().get_monitoring_result(scenario=scenario); simulation = SimulationService().run_mock_simulation(SimulationService().build_default_input(scenario=scenario)); print(monitoring.scenario.scenario_id, simulation.scenario.scenario_id, monitoring.scenario.created_at is not None, simulation.simulation_input.scenario.scenario_id)"`
  - `python3 -m compileall app.py pages src`
- 다음 작업: `pages/01_monitoring.py`, `pages/02_simulation.py`가 서비스만 호출하도록 정리

### 2026-04-04 3순위 완료
- 작업: `Monitoring`, `Simulation` 페이지를 서비스 반환 결과만 렌더링하는 구조로 구현했다.
- 수정 파일: `pages/01_monitoring.py`, `pages/02_simulation.py`, `src/services/simulation_service.py`, `AGENTS.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "import runpy; runpy.run_path('pages/01_monitoring.py'); print('monitoring-page-run-ok')"`
  - `python3 -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"`
- 다음 작업: `pages/03_prediction.py`까지 같은 `ScenarioContext`를 공유하도록 정리하고, 이후 엔진 구현으로 내려가기

### 2026-04-04 4순위 완료
- 작업: `A*` 결과 포맷과 추천 점수 포맷을 search 엔진 계약으로 고정하고, 비용 요소 초안을 코드 상수로 정리했다.
- 수정 파일: `src/engine/search/astar_router.py`, `src/engine/search/score_function.py`, `src/services/simulation_service.py`, `AGENTS.md`
- 검증:
  - `python3 -c "from src.engine.search.astar_router import BusNodeSpec, RouteCandidateSpec, build_mock_route; start = BusNodeSpec('BUS_001', '서울', 37.5665, 126.9780); end = BusNodeSpec('BUS_011', '대구', 35.8714, 128.6014); hub = BusNodeSpec('BUS_007', '대전', 36.3504, 127.3845); candidate = RouteCandidateSpec('SITE_CENTRAL', '중앙 균형안', 36.28, 127.76, 41.0, 17.0); route = build_mock_route(start, end, candidate, via_bus=hub, load_scale=1.1); print(route.route_id, route.total_distance_km, route.estimated_cost, route.path_node_ids)"`
  - `python3 -c "from src.engine.search.score_function import CandidateScoreInput, calculate_mock_score, build_recommendation, rank_recommendations; from src.data.schemas import RouteResult; route_a = RouteResult(route_id='a', start_bus_id='BUS_001', end_bus_id='BUS_011'); route_b = RouteResult(route_id='b', start_bus_id='BUS_001', end_bus_id='BUS_011'); score_a = calculate_mock_score(CandidateScoreInput('SITE_A', 'A', 41.0, 17.0, 29.0, 4.0, 3.0, 1.1)); score_b = calculate_mock_score(CandidateScoreInput('SITE_B', 'B', 54.0, 15.0, 24.0, 3.0, 2.5, 1.1)); ranked = rank_recommendations([build_recommendation('SITE_A', 'A', route_a, score_a, 'a'), build_recommendation('SITE_B', 'B', route_b, score_b, 'b')]); print(score_a.total_score, score_b.total_score, [(item.candidate_id, item.rank) for item in ranked])"`
  - `python3 -c "from src.services.simulation_service import SimulationService; svc = SimulationService(); result = svc.run_mock_simulation(svc.build_default_input(load_scale=1.1)); print(result.selected_route.route_id, result.recommendations[0].candidate_id, result.recommendations[0].score.notes[1], result.warnings[0])"`
  - `python3 -m compileall app.py pages src`
- 다음 작업: `Prediction` 페이지까지 공통 `ScenarioContext`를 공유하도록 정리하고, 이후 실제 엔진 구현 전까지 fallback 규칙을 유지

### 2026-04-04 Prediction 공통화 완료
- 작업: `PredictionService`와 `Prediction` 페이지를 공통 `ScenarioContext`, `warnings`, `fallback` 흐름에 맞췄다.
- 수정 파일: `src/services/prediction_service.py`, `pages/03_prediction.py`, `AGENTS.md`
- 검증:
  - `python3 -c "from src.data.schemas import ScenarioContext; from src.services.prediction_service import PredictionService; scenario = ScenarioContext(scenario_id='shared-001'); result = PredictionService().run_mock_prediction(load_scale=1.1, scenario=scenario); print(result.scenario_id, result.scenario.scenario_id, result.fallback.mode, len(result.warnings))"`
  - `python3 -c "import runpy; runpy.run_path('pages/03_prediction.py'); print('prediction-page-run-ok')"`
  - `python3 -m compileall app.py pages src`
- 다음 작업: 1주차-박차오름 범위에서는 fallback 문구와 서비스 입력 패턴을 더 통일할지 점검하고, 이후 실제 엔진 구현 단계로 넘어가기

### 2026-04-04 서비스 인터페이스 미세정리 및 fallback 규칙 문서화 완료
- 작업: 세 서비스의 공통 입력 축을 `scenario`, `created_at`, `load_scale` 기준으로 정리하고, fallback 규칙 초안을 문서화했다.
- 수정 파일: `src/services/monitoring_service.py`, `src/services/simulation_service.py`, `src/services/prediction_service.py`, `pages/01_monitoring.py`, `AGENTS.md`
- 검증:
  - `python3 -c "from src.data.schemas import ScenarioContext; from src.services.monitoring_service import MonitoringService; from src.services.simulation_service import SimulationService; from src.services.prediction_service import PredictionService; scenario = ScenarioContext(scenario_id='shared-002'); monitoring = MonitoringService().run_mock_monitoring(scenario=scenario, created_at=None, load_scale=1.0); simulation = SimulationService().run_mock_simulation(SimulationService().build_default_input(scenario=scenario, created_at=None, load_scale=1.0)); prediction = PredictionService().run_mock_prediction(scenario=scenario, created_at=None, load_scale=1.0); print(monitoring.fallback.mode, simulation.fallback.mode, prediction.fallback.mode, monitoring.warnings[0], simulation.warnings[0], prediction.warnings[0])"`
  - `python3 -m compileall app.py pages src`
- 다음 작업: 1주차-박차오름 범위는 사실상 정리되었고, 이후에는 실제 엔진 치환 단계로 넘어가기

### 2026-04-04 Streamlit rerun 고려사항 문서화
- 작업: Streamlit rerun 구조를 작업 시 필수 고려사항으로 `AGENTS.md`에 명시했다.
- 수정 파일: `AGENTS.md`
- 검증: 문서 규칙 반영 확인
- 다음 작업: 실제 엔진 연결 단계에서 rerun-safe와 rerun-optimized 여부를 함께 점검

### 2026-04-04 랜딩 페이지 지도 요구사항 문서화
- 작업: 첫 랜딩 페이지의 지도 UX 방향을 `AGENTS.md`에 기록했다. `VWorld` 기반 대한민국 지도, 발전소/송전탑 표시, 좌측 패널 설치 UI, 지도 클릭 후 설정값 입력 흐름, 임시 에셋 교체 예정, `2.5D/3D` 우선 방향을 명시했다.
- 수정 파일: `AGENTS.md`
- 검증: 문서 규칙 반영 확인
- 다음 작업: 실제 랜딩 페이지 구현 단계에서 `VWorld` 연동 방식, 설치 인터랙션, `map_2_5d` fallback 적용 기준을 구체화

### 2026-04-04 설치 지점 3축 좌표 요구사항 문서화
- 작업: 대한민국 지형을 고려한 설치 지점 좌표를 `x, y, z` 3축 기준으로 다뤄야 한다는 요구사항을 `AGENTS.md`에 추가했다. `z`는 고도/지형 높이 정보로 간주하고, 후속 스키마와 지도 상호작용에서도 2차원 좌표로 축소하지 않도록 명시했다.
- 수정 파일: `AGENTS.md`
- 검증: 문서 규칙 반영 확인
- 다음 작업: 실제 랜딩 페이지 구현 단계에서 좌표 스키마, 지도 클릭 이벤트, 고도값 취득 방식과 `2.5D/3D` 표시 전략을 구체화

### 2026-04-09 지도 설계 상시 참조 규칙 문서화
- 작업: 브이월드 기반 랜딩 페이지의 지도 설계 원칙을 특정 주차 문맥이 아니라 상시 참조 규칙으로 정리했다. 지도 관련 작업을 시작할 때 `AGENTS.md`의 지도 섹션을 다시 읽도록 명시하고, `LOD + 영역별 정밀 조회`, 거시 표현용 폴리곤화/mesh 단순화, 클릭 시 고해상도 `x, y, z` 확정, 표현용 geometry와 분석용 좌표 분리, `map_2_5d` fallback 유지 원칙을 일반 규칙으로 정리했다.
- 수정 파일: `AGENTS.md`, `WORK_TIMELINE.md`
- 검증: 문서 규칙 반영 확인, `py -3 -m compileall app.py pages src`
- 다음 작업: 지도 어댑터와 좌표 스키마를 설계할 때 `조회 범위`, `좌표계`, `고도 산정 방식`, `fallback 메타데이터` 필드를 공통 계약으로 구체화

### 2026-04-09 Monitoring 페이지 bare-run 실패 수정
- 작업: `pages/01_monitoring.py`의 전체 선로 상태표에서 `pandas Styler` 의존성을 제거해 bare-run 실패를 없앴다. `st.dataframe(df.style...)`를 plain DataFrame 렌더링으로 바꾸고, 같은 위치의 `use_container_width` 인자도 `width="stretch"`로 정리했다.
- 수정 파일: `pages/01_monitoring.py`, `WORK_TIMELINE.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "import runpy; runpy.run_path('pages/01_monitoring.py'); print('monitoring-page-run-ok')"`
  - `python3 -c "from src.services.monitoring_service import MonitoringService; result = MonitoringService().run_mock_monitoring(load_scale=1.0); print(result.source, result.scenario.scenario_id, len(result.kpis), len(result.line_statuses), result.fallback.mode)"`
- 다음 작업: `streamlit run app.py` 기준으로 Monitoring/Simulation/Prediction 세 페이지가 실제 브라우저 환경에서도 같은 시나리오 흐름으로 안정적으로 열리는지 다시 점검

### 2026-04-09 박차오름 2주차 작업 문서 추가
- 작업: 박차오름의 2주차 `1순위 -> 4순위` 작업을 바로 따라갈 수 있도록 임시 체크리스트 문서 `PARK_CHAOREUM_WEEK2_TASKS.md`를 루트에 추가했다. `A* 최소 버전`, `점수화 v1`, `공통 결과 형식 통일`, `page-service-engine 연결 규칙 확정` 순서와 종료 후 파일 삭제 조건을 함께 기록했다.
- 수정 파일: `PARK_CHAOREUM_WEEK2_TASKS.md`, `WORK_TIMELINE.md`
- 검증: 문서 추가 및 삭제 조건 반영 확인
- 다음 작업: `PARK_CHAOREUM_WEEK2_TASKS.md` 기준으로 1순위 `A* 최소 버전 구현`부터 착수

### 2026-04-09 박차오름 2주차 1순위 A* 최소 버전 구현
- 작업: `src/engine/search/astar_router.py`에 실제 A* 최소 버전을 추가했다. 기존 `build_mock_route()`는 유지하고, `GraphEdgeSpec`, `build_k_nearest_edges()`, `build_astar_route()`를 추가해 `bus graph + candidate + via hub` 기준의 실제 경로 계산이 가능하도록 정리했다. 구간별 `start -> candidate -> end` 또는 `start -> via -> candidate -> end` 탐색, 경로 복원, 실제 `RouteResult` 반환, 비용 추정까지 포함했다. 2주차 임시 작업 문서에도 1순위 완료 상태를 체크했다.
- 수정 파일: `src/engine/search/astar_router.py`, `PARK_CHAOREUM_WEEK2_TASKS.md`, `WORK_TIMELINE.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "from src.engine.search.astar_router import BusNodeSpec, RouteCandidateSpec, build_astar_route, build_k_nearest_edges; buses=[BusNodeSpec('BUS_001','서울',37.5665,126.9780),BusNodeSpec('BUS_003','수원',37.2636,127.0286),BusNodeSpec('BUS_007','대전',36.3504,127.3845),BusNodeSpec('BUS_010','전주',35.8242,127.1480),BusNodeSpec('BUS_011','대구',35.8714,128.6014)]; candidate=RouteCandidateSpec('SITE_CENTRAL','중앙 균형안',36.28,127.76,41.0,17.0); route=build_astar_route(start_bus=buses[0], end_bus=buses[-1], candidate=candidate, bus_nodes=buses, edges=build_k_nearest_edges(buses, neighbor_count=2), via_bus=buses[2], load_scale=1.1); print(route.route_id, route.source, route.path_node_ids, round(route.total_distance_km,1), round(route.estimated_cost,1))"`
- 다음 작업: 2순위 `추천 점수화 v1 구현`에서 실제 route 결과를 입력으로 쓰는 점수 계산 함수와 정렬 로직을 정리

### 2026-04-09 박차오름 2주차 2순위 추천 점수화 v1 구현
- 작업: `src/engine/search/score_function.py`에 실제 route 반영 점수 계산 함수 `calculate_score()`를 추가했다. 기존 `calculate_mock_score()`는 유지하고, route 거리값 반영, 거리 초과 패널티, route 안정성 bonus, 정렬 tie-break 규칙까지 넣어 2주차용 점수화 v1을 분리했다. 임시 작업 문서에도 2순위 완료 상태를 체크했다.
- 수정 파일: `src/engine/search/score_function.py`, `PARK_CHAOREUM_WEEK2_TASKS.md`, `WORK_TIMELINE.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "from src.engine.search.score_function import CandidateScoreInput, calculate_score, build_recommendation, rank_recommendations; from src.data.schemas import RouteResult; route_a = RouteResult(route_id='astar-a', start_bus_id='BUS_001', end_bus_id='BUS_011', total_distance_km=39.0, source='astar'); route_b = RouteResult(route_id='astar-b', start_bus_id='BUS_001', end_bus_id='BUS_011', total_distance_km=60.0, source='astar'); score_a = calculate_score(CandidateScoreInput('SITE_A', 'A', 41.0, 17.0, 29.0, 4.0, 3.0, 1.1), route=route_a); score_b = calculate_score(CandidateScoreInput('SITE_B', 'B', 54.0, 15.0, 24.0, 3.0, 2.5, 1.1), route=route_b); ranked = rank_recommendations([build_recommendation('SITE_A', 'A', route_a, score_a, 'a'), build_recommendation('SITE_B', 'B', route_b, score_b, 'b')]); print(score_a.total_score, score_b.total_score, [(item.candidate_id, item.rank) for item in ranked], score_a.notes[1])"`
- 다음 작업: 3순위 `공통 결과 형식 통일`에서 route/score/service 반환 형식의 source, warnings, fallback 사용 규칙을 정리

### 2026-04-09 박차오름 2주차 3순위 공통 결과 형식 통일
- 작업: `SimulationService`의 actual 진입점과 search 엔진 출력이 기존 dataclass 계약을 그대로 쓰도록 정리했다. actual route는 `RouteResult(source='astar')`, actual score는 `ScoreBreakdown`으로 유지하고, `SimulationResult`는 `source`, `scenario`, `warnings`, `fallback` 메타데이터를 포함한 같은 반환 형식을 유지하도록 맞췄다. 아직 실제 power flow가 없는 delta는 partial `mock_data fallback`으로 명시했다.
- 수정 파일: `src/services/simulation_service.py`, `WORK_TIMELINE.md`
- 검증:
  - `python3 -c "from src.data.schemas import ScenarioContext; from src.services.simulation_service import SimulationService; scenario = ScenarioContext(scenario_id='sim-v1'); svc = SimulationService(); result = svc.run_simulation(svc.build_default_input(scenario=scenario, load_scale=1.1)); print({'source': result.source, 'scenario_id': result.scenario.scenario_id, 'route_source': result.selected_route.source if result.selected_route else None, 'route_id': result.selected_route.route_id if result.selected_route else None, 'top_candidate': result.recommendations[0].candidate_id if result.recommendations else None, 'top_score': result.recommendations[0].score.total_score if result.recommendations and result.recommendations[0].score else None, 'fallback': result.fallback.mode, 'warnings': result.warnings[:2]})"`
  - `python3 -c "from src.data.schemas import ScenarioContext; from src.services.monitoring_service import MonitoringService; from src.services.simulation_service import SimulationService; from src.services.prediction_service import PredictionService; scenario = ScenarioContext(scenario_id='shared-actual'); monitoring = MonitoringService().run_mock_monitoring(scenario=scenario, load_scale=1.0); simulation = SimulationService().run_simulation(SimulationService().build_default_input(scenario=scenario, load_scale=1.0)); prediction = PredictionService().run_mock_prediction(scenario=scenario, load_scale=1.0); print({'ids':[monitoring.scenario.scenario_id, simulation.scenario.scenario_id, prediction.scenario.scenario_id], 'simulation_source': simulation.source, 'route_source': simulation.selected_route.source if simulation.selected_route else None, 'fallback': simulation.fallback.mode})"`
- 다음 작업: 4순위 `page-service-engine 연결 규칙 확정`에서 Simulation 페이지가 actual route/score 결과를 직접 렌더링하도록 연결

### 2026-04-09 박차오름 2주차 4순위 page-service-engine 연결 규칙 확정
- 작업: `pages/02_simulation.py`가 더 이상 `run_mock_simulation()`을 직접 호출하지 않고 `SimulationService.run_simulation()`을 사용하도록 바꿨다. 서비스 내부 호출 흐름은 `입력 정규화 -> actual route/score 계산 -> delta mock fallback -> 결과 조립`으로 고정했고, 페이지는 서비스 반환 dataclass만 렌더링하도록 유지했다. 1~4순위가 끝나서 임시 작업 파일 `PARK_CHAOREUM_WEEK2_TASKS.md`도 규칙대로 삭제했다.
- 수정 파일: `src/services/simulation_service.py`, `pages/02_simulation.py`, `WORK_TIMELINE.md`, `PARK_CHAOREUM_WEEK2_TASKS.md(삭제)`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"`
  - `python3 -c "from src.data.schemas import ScenarioContext; from src.services.simulation_service import SimulationService; scenario = ScenarioContext(scenario_id='sim-v1'); svc = SimulationService(); result = svc.run_simulation(svc.build_default_input(scenario=scenario, load_scale=1.1)); print({'source': result.source, 'route_source': result.selected_route.source if result.selected_route else None, 'top_candidate': result.recommendations[0].candidate_id if result.recommendations else None, 'top_score': result.recommendations[0].score.total_score if result.recommendations and result.recommendations[0].score else None, 'fallback': result.fallback.mode})"`
- 다음 작업: `Monitoring`의 실제 계산값과 `Simulation`의 delta 계산을 연결해 partial `mock_data fallback` 범위를 줄이기

### 2026-04-09 Simulation delta actualization 시작
- 작업: `SimulationService.run_simulation()`의 설치 전후 delta 계산을 `MonitoringService.run_dc_power_flow()` 기준으로 연결했다. 설치 전 baseline은 실제 `DC Power Flow` 결과를 사용하고, 설치 후 값은 추천안의 `route/score`를 반영한 heuristic counterfactual로 계산하도록 `_build_actual_deltas()`를 추가했다. 이에 따라 `peak_utilization`, `risk_lines`, `losses`, `operating_margin`의 before 값이 mock 상수 대신 실제 혼잡 결과를 사용하도록 바뀌었다.
- 수정 파일: `src/services/simulation_service.py`, `WORK_TIMELINE.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "from src.data.schemas import ScenarioContext; from src.services.simulation_service import SimulationService; scenario = ScenarioContext(scenario_id='delta-actual'); svc = SimulationService(); result = svc.run_simulation(svc.build_default_input(scenario=scenario, load_scale=1.1)); print({'source': result.source, 'fallback': result.fallback.mode, 'warning0': result.warnings[0], 'warning1': result.warnings[1], 'deltas': [(d.metric_id, d.before_value, d.after_value, d.unit, d.status) for d in result.deltas]})"`
  - `python3 -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"`
- 다음 작업: heuristic after-state를 실제 counterfactual power flow에 더 가깝게 보정하거나, 추천 경로가 어떤 선로를 완화하는지 line-level 연결 규칙을 추가

### 2026-04-09 박차오름 2주차 3순위 메타데이터 형식 보강
- 작업: `src/services/result_metadata.py`를 추가해 서비스 결과 메타데이터 형식을 공통 헬퍼로 묶었다. `MonitoringService`, `SimulationService`, `PredictionService`가 모두 같은 경고 첫 문구 형식과 `FallbackInfo` 생성 규칙을 쓰도록 정리했다. 이에 따라 mock fallback 경고 첫 줄이 세 서비스에서 동일한 형식으로 맞춰졌고, 정상 경로인 `MonitoringService.run_dc_power_flow()`도 source 안내 문구 형식을 통일했다.
- 수정 파일: `src/services/result_metadata.py`, `src/services/monitoring_service.py`, `src/services/simulation_service.py`, `src/services/prediction_service.py`, `WORK_TIMELINE.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "from src.services.monitoring_service import MonitoringService; from src.services.simulation_service import SimulationService; from src.services.prediction_service import PredictionService; from src.data.schemas import ScenarioContext; scenario = ScenarioContext(scenario_id='meta-check'); m = MonitoringService().run_mock_monitoring(scenario=scenario); s = SimulationService().run_simulation(SimulationService().build_default_input(scenario=scenario)); p = PredictionService().run_mock_prediction(scenario=scenario); print({'monitoring_warning': m.warnings[0], 'simulation_warning': s.warnings[0], 'prediction_warning': p.warnings[0], 'monitoring_fallback': m.fallback.mode, 'simulation_fallback': s.fallback.mode, 'prediction_fallback': p.fallback.mode})"`
  - `python3 -c "from src.services.monitoring_service import MonitoringService; result = MonitoringService().run_dc_power_flow(load_scale=1.0); print(result.warnings[0], result.fallback.mode, result.source)"`
- 다음 작업: 사용자가 원할 때만 4순위 범위 변경을 이어가고, 기본적으로는 공통 계약/메타데이터 정합성 유지에 집중

### 2026-04-09 박차오름 4주차 A* 보정 및 통합 정리
- 작업: `A*` 경로 계산에서 `직결`과 `허브 경유` 경로를 둘 다 평가하고, 반복 노드와 과도한 우회를 패널티로 반영하는 보정 로직을 추가했다. 이에 따라 허브를 억지로 거치며 루프가 생기던 경로를 배제하고, `SimulationService`는 추천 생성, baseline 조회, 결과 조립 흐름을 helper 단위로 정리했다. 지도/3D 쪽은 현재 저장소 기준으로 `VWorld` 어댑터와 지도 페이지 구현이 없어서 `3D 보류 -> map_2_5d fallback`이 맞다는 판단 문서를 추가했다.
- 수정 파일: `src/engine/search/astar_router.py`, `src/engine/search/score_function.py`, `src/services/simulation_service.py`, `docs/map_feasibility_2026-04-09.md`, `WORK_TIMELINE.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "from src.services.simulation_service import SimulationService; from src.data.schemas import ScenarioContext; svc = SimulationService(); result = svc.run_simulation(svc.build_default_input(scenario=ScenarioContext(scenario_id='wk4-check'), load_scale=1.0)); print({'source': result.source, 'fallback': result.fallback.mode, 'summary': result.summary, 'warnings': result.warnings[:2]}); [print(rec.rank, rec.candidate_id, rec.route.total_distance_km if rec.route else None, rec.route.estimated_cost if rec.route else None, rec.route.path_node_ids if rec.route else None, rec.score.total_score if rec.score else None) for rec in result.recommendations]"`
  - `python3 -c "from src.engine.search.astar_router import build_astar_route; from src.services.simulation_service import SimulationService, _to_bus_node_spec, _to_route_candidate_spec, _get_candidate; svc = SimulationService(); bus_nodes = svc._build_bus_nodes(); edges = svc._build_bus_edges(bus_nodes); start = _to_bus_node_spec('BUS_001'); end = _to_bus_node_spec('BUS_011'); via = _to_bus_node_spec('BUS_007'); [print(candidate_id, route.total_distance_km, route.estimated_cost, route.path_node_ids) for candidate_id, route in [(candidate_id, build_astar_route(start, end, _to_route_candidate_spec(candidate_id, _get_candidate(candidate_id, index)), bus_nodes=bus_nodes, edges=edges, via_bus=via, load_scale=1.0)) for index, candidate_id in enumerate(['SITE_NORTH', 'SITE_CENTRAL', 'SITE_SOUTH'])]]"`
  - `python3 -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"`
- 다음 작업: `Beta`가 지도 오버레이를 붙일 때 `map_2_5d` fallback 규칙을 그대로 사용하고, `Simulation` 설치 후 counterfactual을 실제 power flow로 바꾸는 작업은 이후 통합 병목 제거 단계에서 진행

### 2026-04-10 예측 문서에 GNN 병렬 활용 계획 반영
- 작업: `AGENTS.md`와 `meeting_plan/MEETING_PLAN_2026-03-30.md`의 예측 계획을 `LSTM` 단일 중심에서 `LSTM+GNN` 병렬 활용 기준으로 확장했다. `PredictionService` 책임, forecast 엔진 후보, Gamma 역할, 주차별 예측 작업, fallback 문구를 함께 정리했다.
- 수정 파일: `AGENTS.md`, `meeting_plan/MEETING_PLAN_2026-03-30.md`, `WORK_TIMELINE.md`
- 검증:
  - `Select-String -Path AGENTS.md, meeting_plan/MEETING_PLAN_2026-03-30.md -Pattern 'GNN','LSTM' -Encoding UTF8`
- 다음 작업: `Prediction` 실제 구현 단계에서 `feature/graph` 입력 계약과 `LSTM/GNN` 병렬 결과 결합 규칙을 `src/data/schemas.py`와 예측 서비스 인터페이스 기준으로 구체화한다.

### 2026-04-13 1~2주차 계획 대비 구현 점검
- 작업: `meeting_plan/MEETING_PLAN_2026-03-30.md` 기준으로 1주차와 2주차 작업의 실제 구현 상태를 점검했다. `Monitoring`의 `dc_power_flow`와 `Simulation`의 `A*` 경로 흐름은 실제 값이 출력되는 것을 확인했다. 반면 `Prediction`의 baseline 실제 경로는 `PredictionService.run_baseline_prediction()` / `run_lstm_prediction()` 내부에서 `FallbackInfo` 미정의로 즉시 실패해, 2주차 완료 기준인 `예측 그래프 1개가 실제 값으로 나온다`는 아직 충족되지 않는다고 판단했다. 또한 `Prediction` 페이지는 baseline/LSTM 실패 시 mock으로 자동 전환하지 않고 `st.stop()`으로 중단되어 회의안의 fallback 원칙과도 어긋나는 상태임을 확인했다.
- 수정 파일: `WORK_TIMELINE.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "from src.services.monitoring_service import MonitoringService; r=MonitoringService().run_dc_power_flow(load_scale=1.0); print({'source': r.source, 'fallback': r.fallback.mode, 'lines': len(r.line_statuses), 'max_util': r.congestion_summary.max_utilization, 'warning0': r.warnings[0]})"`
  - `python3 -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_simulation(svc.build_default_input(load_scale=1.0)); print({'source': r.source, 'fallback': r.fallback.mode, 'route_source': r.selected_route.source if r.selected_route else None, 'recs': len(r.recommendations), 'deltas': len(r.deltas), 'warning0': r.warnings[0]})"`
  - `python3 -c "from src.services.prediction_service import PredictionService; r=PredictionService().run_mock_prediction(load_scale=1.0); print({'source': r.source, 'fallback': r.fallback.mode, 'preds': len(r.predictions), 'risks': len(r.risk_lines), 'warning0': r.warnings[0]})"`
  - `python3 -c "from pathlib import Path; from src.services.prediction_service import PredictionService; raw_dir=str(Path('data/raw').resolve()); r=PredictionService().run_baseline_prediction(raw_dir=raw_dir, load_scale=1.0); print({'source': r.source, 'fallback': r.fallback.mode, 'preds': len(r.predictions), 'risks': len(r.risk_lines)})"` -> `NameError: name 'FallbackInfo' is not defined`
  - `python3 -c "import runpy; runpy.run_path('pages/01_monitoring.py'); print('monitoring-page-run-ok')"`
  - `python3 -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"`
  - `python3 -c "import runpy; runpy.run_path('pages/03_prediction.py'); print('prediction-page-run-ok')"`
- 다음 작업: `PredictionService`의 baseline/LSTM 반환 경로를 실제로 동작하게 고치고, baseline/LSTM 실패 시 `mock_data` fallback으로 자동 전환되도록 서비스/페이지 흐름을 정리한다. 이후 필요하면 `GNN` 병렬 조합 구조를 회의안 기준으로 어디까지 2주차 범위로 볼지 다시 합의한다.

### 2026-04-13 1~2주차 진행 상황 재점검
- 작업: 회의안 기준으로 1주차, 2주차 완료 조건을 다시 대조했다. 1주차는 세 페이지가 모두 mock 기준으로 열리고 공통 시나리오/계약이 유지되어 완료로 봐도 무방하다고 판단했다. 2주차는 `MonitoringService.run_dc_power_flow()`와 `SimulationService.run_simulation()`이 실제 계산 경로를 반환하는 것을 다시 확인했지만, `PredictionService.run_baseline_prediction()`은 여전히 `FallbackInfo` import 누락으로 실패해 예측 실제 경로는 미완료 상태라고 정리했다. 추가로 `pages/03_prediction.py`는 baseline/LSTM 예외 시 mock fallback으로 전환하지 않고 `st.stop()`으로 중단되며, `feature_builder`는 입력 계약 정의만 존재하고 baseline/LSTM 경로에는 아직 연결되지 않은 상태도 확인했다.
- 수정 파일: `WORK_TIMELINE.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "from src.services.monitoring_service import MonitoringService; r=MonitoringService().run_dc_power_flow(load_scale=1.0); print({'source': r.source, 'fallback': r.fallback.mode, 'lines': len(r.line_statuses), 'max_util': r.congestion_summary.max_utilization, 'warning0': r.warnings[0] if r.warnings else None})"`
  - `python3 -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_simulation(svc.build_default_input(load_scale=1.0)); print({'source': r.source, 'fallback': r.fallback.mode, 'route_source': r.selected_route.source if r.selected_route else None, 'recs': len(r.recommendations), 'deltas': len(r.deltas), 'warning0': r.warnings[0] if r.warnings else None})"`
  - `python3 -c "from src.services.prediction_service import PredictionService; r=PredictionService().run_mock_prediction(load_scale=1.0); print({'source': r.source, 'fallback': r.fallback.mode, 'preds': len(r.predictions), 'risks': len(r.risk_lines), 'warning0': r.warnings[0] if r.warnings else None})"`
  - `python3 -c "from pathlib import Path; from src.services.prediction_service import PredictionService; raw_dir=str(Path('data/raw').resolve()); r=PredictionService().run_baseline_prediction(raw_dir=raw_dir, load_scale=1.0); print({'source': r.source, 'fallback': r.fallback.mode, 'preds': len(r.predictions), 'risks': len(r.risk_lines)})"` -> `NameError: name 'FallbackInfo' is not defined`
  - `python3 -c "import runpy; runpy.run_path('pages/01_monitoring.py'); print('monitoring-page-run-ok')"`
  - `python3 -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"`
  - `python3 -c "import runpy; runpy.run_path('pages/03_prediction.py'); print('prediction-page-run-ok')"`
- 다음 작업: `PredictionService`의 baseline/LSTM 정상 반환과 fallback 메타데이터를 먼저 고치고, `pages/03_prediction.py`에서 baseline/LSTM 실패 시 `mock_data` fallback으로 자동 전환되게 정리한다. 그 다음 `feature_builder`를 실제 예측 경로에 연결할지, 2주차 범위를 baseline 우선으로 닫을지 정리한다.

### 2026-04-13 Prediction baseline 정상 반환 복구
- 작업: `PredictionService.run_baseline_prediction()`의 정상 반환 경로를 복구했다. 반환부에서 사용하던 `FallbackInfo` 타입 import가 빠져 있어 baseline 실제 예측이 `NameError`로 실패하던 문제를 수정했다.
- 수정 파일: `src/services/prediction_service.py`, `WORK_TIMELINE.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "from pathlib import Path; from src.services.prediction_service import PredictionService; raw_dir=str(Path('data/raw').resolve()); r=PredictionService().run_baseline_prediction(raw_dir=raw_dir, load_scale=1.0); print({'source': r.source, 'fallback': r.fallback.mode, 'preds': len(r.predictions), 'risks': len(r.risk_lines), 'scenario_id': r.scenario_id})"`
- 다음 작업: `pages/03_prediction.py`에서 baseline/LSTM 실패 시 `mock_data` fallback으로 자동 전환되게 정리하고, 이어서 `PredictionService.run_lstm_prediction()`의 정상 반환과 실제 추론 경로를 점검한다.

### 2026-04-13 Prediction 페이지 fallback 자동 전환 정리
- 작업: `pages/03_prediction.py`에서 baseline/LSTM 예측 실패 시 더 이상 `st.stop()`으로 중단하지 않고 `PredictionService.run_mock_prediction()`으로 자동 전환되도록 정리했다. 페이지 내부에 `_run_prediction_with_fallback()` 헬퍼를 추가해 baseline 실제 경로는 그대로 유지하고, 실패 시에는 원인 문구를 `warnings`와 `fallback.reason`에 남긴 mock 결과를 렌더링하도록 바꿨다.
- 수정 파일: `pages/03_prediction.py`, `WORK_TIMELINE.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "import runpy; ns=runpy.run_path('pages/03_prediction.py'); helper=ns['_run_prediction_with_fallback']; svc=ns['PredictionService'](); ScenarioContext=ns['ScenarioContext']; result=helper(svc, model_source='Baseline', raw_dir='data/raw', load_scale=1.0, scenario=ScenarioContext(scenario_id='baseline-ok')); print({'source': result.source, 'fallback': result.fallback.mode, 'warnings0': result.warnings[0] if result.warnings else None, 'preds': len(result.predictions)})"`
  - `python3 -c "import runpy; ns=runpy.run_path('pages/03_prediction.py'); helper=ns['_run_prediction_with_fallback']; svc=ns['PredictionService'](); ScenarioContext=ns['ScenarioContext']; result=helper(svc, model_source='Baseline', raw_dir='data/__missing__', load_scale=1.0, scenario=ScenarioContext(scenario_id='baseline-fallback')); print({'source': result.source, 'fallback': result.fallback.mode, 'warnings0': result.warnings[0] if result.warnings else None, 'reason': result.fallback.reason})"`
  - `python3 -c "import runpy; runpy.run_path('pages/03_prediction.py'); print('prediction-page-run-ok')"`
- 다음 작업: `PredictionService.run_lstm_prediction()`의 정상 반환과 실제 학습/추론 경로를 점검하고, 필요한 경우 `Baseline`과 같은 수준으로 failure-to-mock fallback을 서비스 계층에도 통일한다.

### 2026-04-13 Prediction LSTM 정상 반환 및 추론 경로 점검
- 작업: `PredictionService.run_lstm_prediction()`의 정상 반환 경로를 복구하고 실제 학습/추론 흐름을 점검했다. 반환 메타데이터를 `build_no_fallback_info()` 기준으로 정리했고, 저장된 `model.keras`가 현재 Keras 환경에서 역직렬화되지 않을 때는 자동 재학습 후 예측을 계속 수행하도록 서비스 복구 경로를 추가했다. 이후 새로 저장된 모델이 재학습 없이도 바로 로드되는 것을 확인했고, 예외 원인 문구도 페이지에 그대로 노출되지 않도록 짧게 요약되게 정리했다.
- 수정 파일: `src/services/prediction_service.py`, `models/lstm/model.keras`, `models/lstm/scalers.pkl`, `WORK_TIMELINE.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "from pathlib import Path; from src.services.prediction_service import PredictionService; raw_dir=str(Path('data/raw').resolve()); r=PredictionService().run_lstm_prediction(raw_dir=raw_dir, load_scale=1.0, retrain=False, epochs=1); print({'source': r.source, 'fallback': r.fallback.mode, 'preds': len(r.predictions), 'risks': len(r.risk_lines), 'warnings': r.warnings[:2], 'scenario_id': r.scenario_id})"` -> 초기 저장 모델 호환성 문제를 자동 재학습으로 복구한 뒤 `source='lstm'`, `fallback='none'`, `preds=312`, `risks=2`
  - `python3 -c "from pathlib import Path; from src.services.prediction_service import PredictionService; raw_dir=str(Path('data/raw').resolve()); r=PredictionService().run_lstm_prediction(raw_dir=raw_dir, load_scale=1.0, retrain=False, epochs=1); print({'source': r.source, 'fallback': r.fallback.mode, 'preds': len(r.predictions), 'risks': len(r.risk_lines), 'warnings': r.warnings, 'scenario_id': r.scenario_id})"` -> 재실행 시 `warnings=[]`로 저장 모델 즉시 로드 확인
  - `python3 -c "from src.services.prediction_service import _summarize_lstm_model_error; exc=Exception('Unrecognized keyword arguments passed to Dense: {\\'quantization_config\\': None}\\nrest'); print(_summarize_lstm_model_error(exc))"` -> `저장된 model.keras가 현재 Keras 버전의 Dense 설정과 호환되지 않았습니다.`
- 다음 작업: `feature_builder`를 baseline/LSTM 실제 예측 경로에 연결할지 정리하고, 이어서 `Simulation` 설치 후 delta를 실제 counterfactual 계산으로 치환한다.

### 2026-04-13 Prediction feature_builder 실제 경로 연결
- 작업: `feature_builder`를 baseline/LSTM 실제 예측 경로에 연결했다. `src/engine/forecast/feature_builder.py`에 `build_prediction_feature_matrix()`를 추가해 예측 구간 24시간 × 노드별 `ForecastFeatureVector`를 서비스에서 공통으로 생성하도록 정리했고, `BaselineForecaster.predict()`는 이 feature contract의 `timestamp/hour/bus_id`를 직접 사용하도록 바꿨다. `LSTMForecaster.predict()`도 같은 `target_features`를 받아 출력 시각과 노드 순서를 그 계약에 맞추도록 수정했다. `PredictionService`는 baseline/LSTM 진입 전에 공통 feature matrix를 만들고 두 forecaster에 넘기도록 연결했다.
- 수정 파일: `src/engine/forecast/feature_builder.py`, `src/engine/forecast/baseline_forecaster.py`, `src/engine/forecast/lstm_forecaster.py`, `src/services/prediction_service.py`, `WORK_TIMELINE.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "from pathlib import Path; from src.data.adapters.public_data_adapter import load_kpx_csvs; from src.engine.forecast.feature_builder import build_prediction_feature_matrix; raw_dir=str(Path('data/raw').resolve()); load_df=load_kpx_csvs(raw_dir); features=build_prediction_feature_matrix(load_df=load_df, forecast_start=load_df['timestamp'].max()); print({'features': len(features), 'first_bus': features[0].bus_id, 'first_ts': str(features[0].timestamp), 'last_bus': features[-1].bus_id, 'last_ts': str(features[-1].timestamp), 'sample_lag_1h': features[0].load_lag_1h, 'sample_ratio': features[0].regional_demand_ratio})"` -> `features=312`
  - `python3 -c "from pathlib import Path; from src.services.prediction_service import PredictionService; raw_dir=str(Path('data/raw').resolve()); r=PredictionService().run_baseline_prediction(raw_dir=raw_dir, load_scale=1.0); print({'source': r.source, 'fallback': r.fallback.mode, 'preds': len(r.predictions), 'risks': len(r.risk_lines), 'first': (r.predictions[0].timestamp.isoformat(), r.predictions[0].bus_id)})"` -> `source='baseline'`, `fallback='none'`, `preds=312`
  - `python3 -c "from pathlib import Path; from src.services.prediction_service import PredictionService; raw_dir=str(Path('data/raw').resolve()); r=PredictionService().run_lstm_prediction(raw_dir=raw_dir, load_scale=1.0, retrain=False, epochs=1); print({'source': r.source, 'fallback': r.fallback.mode, 'preds': len(r.predictions), 'risks': len(r.risk_lines), 'warnings': r.warnings, 'first': (r.predictions[0].timestamp.isoformat(), r.predictions[0].bus_id)})"` -> `source='lstm'`, `fallback='none'`, `preds=312`, `warnings=[]`
  - `python3 -c "from pathlib import Path; from src.data.adapters.public_data_adapter import load_kpx_csvs; from src.engine.forecast.feature_builder import build_prediction_feature_matrix; from src.engine.forecast.baseline_forecaster import BaselineForecaster; raw_dir=str(Path('data/raw').resolve()); load_df=load_kpx_csvs(raw_dir); features=build_prediction_feature_matrix(load_df=load_df, forecast_start=load_df['timestamp'].max(), bus_ids=['BUS_001'])[:3]; preds=BaselineForecaster().fit(load_df).predict(target_features=features); print([(p.timestamp.isoformat(), p.bus_id) for p in preds])"` -> feature timestamp 순서 직접 반영 확인
  - `python3 -c "from pathlib import Path; from src.data.adapters.public_data_adapter import load_kpx_with_weather; from src.engine.forecast.feature_builder import build_prediction_feature_matrix; from src.engine.forecast.lstm_forecaster import LSTMForecaster; raw_dir=str(Path('data/raw').resolve()); load_df=load_kpx_with_weather(raw_dir); features=build_prediction_feature_matrix(load_df=load_df, forecast_start=load_df['timestamp'].max(), bus_ids=['BUS_001'])[:3]; preds=LSTMForecaster().predict(history_df=load_df, forecast_start=load_df['timestamp'].max(), target_features=features); print([(p.timestamp.isoformat(), p.bus_id) for p in preds])"` -> feature timestamp 순서 직접 반영 확인
- 다음 작업: `Simulation` 설치 후 delta를 heuristic counterfactual 대신 실제 counterfactual 계산으로 치환한다.

### 2026-04-13 Simulation counterfactual delta 실제 계산 연결
- 작업: `SimulationService.run_simulation()`의 설치 후 delta를 heuristic 계산이 아니라 실제 counterfactual DC Power Flow로 치환했다. 설치 전 baseline은 기존 `MonitoringService.run_dc_power_flow()`를 그대로 사용하고, 설치 후에는 상위 혼잡 선로에 병렬 지원선을 추가한 counterfactual line set으로 `dc_power_flow.solve()`를 다시 실행하도록 연결했다. 이 결과를 기준으로 `peak_utilization`, `risk_lines`, `losses`, `operating_margin` delta를 실제 조류 결과에서 계산하게 바꿨고, counterfactual 계산이 실패할 때만 기존 heuristic delta로 내려가도록 fallback 경로를 남겼다.
- 수정 파일: `src/services/simulation_service.py`, `WORK_TIMELINE.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_simulation(svc.build_default_input(load_scale=1.0)); print({'source': r.source, 'fallback': r.fallback.mode, 'warnings': r.warnings[:3], 'deltas': [(d.metric_id, d.before_value, d.after_value, d.improvement, d.status) for d in r.deltas]})"` -> `source='astar'`, `fallback='none'`, `peak_utilization 97.5 -> 85.3`, `risk_lines 6.0 -> 3.0`
  - `python3 -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_simulation(svc.build_default_input(load_scale=1.1)); print({'source': r.source, 'fallback': r.fallback.mode, 'peak': next(d for d in r.deltas if d.metric_id=='peak_utilization').improvement, 'risk': next(d for d in r.deltas if d.metric_id=='risk_lines').improvement, 'warnings': r.warnings[:3]})"` -> 고부하 시나리오에서도 `fallback='none'` 유지 확인
  - `python3 -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); sim=svc.build_default_input(load_scale=1.0); recs=svc._build_recommendations(sim, use_actual_route=True); before=svc._get_monitoring_baseline(simulation_input=sim, created_at=sim.scenario.created_at); after,_=svc._build_counterfactual_monitoring(simulation_input=sim, monitoring_before=before, top_recommendation=recs[0]); print({'before_top3': [(l.line_id, round(l.utilization,4)) for l in before.line_statuses[:3]], 'after_top3': [(l.line_id, round(l.utilization,4)) for l in after.line_statuses[:3]]})"` -> `L12/L06` 보강 후 상위 혼잡 선로 재배치 확인
  - `python3 -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"` -> bare-run 통과
- 다음 작업: `Monitoring` 입력 검증/오류 메시지 보강 또는 `Prediction`의 `GNN` 병렬 조합 범위를 정리한다.

### 2026-04-13 Monitoring 입력 검증 및 오류 메시지 보강
- 작업: `MonitoringService`에 입력 정규화와 검증을 추가했다. `load_scale`는 서비스에서 직접 검증해 `NaN`, 무한대, 0 이하 값은 명시적인 입력 오류로 처리하고, 권장 범위 `0.50× ~ 1.50×`를 벗어나면 결과는 유지하되 경고와 함께 범위 안으로 보정되도록 정리했다. `created_at`, `scenario` 타입 검증도 추가했고, `pages/01_monitoring.py`는 서비스 예외를 그대로 터뜨리지 않고 `입력 검증 실패` / `결과 생성 실패` 메시지로 나눠 보여주게 바꿨다.
- 수정 파일: `src/services/monitoring_service.py`, `pages/01_monitoring.py`, `WORK_TIMELINE.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "from src.services.monitoring_service import MonitoringService; r=MonitoringService().run_dc_power_flow(load_scale=1.0); print({'source': r.source, 'fallback': r.fallback.mode, 'load_scale': r.load_scale, 'warning0': r.warnings[0] if r.warnings else None, 'max_util': r.congestion_summary.max_utilization})"` -> 정상 actual 경로 유지
  - `python3 -c "from src.services.monitoring_service import MonitoringService; r=MonitoringService().run_dc_power_flow(load_scale=1.8); print({'source': r.source, 'fallback': r.fallback.mode, 'load_scale': r.load_scale, 'warnings': r.warnings[:2], 'max_util': r.congestion_summary.max_utilization})"` -> `load_scale=1.50` 보정과 경고 문구 확인
  - `python3 -c "from src.services.monitoring_service import MonitoringService; \ntry:\n    MonitoringService().run_dc_power_flow(load_scale=float('nan'))\nexcept Exception as exc:\n    print(type(exc).__name__, str(exc))"` -> `ValueError: load_scale는 NaN 또는 무한대가 아닌 유한한 숫자여야 합니다.`
  - `python3 -c "import runpy; runpy.run_path('pages/01_monitoring.py'); print('monitoring-page-run-ok')"` -> bare-run 통과
- 다음 작업: `Prediction`의 `GNN` 병렬 조합 범위를 정리할지, 아니면 Monitoring/Simulation 페이지의 Streamlit 경고와 UI 정리까지 이어갈지 결정한다.

### 2026-04-13 Prediction GNN 경로 및 LSTM+GNN 병렬 조합 정리
- 작업: `Prediction`에 그래프 기반 실제 예측 경로를 추가하고, `LSTM + GNN` 병렬 조합 구조를 정리했다. `src/engine/forecast/gnn_forecaster.py`를 새로 추가해 13-버스 인접 그래프와 최근 부하/이웃 부하/기온 편차를 함께 쓰는 최소 GNN 예측기를 구현했다. `PredictionService`에는 `run_gnn_prediction()`과 `run_hybrid_prediction()`을 추가해 GNN 단독 예측과 `LSTM 65% + GNN 35%` 가중 평균 hybrid 예측을 반환하게 했고, 병렬 조합 중 하나라도 실패하면 `baseline_model` fallback으로 자동 전환되게 정리했다. `pages/03_prediction.py`는 모델 선택지를 `Mock / Baseline / LSTM / GNN / LSTM+GNN`으로 확장하고, GNN 및 Hybrid 실행 경로를 같은 fallback 헬퍼에 연결했다. 공통 계약도 `src/data/schemas.py`의 `ResultSource`에 `gnn`, `hybrid`를 추가해 맞췄다.
- 수정 파일: `src/engine/forecast/gnn_forecaster.py`, `src/services/prediction_service.py`, `pages/03_prediction.py`, `src/data/schemas.py`, `WORK_TIMELINE.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "from pathlib import Path; from src.services.prediction_service import PredictionService; raw_dir=str(Path('data/raw').resolve()); r=PredictionService().run_gnn_prediction(raw_dir=raw_dir, load_scale=1.0); print({'source': r.source, 'fallback': r.fallback.mode, 'preds': len(r.predictions), 'risks': len(r.risk_lines), 'first': (r.predictions[0].timestamp.isoformat(), r.predictions[0].bus_id, r.predictions[0].predicted_load_mw)})"` -> `source='gnn'`, `fallback='none'`, `preds=312`, `risks=6`
  - `python3 -c "from pathlib import Path; from src.services.prediction_service import PredictionService; raw_dir=str(Path('data/raw').resolve()); r=PredictionService().run_hybrid_prediction(raw_dir=raw_dir, load_scale=1.0, retrain=False, epochs=1); print({'source': r.source, 'fallback': r.fallback.mode, 'preds': len(r.predictions), 'risks': len(r.risk_lines), 'warnings': r.warnings[:3], 'first': (r.predictions[0].timestamp.isoformat(), r.predictions[0].bus_id, r.predictions[0].predicted_load_mw)})"` -> `source='hybrid'`, `fallback='none'`, `preds=312`, `risks=5`
  - `python3 -c "import types; from pathlib import Path; from src.services.prediction_service import PredictionService; raw_dir=str(Path('data/raw').resolve()); svc=PredictionService(); svc.run_gnn_prediction=types.MethodType(lambda self, **kwargs: (_ for _ in ()).throw(RuntimeError('forced gnn failure')), svc); r=svc.run_hybrid_prediction(raw_dir=raw_dir, load_scale=1.0, retrain=False, epochs=1); print({'source': r.source, 'fallback': r.fallback.mode, 'warnings': r.warnings[:2], 'reason': r.fallback.reason, 'summary': r.summary[:80]})"` -> `source='baseline'`, `fallback='baseline_model'` fallback 확인
  - `python3 -c "import runpy; runpy.run_path('pages/03_prediction.py'); print('prediction-page-run-ok')"` -> bare-run 통과
- 다음 작업: `Prediction` hybrid 경로의 중복 weather load를 줄일지, 아니면 `Monitoring`/`Simulation` 페이지 UI와 경고 문구 정리를 이어갈지 정한다.

### 2026-04-13 Prediction hybrid 데이터 로드 최적화 및 서비스 정리
- 작업: `PredictionService` 내부를 정리해 baseline/LSTM/GNN/hybrid가 공통 helper를 통해 결과를 조립하도록 묶었다. 특히 `run_hybrid_prediction()`은 이제 weather 이력 로드와 target feature 생성을 한 번만 수행한 뒤 LSTM/GNN 분기에서 재사용하므로, 기존처럼 같은 기온 데이터를 두 번 읽지 않는다. 이 과정에서 baseline/LSTM/GNN 실제 경로는 그대로 유지하고, hybrid 실패 시 baseline fallback 동작도 동일하게 유지되도록 맞췄다.
- 수정 파일: `src/services/prediction_service.py`, `WORK_TIMELINE.md`
- 검증:
  - `python3 -m compileall app.py pages src`
  - `python3 -c "from pathlib import Path; from src.services.prediction_service import PredictionService; raw_dir=str(Path('data/raw').resolve()); r=PredictionService().run_lstm_prediction(raw_dir=raw_dir, load_scale=1.0, retrain=False, epochs=1); print({'source': r.source, 'fallback': r.fallback.mode, 'preds': len(r.predictions), 'risks': len(r.risk_lines), 'warnings': r.warnings[:2]})"` -> `source='lstm'`, `fallback='none'`, `preds=312`, `risks=5`
  - `python3 -c "from pathlib import Path; from src.services.prediction_service import PredictionService; raw_dir=str(Path('data/raw').resolve()); r=PredictionService().run_gnn_prediction(raw_dir=raw_dir, load_scale=1.0); print({'source': r.source, 'fallback': r.fallback.mode, 'preds': len(r.predictions), 'risks': len(r.risk_lines)})"` -> `source='gnn'`, `fallback='none'`, `preds=312`, `risks=6`
  - `python3 -c "from pathlib import Path; from src.services.prediction_service import PredictionService; raw_dir=str(Path('data/raw').resolve()); r=PredictionService().run_hybrid_prediction(raw_dir=raw_dir, load_scale=1.0, retrain=False, epochs=1); print({'source': r.source, 'fallback': r.fallback.mode, 'preds': len(r.predictions), 'risks': len(r.risk_lines), 'warnings': r.warnings[:3]})"` -> `source='hybrid'`, `fallback='none'`, `preds=312`, `risks=5`, weather load 1회
  - `python3 -c "import types; from pathlib import Path; from src.services.prediction_service import PredictionService; raw_dir=str(Path('data/raw').resolve()); svc=PredictionService(); svc.run_baseline_prediction=types.MethodType(PredictionService.run_baseline_prediction, svc); svc._predict_gnn=types.MethodType(lambda self, **kwargs: (_ for _ in ()).throw(RuntimeError('forced gnn failure')), svc); r=svc.run_hybrid_prediction(raw_dir=raw_dir, load_scale=1.0, retrain=False, epochs=1); print({'source': r.source, 'fallback': r.fallback.mode, 'warnings': r.warnings[:2], 'reason': r.fallback.reason})"` -> `source='baseline'`, `fallback='baseline_model'`
  - `python3 -c "import runpy; runpy.run_path('pages/03_prediction.py'); print('prediction-page-run-ok')"` -> bare-run 통과
- 다음 작업: 2주차 범위는 종료로 보고, 이후에는 3주차 범위 또는 지도/시나리오 저장 같은 확장 작업으로 넘어간다.

### MVP 완성 이후 예정 - AI 경로 최적화 학습/검증
- 작업: MVP 기능이 완성되면 AI 기반 송전망 경로 최적화를 위해 최적화와 학습을 반복 수행하고, 추천 품질이 실제로 개선되는지 검증한다. 기준 시나리오 대비 경로 비용, 혼잡 완화, 설치 제약 충족률, 재현성, fallback 전환 조건을 함께 점검한다.
- 수정 파일: `미정 (예상 범위: src/engine/search/*, src/engine/optimize/*, src/services/simulation_service.py, 검증 문서)`
- 검증: `MVP 완성 이후 수행 예정`
- 다음 작업: MVP 범위의 지도/엔진/서비스 연결을 먼저 완료한 뒤 학습 데이터셋, 평가지표, 반복 검증 루프를 설계한다.

### 2026-05-06 1~3주차 구조 및 완성도 점검
- 작업: 현재 파일/디렉토리 구조와 `meeting_plan/MEETING_PLAN_2026-03-30.md`의 1~3주차 역할별 완료 상태를 점검했다. 서비스 기준으로 Monitoring DC Power Flow, Simulation A*/counterfactual delta, Prediction baseline/GNN/hybrid 실제 결과가 반환되는 것을 확인했다. 단, `pages/02_simulation.py`는 `folium`, `streamlit_folium` 의존성이 `requirements.txt`에 없어 fresh 환경 bare-run이 실패하며, `ScenarioService`, VWorld 어댑터, 도메인 모델, tests 실코드는 아직 스텁/문서 수준임을 확인했다.
- 수정 파일: `WORK_TIMELINE.md`
- 검증:
  - `.venv310/bin/python -m compileall app.py pages src`
  - `.venv310/bin/python -c "from src.services.monitoring_service import MonitoringService; r=MonitoringService().run_dc_power_flow(load_scale=1.0); print({'source': r.source, 'fallback': r.fallback.mode, 'lines': len(r.line_statuses), 'max_util': r.congestion_summary.max_utilization, 'warnings': r.warnings[:2]})"` -> `source='dc_power_flow'`, `fallback='none'`, `lines=15`
  - `.venv310/bin/python -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_simulation(svc.build_default_input(load_scale=1.0)); print({'source': r.source, 'fallback': r.fallback.mode, 'route_source': r.selected_route.source if r.selected_route else None, 'recs': len(r.recommendations)})"` -> `source='astar'`, `fallback='none'`, `route_source='astar'`, `recs=3`
  - `.venv310/bin/python -c "from pathlib import Path; from src.services.prediction_service import PredictionService; raw_dir=str(Path('data/raw').resolve()); r=PredictionService().run_hybrid_prediction(raw_dir=raw_dir, load_scale=1.0, retrain=False, epochs=1); print({'source': r.source, 'fallback': r.fallback.mode, 'preds': len(r.predictions), 'risks': len(r.risk_lines)})"` -> `source='hybrid'`, `fallback='none'`, `preds=312`
  - `.venv310/bin/python -c "import runpy; runpy.run_path('pages/01_monitoring.py'); print('monitoring-page-run-ok')"` -> 통과
  - `.venv310/bin/python -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"` -> `ModuleNotFoundError: No module named 'folium'`
  - `.venv310/bin/python -c "import runpy; runpy.run_path('pages/03_prediction.py'); print('prediction-page-run-ok')"` -> 통과
- 다음 작업: `folium`/`streamlit-folium` 의존성 누락을 정리하고, Simulation 페이지가 공통 `ScenarioContext`를 명시적으로 공유하도록 보정한 뒤 `ScenarioService` 저장/불러오기와 지도/VWorld 스키마를 3주차 범위로 이어서 구현한다.

### 2026-05-06 Beta 1~2주차 우선순위 1 임시 작업 목록 작성
- 작업: Beta 1~2주차 100% 완료의 선결 조건인 Simulation 페이지 지도 의존성 복구 작업을 임시 체크리스트로 정리했다. `folium`, `streamlit-folium` 의존성 추가, 현재 가상환경 설치, import 검증, Simulation 페이지 bare-run, 전체 compileall, 결과 기록 순서로 나눴다.
- 수정 파일: `tmp_tasks/BETA_WEEK1_2_PRIORITY1.md`, `WORK_TIMELINE.md`
- 검증: 문서 추가 확인
- 다음 작업: 체크리스트 1번부터 순서대로 실행해 `requirements.txt`와 `.venv310` 환경을 맞추고 `pages/02_simulation.py` bare-run 실패를 해소한다.

### 2026-05-06 Beta 1~2주차 우선순위 2 임시 작업 목록 작성
- 작업: Beta 1~2주차 100% 완료를 위해 Simulation 페이지의 후보지별 추천 결과표와 선택 추천안 요약 작업을 임시 체크리스트로 정리했다. 3주차 범위인 시나리오 저장/불러오기는 제외하고, 추천 결과표, 1순위 요약 카드, 추천 근거, fallback/warnings 표시, 입력-결과 연결 표시, 빈 후보지 처리, 검증 명령까지 실행 단위로 나눴다.
- 수정 파일: `tmp_tasks/BETA_WEEK1_2_PRIORITY2.md`, `WORK_TIMELINE.md`
- 검증: 문서 추가 확인
- 다음 작업: 우선순위 1 완료 후 `tmp_tasks/BETA_WEEK1_2_PRIORITY2.md` 순서대로 `pages/02_simulation.py`의 추천 결과 렌더링을 보강한다.

### 2026-05-06 박차오름 3주차 우선순위 3 임시 작업 목록 작성
- 작업: 박차오름 3주차 100% 완료를 위해 Simulation 페이지가 Monitoring/Prediction과 같은 `ScenarioContext`를 공유하도록 만드는 작업을 임시 체크리스트로 정리했다. `pages/02_simulation.py`에 `_get_shared_scenario()`를 추가하고, `SimulationInput` 생성 시 shared scenario를 전달하며, 결과 scenario를 session state에 다시 저장하고, 화면과 검증 명령으로 같은 `scenario_id`를 확인하는 순서로 나눴다.
- 수정 파일: `tmp_tasks/PARK_WEEK3_PRIORITY3_SHARED_SCENARIO.md`, `WORK_TIMELINE.md`
- 검증: 문서 추가 확인
- 다음 작업: 우선순위 1의 지도 의존성 복구 후 `pages/02_simulation.py`에 shared scenario 통합을 적용하고 서비스/페이지 검증을 실행한다.

### 2026-05-06 박차오름 3주차 우선순위 4 임시 작업 목록 작성
- 작업: 박차오름 3주차 100% 완료를 위해 후보지 추천 점수에 실제 counterfactual delta와 혼잡 완화 근거를 반영하는 작업을 임시 체크리스트로 정리했다. `score_function.py`의 impact 입력과 bonus 계산, `SimulationService`의 후보별 counterfactual impact 계산, 1순위 delta 재사용, 추천 rationale 보강, fallback/warnings 정리, 서비스/회귀 검증 명령까지 실행 단위로 나눴다.
- 수정 파일: `tmp_tasks/PARK_WEEK3_PRIORITY4_SCORE_WITH_DELTA.md`, `WORK_TIMELINE.md`
- 검증: 문서 추가 확인
- 다음 작업: 우선순위 3의 shared scenario 통합 후 `src/engine/search/score_function.py`와 `src/services/simulation_service.py`에 후보별 delta 기반 점수화를 적용한다.

### 2026-05-06 Gamma 3주차 우선순위 5 임시 작업 목록 작성
- 작업: Gamma 3주차 100% 완료를 위해 Prediction 테스트/QA 보강 작업을 임시 체크리스트로 정리했다. `feature_builder` 계약, PredictionService mock/baseline/GNN/hybrid 반환 계약, hybrid 조합 및 fallback, 위험도/설명 출력, pytest marker와 검증 명령, LSTM slow 테스트 분리 기준까지 실행 단위로 나눴다.
- 수정 파일: `tmp_tasks/GAMMA_WEEK3_PRIORITY5_PREDICTION_TESTS.md`, `WORK_TIMELINE.md`
- 검증: 문서 추가 확인
- 다음 작업: `tests/test_prediction_feature_builder.py`, `tests/test_prediction_service_contract.py`, `tests/test_prediction_risk_and_fallback.py`를 추가하고 빠른 pytest와 compileall 검증을 실행한다.

### 2026-05-06 우선순위 MD 전수 재검토 및 보정
- 작업: 우선순위 MD 작성 당시에는 핵심 파일 중심으로 확인했으나, 이번에 `.py`, 주요 `.md`, 설정 파일, 임시 작업 문서 전체를 다시 확인했다. 바이너리 모델, PDF/PPTX, CSV 원본 데이터는 코드가 아니므로 존재 여부와 연동 관계만 확인했다. 재검토 결과 기존 우선순위 방향은 유지하되, `pages/02_simulation.py`의 top-level `folium` import, 페이지 직접 `dc_power_flow` 지도 표시, `SimulationService`의 `created_at` 처리, counterfactual score 계산 순환 가능성, Prediction 테스트의 외부 weather 호출 가능성을 각 우선순위 문서에 보강했다.
- 수정 파일: `tmp_tasks/BETA_WEEK1_2_PRIORITY1.md`, `tmp_tasks/BETA_WEEK1_2_PRIORITY2.md`, `tmp_tasks/PARK_WEEK3_PRIORITY3_SHARED_SCENARIO.md`, `tmp_tasks/PARK_WEEK3_PRIORITY4_SCORE_WITH_DELTA.md`, `tmp_tasks/GAMMA_WEEK3_PRIORITY5_PREDICTION_TESTS.md`, `WORK_TIMELINE.md`
- 검증:
  - `git status --short`
  - `rg --files --hidden -g '!__pycache__' -g '!*.pyc' -g '!.git/**' -g '!.idea/**' -g '!.venv/**' -g '!.venv310/**'`
  - `find . -path './.git' -prune -o -path './.idea' -prune -o -path './.venv' -prune -o -path './.venv310' -prune -o -path './__pycache__' -prune -o -type f -name '*.py' -print`
  - `find . -path './.git' -prune -o -path './.idea' -prune -o -path './.venv' -prune -o -path './.venv310' -prune -o -path './__pycache__' -prune -o -type f -name '*.md' -print`
  - `rg -n "folium|streamlit_folium|sgop_shared_scenario|CandidateImpact|pytest|_load_weather_history|fetch_historical|use_container_width|width=\"stretch\""`
  - `wc -l app.py pages/*.py src/**/*.py src/**/**/*.py tmp_tasks/*.md requirements.txt meeting_plan/*.md DEVELOPMENT_FLOW_2026-03-30.md docs/*.md tests/*.md README.md`
- 다음 작업: 문서 보정된 순서대로 우선순위 1부터 구현하되, 이번 작업 범위에서는 실제 코드 구현을 진행하지 않는다.

### 2026-05-06 Beta 1~2주차 우선순위 1 완료
- 작업: Simulation 페이지가 새 환경에서도 import 오류 없이 실행되도록 지도 의존성을 정리했다. `requirements.txt`에 `folium>=0.16`, `streamlit-folium>=0.20`을 추가했고, 현재 `.venv310` 환경에는 `folium 0.20.0`, `streamlit-folium 0.26.2`가 설치되었다. 최초 sandbox 실행은 네트워크 제한으로 실패했으며, 승인된 pip install 실행으로 설치를 완료했다.
- 수정 파일: `requirements.txt`, `WORK_TIMELINE.md`
- 검증:
  - `.venv310/bin/python -m pip install folium streamlit-folium` -> 최초 sandbox 실행은 DNS/network 제한으로 실패
  - `.venv310/bin/python -m pip install folium streamlit-folium` -> 승인 실행 후 `Successfully installed branca-0.8.2 folium-0.20.0 streamlit-folium-0.26.2 xyzservices-2026.3.0`
  - `.venv310/bin/python -m pip show folium streamlit-folium` -> `folium 0.20.0`, `streamlit-folium 0.26.2`
  - `.venv310/bin/python -c "import folium; from streamlit_folium import st_folium; print('map-import-ok')"` -> `map-import-ok`
  - `.venv310/bin/python -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"` -> `simulation-page-run-ok`
  - `.venv310/bin/python -m compileall app.py pages src` -> 통과
  - `.venv310/bin/python -m pip install -r requirements.txt` -> 모든 요구 패키지 충족 확인
- 다음 작업: 우선순위 2로 넘어가 `pages/02_simulation.py`에 후보지별 추천 결과표, 1순위 추천안 요약, warnings/fallback 표시를 보강한다.

### 2026-05-06 전체 구조 및 코드 내용 파악
- 작업: 사용자 요청에 따라 저장소 전체 디렉터리 구조, Python 코드, 주요 문서, 임시 작업 문서, 설정, 데이터/모델 산출물의 역할을 전수 파악했다. 코드 기준 현재 핵심 흐름은 `app.py -> pages/* -> src/services/* -> src/engine/* -> src/data/*`이며, Monitoring은 DC Power Flow actual 경로, Simulation은 A*와 counterfactual delta actual 경로, Prediction은 baseline/LSTM/GNN/hybrid 경로가 연결되어 있다. 반면 `ScenarioService`, VWorld 어댑터, domain 모델, optimization/explain/recommend 일부, 실제 pytest 파일은 아직 스텁/문서 수준이다.
- 수정 파일: `WORK_TIMELINE.md`
- 검증:
  - `git status --short`
  - `rg --files --hidden -g '!.git/**' -g '!.idea/**' -g '!.venv/**' -g '!.venv310/**' -g '!__pycache__/**' -g '!*.pyc'`
  - `wc -l app.py pages/*.py src/**/*.py src/**/**/*.py *.md meeting_plan/*.md docs/*.md tests/*.md tmp_tasks/*.md requirements.txt .streamlit/config.toml`
  - `python3 -m compileall app.py pages src` -> 통과
  - `.venv310/bin/python -c "from src.services.monitoring_service import MonitoringService; r=MonitoringService().run_dc_power_flow(load_scale=1.0); print({'source': r.source, 'fallback': r.fallback.mode, 'lines': len(r.line_statuses), 'max_util': r.congestion_summary.max_utilization})"` -> `source='dc_power_flow'`, `fallback='none'`, `lines=15`
  - `.venv310/bin/python -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_simulation(svc.build_default_input(load_scale=1.0)); print({'source': r.source, 'fallback': r.fallback.mode, 'recs': len(r.recommendations), 'top': r.recommendations[0].candidate_id if r.recommendations else None})"` -> `source='astar'`, `fallback='none'`, `recs=3`
  - `.venv310/bin/python -c "from pathlib import Path; from src.services.prediction_service import PredictionService; raw_dir=str(Path('data/raw').resolve()); r=PredictionService().run_baseline_prediction(raw_dir=raw_dir, load_scale=1.0); print({'source': r.source, 'fallback': r.fallback.mode, 'preds': len(r.predictions), 'risks': len(r.risk_lines)})"` -> `source='baseline'`, `fallback='none'`, `preds=312`
  - `.venv310/bin/python -c "import runpy; runpy.run_path('pages/01_monitoring.py'); print('monitoring-page-run-ok')"` -> 통과, Streamlit bare-mode 경고와 `use_container_width` deprecation 경고 확인
  - `.venv310/bin/python -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"` -> 통과, Streamlit bare-mode 경고 확인
  - `.venv310/bin/python -c "import runpy; runpy.run_path('pages/03_prediction.py'); print('prediction-page-run-ok')"` -> 통과, Streamlit bare-mode 경고 확인
- 다음 작업: 기존 타임라인의 우선순위대로 `pages/02_simulation.py` 추천 결과 렌더링 보강, Simulation shared scenario 통합, 후보별 counterfactual delta 기반 점수화, Prediction 테스트 추가를 순서대로 진행한다.

### 2026-05-06 Beta 1~2주차 우선순위 2 완료
- 작업: `pages/02_simulation.py`에 후보지별 추천 결과표와 1순위 추천안 요약을 추가했다. 페이지 내부 helper로 `SimulationResult.recommendations`를 표 데이터로 변환하고, 1순위 후보의 총점/경로 길이/예상 비용/경유 노드와 route summary/rationale을 delta보다 먼저 보여주도록 정리했다. 또한 입력값 요약, fallback/warnings 표시, 후보지 미선택 시 기본 후보 사용 안내, 후보지별 추천 근거 expander를 추가했다. 서비스 계산과 지도 직접 계산 구조는 이번 Beta 1~2주차 범위 밖이라 그대로 유지했다.
- 수정 파일: `pages/02_simulation.py`, `WORK_TIMELINE.md`
- 검증:
  - `.venv310/bin/python -m compileall app.py pages src` -> 통과
  - `.venv310/bin/python -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"` -> 통과, Streamlit bare-mode 경고 확인
  - `.venv310/bin/python -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_simulation(svc.build_default_input(load_scale=1.0)); print({'source': r.source, 'fallback': r.fallback.mode, 'recs': len(r.recommendations), 'top': r.recommendations[0].candidate_id if r.recommendations else None, 'route': r.selected_route.route_id if r.selected_route else None})"` -> `source='astar'`, `fallback='none'`, `recs=3`, `top='SITE_SOUTH'`
  - `.venv310/bin/python -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_simulation(svc.build_default_input(candidate_site_ids=[], load_scale=1.0)); print({'candidates': len(r.simulation_input.candidate_site_ids), 'recs': len(r.recommendations), 'top': r.recommendations[0].candidate_id if r.recommendations else None})"` -> 후보지 0개 입력 시 기본 후보 3개 사용 확인
- 다음 작업: `PARK_WEEK3_PRIORITY3_SHARED_SCENARIO.md` 기준으로 Simulation 페이지가 Monitoring/Prediction과 같은 `ScenarioContext`를 공유하도록 통합한다.

### 2026-05-06 Gamma 3주차 우선순위 5 완료
- 작업: Prediction 파트의 빠른 pytest 테스트를 추가했다. `tests/conftest.py`에 synthetic load/weather fixture와 prediction helper를 두고, `feature_builder`의 lag/time/matrix 계약, `PredictionService.run_mock_prediction()` 반환 계약, `BaselineForecaster`와 `GNNForecaster`의 synthetic 예측 계약, `PredictionService.run_gnn_prediction()`의 synthetic weather 경로, hybrid 가중 평균/키 불일치, hybrid 실패 시 baseline fallback, 위험 선로 정렬/설명 출력을 검증했다. 실제 LSTM 모델 로드/학습 테스트는 기본 빠른 테스트에서 제외하고, `pytest.ini`에 `integration`, `slow` marker를 등록해 후속 분리 기준을 마련했다.
- 수정 파일: `pytest.ini`, `tests/conftest.py`, `tests/test_prediction_feature_builder.py`, `tests/test_prediction_service_contract.py`, `tests/test_prediction_risk_and_fallback.py`, `WORK_TIMELINE.md`
- 검증:
  - `.venv310/bin/python -m pytest tests -q` -> 11개 통과
  - `.venv310/bin/python -m pytest tests -q -m "not integration and not slow"` -> 11개 통과
  - `.venv310/bin/python -m pytest tests/test_prediction_feature_builder.py -q` -> 3개 통과
  - `.venv310/bin/python -m compileall app.py pages src tests` -> 통과
- 남은 테스트 갭: 실제 `data/raw` 기반 baseline/GNN 통합 테스트와 저장된 LSTM 모델 로드/재학습 테스트는 아직 포함하지 않았다. 이 둘은 외부 데이터/모델 상태와 실행 시간이 개입되므로 후속 `integration` 또는 `slow` 테스트로 분리하는 것이 맞다.
- 다음 작업: `PARK_WEEK3_PRIORITY3_SHARED_SCENARIO.md` 기준으로 Simulation 페이지 shared `ScenarioContext` 통합을 진행하거나, Prediction 통합/slow 테스트를 별도 범위로 추가한다.

### 2026-05-06 박차오름 3주차 우선순위 3 완료
- 작업: `pages/02_simulation.py`가 Monitoring/Prediction과 같은 Streamlit session state 키인 `sgop_shared_scenario`를 사용하도록 통합했다. Simulation 페이지에 `_get_shared_scenario()`를 추가하고, `SimulationService.build_default_input()`과 `run_simulation()` 호출에 shared `ScenarioContext`와 기준 시각을 전달하도록 변경했다. 결과 반환 후에는 `sim_result.scenario`를 다시 session state에 저장하며, 화면 caption에 `scenario_id`를 표시해 입력-결과 연결 상태를 확인할 수 있게 했다. 시나리오 저장/불러오기는 이번 범위에서 제외했다.
- 수정 파일: `pages/02_simulation.py`, `WORK_TIMELINE.md`
- 검증:
  - `.venv310/bin/python -c "from src.data.schemas import ScenarioContext; from src.services.monitoring_service import MonitoringService; from src.services.simulation_service import SimulationService; from src.services.prediction_service import PredictionService; scenario=ScenarioContext(scenario_id='shared-week3'); monitoring=MonitoringService().run_dc_power_flow(scenario=scenario, load_scale=1.0); svc=SimulationService(); simulation=svc.run_simulation(svc.build_default_input(scenario=scenario, load_scale=1.0)); prediction=PredictionService().run_mock_prediction(scenario=scenario, load_scale=1.0); print([monitoring.scenario.scenario_id, simulation.scenario.scenario_id, prediction.scenario.scenario_id], simulation.source, simulation.fallback.mode)"` -> `['shared-week3', 'shared-week3', 'shared-week3'] astar none`
  - `.venv310/bin/python -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"` -> 통과, Streamlit bare-mode 경고 확인
  - `.venv310/bin/python -m compileall app.py pages src` -> 통과
- 다음 작업: `PARK_WEEK3_PRIORITY4_SCORE_WITH_DELTA.md` 기준으로 후보지별 추천 점수에 실제 counterfactual delta와 혼잡 완화 근거를 반영한다.

### 2026-05-06 박차오름 3주차 우선순위 4 완료
- 작업: 후보지 추천 점수에 후보별 counterfactual delta 기반 impact를 반영했다. `score_function.py`에 `CandidateImpactInput`과 counterfactual bonus 산식을 추가하고, `calculate_score()`가 실제 최대 이용률 개선, 위험 선로 감소, 손실 감소, 운영 여유도 증가를 `ScoreBreakdown.congestion_relief`와 `notes`에 반영하도록 확장했다. `SimulationService.run_simulation()`은 이제 monitoring baseline을 먼저 계산한 뒤 후보별 route/base score/counterfactual delta/final score를 만들고 rank를 정한다. 최종 `SimulationResult.deltas`는 1순위 후보 점수화에 사용된 delta를 재사용한다. 후보별 impact 계산 실패는 해당 후보 notes/warnings에만 남기고 전체 simulation fallback으로 전파하지 않게 했다.
- 수정 파일: `src/engine/search/score_function.py`, `src/services/simulation_service.py`, `WORK_TIMELINE.md`
- 검증:
  - `.venv310/bin/python -m compileall app.py pages src` -> 통과
  - `.venv310/bin/python -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_simulation(svc.build_default_input(load_scale=1.0)); print({'source': r.source, 'fallback': r.fallback.mode, 'top': r.recommendations[0].candidate_id, 'top_score': r.recommendations[0].score.total_score, 'notes': r.recommendations[0].score.notes, 'deltas': [(d.metric_id, d.improvement) for d in r.deltas]})"` -> `source='astar'`, `fallback='none'`, top `SITE_SOUTH`, notes에 counterfactual 개선 근거와 bonus 반영 확인
  - `.venv310/bin/python -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_simulation(svc.build_default_input(load_scale=1.0)); [print(rec.rank, rec.candidate_id, rec.score.total_score, rec.score.congestion_relief, rec.score.notes[-2:]) for rec in r.recommendations]"` -> 후보 3개 모두 final score와 counterfactual notes 확인
  - `.venv310/bin/python -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_simulation(svc.build_default_input(load_scale=1.2)); print({'source': r.source, 'fallback': r.fallback.mode, 'top': r.recommendations[0].candidate_id, 'warnings': r.warnings[:5], 'deltas': [(d.metric_id, d.before_value, d.after_value, d.improvement) for d in r.deltas]})"` -> 고부하 조건에서도 actual 경로 유지
  - `.venv310/bin/python -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_mock_simulation(svc.build_default_input(load_scale=1.0)); print({'source': r.source, 'fallback': r.fallback.mode, 'recs': len(r.recommendations), 'top': r.recommendations[0].candidate_id})"` -> mock 경로 유지
  - `.venv310/bin/python -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); svc._build_counterfactual_monitoring=lambda **kwargs: (_ for _ in ()).throw(RuntimeError('forced candidate impact failure')); r=svc.run_simulation(svc.build_default_input(load_scale=1.0)); print({'source': r.source, 'fallback': r.fallback.mode, 'warnings': r.warnings[:2], 'top': r.recommendations[0].candidate_id, 'notes': r.recommendations[0].score.notes[-2:]})"` -> 후보별 impact 실패가 전체 fallback으로 전파되지 않음
  - `.venv310/bin/python -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"` -> 통과, Streamlit bare-mode 경고 확인
  - `.venv310/bin/python -m pytest tests -q` -> 11개 통과
- 다음 작업: Beta 3주차 범위의 시나리오 저장/불러오기 또는 `ScenarioService` 저장 책임 구현을 진행한다.

### 2026-05-11 박차오름 4주차 우선순위 1 ScenarioService 최소 구현 완료
- 작업: 박차오름 4주차 통합 로직 정리의 선행 작업으로 `ScenarioService` 저장 계층을 구현했다. 기본 저장 위치는 `data/private/scenarios.json`로 두고, 테스트 가능하도록 `storage_path` 주입을 지원한다. `ScenarioContext`를 JSON으로 저장/조회/목록화/삭제할 수 있게 했고, `created_at`은 ISO 문자열로 직렬화 후 복원한다. 같은 `scenario_id` 저장은 덮어쓰기 방식으로 처리하며, 빈 `scenario_id`, 잘못된 JSON 저장소, 잘못된 레코드는 명확한 예외를 내도록 정리했다. 페이지 UI 연결은 Beta 범위로 남기고 서비스 계약과 테스트만 닫았다.
- 수정 파일: `src/services/scenario_service.py`, `tests/test_scenario_service.py`, `WORK_TIMELINE.md`
- 검증:
  - `.venv310/bin/python -m pytest tests/test_scenario_service.py -q` -> 10개 통과
  - `.venv310/bin/python -m pytest tests -q` -> 21개 통과
  - `.venv310/bin/python -m compileall app.py pages src tests` -> 통과
  - `.venv310/bin/python -c "from datetime import datetime; from tempfile import TemporaryDirectory; from pathlib import Path; from src.data.schemas import ScenarioContext; from src.services.scenario_service import ScenarioService; d=TemporaryDirectory(); svc=ScenarioService(Path(d.name)/'scenarios.json'); s=ScenarioContext(scenario_id='demo', title='Demo', created_at=datetime(2026,1,1)); svc.save_scenario(s); print(svc.load_scenario('demo').scenario_id, len(svc.list_scenarios()))"` -> `demo 1`
- 다음 작업: 박차오름 4주차 우선순위 2로 넘어가 A* 비용 함수와 추천 점수 설명 가능성을 보정한다. Beta가 UI를 붙일 때는 `ScenarioService.save_scenario()`, `list_scenarios()`, `load_scenario()`를 사용하면 된다.

### 2026-05-11 박차오름 4주차 우선순위 2 A* 비용/점수 설명 보정 완료
- 작업: A* 경로 보정과 추천 점수화가 발표 가능한 기준으로 설명되도록 정리했다. `astar_router.py`의 우회 거리, 릴레이 홉, 반복 노드, 고부하, 예상 비용 계수를 이름 있는 정책 상수로 분리하고, `RouteResult.summary`에 실제 거리/우회/릴레이/반복/고부하 패널티를 함께 반영한다는 설명을 남겼다. `score_function.py`는 총점 산식, 경로 입력, 비용 반영, 혼잡 보상, counterfactual 개선 근거가 `ScoreBreakdown.notes`에 나뉘어 들어가도록 보강했다. `SimulationService._build_rationale()`는 A* 경로 길이, 예상 비용, 거리 비용, 공사비 비용, 환경·정책 리스크, counterfactual 개선분을 한 문장 흐름으로 설명하도록 정리했다. UI는 변경하지 않았다.
- 수정 파일: `src/engine/search/astar_router.py`, `src/engine/search/score_function.py`, `src/services/simulation_service.py`, `tests/test_simulation_route_score.py`, `WORK_TIMELINE.md`
- 검증:
  - `.venv310/bin/python -m pytest tests/test_simulation_route_score.py -q` -> 6개 통과
  - `.venv310/bin/python -m pytest tests -q` -> 27개 통과
  - `.venv310/bin/python -m compileall app.py pages src tests` -> 통과
  - `.venv310/bin/python -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_simulation(svc.build_default_input(load_scale=1.0)); print(r.source, r.fallback.mode); [print(rec.rank, rec.candidate_id, rec.score.total_score, rec.score.notes[-2:], rec.rationale) for rec in r.recommendations]"` -> `astar none`, `SITE_SOUTH` 1순위와 counterfactual 개선 근거 출력 확인
  - `.venv310/bin/python -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"` -> 통과, Streamlit bare-mode 경고만 확인
- 다음 작업: 박차오름 4주차 우선순위 3으로 넘어가 `VWorld` 최소 계약과 `map_2_5d` fallback 판단을 코드/문서에 고정한다.

### 2026-05-11 박차오름 4주차 우선순위 2 세부 평가 지표 UI 연결 완료
- 작업: `pages/02_simulation.py`의 `세부 평가 지표 보기` expander 내부만 보강했다. 기존에는 혼잡 완화, 공사비, 환경, 정책 일부 항목만 막대로 보였으나, 이제 `ScoreBreakdown`의 기본 점수, 혼잡 완화 보상, 거리 비용, 공사비 비용, 환경 리스크, 정책 리스크, 최종 총점이 모두 표와 지표로 표시된다. 또한 A* 경로 요약과 `ScoreBreakdown.notes` 전체를 같은 expander 안에 출력해 서비스/엔진에서 만든 산정 근거가 UI까지 이어지게 했다. 페이지 전체 레이아웃, 지도, 저장/불러오기 UI는 건드리지 않았다.
- 수정 파일: `pages/02_simulation.py`, `WORK_TIMELINE.md`
- 검증:
  - `.venv310/bin/python -m compileall app.py pages src tests` -> 통과
  - `.venv310/bin/python -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"` -> 통과, Streamlit bare-mode 경고만 확인
  - `.venv310/bin/python -m pytest tests/test_simulation_route_score.py -q` -> 6개 통과
  - `.venv310/bin/python -m pytest tests -q` -> 27개 통과
- 다음 작업: 박차오름 4주차 우선순위 3으로 넘어가기 전에 필요하면 이 UI 변경까지 포함한 커밋 메시지를 정리한다.

### 2026-05-11 박차오름 4주차 우선순위 3 VWorld 최소 계약 및 map_2_5d fallback 판단 완료
- 작업: `src/data/adapters/vworld_adapter.py`에 VWorld WebGL 연결 준비용 최소 계약을 구현했다. `VWORLD_API_KEY`는 기존 `settings.py` 설정을 통해 읽고, `build_webgl_script_url()`이 `https://map.vworld.kr/js/webglMapInit.js.do?version=3.0&apiKey=...` 형식의 script URL을 만든다. `domain=localhost:8501` 같은 도메인 파라미터도 query parameter로 붙일 수 있게 했다. `get_map_capability()`는 키가 없으면 `FallbackInfo(mode="map_2_5d")`를 반환하고, 키가 있어도 MVP에서 WebGL 3D 검증을 보류할 경우 `prefer_webgl=False`로 Folium/2.5D fallback 판단을 명시할 수 있게 했다. API key 값은 warning/fallback reason에 노출하지 않는다. `docs/map_feasibility_2026-04-09.md`에는 현재 MVP 판단을 `2.5D/Folium 유지 + VWorld WebGL 연결 준비`로 최신화했다.
- 수정 파일: `src/data/adapters/vworld_adapter.py`, `tests/test_vworld_adapter.py`, `docs/map_feasibility_2026-04-09.md`, `WORK_TIMELINE.md`
- 검증:
  - `.venv310/bin/python -m pytest tests/test_vworld_adapter.py -q` -> 7개 통과
  - `.venv310/bin/python -m pytest tests -q` -> 34개 통과
  - `.venv310/bin/python -m compileall app.py pages src tests` -> 통과
  - `.venv310/bin/python -c "from src.data.adapters.vworld_adapter import get_map_capability; c=get_map_capability(domain='localhost:8501', prefer_webgl=False); print(c.rendering_mode, c.fallback.mode, bool(c.webgl_script_url))"` -> `map_2_5d map_2_5d True`
- 다음 작업: 박차오름 4주차 우선순위 4로 넘어가 Monitoring actual → Simulation actual → Prediction mock/baseline 흐름의 공통 `scenario_id`, `source`, `fallback`, `warnings` 계약을 통합 테스트로 고정한다.
