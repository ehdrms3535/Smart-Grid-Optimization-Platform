# Beta 1~2주차 우선순위 2 작업 체크리스트

## 목적
- `pages/02_simulation.py`에 후보지별 추천 결과표와 선택 추천안 요약을 추가한다.
- Beta 2주차 범위인 `A* 결과를 시뮬레이션 페이지에 연결`, `설치 전후 비교 흐름 연결`, `시나리오 입력값을 결과 카드와 연결`, `후보지별 비교 UI 정리`를 100% 완료 상태로 만든다.
- 3주차 범위인 시나리오 저장/불러오기, 고급 추천 비교 화면, 장기 흐름 관리는 이 문서에서 제외한다.

## 현재 상태
- `pages/02_simulation.py`는 다음 입력을 `SimulationService`에 전달한다.
  - 시작 버스
  - 종료 버스
  - 후보지 목록
  - 부하 배율
- `SimulationService.run_simulation()`은 다음 결과를 반환한다.
  - `selected_route`
  - `recommendations`
  - `deltas`
  - `summary`
  - `warnings`
  - `fallback`
- 현재 페이지는 지도와 설치 전/후 delta 카드를 보여준다.
- 하지만 후보지별 추천 결과 전체를 표로 보여주지 않는다.
- 선택된 1순위 추천안의 핵심 요약도 별도 카드로 충분히 드러나지 않는다.
- 전수 재확인 결과:
  - `pages/02_simulation.py`는 지도 선로 표시를 위해 `dc_power_flow.solve()`를 페이지에서 직접 호출한다.
  - 추천/경로/점수/delta 결과는 `SimulationService.run_simulation()`의 `sim_result`에서 받아온다.
  - 이 우선순위에서는 지도 계산 구조를 리팩터링하지 않고, 추천 결과 렌더링만 보강한다.
  - 결과표와 요약 카드는 반드시 `sim_result.recommendations`, `sim_result.selected_route`, `sim_result.deltas` 기준으로 만든다.

## 작업 0. 선행 조건 확인
- 우선순위 1 작업이 먼저 끝나야 한다.
- 확인할 항목:
  - `folium`, `streamlit-folium` 의존성 추가 완료
  - `pages/02_simulation.py` bare-run 통과

## 작업 1. 결과 렌더링에 필요한 데이터 항목 확정
- 대상 결과 객체: `SimulationResult`
- 후보지별 결과표에 사용할 필드:
  - `RecommendationResult.rank`
  - `RecommendationResult.candidate_id`
  - `RecommendationResult.candidate_label`
  - `RecommendationResult.route.route_id`
  - `RecommendationResult.route.total_distance_km`
  - `RecommendationResult.route.estimated_cost`
  - `RecommendationResult.route.source`
  - `RecommendationResult.score.total_score`
  - `RecommendationResult.score.distance_cost`
  - `RecommendationResult.score.construction_cost`
  - `RecommendationResult.score.congestion_relief`
  - `RecommendationResult.score.environmental_risk`
  - `RecommendationResult.score.policy_risk`
  - `RecommendationResult.rationale`
- 선택 추천안 요약에 사용할 필드:
  - 1순위 추천안의 후보지명
  - 1순위 추천안의 총점
  - 1순위 추천안의 경로 길이
  - 1순위 추천안의 예상 비용
  - 1순위 추천안의 경로 노드 수 또는 경유 노드
  - `selected_route.summary`

## 작업 2. 페이지 내부 helper 추가
- 대상 파일: `pages/02_simulation.py`
- 권장 helper:

```python
def _build_recommendation_rows(sim_result):
    ...
```

- helper 책임:
  - `sim_result.recommendations`를 DataFrame 렌더링용 `list[dict]`로 변환한다.
  - `route` 또는 `score`가 `None`이어도 페이지가 죽지 않게 기본값을 넣는다.
  - 숫자는 UI 표시용으로 적절히 반올림한다.
  - 후보지 수는 `selected_candidates`가 아니라 `sim_result.simulation_input.candidate_site_ids` 기준으로 표시한다.

- 표 컬럼 권장안:
  - `순위`
  - `후보지`
  - `총점`
  - `경로 길이 (km)`
  - `예상 비용`
  - `혼잡 완화`
  - `거리 비용`
  - `공사 비용`
  - `환경 리스크`
  - `정책 리스크`
  - `경로 소스`

## 작업 3. 선택 추천안 요약 카드 추가
- 위치 권장:
  - 오른쪽 패널 `설치 전/후 비교 (Deltas)` 위
  - 또는 지도 아래 `추천 결과` 섹션의 첫 부분
- 표시 항목:
  - `1순위 추천안`
  - `총점`
  - `경로 길이`
  - `예상 비용`
  - `경유 노드`
- 구현 방식:
  - `st.metric()` 3~4개를 한 줄에 배치
  - 후보지명과 route summary는 `st.info()` 또는 `st.caption()`으로 표시
- 완료 기준:
  - 사용자가 어떤 후보지가 선택되었는지 delta 카드보다 먼저 알 수 있다.
  - `selected_route`가 없는 경우에도 안내 메시지가 나온다.

## 작업 4. 후보지별 추천 결과표 추가
- 위치 권장:
  - 지도/오른쪽 패널 아래 전체 폭 섹션
- 구현 방식:

```python
rows = _build_recommendation_rows(sim_result)
st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True)
```

- 추가 import:
  - 현재 `pages/02_simulation.py`에는 `pandas` import가 없다.
  - 결과표를 DataFrame으로 만들면 `import pandas as pd`가 필요하다.
- 주의:
  - 새 공통 스키마를 만들지 않는다.
  - 페이지 안에서 추천 점수를 다시 계산하지 않는다.
  - `SimulationService`가 반환한 순위와 점수를 그대로 보여준다.
- 완료 기준:
  - 후보지 3개가 모두 보인다.
  - 1순위만이 아니라 2순위, 3순위 점수와 경로 길이도 비교 가능하다.
  - 후보지를 사이드바에서 줄이면 표도 선택된 후보지만 보여준다.

## 작업 5. 추천 근거 표시 추가
- 후보지별 `rationale`은 표에 넣으면 길어질 수 있다.
- 권장 방식:
  - 1순위 추천안의 `rationale`은 요약 카드에 표시한다.
  - 전체 후보의 `rationale`은 `st.expander("후보지별 추천 근거")` 안에서 순위별로 표시한다.
- 완료 기준:
  - 발표자가 왜 이 후보지가 1순위인지 문장으로 설명할 수 있다.

## 작업 6. fallback/warnings 표시 보강
- 현재 Simulation 페이지는 `sim_result.warnings`와 `sim_result.fallback`을 거의 표시하지 않는다.
- 추가 위치:
  - 페이지 제목 아래 또는 종합 요약 근처
- 표시 규칙:
  - `sim_result.fallback.enabled`이면 `st.warning(...)`
  - `sim_result.warnings`는 `st.caption(...)`으로 표시
- 완료 기준:
  - A* 또는 counterfactual 계산이 fallback으로 내려가도 화면에서 숨겨지지 않는다.

## 작업 7. 입력-결과 연결 상태 표시
- Beta 2주차의 `시나리오 입력값을 결과 카드와 연결`을 완료로 보려면 현재 입력값이 결과 화면에 보여야 한다.
- 표시 항목:
  - 시작 버스
  - 종료 버스
  - 후보지 수
  - 부하 배율
  - 결과 source
- 위치:
  - 제목 아래 caption
  - 또는 오른쪽 패널 상단
- 완료 기준:
  - 화면만 봐도 어떤 입력으로 결과가 생성됐는지 알 수 있다.

## 작업 8. 빈 후보지 입력 처리
- 현재 `SimulationService._normalize_input()`은 후보지가 비면 기본 후보 3개를 사용한다.
- 페이지에서 사용자가 후보지를 모두 해제했을 때 UX를 명확히 해야 한다.
- 선택지:
  - 페이지에서 `st.warning("후보지가 비어 기본 후보지를 사용합니다.")` 표시
  - 또는 multiselect가 최소 1개를 유지하도록 안내
- 완료 기준:
  - 후보지 0개 상태에서도 페이지가 죽지 않는다.
  - 기본 후보지 사용 여부가 화면에 표시된다.
  - 결과표는 정규화 이후의 실제 사용 후보지 목록과 일치한다.

## 작업 9. 검증 명령
- 우선순위 1 완료 후 실행한다.

```bash
.venv310/bin/python -m compileall app.py pages src
```

```bash
.venv310/bin/python -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"
```

```bash
.venv310/bin/python -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_simulation(svc.build_default_input(load_scale=1.0)); print({'source': r.source, 'fallback': r.fallback.mode, 'recs': len(r.recommendations), 'top': r.recommendations[0].candidate_id if r.recommendations else None, 'route': r.selected_route.route_id if r.selected_route else None})"
```

## 최종 완료 기준
- Simulation 페이지가 후보지별 추천 결과표를 보여준다.
- 1순위 선택 추천안 요약이 delta보다 먼저 또는 명확한 위치에 보인다.
- 시작/종료/후보지/부하 배율 입력값이 결과 화면에 연결되어 보인다.
- `warnings`와 `fallback`이 숨겨지지 않는다.
- 후보지 0개 입력에도 페이지가 중단되지 않는다.
- 이 작업은 저장/불러오기 없이 끝나야 한다. 저장/불러오기는 Beta 3주차 범위다.

## 완료 후 삭제 조건
- 체크리스트의 모든 항목이 구현되고 `WORK_TIMELINE.md`에 검증 결과가 기록되면 이 임시 파일은 삭제해도 된다.
