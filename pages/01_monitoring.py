# 송전망 혼잡 상태를 보여주는 모니터링 페이지를 구성한다.
from __future__ import annotations

from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.data.schemas import MonitoringKpi, MonitoringResult, ScenarioContext
from src.services.monitoring_service import MonitoringService


st.set_page_config(
    page_title="모니터링 | SGOP",
    page_icon="⚡",
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


def _format_kpi_value(kpi: MonitoringKpi) -> str:
    if kpi.unit == "lines":
        return f"{int(kpi.value)} {kpi.unit}"
    if kpi.unit == "%":
        return f"{kpi.value:.1f}{kpi.unit}"
    return f"{kpi.value:,.1f} {kpi.unit}"


def _format_kpi_delta(kpi: MonitoringKpi) -> str | None:
    if kpi.delta is None:
        return None
    sign = "+" if kpi.delta >= 0 else ""
    if kpi.unit == "MW":
        return f"{sign}{kpi.delta:,.1f} {kpi.unit}"
    return f"{sign}{kpi.delta:.1f}{kpi.unit}"


service = MonitoringService()

with st.sidebar:
    st.header("모니터링 설정")
    load_scale = st.slider(
        "부하 배율",
        min_value=0.80,
        max_value=1.30,
        value=1.00,
        step=0.05,
        help="서비스 mock 결과에 적용할 부하 시나리오 배율입니다.",
    )
    st.caption("페이지는 MonitoringService 결과만 렌더링합니다.")


with st.spinner("모니터링 결과를 생성하는 중입니다..."):
    result: MonitoringResult = service.get_monitoring_result(
        scenario=_get_shared_scenario(),
        load_scale=load_scale,
    )

st.session_state.sgop_shared_scenario = result.scenario

st.title("⚡ 송전망 모니터링")
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

metric_columns = st.columns(len(result.kpis)) if result.kpis else []
for column, kpi in zip(metric_columns, result.kpis):
    column.metric(
        kpi.label,
        _format_kpi_value(kpi),
        delta=_format_kpi_delta(kpi),
    )

st.divider()
st.subheader("총부하 추세")

trend_df = pd.DataFrame(
    [
        {
            "timestamp": point.timestamp,
            "total_load_mw": point.value,
            "label": point.label,
        }
        for point in result.trend_points
    ]
)

if trend_df.empty:
    st.warning("표시할 추세 데이터가 없습니다.")
else:
    trend_fig = go.Figure()
    trend_fig.add_trace(
        go.Scatter(
            x=trend_df["timestamp"],
            y=trend_df["total_load_mw"],
            mode="lines+markers",
            line={"width": 3, "color": "#1f77b4"},
            marker={"size": 6},
            name="총부하",
            hovertemplate="%{x|%H:%M}<br>%{y:,.1f} MW<extra></extra>",
        )
    )
    trend_fig.update_layout(
        height=360,
        margin={"t": 20, "b": 40},
        xaxis_title="시각",
        yaxis_title="총부하 (MW)",
        hovermode="x unified",
    )
    st.plotly_chart(trend_fig, width="stretch")

st.divider()
col_left, col_right = st.columns([1.1, 1.4])

with col_left:
    st.subheader("위험 선로 현황")
    line_df = pd.DataFrame(
        [
            {
                "line_id": line.line_id,
                "구간": f"{line.from_bus_name} -> {line.to_bus_name}",
                "flow_mw": line.flow_mw,
                "utilization_pct": round(line.utilization * 100.0, 1),
                "risk_level": line.risk_level,
            }
            for line in result.line_statuses
        ]
    )

    if line_df.empty:
        st.warning("표시할 선로 상태가 없습니다.")
    else:
        utilization_fig = go.Figure()
        utilization_fig.add_trace(
            go.Bar(
                x=line_df["line_id"],
                y=line_df["utilization_pct"],
                marker_color=["#d62728" if value >= 90 else "#ff7f0e" if value >= 75 else "#f2c744" for value in line_df["utilization_pct"]],
                hovertemplate="%{x}<br>%{y:.1f}%<extra></extra>",
                name="이용률",
            )
        )
        utilization_fig.update_layout(
            height=320,
            margin={"t": 20, "b": 20},
            xaxis_title="선로",
            yaxis_title="이용률 (%)",
            showlegend=False,
        )
        st.plotly_chart(utilization_fig, width="stretch")

with col_right:
    st.subheader("선로 상태 테이블")
    if line_df.empty:
        st.info("현재 선로 상태를 표시할 수 없습니다.")
    else:
        st.dataframe(
            line_df.rename(
                columns={
                    "line_id": "선로 ID",
                    "flow_mw": "전력 흐름 (MW)",
                    "utilization_pct": "이용률 (%)",
                    "risk_level": "위험도",
                }
            ),
            width="stretch",
            hide_index=True,
        )
