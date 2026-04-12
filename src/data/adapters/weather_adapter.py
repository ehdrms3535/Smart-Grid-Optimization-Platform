# Open-Meteo API로 기상 데이터를 가져와 SGOP 형식으로 변환한다.
"""
weather_adapter — Open-Meteo 기온 데이터 로더

출처  : https://open-meteo.com (무료, 키 불필요)
데이터: 시간별 기온(temperature_2m, °C)
대상  : 13개 도시 버스 노드
캐시  : data/weather/{bus_id}.csv (재요청 방지)
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

_BUS_GEO: dict[str, tuple[str, float, float]] = {
    "BUS_001": ("서울",  37.566, 126.978),
    "BUS_002": ("인천",  37.457, 126.705),
    "BUS_003": ("수원",  37.264, 127.029),
    "BUS_004": ("춘천",  37.874, 127.734),
    "BUS_005": ("강릉",  37.751, 128.876),
    "BUS_006": ("원주",  37.343, 127.921),
    "BUS_007": ("대전",  36.351, 127.385),
    "BUS_008": ("청주",  36.640, 127.489),
    "BUS_009": ("광주",  35.160, 126.852),
    "BUS_010": ("전주",  35.820, 127.148),
    "BUS_011": ("대구",  35.872, 128.602),
    "BUS_012": ("울산",  35.539, 129.312),
    "BUS_013": ("부산",  35.180, 129.075),
}

_CACHE_DIR = Path(__file__).resolve().parents[3] / "data" / "weather"
_ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"


def fetch_historical(
    start_date: str,
    end_date: str,
    force_refresh: bool = False,
) -> pd.DataFrame:
    """전체 버스 시간별 기온 이력을 반환한다.

    Parameters
    ----------
    start_date    : "YYYY-MM-DD"
    end_date      : "YYYY-MM-DD"
    force_refresh : True 이면 캐시를 무시하고 재요청

    Returns
    -------
    DataFrame : timestamp, bus_id, temperature_c
    """
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    frames: list[pd.DataFrame] = []

    for bus_id, (name, lat, lon) in _BUS_GEO.items():
        cache_path = _CACHE_DIR / f"{bus_id}.csv"

        if not force_refresh and cache_path.exists():
            df = pd.read_csv(cache_path, parse_dates=["timestamp"])
            # 캐시 범위가 요청 범위를 커버하면 그대로 사용
            if (
                str(df["timestamp"].min().date()) <= start_date
                and str(df["timestamp"].max().date()) >= end_date
            ):
                frames.append(df)
                continue

        print(f"  [날씨] {name}({bus_id}) 다운로드 중...")
        resp = requests.get(
            _ARCHIVE_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "start_date": start_date,
                "end_date": end_date,
                "hourly": "temperature_2m",
                "timezone": "Asia/Seoul",
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        df = pd.DataFrame({
            "timestamp": pd.to_datetime(data["hourly"]["time"]),
            "bus_id": bus_id,
            "temperature_c": data["hourly"]["temperature_2m"],
        }).dropna()

        df.to_csv(cache_path, index=False)
        frames.append(df)
        time.sleep(0.3)  # API 요청 간격

    return pd.concat(frames, ignore_index=True).sort_values(["bus_id", "timestamp"])


def fetch_recent(past_days: int = 3, forecast_days: int = 2) -> pd.DataFrame:
    """최근 과거 + 단기 예보 기온을 반환한다 (predict 시 lookback 창에 사용).

    Parameters
    ----------
    past_days     : 과거 몇 일치 포함 (lookback 24h 커버용)
    forecast_days : 예보 몇 일치 포함

    Returns
    -------
    DataFrame : timestamp, bus_id, temperature_c
    """
    frames: list[pd.DataFrame] = []

    for bus_id, (name, lat, lon) in _BUS_GEO.items():
        resp = requests.get(
            _FORECAST_URL,
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "temperature_2m",
                "timezone": "Asia/Seoul",
                "past_days": past_days,
                "forecast_days": forecast_days,
            },
            timeout=30,
        )
        resp.raise_for_status()
        data = resp.json()

        df = pd.DataFrame({
            "timestamp": pd.to_datetime(data["hourly"]["time"]),
            "bus_id": bus_id,
            "temperature_c": data["hourly"]["temperature_2m"],
        }).dropna()

        frames.append(df)
        time.sleep(0.2)

    return pd.concat(frames, ignore_index=True).sort_values(["bus_id", "timestamp"])
