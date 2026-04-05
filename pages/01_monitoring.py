# 송전망 혼잡 상태를 보여주는 모니터링 페이지를 구성한다.
from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from src.services.monitoring_service import run_mock_monitoring

# ── 상수 ──────────────────────────────────────────────────────────────────────

_STATUS_COLOR: dict[str, str] = {
    "normal":   "#2ecc71",
    "warning":  "#f39c12",
    "critical": "#e74c3c",
    "overload": "#8e44ad",
}

_STATUS_LABEL: dict[str, str] = {
    "normal":   "정상",
    "warning":  "경고",
    "critical": "위험",
    "overload": "과부하",
}

_STATUS_BG: dict[str, str] = {
    "normal":   "#d5f5e3",
    "warning":  "#fdebd0",
    "critical": "#fadbd8",
    "overload": "#e8daef",
}

# ── 페이지 설정 ────────────────────────────────────────────────────────────────

st.set_page_config(page_title="모니터링 | SGOP", layout="wide")
st.title("송전망 혼잡도 모니터링")
st.caption("선로별 이용률과 혼잡 상태를 실시간으로 확인합니다. (1주차 mock 데이터)")

# ── 사이드바 ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.header("파라미터")
    load_scale = st.slider(
        "부하 배율",
        min_value=0.5,
        max_value=1.5,
        value=1.0,
        step=0.05,
        help="전체 부하의 배율. 1.3 이상이면 위험·과부하 선로가 늘어납니다.",
    )
    st.divider()
    if st.button("새로고침", use_container_width=True):
        st.cache_data.clear()
    st.caption("데이터 소스: mock (1주차)")

# ── 데이터 로드 ────────────────────────────────────────────────────────────────

@st.cache_data(ttl=30)
def _load(scale: float):
    return run_mock_monitoring(scale)


result = _load(load_scale)
s = result.summary
lines = result.line_statuses

# ── KPI 카드 ───────────────────────────────────────────────────────────────────

st.subheader("KPI")
k1, k2, k3, k4 = st.columns(4)

k1.metric(
    label="평균 이용률",
    value=f"{s.avg_utilization * 100:.1f}%",
    help="전체 선로의 평균 이용률 (flow / capacity)",
)
k2.metric(
    label="위험·과부하 선로",
    value=f"{s.critical_count + s.overload_count}개",
    delta=f"경고 {s.warning_count}개",
    delta_color="off",
)
k3.metric(
    label="총 추정 손실",
    value=f"{s.total_loss_mw:.1f} MW",
    help="선로 저항 손실 합계 (단순 모델)",
)
k4.metric(
    label="최대 이용률",
    value=f"{s.max_utilization * 100:.1f}%",
    delta=f"선로 {s.max_utilization_line_id}",
    delta_color="off",
)

st.divider()

# ── 상태 요약 배지 ─────────────────────────────────────────────────────────────

st.subheader("상태 요약")
b1, b2, b3, b4 = st.columns(4)
b1.metric("정상", f"{s.normal_count}개")
b2.metric("경고", f"{s.warning_count}개")
b3.metric("위험", f"{s.critical_count}개")
b4.metric("과부하", f"{s.overload_count}개")

st.divider()

# ── 차트 + 위험 선로 패널 ──────────────────────────────────────────────────────

col_chart, col_danger = st.columns([3, 2])

with col_chart:
    st.subheader("선로별 이용률")

    bar_x = [f"{l.from_bus_name}→{l.to_bus_name}" for l in lines]
    bar_y = [l.utilization * 100 for l in lines]
    bar_colors = [_STATUS_COLOR[l.status] for l in lines]

    fig = go.Figure(
        go.Bar(
            x=bar_x,
            y=bar_y,
            marker_color=bar_colors,
            text=[f"{v:.1f}%" for v in bar_y],
            textposition="outside",
            hovertemplate="%{x}<br>이용률: %{y:.1f}%<extra></extra>",
        )
    )
    fig.add_hline(
        y=70,
        line_dash="dash",
        line_color=_STATUS_COLOR["warning"],
        annotation_text="경고 70%",
        annotation_position="top right",
    )
    fig.add_hline(
        y=90,
        line_dash="dash",
        line_color=_STATUS_COLOR["critical"],
        annotation_text="위험 90%",
        annotation_position="top right",
    )
    fig.update_layout(
        yaxis_title="이용률 (%)",
        yaxis_range=[0, max(bar_y) * 1.2 + 5],
        xaxis_tickangle=-30,
        height=420,
        margin=dict(t=30, b=10, l=10, r=10),
        plot_bgcolor="white",
    )
    st.plotly_chart(fig, use_container_width=True)

with col_danger:
    st.subheader("위험·경고 선로")

    danger_lines = sorted(
        [l for l in lines if l.status in ("overload", "critical", "warning")],
        key=lambda l: l.utilization,
        reverse=True,
    )

    if danger_lines:
        for l in danger_lines:
            color = {"warning": "orange", "critical": "red", "overload": "violet"}[l.status]
            label = _STATUS_LABEL[l.status]
            st.markdown(
                f":{color}[**[{l.line_id}] {l.from_bus_name} → {l.to_bus_name}**]  \n"
                f"이용률 **{l.utilization * 100:.1f}%** &nbsp;|&nbsp; "
                f"{l.flow_mw} MW / {l.capacity_mw:.0f} MW &nbsp;|&nbsp; :{color}[{label}]"
            )
            st.divider()
    else:
        st.success("위험·경고 선로가 없습니다.")

# ── 전체 선로 상태표 ───────────────────────────────────────────────────────────

st.subheader("전체 선로 상태표")

rows = [
    {
        "선로 ID": l.line_id,
        "구간": f"{l.from_bus_name} → {l.to_bus_name}",
        "흐름 (MW)": l.flow_mw,
        "용량 (MW)": l.capacity_mw,
        "이용률 (%)": round(l.utilization * 100, 1),
        "손실 (MW)": l.loss_mw,
        "상태": _STATUS_LABEL[l.status],
    }
    for l in sorted(lines, key=lambda l: l.utilization, reverse=True)
]
df = pd.DataFrame(rows)


def _color_status(val: str) -> str:
    reverse = {v: k for k, v in _STATUS_LABEL.items()}
    bg = _STATUS_BG.get(reverse.get(val, ""), "")
    return f"background-color: {bg}" if bg else ""


st.dataframe(
    df.style.applymap(_color_status, subset=["상태"]),
    use_container_width=True,
    hide_index=True,
)

st.caption(
    f"기준 시각: {result.created_at.strftime('%Y-%m-%d %H:%M:%S')} | "
    f"소스: {result.source} | 부하 배율: {result.load_scale:.2f}×"
)
