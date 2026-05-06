# Beta 1~2주차 우선순위 1 작업 체크리스트

## 목적
- `pages/02_simulation.py`가 새 환경에서도 import 오류 없이 실행되게 만든다.
- 현재 실패 원인인 `folium`, `streamlit_folium` 의존성 누락을 정리한다.
- 이 작업은 Beta 1~2주차 100% 완료를 위한 선결 조건이다.

## 현재 확인된 문제
- `pages/02_simulation.py`는 아래 패키지를 import 한다.
  - `folium`
  - `streamlit_folium`
- 하지만 `requirements.txt`에는 해당 패키지가 없다.
- 두 패키지는 `pages/02_simulation.py` 최상단에서 바로 import 되므로, 특정 UI 경로를 타기 전에도 import 오류가 발생한다.
- 전수 재확인 범위:
  - 모든 `.py` 파일과 주요 `.md`/설정 파일을 확인했다.
  - `folium`/`streamlit_folium` import 는 현재 `pages/02_simulation.py`에만 존재한다.
  - `requirements.txt`에는 여전히 두 패키지가 없다.
- 검증 결과:
  - `.venv310/bin/python -c "import runpy; runpy.run_path('pages/02_simulation.py')"`
  - 실패: `ModuleNotFoundError: No module named 'folium'`

## 작업 1. requirements 의존성 추가
- 대상 파일: `requirements.txt`
- 추가 위치: Streamlit/Plotly 등 화면 의존성 근처 또는 별도 `# Mapping` 섹션
- 추가 내용:

```txt
# Mapping
folium>=0.16
streamlit-folium>=0.20
```

## 작업 2. 현재 가상환경에 패키지 설치
- 대상 환경: `.venv310`
- 우선 현재 환경을 바로 맞추는 명령:

```bash
.venv310/bin/python -m pip install folium streamlit-folium
```

- `requirements.txt` 수정 후 새 환경 재현성을 확인하는 명령:

```bash
.venv310/bin/python -m pip install -r requirements.txt
```

- 주의:
  - 설치 패키지 이름은 `streamlit-folium`
  - Python import 이름은 `streamlit_folium`
  - 직접 설치만 하고 `requirements.txt`를 고치지 않으면 새 환경에서 같은 문제가 재발한다.

## 작업 3. import 단독 검증
- 실행 명령:

```bash
.venv310/bin/python -c "import folium; from streamlit_folium import st_folium; print('map-import-ok')"
```

- 설치 메타데이터 확인:

```bash
.venv310/bin/python -m pip show folium streamlit-folium
```

- 완료 기준:
  - `map-import-ok` 출력
  - `ModuleNotFoundError` 없음
  - `pip show`에서 두 패키지가 모두 확인됨

## 작업 4. Simulation 페이지 bare-run 검증
- 실행 명령:

```bash
.venv310/bin/python -c "import runpy; runpy.run_path('pages/02_simulation.py'); print('simulation-page-run-ok')"
```

- 완료 기준:
  - `simulation-page-run-ok` 출력
  - `folium` 또는 `streamlit_folium` import 오류 없음

## 작업 5. 전체 정적 검증
- 실행 명령:

```bash
.venv310/bin/python -m compileall app.py pages src
```

- 완료 기준:
  - compile error 없음

## 작업 6. 결과 기록
- 대상 파일: `WORK_TIMELINE.md`
- 기록 항목:
  - 날짜
  - 작업 요약
  - 수정 파일
  - 검증 명령과 결과
  - 다음 작업

## 최종 완료 기준
- `requirements.txt`만 보고 새 환경을 만든 사람도 Simulation 페이지를 열 수 있다.
- 현재 `.venv310`에서도 `pages/02_simulation.py` bare-run이 통과한다.
- Beta 1~2주차의 다음 작업인 후보지별 결과표/UI 보강을 진행할 수 있는 상태가 된다.

## 완료 후 삭제 조건
- 이 체크리스트의 모든 항목이 완료되고 `WORK_TIMELINE.md`에 결과가 기록되면 이 임시 파일은 삭제해도 된다.
