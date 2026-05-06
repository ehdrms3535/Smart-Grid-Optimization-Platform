# Gamma 3주차 우선순위 5 작업 체크리스트

## 목적
- Prediction 파트에 실제 테스트 케이스를 추가해 Gamma 3주차의 `테스트 케이스 작성 시작`을 완료 상태로 만든다.
- 대상은 `feature_builder`, baseline/GNN/hybrid 예측 경로, 위험도/설명 출력, fallback 동작이다.
- 현재 `tests/`에는 `README.md`만 있고 실제 테스트 파일이 없다.

## 현재 상태
- `pages/03_prediction.py`
  - Mock / Baseline / LSTM / GNN / LSTM+GNN 선택 UI가 있다.
  - 시나리오 A 저장 후 B와 비교하는 UI가 있다.
- `src/services/prediction_service.py`
  - `run_mock_prediction()`
  - `run_baseline_prediction()`
  - `run_lstm_prediction()`
  - `run_gnn_prediction()`
  - `run_hybrid_prediction()`
  - hybrid 실패 시 baseline fallback 흐름이 있다.
- `src/engine/forecast/feature_builder.py`
  - `build_feature_vector()`
  - `build_feature_matrix()`
  - `build_prediction_feature_matrix()`
- `tests/`
  - 현재 실제 테스트 없음.
- 전수 재확인 결과:
  - `PredictionService.run_lstm_prediction()`, `run_gnn_prediction()`, `run_hybrid_prediction()`은 `_load_weather_history()`를 통해 `load_kpx_with_weather()`를 호출한다.
  - `load_kpx_with_weather()`는 캐시가 부족하면 `weather_adapter.fetch_historical()`에서 외부 Open-Meteo 요청을 수행할 수 있다.
  - 빠른 단위 테스트는 네트워크와 저장 모델에 의존하지 않도록 synthetic DataFrame 또는 monkeypatch를 우선 사용한다.

## 작업 0. 테스트 범위 결정
- 3주차 완료 목적의 최소 테스트는 다음 네 묶음이다.
  - feature contract 테스트
  - PredictionService 반환 계약 테스트
  - 위험도/설명 테스트
  - hybrid fallback 테스트
- LSTM 실제 학습/추론은 무겁기 때문에 기본 테스트에서는 제외하거나 monkeypatch로 대체한다.
- 실제 LSTM 모델 로드 테스트는 `slow` 테스트로 분리한다.

## 작업 1. 테스트 파일 구조 추가
- 권장 파일:

```text
tests/
  README.md
  conftest.py
  test_prediction_feature_builder.py
  test_prediction_service_contract.py
  test_prediction_risk_and_fallback.py
```

- 역할:
  - `conftest.py`: synthetic load/weather fixture와 공통 helper
  - `test_prediction_feature_builder.py`: feature matrix 생성 계약 검증
  - `test_prediction_service_contract.py`: mock/baseline/GNN/hybrid 결과 형태 검증
  - `test_prediction_risk_and_fallback.py`: risk_lines, explanation, fallback 검증

## 작업 2. 공통 synthetic load fixture 작성
- 테스트마다 real `data/raw`에 의존하면 느리고 깨지기 쉽다.
- 우선 synthetic DataFrame을 helper로 만든다.
- 권장 helper 위치:
  - 각 테스트 파일 내부 함수
  - 또는 `tests/conftest.py`

```python
def build_load_df(bus_ids=("BUS_001", "BUS_002"), hours=96):
    ...
```

- 필수 컬럼:
  - `timestamp`
  - `bus_id`
  - `bus_name`
  - `load_mw`
  - `generation_mw`
  - 선택: `temperature_c`
- 완료 기준:
  - `feature_builder`와 GNN forecaster가 synthetic df만으로 동작한다.

## 작업 3. feature_builder 테스트
- 대상 파일: `tests/test_prediction_feature_builder.py`
- 테스트 1: `build_feature_vector()` 기본 계약
  - lag 값이 들어가는지 확인
  - `hour`, `day_of_week`, `month` 확인
  - `regional_demand_ratio`가 0~1 범위인지 확인
- 테스트 2: `build_prediction_feature_matrix()` 개수 확인
  - bus 2개, horizon 24면 feature 48개
  - 실제 서비스 기준 bus 13개, horizon 24면 feature 312개
- 테스트 3: lag 부족 시 0.0 fallback 확인
  - 이력이 부족한 timestamp를 넣고 `load_lag_72h == 0.0` 확인

## 작업 4. PredictionService mock 계약 테스트
- 대상 파일: `tests/test_prediction_service_contract.py`
- 테스트 내용:

```python
result = PredictionService().run_mock_prediction(load_scale=1.0, scenario=scenario)
```

- 확인 항목:
  - `result.source == "mock"`
  - `result.fallback.mode == "mock_data"`
  - `result.scenario.scenario_id == scenario.scenario_id`
  - `len(result.predictions) == 24 * 13`
  - `result.forecast_horizon_h == 24`
  - 모든 prediction의 `predicted_load_mw >= 0`

## 작업 5. baseline 계약 테스트
- 두 가지 선택지가 있다.

### 선택 A. 빠른 단위 테스트
- `BaselineForecaster`를 synthetic df로 직접 테스트한다.
- 장점: 빠름, 외부 파일 의존 없음.
- 단점: `PredictionService.run_baseline_prediction()` 전체 경로 검증은 아님.

### 선택 B. 통합 테스트
- 실제 `data/raw`를 사용해 `PredictionService.run_baseline_prediction()`을 호출한다.
- 장점: 현재 서비스 실제 경로 검증.
- 단점: raw fixture에 의존.

- 권장:
  - 기본 테스트는 선택 A.
  - 선택 B는 `@pytest.mark.integration`으로 분리.

- 통합 테스트 확인 항목:
  - `source == "baseline"`
  - `fallback.mode == "none"`
  - `len(predictions) == 312`
  - `summary`가 비어 있지 않음

## 작업 6. GNN 계약 테스트
- 대상:
  - 빠른 단위 테스트: `GNNForecaster`
  - 통합 테스트: `PredictionService.run_gnn_prediction()`
- 기본 테스트는 synthetic df로 `GNNForecaster.fit().predict()`를 검증한다.
- 확인 항목:
  - 예측 개수 = horizon x bus count
  - confidence lower <= predicted <= confidence upper
  - 예측값이 음수가 아님
- 통합 테스트는 `@pytest.mark.integration`으로 분리한다.

## 작업 7. hybrid 조합 테스트
- 대상 함수:
  - `src.services.prediction_service._combine_prediction_lists`
- 테스트 내용:
  - primary와 secondary 예측 리스트를 만든다.
  - `primary_weight=0.65`, `secondary_weight=0.35`
  - 결과 예측값이 가중 평균과 일치하는지 확인한다.
- 실패 케이스:
  - primary/secondary key가 맞지 않으면 `ValueError` 발생 확인.

## 작업 8. hybrid fallback 테스트
- 목표:
  - `run_hybrid_prediction()`에서 LSTM 또는 GNN branch가 실패하면 baseline fallback으로 내려가는지 검증한다.
- 무거운 TensorFlow 실행을 피하기 위해 monkeypatch를 사용한다.
- 권장 방식:
  - `_load_weather_history`는 synthetic df 반환
  - `_predict_lstm` 또는 `_predict_gnn`은 강제 예외 발생
  - `run_baseline_prediction`은 빠른 fake `PredictionResult` 반환 또는 실제 baseline 경로 사용
- 권장 우선순위:
  - 기본 빠른 테스트에서는 `run_baseline_prediction`도 fake로 대체한다.
  - 실제 `data/raw` 기반 baseline 호출은 `integration` 테스트로만 둔다.
- 확인 항목:
  - `result.source == "baseline"`
  - `result.fallback.mode == "baseline_model"`
  - `result.fallback.enabled is True`
  - `warnings`에 실패 원인이 포함됨

## 작업 9. 위험도/설명 테스트
- 대상:
  - `PredictionService._compute_risk_lines()`
  - 또는 public `run_mock_prediction(load_scale=...)`
- 확인 항목:
  - `risk_lines`는 `predicted_utilization` 내림차순이다.
  - `risk_level != "low"`인 선로만 포함된다.
  - 각 `RiskLine.explanation`이 빈 문자열이 아니다.
  - `peak_risk_hour`는 0~23 범위다.
- 부하 배율을 높이면 위험 선로 수가 늘거나 유지되는지 확인할 수 있다.

## 작업 10. Prediction 페이지 fallback helper 테스트
- 대상:
  - `pages/03_prediction.py`의 `_run_prediction_with_fallback()`
- 접근:
  - `runpy.run_path("pages/03_prediction.py")`로 helper를 가져온다.
  - fake service 또는 monkeypatch service를 써서 Baseline/GNN 실패를 강제로 만든다.
- 확인 항목:
  - 실패 시 mock 결과 반환
  - `fallback.mode == "mock_data"`
  - warning 첫 항목에 실패한 model source가 들어감
- 주의:
  - Streamlit page bare-run은 warning이 많이 뜰 수 있다.
  - 너무 불안정하면 이 테스트는 후순위로 두고 service fallback 테스트를 먼저 완료한다.
  - 이 테스트 때문에 `pages/03_prediction.py`의 사용자 UI 구조를 바꾸지는 않는다.

## 작업 11. pytest 설정 추가 여부 판단
- 현재 `pytest`는 `requirements.txt`에 있다.
- marker를 쓰려면 `pytest.ini` 추가를 검토한다.
- 권장 파일:

```ini
[pytest]
markers =
    integration: tests that use repository data files or saved models
    slow: tests that may load TensorFlow models or train predictors
```

- 단, marker를 당장 쓰지 않는다면 `pytest.ini`는 생략 가능하다.
- `@pytest.mark.integration` 또는 `@pytest.mark.slow`를 하나라도 쓰면 `pytest.ini`를 함께 추가한다.

## 작업 12. 기본 검증 명령
- 빠른 테스트:

```bash
.venv310/bin/python -m pytest tests -q
```

- integration 제외:

```bash
.venv310/bin/python -m pytest tests -q -m "not integration and not slow"
```

- 특정 파일:

```bash
.venv310/bin/python -m pytest tests/test_prediction_feature_builder.py -q
```

- 전체 정적 검증:

```bash
.venv310/bin/python -m compileall app.py pages src tests
```

## 작업 13. 테스트 작성 후 기대 최소 개수
- 최소 8개 테스트를 권장한다.
  - feature vector 기본 계약 1개
  - feature matrix 개수 1개
  - lag fallback 1개
  - mock prediction contract 1개
  - GNN forecaster contract 1개
  - hybrid combine weighted average 1개
  - hybrid combine key mismatch 1개
  - hybrid fallback 1개
  - risk/explanation 1개

## 작업 14. 결과 기록
- 대상 파일: `WORK_TIMELINE.md`
- 기록 내용:
  - 추가한 테스트 파일
  - 테스트 범위
  - 실행한 pytest 명령
  - compileall 결과
  - 남은 test gap

## 최종 완료 기준
- `tests/`에 Prediction 관련 실제 테스트 파일이 존재한다.
- 빠른 pytest가 통과한다.
- `feature_builder`, mock prediction, GNN 또는 baseline, hybrid fallback, risk/explanation 중 최소 4개 축이 검증된다.
- `WORK_TIMELINE.md`에 검증 결과가 기록된다.
- LSTM 실제 학습 테스트는 slow/integration으로 분리되거나 명시적으로 제외 사유가 남는다.

## 완료 후 삭제 조건
- 체크리스트의 모든 항목이 구현되고 `WORK_TIMELINE.md`에 검증 결과가 기록되면 이 임시 파일은 삭제해도 된다.
