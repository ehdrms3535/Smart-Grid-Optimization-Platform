# 박차오름 3주차 우선순위 4 작업 체크리스트

## 목적
- 후보지 추천 점수에 실제 `counterfactual delta`와 혼잡 완화 근거를 반영한다.
- 박차오름 3주차 범위인 `후보지 점수화 보강`을 완료 상태로 만든다.
- 현재는 A* 경로 거리와 정적 후보지 속성 중심으로 점수를 계산하고, 설치 전후 delta는 1순위 후보에 대해서만 사후 계산한다.
- 목표는 후보지별 추천 순위가 실제 혼잡 완화 효과를 더 직접적으로 반영하게 만드는 것이다.

## 현재 상태
- `src/engine/search/score_function.py`
  - `calculate_score()`는 route 거리와 정적 후보지 입력을 사용한다.
  - `ScoreBreakdown.congestion_relief`는 후보지 기본값, 부하 보정, route bonus를 더한 값이다.
  - 실제 DC Power Flow 설치 전후 개선량은 점수에 반영하지 않는다.
- `src/services/simulation_service.py`
  - `_build_recommendations()`에서 후보별 route와 score를 만든 뒤 rank를 정한다.
  - 그 다음 `run_simulation()`에서 1순위 추천안만 대상으로 counterfactual delta를 계산한다.
  - 따라서 2순위/3순위 후보는 실제 delta가 계산되지 않는다.
- 전수 재확인 결과:
  - `_build_counterfactual_line_inputs()`는 현재 `top_recommendation.score.congestion_relief`를 사용해 병렬 지원선 강도를 정한다.
  - 따라서 후보별 실제 impact 점수화를 할 때는 `base score -> counterfactual delta -> impact 반영 final score` 순서를 반드시 지켜 순환 계산을 피한다.
  - `CandidateImpactInput`은 아직 코드에 없으며, 추가 시 `src/services/simulation_service.py`에서 import 해야 한다.

## 작업 0. 선행 조건 확인
- 권장 선행 작업:
  - 우선순위 1: Simulation 페이지 지도 의존성 복구
  - 우선순위 3: Simulation 페이지 공통 `ScenarioContext` 통합
- 이 작업 자체는 서비스/엔진 계층 중심이라 페이지 작업 전에도 일부 구현 가능하다.

## 작업 1. 점수 보강 방식 결정
- 기본 방침:
  - 새 스키마를 크게 늘리지 않고 `ScoreBreakdown`의 기존 필드와 `notes`를 우선 활용한다.
  - 후보별 실제 개선량은 `ScoreBreakdown.congestion_relief`에 반영하고, 세부 값은 `notes`와 `RecommendationResult.rationale`에 남긴다.
- 필요한 경우에만 `src/data/schemas.py`에 새 타입을 추가한다.
- 권장: 새 공통 스키마 추가 없이 `score_function.py` 내부 dataclass로 시작한다.

## 작업 2. `score_function.py`에 후보 영향 입력 타입 추가
- 대상 파일: `src/engine/search/score_function.py`
- 추가 후보 dataclass:

```python
@dataclass(frozen=True, slots=True)
class CandidateImpactInput:
    peak_utilization_improvement: float = 0.0
    risk_line_reduction: float = 0.0
    loss_reduction_mw: float = 0.0
    operating_margin_gain: float = 0.0
```

- 의미:
  - `peak_utilization_improvement`: 최대 이용률 개선 폭, `%p`
  - `risk_line_reduction`: 고위험/경고 선로 감소 수
  - `loss_reduction_mw`: 송전 손실 감소량, MW
  - `operating_margin_gain`: 운영 여유도 증가량, `%p`

## 작업 3. 영향 점수 가중치 추가
- 대상 파일: `src/engine/search/score_function.py`
- 권장 상수:

```python
PEAK_UTILIZATION_RELIEF_FACTOR = 0.45
RISK_LINE_REDUCTION_FACTOR = 3.0
LOSS_REDUCTION_FACTOR = 0.35
OPERATING_MARGIN_GAIN_FACTOR = 0.35
MAX_COUNTERFACTUAL_BONUS = 18.0
```

- 목적:
  - 실제 delta가 너무 크게 점수를 뒤집지 않게 상한을 둔다.
  - route/공사비/환경 리스크와 균형을 맞춘다.

## 작업 4. `calculate_score()` 시그니처 확장
- 현재:

```python
def calculate_score(
    score_input: CandidateScoreInput,
    *,
    route: RouteResult | None = None,
) -> ScoreBreakdown:
```

- 변경 방향:

```python
def calculate_score(
    score_input: CandidateScoreInput,
    *,
    route: RouteResult | None = None,
    impact: CandidateImpactInput | None = None,
) -> ScoreBreakdown:
```

- 완료 기준:
  - 기존 호출부가 `impact` 없이도 그대로 동작한다.
  - `impact`가 있으면 `congestion_relief`에 counterfactual bonus가 더해진다.

## 작업 5. counterfactual bonus 계산 helper 추가
- 대상 파일: `src/engine/search/score_function.py`
- 권장 helper:

```python
def _calculate_counterfactual_bonus(impact: CandidateImpactInput | None) -> float:
    ...
```

- 계산 방향:
  - 최대 이용률 개선 + 위험 선로 감소 + 손실 감소 + 운영 여유도 증가를 점수화한다.
  - 음수 개선은 0으로 바꿔 감점 대신 bonus 미적용으로 시작한다.
  - 최종 bonus는 `MAX_COUNTERFACTUAL_BONUS` 이하로 제한한다.

## 작업 6. `ScoreBreakdown.notes`에 실제 개선 근거 추가
- `impact`가 있는 경우 notes에 아래 정보를 넣는다.
  - 최대 이용률 개선: `x.x%p`
  - 위험 선로 감소: `x.x개`
  - 손실 감소: `x.x MW`
  - 운영 여유도 증가: `x.x%p`
  - counterfactual bonus: `x.x점`
- 완료 기준:
  - 추천 결과표나 expander에서 왜 점수가 올라갔는지 설명할 수 있다.

## 작업 7. `SimulationService.run_simulation()` 데이터 흐름 보정
- 현재 흐름:

```text
입력 정규화
-> 후보별 route/score 생성
-> monitoring_before 계산
-> 1순위 후보 delta 계산
-> 결과 조립
```

- 변경 목표 흐름:

```text
입력 정규화
-> monitoring_before 계산
-> 후보별 route 생성
-> 후보별 base score 생성
-> 후보별 counterfactual delta 계산
-> 후보별 impact 반영 final score 생성
-> rank 정렬
-> 1순위 후보 delta를 selected result로 사용
-> 결과 조립
```

- 이유:
  - 추천 순위를 정하기 전에 후보별 실제 개선 효과를 알아야 한다.

## 작업 8. `_build_recommendations()` 확장
- 대상 파일: `src/services/simulation_service.py`
- 현재 시그니처:

```python
def _build_recommendations(
    self,
    simulation_input: SimulationInput,
    *,
    use_actual_route: bool,
) -> list[RecommendationResult]:
```

- 변경 방향:

```python
def _build_recommendations(
    self,
    simulation_input: SimulationInput,
    *,
    use_actual_route: bool,
    monitoring_before: MonitoringResult | None = None,
) -> list[RecommendationResult]:
```

- 동작:
  - `monitoring_before`가 있고 actual route일 때 후보별 impact를 계산한다.
  - 없으면 기존 점수 방식으로 동작한다.
- 완료 기준:
  - `run_mock_simulation()` 기존 동작이 깨지지 않는다.
  - `run_simulation()` actual 경로에서는 impact 반영 점수를 사용한다.
  - `score_function.py`와 `simulation_service.py` 사이에 순환 import가 생기지 않는다.

## 작업 9. 후보별 counterfactual impact 계산 helper 추가
- 대상 파일: `src/services/simulation_service.py`
- 권장 helper:

```python
def _build_candidate_impact(
    self,
    *,
    simulation_input: SimulationInput,
    monitoring_before: MonitoringResult,
    recommendation: RecommendationResult,
) -> tuple[CandidateImpactInput, list[SimulationDelta], list[str]]:
    ...
```

- 내부 흐름:
  1. 후보 route와 base score로 임시 `RecommendationResult`를 만든다.
  2. `_build_counterfactual_monitoring()`을 호출한다.
  3. `_build_actual_deltas()`로 candidate별 delta를 만든다.
  4. delta에서 `peak_utilization`, `risk_lines`, `losses`, `operating_margin` 값을 뽑아 `CandidateImpactInput`을 만든다.
  5. 실패 시 heuristic delta로 내려가거나 impact 0으로 처리한다.

- 주의:
  - 실패한 후보 하나 때문에 전체 simulation이 mock fallback으로 떨어지면 안 된다.
  - 후보별 impact 계산 실패는 해당 후보의 notes/warnings에만 남기고, 나머지 후보는 계속 계산한다.
  - `_build_counterfactual_monitoring()`이 요구하는 `top_recommendation.score`에는 impact 반영 전 base score를 넣는다.
  - 최종 추천 결과에는 impact 반영 후 다시 계산한 score를 넣는다.

## 작업 10. 1순위 delta 재사용 구조 정리
- 후보별 impact 계산에서 각 후보의 delta가 이미 나온다.
- 최종 `recommendations`를 rank한 뒤 1순위 후보의 delta를 `SimulationResult.deltas`로 써야 한다.
- 권장 방식:
  - 내부 dict를 만든다.

```python
candidate_deltas_by_id: dict[str, list[SimulationDelta]]
```

- 최종 1순위:

```python
top_candidate_id = recommendations[0].candidate_id
deltas = candidate_deltas_by_id.get(top_candidate_id, fallback_deltas)
```

- 완료 기준:
  - `SimulationResult.deltas`가 점수화에 사용된 동일 후보의 delta와 일치한다.

## 작업 11. 추천 rationale 보강
- 대상 파일: `src/services/simulation_service.py`
- `_build_rationale()`에 실제 delta 기반 문장을 추가한다.
- 예시:

```text
중앙 균형안은 최대 이용률을 12.2%p 낮추고 위험 선로를 3개 줄이는 계산 결과를 반영해 1순위로 추천됩니다.
```

- 완료 기준:
  - 추천 근거가 정적 문장만이 아니라 실제 개선량을 언급한다.

## 작업 12. fallback/warnings 정리
- 후보별 impact 계산이 모두 성공하면:
  - `fallback.mode = none`
  - warning에는 actual source 안내 정도만 남긴다.
- 일부 후보 impact가 실패하면:
  - 전체 fallback을 켜지 않는 방향 권장
  - `warnings`에 후보별 실패 문구 추가
  - 해당 후보 score notes에도 실패 문구 추가
- 전체 counterfactual이 불가능하면:
  - 기존 `_resolve_deltas()` fallback 흐름을 유지한다.
- 경계:
  - 이 작업은 점수 산식과 서비스 흐름 보강까지만 한다.
  - 지도 UI, 시나리오 저장/불러오기, VWorld 연동은 여기서 건드리지 않는다.

## 작업 13. 서비스 검증 명령
- 기본 actual 경로:

```bash
.venv310/bin/python -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_simulation(svc.build_default_input(load_scale=1.0)); print({'source': r.source, 'fallback': r.fallback.mode, 'top': r.recommendations[0].candidate_id, 'top_score': r.recommendations[0].score.total_score, 'notes': r.recommendations[0].score.notes, 'deltas': [(d.metric_id, d.improvement) for d in r.deltas]})"
```

- 후보 3개 모두 점수/notes 확인:

```bash
.venv310/bin/python -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_simulation(svc.build_default_input(load_scale=1.0)); [print(rec.rank, rec.candidate_id, rec.score.total_score, rec.score.congestion_relief, rec.score.notes[-2:]) for rec in r.recommendations]"
```

- 고부하 조건:

```bash
.venv310/bin/python -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_simulation(svc.build_default_input(load_scale=1.2)); print({'source': r.source, 'fallback': r.fallback.mode, 'top': r.recommendations[0].candidate_id, 'warnings': r.warnings[:5], 'deltas': [(d.metric_id, d.before_value, d.after_value, d.improvement) for d in r.deltas]})"
```

## 작업 14. 회귀 검증
- Mock 경로 유지:

```bash
.venv310/bin/python -c "from src.services.simulation_service import SimulationService; svc=SimulationService(); r=svc.run_mock_simulation(svc.build_default_input(load_scale=1.0)); print({'source': r.source, 'fallback': r.fallback.mode, 'recs': len(r.recommendations), 'top': r.recommendations[0].candidate_id})"
```

- 전체 compile:

```bash
.venv310/bin/python -m compileall app.py pages src
```

- 우선순위 1 완료 후 페이지 bare-run:

```bash
.venv310/bin/python -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"
```

## 최종 완료 기준
- 후보지별 추천 점수가 실제 counterfactual delta를 반영한다.
- 1순위 후보의 `SimulationResult.deltas`가 점수화에 사용된 동일 후보의 delta와 일치한다.
- `ScoreBreakdown.notes`에 실제 개선 근거가 남는다.
- `RecommendationResult.rationale`에 실제 개선량이 언급된다.
- 후보 하나의 impact 계산 실패가 전체 simulation 실패로 번지지 않는다.
- 기존 mock simulation 호출은 깨지지 않는다.

## 완료 후 삭제 조건
- 체크리스트의 모든 항목이 구현되고 `WORK_TIMELINE.md`에 검증 결과가 기록되면 이 임시 파일은 삭제해도 된다.
