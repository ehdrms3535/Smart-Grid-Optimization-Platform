# 공공 데이터 응답을 SGOP에서 사용할 수 있는 구조로 변환한다.
"""
public_data_adapter — KPX 전력수급현황 CSV 로더

원본 데이터
-----------
출처  : 한국전력거래소 오늘전력수급현황 (https://openapi.kpx.or.kr/sukub.do)
형식  : CSV, EUC-KR, 5분 간격
컬럼  : 기준일시, 공급능력(MW), 현재수요(MW), 최대예측수요(MW),
        공급예비력(MW), 공급예비율(%), 운영예비력(MW), 운영예비율(%)

출력 계약
---------
load_df : pd.DataFrame
    컬럼 : timestamp (datetime), bus_id (str), bus_name (str),
            load_mw (float), generation_mw (float)
    주기  : 1시간 (원본 5분 → 평균 리샘플)
    범위  : data/raw/sukub*.csv 전체 기간
"""
from __future__ import annotations

import glob
from pathlib import Path

import pandas as pd

# ── 13-노드 비율 정의 (peak_mw 기준) ──────────────────────────────────────────
_BUS_PEAK: dict[str, tuple[str, float]] = {
    "BUS_001": ("서울",  7000),
    "BUS_002": ("인천",  3500),
    "BUS_003": ("수원",  2500),
    "BUS_004": ("춘천",  1000),
    "BUS_005": ("강릉",   800),
    "BUS_006": ("원주",  1200),
    "BUS_007": ("대전",  3000),
    "BUS_008": ("청주",  1500),
    "BUS_009": ("광주",  2500),
    "BUS_010": ("전주",  1200),
    "BUS_011": ("대구",  3500),
    "BUS_012": ("울산",  2000),
    "BUS_013": ("부산",  4000),
}

_TOTAL_PEAK = sum(v[1] for v in _BUS_PEAK.values())  # 37,200 MW
_BUS_RATIO: dict[str, float] = {k: v[1] / _TOTAL_PEAK for k, v in _BUS_PEAK.items()}


def load_kpx_csvs(raw_dir: str | Path) -> pd.DataFrame:
    """data/raw/sukub*.csv 를 모두 읽어 시간별 노드 부하 DataFrame 으로 반환한다."""
    raw_dir = Path(raw_dir)
    csv_files = sorted(glob.glob(str(raw_dir / "sukub*.csv")))
    if not csv_files:
        raise FileNotFoundError(f"sukub*.csv 파일이 없습니다: {raw_dir}")

    frames = [_read_one(p) for p in csv_files]
    frames = [f for f in frames if f is not None]

    if not frames:
        raise ValueError("읽을 수 있는 CSV 파일이 없습니다.")

    national = (
        pd.concat(frames, ignore_index=True)
        .drop_duplicates("timestamp")
        .sort_values("timestamp")
        .set_index("timestamp")
    )

    # 5분 → 1시간 평균 리샘플
    national_hourly = national.resample("1h").mean().dropna()

    return _distribute_to_nodes(national_hourly)


def _read_one(path: str) -> pd.DataFrame | None:
    """단일 CSV 파일을 읽어 timestamp / demand_mw / supply_mw DataFrame 반환."""
    for enc in ("euc-kr", "cp949", "utf-8-sig", "utf-8"):
        try:
            raw = pd.read_csv(path, encoding=enc, header=0)
            break
        except UnicodeDecodeError:
            continue
    else:
        return None

    # 컬럼을 위치로 매핑 (인코딩 무관하게 안전)
    raw.columns = [
        "ts_raw", "supply_mw", "demand_mw", "max_pred_mw",
        "supply_reserve_mw", "supply_reserve_pct",
        "op_reserve_mw", "op_reserve_pct",
    ]

    raw["timestamp"] = pd.to_datetime(
        raw["ts_raw"].astype(str).str[:12],
        format="%Y%m%d%H%M",
        errors="coerce",
    )
    raw["demand_mw"] = pd.to_numeric(raw["demand_mw"], errors="coerce")
    raw["supply_mw"] = pd.to_numeric(raw["supply_mw"], errors="coerce")

    return raw[["timestamp", "demand_mw", "supply_mw"]].dropna()


def load_kpx_with_weather(raw_dir: str | Path) -> pd.DataFrame:
    """KPX 부하 데이터에 Open-Meteo 기온을 합쳐 반환한다.

    Returns
    -------
    load_df 와 동일한 계약 + temperature_c 컬럼 추가
    """
    from src.data.adapters.weather_adapter import fetch_historical

    load_df = load_kpx_csvs(raw_dir)
    start = str(load_df["timestamp"].min().date())
    end   = str(load_df["timestamp"].max().date())

    print(f"[날씨] {start} ~ {end} 기온 데이터 로딩 중...")
    weather_df = fetch_historical(start, end)

    merged = load_df.merge(weather_df, on=["timestamp", "bus_id"], how="left")
    missing = merged["temperature_c"].isna().sum()
    if missing > 0:
        merged["temperature_c"] = merged["temperature_c"].ffill().bfill()
        print(f"[날씨] {missing}개 결측 → ffill 보완")

    return merged


def _distribute_to_nodes(national_hourly: pd.DataFrame) -> pd.DataFrame:
    """전국 총수요를 13개 노드에 비율로 분배한다."""
    rows: list[dict] = []
    for ts, row in national_hourly.iterrows():
        national_load = float(row["demand_mw"])
        national_supply = float(row["supply_mw"])
        for bus_id, (bus_name, _) in _BUS_PEAK.items():
            ratio = _BUS_RATIO[bus_id]
            # 울산(BUS_012)만 발전 노드 — 공급능력 × 비율로 근사
            gen_mw = national_supply * _BUS_RATIO["BUS_012"] if bus_id == "BUS_012" else 0.0
            rows.append({
                "timestamp": ts,
                "bus_id": bus_id,
                "bus_name": bus_name,
                "load_mw": round(max(0.0, national_load * ratio), 1),
                "generation_mw": round(max(0.0, gen_mw), 1),
            })

    return pd.DataFrame(rows)
