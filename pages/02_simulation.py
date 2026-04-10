from __future__ import annotations
from datetime import datetime
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

# 오름님이 만든 엔진 모듈 임포트
from src.engine.powerflow.dc_power_flow import solve, build_default_buses, build_default_line_inputs

st.set_page_config(page_title="시뮬레이션 | SGOP", layout="wide")

<<<<<<< Updated upstream
st.set_page_config(
    page_title="시뮬레이션 | SGOP",
    page_icon="🗺️",
    layout="wide",
)


def _get_shared_scenario() -> ScenarioContext:
    scenario = st.session_state.get("sgop_shared_scenario")
    if isinstance(scenario, ScenarioContext):
        return scenario

    created_at = datetime.now().replace(minute=0, second=0, microsecond=0)
    scenario = ScenarioContext(
        scenario_id="sgop-demo-scenario",
        title="SGOP Demo Scenario",
        description="Monitoring과 Simulation이 공유하는 기본 시나리오",
        region="South Korea",
        created_at=created_at,
        created_by="streamlit-session",
    )
    st.session_state.sgop_shared_scenario = scenario
    return scenario


service = SimulationService()
bus_options = service.list_bus_options()
candidate_options = service.list_candidate_options()
bus_ids = [bus_id for bus_id, _ in bus_options]
candidate_ids = [candidate_id for candidate_id, _ in candidate_options]
bus_labels = {bus_id: f"{name} ({bus_id})" for bus_id, name in bus_options}
candidate_labels = {
    candidate_id: f"{label} ({candidate_id})"
    for candidate_id, label in candidate_options
}

with st.sidebar:
    st.header("시뮬레이션 입력")
    start_bus_id = st.selectbox(
        "시작 버스",
        options=bus_ids,
        index=bus_ids.index("BUS_001"),
        format_func=lambda bus_id: bus_labels[bus_id],
    )
    end_bus_id = st.selectbox(
        "종료 버스",
        options=bus_ids,
        index=bus_ids.index("BUS_011"),
        format_func=lambda bus_id: bus_labels[bus_id],
    )
    candidate_site_ids = st.multiselect(
        "후보지",
        options=candidate_ids,
        default=candidate_ids,
        format_func=lambda candidate_id: candidate_labels[candidate_id],
    )
    load_scale = st.slider(
        "부하 배율",
        min_value=0.80,
        max_value=1.30,
        value=1.00,
        step=0.05,
    )
    notes = st.text_area(
        "시나리오 메모",
        value="주요 혼잡 구간 우회와 운영 여유도 확보를 목표로 한 mock 시뮬레이션",
        height=120,
    )
    st.caption("페이지는 SimulationService 입력/출력 계약만 사용합니다.")


st.title("🗺️ 송전탑 설치 시뮬레이션")

if start_bus_id == end_bus_id:
    st.error("시작 버스와 종료 버스는 다르게 선택해야 합니다.")
    st.stop()

if not candidate_site_ids:
    st.error("후보지는 1개 이상 선택해야 합니다.")
    st.stop()

simulation_input = SimulationInput(
    scenario=_get_shared_scenario(),
    start_bus_id=start_bus_id,
    end_bus_id=end_bus_id,
    candidate_site_ids=candidate_site_ids,
    load_scale=load_scale,
    notes=notes,
)

with st.spinner("시뮬레이션 결과를 생성하는 중입니다..."):
    result: SimulationResult = service.run_simulation(simulation_input)

st.session_state.sgop_shared_scenario = result.scenario

st.caption(
    f"기준 시각: {result.created_at:%Y-%m-%d %H:%M}  |  "
    f"소스: {result.source.upper()}  |  "
    f"시나리오: {result.scenario.scenario_id}"
)
st.info(result.summary)

if result.fallback.enabled:
    st.warning(
        f"Fallback 사용 중: `{result.fallback.mode}`  |  {result.fallback.reason}"
    )

for warning in result.warnings:
    st.caption(f"- {warning}")

top_recommendation = result.recommendations[0] if result.recommendations else None
peak_delta = next(
    (delta for delta in result.deltas if delta.metric_id == "peak_utilization"),
    None,
)

metric_cols = st.columns(4)
metric_cols[0].metric(
    "1순위 후보",
    top_recommendation.candidate_label if top_recommendation else "-",
)
metric_cols[1].metric(
    "추천 총점",
    f"{top_recommendation.score.total_score:.1f}"
    if top_recommendation and top_recommendation.score
    else "-",
)
metric_cols[2].metric(
    "적용 경로 길이",
    f"{top_recommendation.route.total_distance_km:.1f} km"
    if top_recommendation and top_recommendation.route
    else "-",
)
metric_cols[3].metric(
    "최대 이용률 개선",
    f"{peak_delta.improvement:.1f}%p" if peak_delta else "-",
)

st.divider()
col_left, col_right = st.columns([1.1, 1.2])

with col_left:
    st.subheader("🗺️ 선정 경로 (지도 시각화)")
=======
# --- 1. 혼잡도에 따른 색상 결정 함수 (나현님 파트) ---
def get_congestion_color(flow_mw, capacity_mw):
    """흐름량과 용량을 비교해 색상을 반환합니다."""
    if capacity_mw <= 0: return "#9ca3af" # 용량 정보 없음
>>>>>>> Stashed changes
    
    # 혼잡도 계산 (%)
    congestion = (abs(flow_mw) / capacity_mw) * 100
    
    if congestion >= 80:
        return "#ef4444"  # 빨간색 (80% 이상: 위험)
    elif congestion >= 50:
        return "#eab308"  # 노란색 (50~80%: 주의)
    else:
        return "#22c55e"  # 초록색 (50% 미만: 원활)

# --- 2. 사이드바 입력창 ---
with st.sidebar:
    st.header("⚡ 시뮬레이션 제어")
    load_scale = st.slider("시스템 전체 부하 배율", 0.5, 1.5, 1.0, 0.05)
    st.caption("부하를 높이면 선로 혼잡도가 실시간으로 계산됩니다.")

st.title("🗺️ 송전망 혼잡도 실시간 시뮬레이션")

# --- 3. 엔진 가동 (박차오름님 파트 호출) ---
# 기본 버스와 선로 데이터를 가져와서 실제 전력 흐름을 계산합니다.
buses = build_default_buses(load_scale=load_scale)
lines = build_default_line_inputs()
result = solve(buses, lines)

if not result.converged:
    st.error(f"계산 실패: {result.error}")
    st.stop()

# --- 4. 메인 화면 레이아웃 ---
col_map, col_info = st.columns([2, 1])

with col_map:
    st.subheader("📍 실시간 계통 혼잡 지도")
    
    # 지도 초기 위치 (서울 중심)
    m = folium.Map(location=[37.5665, 126.9780], zoom_start=10, tiles='CartoDB positron')
    
    # 노드(Bus) 정보를 사전 형태로 변환 (위치 찾기용)
    # 실제 프로젝트에서는 DB나 다른 스키마에서 위경도를 가져와야 합니다.
    # 여기서는 예시 좌표를 사용합니다.
    bus_coords = {
        "B01": [37.78, 127.48], "B02": [37.85, 127.05], "B03": [37.24, 127.17],
        "B04": [37.01, 127.21], "B05": [36.93, 126.88], "B06": [37.55, 127.12],
        "B07": [37.36, 127.11], "B08": [37.54, 127.18], "B09": [37.26, 127.02],
        "B10": [37.38, 126.81], "B11": [37.52, 126.65], "B12": [37.49, 127.05],
        "B13": [37.60, 127.03]
    }

    # 선로(Line) 그리기 및 색상 입히기
    for line in lines:
        if line.from_bus in bus_coords and line.to_bus in bus_coords:
            start_pos = bus_coords[line.from_bus]
            end_pos = bus_coords[line.to_bus]
            
            # 엔진 결과에서 현재 선로의 흐름량(MW) 가져오기
            current_flow = result.line_flows.get(line.line_id, 0)
            # 혼잡도 색상 결정
            line_color = get_congestion_color(current_flow, line.capacity_mw)
            
            # 지도에 선 그리기
            folium.PolyLine(
                locations=[start_pos, end_pos],
                color=line_color,
                weight=5,
                opacity=0.8,
                tooltip=f"선로: {line.line_id} | 흐름: {abs(current_flow)}MW / {line.capacity_mw}MW"
            ).add_to(m)

    st_folium(m, width="100%", height=500, returned_objects=[])

with col_info:
    st.subheader("📊 주요 지표")
    
    # 가장 혼잡한 선로 찾기
    max_line_id = max(result.line_flows, key=lambda k: abs(result.line_flows[k]))
    max_flow = abs(result.line_flows[max_line_id])
    
    # 현재 부하 상태 표시
    st.metric("전체 부하 배율", f"{load_scale:.2f}x")
    st.metric("최대 조류 선로", f"{max_line_id}", f"{max_flow} MW")
    
    st.divider()
    st.write("**💡 분석 리포트**")
    if load_scale > 1.2:
        st.warning("⚠️ 부하가 높아 일부 구간에 병목 현상이 발생하고 있습니다. 신규 송전탑 설치 제안이 필요합니다.")
    else:
        st.success("✅ 현재 계통은 안정적인 상태입니다.")