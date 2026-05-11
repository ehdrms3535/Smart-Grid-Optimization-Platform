# SGOP 평가 기준에 따라 후보 해의 점수를 계산한다.
from __future__ import annotations

from dataclasses import dataclass, replace

from src.data.schemas import RecommendationResult, RouteResult, ScoreBreakdown


DISTANCE_COST_FACTOR = 0.58
CONSTRUCTION_COST_FACTOR = 1.85
ENVIRONMENTAL_RISK_FACTOR = 2.2
POLICY_RISK_FACTOR = 2.0
LOAD_SCALE_BONUS_FACTOR = 18.0
ROUTE_STABILITY_BONUS = 4.0
DISTANCE_GAP_PENALTY_FACTOR = 0.22
ROUTE_DISTANCE_NORMALIZATION_KM = 10.0
BASE_RECOMMENDATION_SCORE = 100.0
PEAK_UTILIZATION_RELIEF_FACTOR = 0.45
RISK_LINE_REDUCTION_FACTOR = 3.0
LOSS_REDUCTION_FACTOR = 0.35
OPERATING_MARGIN_GAIN_FACTOR = 0.35
MAX_COUNTERFACTUAL_BONUS = 18.0


@dataclass(frozen=True)
class CandidateScoreInput:
    """점수 계산에 필요한 최소 입력 묶음."""

    candidate_id: str
    candidate_label: str
    distance_km: float
    construction_cost: float
    congestion_relief: float
    environmental_risk: float
    policy_risk: float
    load_scale: float = 1.0


@dataclass(frozen=True)
class CandidateImpactInput:
    """후보지별 counterfactual delta를 점수에 반영하기 위한 입력."""

    peak_utilization_improvement: float = 0.0
    risk_line_reduction: float = 0.0
    loss_reduction_mw: float = 0.0
    operating_margin_gain: float = 0.0


def calculate_mock_score(score_input: CandidateScoreInput) -> ScoreBreakdown:
    """1주차용 mock 점수 분해 결과를 공통 ScoreBreakdown 형식으로 반환한다."""

    load_bonus = max(0.0, score_input.load_scale - 1.0) * LOAD_SCALE_BONUS_FACTOR
    distance_cost = round(score_input.distance_km * DISTANCE_COST_FACTOR, 1)
    construction_cost = round(score_input.construction_cost * CONSTRUCTION_COST_FACTOR, 1)
    congestion_relief = round(score_input.congestion_relief + load_bonus, 1)
    environmental_risk = round(
        score_input.environmental_risk * ENVIRONMENTAL_RISK_FACTOR,
        1,
    )
    policy_risk = round(score_input.policy_risk * POLICY_RISK_FACTOR, 1)

    return _build_score_breakdown(
        distance_cost=distance_cost,
        construction_cost=construction_cost,
        congestion_relief=congestion_relief,
        environmental_risk=environmental_risk,
        policy_risk=policy_risk,
        notes=[
            "현재 점수는 mock 가중치로 계산됩니다.",
            "비용 요소: 거리 0.58, 공사비 1.85, 환경 2.2, 정책 2.0, 부하 보정 18.0",
        ],
    )


def calculate_score(
    score_input: CandidateScoreInput,
    *,
    route: RouteResult | None = None,
    impact: CandidateImpactInput | None = None,
) -> ScoreBreakdown:
    """2주차용 실제 route 반영 점수 계산 함수."""

    resolved_distance_km = _resolve_distance_km(score_input, route)
    distance_gap_penalty = max(0.0, resolved_distance_km - score_input.distance_km)
    normalized_distance = resolved_distance_km / ROUTE_DISTANCE_NORMALIZATION_KM
    normalized_distance_gap = distance_gap_penalty / ROUTE_DISTANCE_NORMALIZATION_KM
    load_bonus = max(0.0, score_input.load_scale - 1.0) * LOAD_SCALE_BONUS_FACTOR
    route_bonus = (
        ROUTE_STABILITY_BONUS
        if route is not None and route.source in {"astar", "heuristic"}
        else 0.0
    )
    counterfactual_bonus = _calculate_counterfactual_bonus(impact)

    distance_cost = round(
        (normalized_distance * DISTANCE_COST_FACTOR)
        + (normalized_distance_gap * DISTANCE_GAP_PENALTY_FACTOR),
        1,
    )
    construction_cost = round(score_input.construction_cost * CONSTRUCTION_COST_FACTOR, 1)
    congestion_relief = round(
        score_input.congestion_relief
        + load_bonus
        + route_bonus
        + counterfactual_bonus,
        1,
    )
    environmental_risk = round(
        score_input.environmental_risk * ENVIRONMENTAL_RISK_FACTOR,
        1,
    )
    policy_risk = round(score_input.policy_risk * POLICY_RISK_FACTOR, 1)

    notes = [
        "현재 점수는 보정된 A* 경로 기준 가중치로 계산됩니다.",
        (
            f"사용 거리 {resolved_distance_km:.1f}km"
            + (
                f" (route source: {route.source})"
                if route is not None
                else " (candidate baseline)"
            )
        ),
        (
            "비용 요소: 거리 0.58(10km 단위), 거리 초과 패널티 0.22(10km 단위), 공사비 1.85, "
            "환경 2.2, 정책 2.0, 부하 보정 18.0, route bonus 4.0"
        ),
    ]
    if impact is not None:
        notes.extend([
            (
                "counterfactual 개선 근거: "
                f"최대 이용률 {max(0.0, impact.peak_utilization_improvement):.1f}%p 개선, "
                f"위험 선로 {max(0.0, impact.risk_line_reduction):.1f}개 감소, "
                f"손실 {max(0.0, impact.loss_reduction_mw):.1f} MW 감소, "
                f"운영 여유도 {max(0.0, impact.operating_margin_gain):.1f}%p 증가"
            ),
            f"counterfactual bonus {counterfactual_bonus:.1f}점 반영",
        ])

    return _build_score_breakdown(
        distance_cost=distance_cost,
        construction_cost=construction_cost,
        congestion_relief=congestion_relief,
        environmental_risk=environmental_risk,
        policy_risk=policy_risk,
        notes=notes,
    )


def build_recommendation(
    candidate_id: str,
    candidate_label: str,
    route: RouteResult,
    score: ScoreBreakdown,
    rationale: str,
) -> RecommendationResult:
    """서비스 계층이 사용할 RecommendationResult 공통 형식을 만든다."""

    return RecommendationResult(
        candidate_id=candidate_id,
        candidate_label=candidate_label,
        route=route,
        score=score,
        rationale=rationale,
    )


def rank_recommendations(
    recommendations: list[RecommendationResult],
) -> list[RecommendationResult]:
    """추천안을 total_score 기준으로 정렬하고 rank 를 부여한다."""

    ordered = sorted(
        recommendations,
        key=lambda recommendation: (
            -(
                recommendation.score.total_score
                if recommendation.score is not None
                else float("-inf")
            ),
            recommendation.route.total_distance_km
            if recommendation.route is not None
            else float("inf"),
            recommendation.candidate_id,
        ),
    )

    return [
        replace(recommendation, rank=rank)
        for rank, recommendation in enumerate(ordered, start=1)
    ]


def _resolve_distance_km(
    score_input: CandidateScoreInput,
    route: RouteResult | None,
) -> float:
    if route is not None and route.total_distance_km > 0:
        return route.total_distance_km
    return score_input.distance_km


def _calculate_counterfactual_bonus(impact: CandidateImpactInput | None) -> float:
    if impact is None:
        return 0.0

    bonus = (
        max(0.0, impact.peak_utilization_improvement) * PEAK_UTILIZATION_RELIEF_FACTOR
        + max(0.0, impact.risk_line_reduction) * RISK_LINE_REDUCTION_FACTOR
        + max(0.0, impact.loss_reduction_mw) * LOSS_REDUCTION_FACTOR
        + max(0.0, impact.operating_margin_gain) * OPERATING_MARGIN_GAIN_FACTOR
    )
    return round(min(MAX_COUNTERFACTUAL_BONUS, bonus), 1)


def _build_score_breakdown(
    *,
    distance_cost: float,
    construction_cost: float,
    congestion_relief: float,
    environmental_risk: float,
    policy_risk: float,
    notes: list[str],
) -> ScoreBreakdown:
    total_score = round(
        BASE_RECOMMENDATION_SCORE
        + congestion_relief
        - distance_cost
        - construction_cost
        - environmental_risk
        - policy_risk,
        1,
    )

    return ScoreBreakdown(
        total_score=total_score,
        distance_cost=distance_cost,
        construction_cost=construction_cost,
        congestion_relief=congestion_relief,
        environmental_risk=environmental_risk,
        policy_risk=policy_risk,
        notes=notes,
    )
