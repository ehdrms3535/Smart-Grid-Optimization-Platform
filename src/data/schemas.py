# SGOP의 입력과 출력에 쓰이는 공통 데이터 스키마를 정의한다.
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal


ResultSource = Literal[
    "mock",
    "baseline",
    "lstm",
    "dc_power_flow",
    "heuristic",
    "astar",
    "manual",
]
RiskLevel = Literal["low", "medium", "high", "critical"]
FallbackMode = Literal[
    "none",
    "mock_data",
    "baseline_model",
    "cached_result",
    "manual_override",
    "map_2_5d",
]


# ── 공통 메타데이터 / 서비스 계약 ─────────────────────────────────────────────

@dataclass
class FallbackInfo:
    """주 경로가 실패했을 때 어떤 fallback 을 사용했는지 기록한다."""

    enabled: bool
    mode: FallbackMode = "none"
    reason: str = ""
    primary_path: str = ""
    active_path: str = ""


@dataclass
class ScenarioContext:
    """Monitoring, Simulation, Prediction 이 공유하는 시나리오 식별자."""

    scenario_id: str
    title: str = ""
    description: str = ""
    region: str = ""
    created_at: datetime | None = None
    created_by: str = ""


@dataclass
class TimeSeriesPoint:
    """페이지 차트에서 공통으로 쓰는 단일 시계열 포인트."""

    timestamp: datetime
    value: float
    label: str = ""


@dataclass
class MonitoringKpi:
    """모니터링 상단 KPI 카드의 단일 항목."""

    metric_id: str
    label: str
    value: float
    unit: str
    status: Literal["normal", "warning", "critical"] = "normal"
    delta: float | None = None


@dataclass
class LineStatusSnapshot:
    """특정 시점의 선로 상태를 페이지/서비스 간 동일 형식으로 전달한다."""

    line_id: str
    from_bus: str
    to_bus: str
    from_bus_name: str
    to_bus_name: str
    flow_mw: float
    utilization: float
    risk_level: RiskLevel


@dataclass
class RoutePoint:
    """지도 오버레이와 경로 표시에 공통으로 쓰는 경유점."""

    point_id: str
    label: str
    latitude: float
    longitude: float


@dataclass
class RouteResult:
    """A* 또는 휴리스틱 탐색 결과의 최소 공통 형식."""

    route_id: str
    start_bus_id: str
    end_bus_id: str
    path_node_ids: list[str] = field(default_factory=list)
    waypoints: list[RoutePoint] = field(default_factory=list)
    total_distance_km: float = 0.0
    estimated_cost: float = 0.0
    source: ResultSource = "mock"
    summary: str = ""


@dataclass
class ScoreBreakdown:
    """추천 결과 점수화를 구성하는 비용/보상 요소 묶음."""

    total_score: float
    distance_cost: float = 0.0
    construction_cost: float = 0.0
    congestion_relief: float = 0.0
    environmental_risk: float = 0.0
    policy_risk: float = 0.0
    notes: list[str] = field(default_factory=list)


@dataclass
class RecommendationResult:
    """후보지별 추천 결과를 정렬 가능한 형식으로 표현한다."""

    candidate_id: str
    candidate_label: str
    rank: int = 0
    route: RouteResult | None = None
    score: ScoreBreakdown | None = None
    rationale: str = ""


@dataclass
class SimulationDelta:
    """설치 전후 비교 표에 들어갈 단일 변화량."""

    metric_id: str
    label: str
    before_value: float
    after_value: float
    unit: str
    improvement: float
    status: Literal["improved", "unchanged", "worsened"] = "unchanged"


@dataclass
class SimulationInput:
    """Simulation 페이지와 서비스가 공유하는 입력 계약."""

    scenario: ScenarioContext
    start_bus_id: str = ""
    end_bus_id: str = ""
    candidate_site_ids: list[str] = field(default_factory=list)
    load_scale: float = 1.0
    notes: str = ""


@dataclass
class MonitoringResult:
    """Monitoring 서비스의 공통 반환 형식."""

    scenario: ScenarioContext
    created_at: datetime
    source: ResultSource
    kpis: list[MonitoringKpi] = field(default_factory=list)
    line_statuses: list[LineStatusSnapshot] = field(default_factory=list)
    trend_points: list[TimeSeriesPoint] = field(default_factory=list)
    summary: str = ""
    warnings: list[str] = field(default_factory=list)
    fallback: FallbackInfo = field(default_factory=lambda: FallbackInfo(enabled=False))


@dataclass
class SimulationResult:
    """Simulation 서비스의 공통 반환 형식."""

    scenario: ScenarioContext
    created_at: datetime
    source: ResultSource
    simulation_input: SimulationInput
    selected_route: RouteResult | None = None
    recommendations: list[RecommendationResult] = field(default_factory=list)
    deltas: list[SimulationDelta] = field(default_factory=list)
    summary: str = ""
    warnings: list[str] = field(default_factory=list)
    fallback: FallbackInfo = field(default_factory=lambda: FallbackInfo(enabled=False))


# ── 예측 피처 ─────────────────────────────────────────────────────────────────

@dataclass
class ForecastFeatureVector:
    """DC Power Flow 이후 예측 모델에 투입되는 단일 타임스텝 피처 벡터.

    입력 계약
    ---------
    - 과거 부하 lag: 1h / 6h / 12h / 24h / 48h / 72h (MW, 없으면 0.0)
    - 시간 특성: hour (0-23), day_of_week (0=월 … 6=일), is_weekend, is_holiday, month
    - 계통 특성: total_generation_mw, regional_demand_ratio (해당 노드 / 전체)

    출력 계약
    ---------
    ForecastFeatureVector 인스턴스 (lstm_forecaster / baseline 양쪽에서 공통 사용)
    """

    timestamp: datetime
    bus_id: str

    # 과거 부하 이력 (MW)
    load_lag_1h: float
    load_lag_6h: float
    load_lag_12h: float
    load_lag_24h: float
    load_lag_48h: float
    load_lag_72h: float

    # 시간 특성
    hour: int            # 0-23
    day_of_week: int     # 0=월 … 6=일
    is_weekend: bool
    is_holiday: bool
    month: int           # 1-12

    # 계통 특성
    total_generation_mw: float
    regional_demand_ratio: float  # 해당 노드 부하 / 전체 부하 (0.0-1.0)


# ── 예측 결과 ─────────────────────────────────────────────────────────────────

@dataclass
class HourlyLoadPrediction:
    """단일 노드·단일 시각의 예측값과 신뢰구간."""

    timestamp: datetime
    bus_id: str
    predicted_load_mw: float
    confidence_lower_mw: float
    confidence_upper_mw: float


@dataclass
class RiskLine:
    """24시간 예측 구간 중 혼잡 위험이 높은 선로 정보.

    risk_level 기준
    ---------------
    critical : 이용률 >= 90%  (즉각 대응 필요)
    high     : 이용률 >= 75%  (모니터링 강화)
    medium   : 이용률 >= 55%  (주의 관찰)
    low      : 이용률 < 55%   (정상)
    """

    line_id: str
    from_bus: str
    to_bus: str
    from_bus_name: str
    to_bus_name: str
    peak_risk_hour: int           # 위험 피크 시각 (0-23)
    predicted_utilization: float  # 0.0-1.0+ (1.0 = 열적한계 100%)
    risk_level: RiskLevel
    explanation: str              # xAI 규칙 기반 설명 문장


@dataclass
class PredictionResult:
    """PredictionService.run_mock_prediction() 의 최종 반환값.

    source 값
    ----------
    "mock"     : 합성 sinusoidal 데이터 (1주차 기본값)
    "baseline" : 이동평균 / 계절성 분해 baseline 모델
    "lstm"     : 훈련된 LSTM 모델
    """

    scenario_id: str
    created_at: datetime
    load_scale: float
    forecast_horizon_h: int           # 예측 시간 수 (기본 24)
    predictions: list[HourlyLoadPrediction]
    risk_lines: list[RiskLine]        # risk_level != "low" 인 선로만 포함, 이용률 내림차순
    summary: str
    source: Literal["lstm", "baseline", "mock"]
    scenario: ScenarioContext | None = None
    warnings: list[str] = field(default_factory=list)
    fallback: FallbackInfo = field(default_factory=lambda: FallbackInfo(enabled=False))
