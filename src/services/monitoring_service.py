# 모니터링 흐름과 혼잡 요약 생성을 조율한다.
from __future__ import annotations

import random
from datetime import datetime
from src.data.schemas import (
    CongestionStatus,
    CongestionSummary,
    LineStatus,
    MonitoringResult,
)

# ── 한국 345kV 주요 버스 (13개) ────────────────────────────────────────────────
# (bus_id, 이름)
_BUSES: dict[str, str] = {
    "B01": "신가평",
    "B02": "양주",
    "B03": "신용인",
    "B04": "신안성",
    "B05": "신평택",
    "B06": "서울동",
    "B07": "분당",
    "B08": "동서울",
    "B09": "수원",
    "B10": "신시흥",
    "B11": "인천북",
    "B12": "신강남",
    "B13": "신서울",
}

# ── mock 선로 정의 ─────────────────────────────────────────────────────────────
# (line_id, from_bus, to_bus, base_flow_mw, capacity_mw)
# base_flow_mw: 부하 배율 1.0 기준 기본 전력 흐름
# capacity_mw : 열적 한계 용량
_MOCK_LINE_DEFS: list[tuple[str, str, str, float, float]] = [
    ("L01", "B01", "B02", 210.0, 400.0),   # 신가평 → 양주
    ("L02", "B02", "B06", 285.0, 400.0),   # 양주 → 서울동
    ("L03", "B13", "B06", 260.0, 350.0),   # 신서울 → 서울동
    ("L04", "B06", "B08", 175.0, 300.0),   # 서울동 → 동서울
    ("L05", "B06", "B12", 310.0, 350.0),   # 서울동 → 신강남  (경고 구간)
    ("L06", "B08", "B07", 140.0, 200.0),   # 동서울 → 분당
    ("L07", "B12", "B07", 185.0, 200.0),   # 신강남 → 분당    (경고 구간)
    ("L08", "B07", "B03", 155.0, 250.0),   # 분당 → 신용인
    ("L09", "B03", "B09", 125.0, 200.0),   # 신용인 → 수원
    ("L10", "B09", "B04", 108.0, 200.0),   # 수원 → 신안성
    ("L11", "B04", "B05", 92.0,  180.0),   # 신안성 → 신평택
    ("L12", "B05", "B10", 145.0, 150.0),   # 신평택 → 신시흥  (위험 구간)
    ("L13", "B10", "B11", 68.0,  180.0),   # 신시흥 → 인천북
    ("L14", "B11", "B13", 115.0, 250.0),   # 인천북 → 신서울
    ("L15", "B02", "B11", 78.0,  250.0),   # 양주 → 인천북
]


def _congestion_status(utilization: float) -> CongestionStatus:
    if utilization >= 1.0:
        return "overload"
    if utilization >= 0.9:
        return "critical"
    if utilization >= 0.7:
        return "warning"
    return "normal"


def _build_summary(lines: list[LineStatus]) -> CongestionSummary:
    counts: dict[str, int] = {"normal": 0, "warning": 0, "critical": 0, "overload": 0}
    for line in lines:
        counts[line.status] += 1

    avg_util = sum(l.utilization for l in lines) / len(lines)
    total_loss = sum(l.loss_mw for l in lines)
    max_line = max(lines, key=lambda l: l.utilization)

    return CongestionSummary(
        total_lines=len(lines),
        normal_count=counts["normal"],
        warning_count=counts["warning"],
        critical_count=counts["critical"],
        overload_count=counts["overload"],
        avg_utilization=round(avg_util, 4),
        total_loss_mw=round(total_loss, 2),
        max_utilization=round(max_line.utilization, 4),
        max_utilization_line_id=max_line.line_id,
    )


def run_mock_monitoring(load_scale: float = 1.0) -> MonitoringResult:
    """mock 선로 데이터로 MonitoringResult 를 생성한다.

    Parameters
    ----------
    load_scale:
        전체 부하 배율. 1.0 = 기준 부하, 1.3 이상이면 위험·과부하 선로 증가.

    Returns
    -------
    MonitoringResult
        source="mock" 으로 설정된 모니터링 결과.
    """
    rng = random.Random(42)  # 재현 가능한 난수 (seed 고정)

    lines: list[LineStatus] = []
    for lid, fb, tb, base_flow, cap in _MOCK_LINE_DEFS:
        # 선로마다 ±4% 노이즈 추가 (실제 측정값처럼 보이게)
        noise = 1.0 + rng.uniform(-0.04, 0.04)
        flow = round(base_flow * load_scale * noise, 1)
        util = round(flow / cap, 4)
        # 단순 저항 손실 모델: P_loss = flow * r_pu * utilization
        loss = round(flow * 0.004 * util, 2)

        lines.append(
            LineStatus(
                line_id=lid,
                from_bus=fb,
                to_bus=tb,
                from_bus_name=_BUSES[fb],
                to_bus_name=_BUSES[tb],
                flow_mw=flow,
                capacity_mw=cap,
                utilization=util,
                status=_congestion_status(util),
                loss_mw=loss,
            )
        )

    return MonitoringResult(
        scenario_id="mock-001",
        created_at=datetime.now(),
        load_scale=load_scale,
        line_statuses=lines,
        summary=_build_summary(lines),
        source="mock",
    )
