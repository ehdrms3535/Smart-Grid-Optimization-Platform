from __future__ import annotations
from datetime import datetime

import pandas as pd
import streamlit as st
import folium
from streamlit_folium import st_folium

from src.data.schemas import ScenarioContext, SimulationResult
from src.engine.powerflow.dc_power_flow import solve, build_default_buses, build_default_line_inputs
from src.services.simulation_service import SimulationService

st.set_page_config(page_title="시뮬레이션 | SGOP", layout="wide")

# --- 1. 서비스 초기화 및 색상 로직 ---
@st.cache_resource
def get_service():
    return SimulationService()

sim_service = get_service()

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

bus_options = sim_service.list_bus_options()
candidate_options = sim_service.list_candidate_options()

def get_congestion_color(flow_mw, capacity_mw):
    if capacity_mw <= 0: return "#9ca3af"
    congestion = (abs(flow_mw) / capacity_mw) * 100
    if congestion >= 80: return "#ef4444"  # 빨강
    elif congestion >= 50: return "#eab308" # 노랑
    else: return "#22c55e" # 초록

# --- 세션 상태(Session State) 초기화 ---
if 'sim_run' not in st.session_state:
    st.session_state.sim_run = False

def _build_recommendation_rows(sim_result: SimulationResult) -> list[dict]:
    rows: list[dict] = []
    for recommendation in sim_result.recommendations:
        route = recommendation.route
        score = recommendation.score
        rows.append({
            "순위": recommendation.rank,
            "후보지": f"{recommendation.candidate_label} ({recommendation.candidate_id})",
            "총점": round(score.total_score, 1) if score else None,
            "경로 길이 (km)": round(route.total_distance_km, 1) if route else None,
            "예상 비용": round(route.estimated_cost, 1) if route else None,
            "혼잡 완화": round(score.congestion_relief, 1) if score else None,
            "거리 비용": round(score.distance_cost, 1) if score else None,
            "공사 비용": round(score.construction_cost, 1) if score else None,
            "환경 리스크": round(score.environmental_risk, 1) if score else None,
            "정책 리스크": round(score.policy_risk, 1) if score else None,
            "경로 소스": route.source if route else "-",
        })
    return rows

def _format_route_nodes(sim_result: SimulationResult) -> str:
    route = sim_result.selected_route
    if route is None or not route.path_node_ids:
        return "-"
    return " -> ".join(route.path_node_ids)

# --- 2. 사이드바 입력창 (Form으로 묶어서 한 번에 실행!) ---
with st.sidebar:
    st.header("⚡ 시뮬레이션 제어")
    
    with st.form("simulation_form"):
        start_bus = st.selectbox("시작 버스", options=[b[0] for b in bus_options], format_func=lambda x: dict(bus_options)[x], index=0)
        end_bus = st.selectbox("종료 버스", options=[b[0] for b in bus_options], format_func=lambda x: dict(bus_options)[x], index=10)
        
        selected_candidates = st.multiselect(
            "경유 후보지 선택", 
            options=[c[0] for c in candidate_options],
            default=[c[0] for c in candidate_options],
            format_func=lambda x: dict(candidate_options)[x]
        )
        
        load_scale = st.slider("시스템 전체 부하 배율", 0.5, 1.5, 1.0, 0.05)
        
        submitted = st.form_submit_button("🚀 시뮬레이션 실행", type="primary", use_container_width=True)

st.title("🗺️ 송전망 혼잡도 및 A* 최적 경로 시뮬레이션")

# --- 3. 엔진 가동 (버튼을 눌렀을 때만 작동) ---
if submitted:
    with st.spinner("AI가 최적 경로 및 혼잡도를 계산 중입니다... 🔄"):
        buses = build_default_buses(load_scale=load_scale)
        lines = build_default_line_inputs()
        st.session_state.pf_result = solve(buses, lines)

        shared_scenario = _get_shared_scenario()
        shared_created_at = shared_scenario.created_at

        sim_input = sim_service.build_default_input(
            scenario=shared_scenario,
            created_at=shared_created_at,
            start_bus_id=start_bus, 
            end_bus_id=end_bus, 
            candidate_site_ids=selected_candidates, 
            load_scale=load_scale
        )
        sim_result = sim_service.run_simulation(
            sim_input,
            created_at=shared_created_at,
        )
        
        st.session_state.sim_result = sim_result
        st.session_state.lines = lines 
        st.session_state.sgop_shared_scenario = sim_result.scenario
        st.session_state.selected_candidates = selected_candidates
        st.session_state.sim_run = True

# --- 4. 화면 레이아웃 (계산 완료 상태일 때만 화면 렌더링) ---
if st.session_state.sim_run:
    pf_result = st.session_state.pf_result
    sim_result = st.session_state.sim_result
    lines = st.session_state.lines
    selected_candidates = st.session_state.selected_candidates

    # 팀원들이 추가한 안내 메시지 및 시나리오 캡션
    if not selected_candidates:
        st.warning("후보지가 비어 기본 후보지를 사용합니다.")

    st.caption(
        f"시나리오: {sim_result.scenario.scenario_id}  |  "
        f"입력: {sim_result.simulation_input.start_bus_id} -> "
        f"{sim_result.simulation_input.end_bus_id}  |  "
        f"후보지 {len(sim_result.simulation_input.candidate_site_ids)}개  |  "
        f"부하 배율 {sim_result.simulation_input.load_scale:.2f}x  |  "
        f"소스: {sim_result.source.upper()}"
    )

    if sim_result.fallback.enabled:
        st.warning(f"Fallback 사용 중: `{sim_result.fallback.mode}` | {sim_result.fallback.reason}")

    for warning in sim_result.warnings:
        st.caption(f"- {warning}")

    col_map, col_info = st.columns([2, 1])

    with col_map:
        st.subheader("📍 A* 최적 경로 및 계통 혼잡 지도")
        m = folium.Map(location=[36.5, 127.5], zoom_start=7, tiles='CartoDB positron')
        
        bus_coords = {
            "BUS_001": [37.5665, 126.9780], "BUS_002": [37.4563, 126.7052], 
            "BUS_003": [37.2636, 127.0286], "BUS_004": [37.8813, 127.7298],
            "BUS_005": [37.7519, 128.8761], "BUS_006": [37.3422, 127.9202],
            "BUS_007": [36.3504, 127.3845], "BUS_008": [36.6424, 127.4890],
            "BUS_009": [35.1595, 126.8526], "BUS_010": [35.8242, 127.1480],
            "BUS_011": [35.8714, 128.6014], "BUS_012": [35.5384, 129.3114],
            "BUS_013": [35.1796, 129.0756]
        }

        for line in lines:
            f_num = line.from_bus.replace('B', '')
            t_num = line.to_bus.replace('B', '')
            f_bus = f"BUS_{f_num.zfill(3)}"
            t_bus = f"BUS_{t_num.zfill(3)}"
            
            if f_bus in bus_coords and t_bus in bus_coords:
                current_flow = pf_result.line_flows.get(line.line_id, 0)
                folium.PolyLine(
                    locations=[bus_coords[f_bus], bus_coords[t_bus]],
                    color=get_congestion_color(current_flow, line.capacity_mw),
                    weight=4, opacity=0.4
                ).add_to(m)

        if sim_result.selected_route and sim_result.selected_route.waypoints:
            route_coords = [[wp.latitude, wp.longitude] for wp in sim_result.selected_route.waypoints]
            
            folium.PolyLine(
                locations=route_coords,
                color="#2563eb",
                weight=5,
                dash_array="10",
                tooltip="추천 A* 신규 송전 경로",
                opacity=0.9
            ).add_to(m)
            
            for wp in sim_result.selected_route.waypoints:
                folium.CircleMarker(
                    location=[wp.latitude, wp.longitude],
                    radius=6, popup=wp.label, tooltip=wp.label,
                    color="#2563eb", fill=True, fill_color="#ffffff", fill_opacity=1.0
                ).add_to(m)

        legend_html = '''
        <div style="position: fixed; 
             bottom: 30px; left: 30px; width: 170px; height: 135px; 
             background-color: rgba(255, 255, 255, 0.95); z-index:9999; font-size:13px;
             border: 1px solid #e5e7eb; border-radius: 8px; padding: 10px;
             box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);">
             <div style="font-weight: bold; margin-bottom: 5px;">🚥 선로 상태 범례</div>
             <div style="margin-bottom: 2px;"><span style="color:#22c55e; font-size:16px;">■</span> 원활 (50% 미만)</div>
             <div style="margin-bottom: 2px;"><span style="color:#eab308; font-size:16px;">■</span> 주의 (50~80%)</div>
             <div style="margin-bottom: 2px;"><span style="color:#ef4444; font-size:16px;">■</span> 혼잡 (80% 이상)</div>
             <div><span style="color:#2563eb; font-weight:bold; font-size:16px;">╍</span> 신규 A* 경로</div>
        </div>
        '''
        m.get_root().html.add_child(folium.Element(legend_html))

        st_folium(m, width="100%", height=650, returned_objects=[])

    with col_info:
        # --- 설치 전/후 비교 카드 ---
        st.subheader("📊 설치 전/후 비교")
        if sim_result.deltas:
            for delta in sim_result.deltas:
                delta_color = "normal" if delta.status != "worsened" else "inverse"
                st.metric(
                    label=delta.label,
                    value=f"{delta.after_value} {delta.unit}",
                    delta=f"{delta.improvement} {delta.unit} ({'개선' if delta.improvement > 0 else '증가'})",
                    delta_color=delta_color
                )
        
        st.divider()

        # --- 🏆 AI 1순위 추천 사유 및 세부 점수표 ---
        if sim_result.recommendations:
            top_rec = sim_result.recommendations[0]
            st.subheader("🏆 AI 1순위 추천 분석")
            
            st.success(f"**추천 사유:**\n{top_rec.rationale}")
            
            with st.expander(f"세부 평가 지표 보기 (총점: {top_rec.score.total_score:.1f}점)", expanded=True):
                sc = top_rec.score
                st.caption(f"혼잡 완화 기여도 ({sc.congestion_relief:.1f}점)")
                st.progress(min(sc.congestion_relief / 50.0, 1.0)) 
                
                st.caption(f"건설 비용 효율성 ({sc.construction_cost:.1f}점)")
                st.progress(min(sc.construction_cost / 30.0, 1.0)) 
                
                st.caption(f"환경 리스크 안정성 ({sc.environmental_risk:.1f}점)")
                st.progress(min(sc.environmental_risk / 10.0, 1.0))
                
                st.caption(f"정책 부합성 ({sc.policy_risk:.1f}점)")
                st.progress(min(sc.policy_risk / 10.0, 1.0))

    # --- 팀원들이 만든 하단 데이터 표 영역 ---
    st.divider()
    st.subheader("📋 전체 후보지별 추천 결과 데이터")

    recommendation_rows = _build_recommendation_rows(sim_result)
    if recommendation_rows:
        st.dataframe(
            pd.DataFrame(recommendation_rows),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("표시할 추천 결과가 없습니다.")

else:
    # 초기 안내 화면
    st.info("👈 좌측 사이드바에서 조건을 설정하고 **[🚀 시뮬레이션 실행]** 버튼을 눌러주세요.")