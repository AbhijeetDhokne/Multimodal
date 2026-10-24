from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import Field

from app.schemas.common import StrictModel

RiskSeverity = Literal["low", "medium", "high"]


class WeatherLocation(StrictModel):
    name: str
    region: str | None = None
    country: str | None = None
    latitude: float
    longitude: float
    timezone: str


class CurrentWeather(StrictModel):
    temperature_c: float
    feels_like_c: float
    humidity_pct: int = Field(ge=0, le=100)
    wind_speed_kmh: float = Field(ge=0)
    precipitation_mm: float = Field(ge=0)
    weather_code: int
    condition: str
    is_day: bool


class ForecastDay(StrictModel):
    date: date
    min_c: float
    max_c: float
    precipitation_probability_pct: int = Field(ge=0, le=100)
    precipitation_mm: float = Field(ge=0)
    wind_max_kmh: float = Field(ge=0)
    condition: str


class WeatherAdvisory(StrictModel):
    severity: RiskSeverity
    activity: str = Field(min_length=2, max_length=80)
    advice: str = Field(min_length=8, max_length=400)


class WorkWindow(StrictModel):
    date: date
    window: str = Field(min_length=3, max_length=40)
    suitability: Literal["good", "caution", "poor"]
    reason: str = Field(min_length=5, max_length=200)


class WeatherResult(StrictModel):
    location: WeatherLocation
    current: CurrentWeather
    forecast: list[ForecastDay] = Field(min_length=1, max_length=10)
    advisories: list[WeatherAdvisory] = Field(min_length=1, max_length=12)
    work_windows: list[WorkWindow] = Field(min_length=1, max_length=10)
    summary: str = Field(min_length=20, max_length=1000)
    data_source: Literal["open-meteo", "demo"]
    disclaimer: str = Field(min_length=20, max_length=500)
