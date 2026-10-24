from __future__ import annotations

import time
from datetime import date
from typing import Any

import httpx

from app.config import settings
from app.schemas.weather import (
    CurrentWeather,
    ForecastDay,
    WeatherAdvisory,
    WeatherLocation,
    WeatherResult,
    WorkWindow,
)
from app.services.demo import demo_weather, weather_condition

_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
_FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
_cache: dict[str, tuple[float, WeatherResult]] = {}


def _cache_key(city: str | None, lat: float | None, lon: float | None) -> str:
    if lat is not None and lon is not None:
        return f"coords:{lat:.3f},{lon:.3f}"
    return f"city:{(city or '').strip().lower()}"


async def _geocode(client: httpx.AsyncClient, city: str) -> dict[str, Any]:
    response = await client.get(
        _GEOCODE_URL,
        params={"name": city, "count": 1, "language": "en", "format": "json"},
    )
    response.raise_for_status()
    results = response.json().get("results") or []
    if not results:
        raise ValueError(f"Could not find the location '{city}'.")
    return results[0]


def _advisories(current: CurrentWeather, forecast: list[ForecastDay]) -> list[WeatherAdvisory]:
    advisories: list[WeatherAdvisory] = []
    today = forecast[0] if forecast else None
    if (today and today.precipitation_probability_pct >= 55) or current.precipitation_mm > 0:
        advisories.append(
            WeatherAdvisory(
                severity="high",
                activity="Concrete placement",
                advice="Rain is likely. Postpone exposed pours or provide complete weather protection and monitor surface damage.",
            )
        )
        advisories.append(
            WeatherAdvisory(
                severity="medium",
                activity="Excavation",
                advice="Inspect slopes and shoring before entry, keep pumps ready, and maintain perimeter drainage.",
            )
        )
    if current.temperature_c >= 36 or (today and today.max_c >= 37):
        advisories.append(
            WeatherAdvisory(
                severity="high",
                activity="Concrete and rebar work",
                advice="Heat increases evaporation and heat-stress risk. Shift work earlier, provide shade and fluids, and cure promptly.",
            )
        )
    if current.wind_speed_kmh >= 28 or (today and today.wind_max_kmh >= 30):
        advisories.append(
            WeatherAdvisory(
                severity="high",
                activity="Lifting operations",
                advice="Wind may exceed safe lifting limits. Suspend crane lifts above the manufacturer's threshold.",
            )
        )
    if current.humidity_pct >= 85:
        advisories.append(
            WeatherAdvisory(
                severity="medium",
                activity="Painting and coatings",
                advice="High humidity slows drying and can affect finish adhesion. Check dew point and manufacturer limits.",
            )
        )
    if not advisories:
        advisories.append(
            WeatherAdvisory(
                severity="low",
                activity="General site work",
                advice="Conditions are broadly workable. Maintain normal safety, dust control, and curing measures.",
            )
        )
    advisories.append(
        WeatherAdvisory(
            severity="low",
            activity="Daily planning",
            advice="Recheck the forecast before the next shift and include weather in the daily briefing.",
        )
    )
    return advisories


def _work_windows(forecast: list[ForecastDay]) -> list[WorkWindow]:
    windows: list[WorkWindow] = []
    for day in forecast[:5]:
        if day.precipitation_probability_pct >= 65:
            suitability, reason = "poor", "High rain probability; prioritise covered or indoor work."
        elif day.max_c >= 37:
            suitability, reason = "caution", "Heat-stress risk; use early-morning shifts and hydration breaks."
        elif day.wind_max_kmh >= 30:
            suitability, reason = "caution", "Wind-sensitive lifting may need to stop."
        else:
            suitability, reason = "good", "Conditions suit normal site activities."
        windows.append(
            WorkWindow(
                date=day.date,
                window="06:00-11:00" if day.max_c >= 34 else "07:00-17:00",
                suitability=suitability,  # type: ignore[arg-type]
                reason=reason,
            )
        )
    return windows


async def get_weather(
    *, city: str | None, latitude: float | None, longitude: float | None
) -> tuple[WeatherResult, str, list[str]]:
    key = _cache_key(city, latitude, longitude)
    cached = _cache.get(key)
    if cached and time.time() - cached[0] < settings.weather_cache_seconds:
        return cached[1], "open-meteo", []

    if settings.weather_provider == "offline":
        result = demo_weather(city or "", latitude, longitude)
        return result, "demo", ["Weather provider is set to offline; deterministic demo weather is shown."]

    try:
        async with httpx.AsyncClient(timeout=settings.weather_timeout_seconds) as client:
            if latitude is not None and longitude is not None:
                lat, lon = latitude, longitude
                name = city or "Selected site"
                region = country = None
                timezone = "auto"
            elif city:
                place = await _geocode(client, city)
                lat, lon = float(place["latitude"]), float(place["longitude"])
                name = place.get("name") or city
                region = place.get("admin1")
                country = place.get("country")
                timezone = place.get("timezone") or "auto"
            else:
                raise ValueError("Provide a city or latitude/longitude.")

            response = await client.get(
                _FORECAST_URL,
                params={
                    "latitude": lat,
                    "longitude": lon,
                    "current": ",".join(
                        [
                            "temperature_2m",
                            "apparent_temperature",
                            "relative_humidity_2m",
                            "wind_speed_10m",
                            "precipitation",
                            "weather_code",
                            "is_day",
                        ]
                    ),
                    "daily": ",".join(
                        [
                            "weather_code",
                            "temperature_2m_max",
                            "temperature_2m_min",
                            "precipitation_sum",
                            "precipitation_probability_max",
                            "wind_speed_10m_max",
                        ]
                    ),
                    "timezone": timezone,
                    "forecast_days": 7,
                },
            )
            response.raise_for_status()
            payload = response.json()

        current_data = payload["current"]
        daily = payload["daily"]
        current = CurrentWeather(
            temperature_c=float(current_data["temperature_2m"]),
            feels_like_c=float(current_data["apparent_temperature"]),
            humidity_pct=int(current_data["relative_humidity_2m"]),
            wind_speed_kmh=float(current_data["wind_speed_10m"]),
            precipitation_mm=float(current_data["precipitation"]),
            weather_code=int(current_data["weather_code"]),
            condition=weather_condition(int(current_data["weather_code"])),
            is_day=bool(current_data["is_day"]),
        )
        forecast: list[ForecastDay] = []
        for index, day_value in enumerate(daily["time"]):
            forecast.append(
                ForecastDay(
                    date=date.fromisoformat(day_value),
                    min_c=float(daily["temperature_2m_min"][index]),
                    max_c=float(daily["temperature_2m_max"][index]),
                    precipitation_probability_pct=int(
                        daily.get("precipitation_probability_max", [0] * 7)[index] or 0
                    ),
                    precipitation_mm=float(daily["precipitation_sum"][index] or 0),
                    wind_max_kmh=float(daily["wind_speed_10m_max"][index]),
                    condition=weather_condition(int(daily["weather_code"][index])),
                )
            )
        location = WeatherLocation(
            name=name,
            region=region,
            country=country,
            latitude=float(payload.get("latitude", lat)),
            longitude=float(payload.get("longitude", lon)),
            timezone=payload.get("timezone", "UTC"),
        )
        advisories = _advisories(current, forecast)
        summary = (
            f"{name} is currently {current.condition.lower()} at {current.temperature_c:.0f}°C "
            f"with {current.humidity_pct}% humidity and winds near {current.wind_speed_kmh:.0f} km/h. "
            f"Over the next 7 days, highs range from {min(day.max_c for day in forecast):.0f}°C to "
            f"{max(day.max_c for day in forecast):.0f}°C; peak rain probability is "
            f"{max(day.precipitation_probability_pct for day in forecast)}%."
        )
        result = WeatherResult(
            location=location,
            current=current,
            forecast=forecast,
            advisories=advisories,
            work_windows=_work_windows(forecast),
            summary=summary,
            data_source="open-meteo",
            disclaimer=(
                "Forecast data from Open-Meteo. Use official warnings for safety-critical go/no-go decisions."
            ),
        )
        _cache[key] = (time.time(), result)
        return result, "open-meteo", []
    except Exception as exc:  # noqa: BLE001 - weather must remain usable offline
        result = demo_weather(city or "", latitude, longitude)
        message = str(exc).strip() or exc.__class__.__name__
        if len(message) > 240:
            message = message[:240] + "..."
        return (
            result,
            "fallback",
            [f"Live weather unavailable; demo weather shown. Reason: {message}"],
        )
