"""Deterministic offline intelligence engine.

Used when no LLM API key is configured or when a live AI call fails validation.
It keeps the whole platform demonstrable without network access while clearly
marking results as demo output in the API envelope.
"""

from __future__ import annotations

import math
import random
from datetime import date, timedelta

from app.schemas.assistant import AssistantRequest, AssistantResult
from app.schemas.crack import CrackMeasurement, CrackResult
from app.schemas.knowledge import KnowledgeReference, KnowledgeRequest, KnowledgeResult
from app.schemas.planning import (
    ColorSwatch,
    CostBreakdown,
    DesignConcept,
    FloorPlan,
    MaterialItem,
    PlanningRequest,
    PlanningResult,
    RoomLayout,
    Schedule,
    Task,
)
from app.schemas.safety import Hazard, PpeCompliance, SafetyResult
from app.schemas.valuation import (
    Comparable,
    ValuationFactor,
    ValuationRequest,
    ValuationResult,
)
from app.schemas.weather import (
    CurrentWeather,
    ForecastDay,
    WeatherAdvisory,
    WeatherLocation,
    WeatherResult,
    WorkWindow,
)
from app.services.image_utils import ImageStats

DISCLAIMER_SAFETY = (
    "AI-assisted preliminary assessment only. It does not replace a competent safety "
    "officer, site inspection, or statutory compliance review."
)
DISCLAIMER_CRACK = (
    "AI-assisted visual screening only. Crack severity must be confirmed by a qualified "
    "structural engineer, especially for load-bearing elements."
)
DISCLAIMER_VALUATION = (
    "Indicative estimate for planning only, not a certified valuation. Verify title, "
    "encumbrances, approvals, and recent transactions with a registered valuer."
)
DISCLAIMER_KNOWLEDGE = (
    "General construction guidance for education. Always follow the latest local codes, "
    "project specifications, and advice from qualified professionals."
)

CITY_FACTORS = {
    "mumbai": 1.35,
    "delhi": 1.20,
    "new delhi": 1.20,
    "bengaluru": 1.25,
    "bangalore": 1.25,
    "hyderabad": 1.15,
    "chennai": 1.12,
    "pune": 1.15,
    "kolkata": 1.00,
    "ahmedabad": 0.95,
    "jaipur": 0.90,
    "lucknow": 0.88,
    "noida": 1.10,
    "gurugram": 1.20,
    "gurgaon": 1.20,
    "chandigarh": 1.00,
    "kochi": 0.98,
    "indore": 0.88,
    "surat": 0.92,
    "nagpur": 0.86,
    "bhopal": 0.85,
    "patna": 0.82,
    "coimbatore": 0.90,
}

VALUATION_RATES = {
    "mumbai": 24000,
    "delhi": 15000,
    "new delhi": 15000,
    "bengaluru": 12000,
    "bangalore": 12000,
    "hyderabad": 9000,
    "chennai": 9500,
    "pune": 10000,
    "kolkata": 7500,
    "ahmedabad": 6500,
    "jaipur": 5500,
    "lucknow": 5000,
    "noida": 8500,
    "gurugram": 9500,
    "gurgaon": 9500,
    "chandigarh": 6000,
    "kochi": 6500,
    "indore": 5000,
    "surat": 5200,
    "nagpur": 4800,
    "bhopal": 4600,
    "patna": 4500,
    "coimbatore": 5500,
}


def _rng(*parts: object) -> random.Random:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
    import hashlib

    return random.Random(int.from_bytes(hashlib.sha256(raw).digest()[:8], "big"))


def _city_factor(city: str) -> float:
    return CITY_FACTORS.get(city.strip().lower(), 0.95)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _title_city(city: str) -> str:
    return " ".join(part.capitalize() for part in city.strip().split())


# ---------------------------------------------------------------------------
# Safety
# ---------------------------------------------------------------------------

HAZARD_LIBRARY: dict[str, dict[str, object]] = {
    "fall": {
        "title": "Fall from height / unprotected edge",
        "description": "Workers are exposed near an unguarded slab edge or opening with no continuous guardrail or personal fall-arrest system.",
        "action": "Erect double-rail guardrails and toe boards, cover openings with load-rated covers, and enforce full-body harness use with anchor points.",
        "ppe": ["Full-body harness", "Safety helmet", "Safety boots"],
    },
    "ppe": {
        "title": "PPE non-compliance",
        "description": "One or more workers appear to be missing task-critical personal protective equipment for the activity being performed.",
        "action": "Stop the task, issue the missing PPE, brief the crew, and record the violation in the daily safety register.",
        "ppe": ["Safety helmet", "High-visibility vest", "Safety boots"],
    },
    "electrical": {
        "title": "Exposed temporary electrical hazard",
        "description": "Temporary cables, distribution boards, or connections show signs of poor guarding, damage, or contact with water.",
        "action": "Isolate the circuit, use RCD-protected distribution boards, route cables overhead, and have a licensed electrician inspect the installation.",
        "ppe": ["Electrical gloves", "Safety boots", "Arc-rated clothing"],
    },
    "housekeeping": {
        "title": "Poor housekeeping and trip hazards",
        "description": "Loose materials, debris, and stored items are obstructing access routes and emergency exits on the working level.",
        "action": "Clear access routes, designate material storage zones, and schedule end-of-shift housekeeping with assigned accountability.",
        "ppe": ["Safety boots", "Gloves"],
    },
    "scaffolding": {
        "title": "Incomplete or untagged scaffolding",
        "description": "Scaffold sections lack complete platforms, guardrails, base plates, or a current inspection tag.",
        "action": "Tag and isolate the scaffold, complete missing components, and release it only after a competent person's inspection.",
        "ppe": ["Full-body harness", "Safety helmet", "Safety boots"],
    },
    "fire": {
        "title": "Hot-work and fire risk",
        "description": "Welding, grinding, or other hot work is occurring near combustible material without adequate fire watch controls.",
        "action": "Issue a hot-work permit, remove combustibles, provide fire extinguishers, and maintain a trained fire watch for 60 minutes after work.",
        "ppe": ["Welding shield", "Flame-resistant clothing", "Safety boots"],
    },
    "lifting": {
        "title": "Uncontrolled lifting operation",
        "description": "A lifting zone is active with personnel, rigging, or load path conditions that are not fully controlled.",
        "action": "Establish an exclusion zone, verify rigging and lift plans, use a banksman, and stop the lift in high wind or poor visibility.",
        "ppe": ["Safety helmet", "High-visibility vest", "Safety boots"],
    },
    "excavation": {
        "title": "Excavation instability and edge protection",
        "description": "The excavation shows inadequate shoring, sloped banks, edge barriers, or safe access for the soil conditions.",
        "action": "Reassess soil conditions, install shoring or safe batter, barricade the perimeter, and provide a secured ladder within 7.5 m of the work face.",
        "ppe": ["Safety helmet", "Safety boots", "High-visibility vest"],
    },
    "chemical": {
        "title": "Chemical and dust exposure",
        "description": "Workers may be exposed to silica dust, solvent vapours, or cementitious materials without suitable respiratory and skin protection.",
        "action": "Use dust suppression or extraction, provide correct respirators and gloves, and make safety data sheets available at the point of use.",
        "ppe": ["Respirator", "Safety goggles", "Chemical gloves"],
    },
    "housekeeping2": {
        "title": "Unsafe material stacking",
        "description": "Materials are stacked at excessive height or on uneven ground, creating a collapse and access risk.",
        "action": "Limit stack heights, use dunnage, keep stacks away from edges and access routes, and assign a storage plan.",
        "ppe": ["Safety boots", "Gloves", "Safety helmet"],
    },
}

KEYWORD_HAZARDS = {
    "fall": ["height", "edge", "opening", "roof", "slab", "ladder", "platform", "parapet"],
    "ppe": ["helmet", "ppe", "vest", "harness", "gloves", "goggles", "shoe"],
    "electrical": ["wire", "electrical", "cable", "panel", "shock", "db", "temporary power"],
    "housekeeping": ["debris", "clutter", "trip", "waste", "material", "housekeeping"],
    "scaffolding": ["scaffold", "bamboo", "prop", "staging"],
    "fire": ["weld", "hot work", "fire", "gas", "cylinder", "flammable", "grind"],
    "lifting": ["crane", "lift", "hoist", "rigging", "load", "banksman"],
    "excavation": ["excavation", "excavat", "trench", "pit", "shoring", "soil"],
    "chemical": ["chemical", "paint", "solvent", "silica", "dust", "epoxy"],
}

HAZARD_LOCATIONS = [
    "North facade, Level 2",
    "Main access ramp",
    "Material storage yard",
    "Level 1 slab edge",
    "Temporary power distribution area",
    "Scaffold access stair",
    "Excavation perimeter",
    "Lifting zone near tower crane",
    "Ground floor work front",
]

SEVERITY_WEIGHT = {"low": 6, "medium": 13, "high": 22, "critical": 32}
LIKELIHOOD_WEIGHT = {"rare": 0, "unlikely": 1, "possible": 3, "likely": 5, "almost_certain": 7}


def demo_safety(
    *,
    description: str,
    project_type: str,
    location: str,
    activity: str,
    stats: ImageStats | None,
) -> SafetyResult:
    text = description.lower()
    rng = _rng(description, project_type, location, activity, stats.seed if stats else "text")
    categories: list[str] = []

    for category, keywords in KEYWORD_HAZARDS.items():
        if any(keyword in text for keyword in keywords):
            categories.append(category)

    if not categories:
        defaults = ["fall", "housekeeping", "ppe"]
        if project_type in {"industrial", "infrastructure"}:
            defaults = ["lifting", "fall", "ppe"]
        if project_type == "commercial":
            defaults = ["electrical", "housekeeping", "fall"]
        categories = defaults

    if stats is not None:
        if stats.brightness < 55:
            categories.append("electrical")
        if stats.edge_density > 0.16:
            categories.append("fall")
    else:
        categories.append("ppe")

    categories = list(dict.fromkeys(categories))[:6]
    if len(categories) < 3:
        for extra in ["ppe", "housekeeping", "fall"]:
            if extra not in categories:
                categories.append(extra)
            if len(categories) >= 3:
                break

    hazards: list[Hazard] = []
    urgent = any(word in text for word in ["critical", "severe", "urgent", "danger", "collapse"])
    for index, category in enumerate(categories, start=1):
        library_key = "housekeeping" if category == "housekeeping" else category
        item = HAZARD_LIBRARY.get(library_key, HAZARD_LIBRARY["housekeeping"])
        severity = rng.choices(
            ["medium", "high", "critical"],
            weights=[55, 33, 12] if not urgent else [30, 42, 28],
            k=1,
        )[0]
        if category == "ppe":
            severity = "high" if severity != "critical" else "critical"
        likelihood = rng.choices(
            ["possible", "likely", "almost_certain"], weights=[38, 42, 20], k=1
        )[0]
        hazard = Hazard(
            id=f"H-{index:02d}",
            title=str(item["title"]),
            category=category,  # type: ignore[arg-type]
            severity=severity,  # type: ignore[arg-type]
            likelihood=likelihood,  # type: ignore[arg-type]
            location=rng.choice(HAZARD_LOCATIONS),
            description=str(item["description"]),
            corrective_action=str(item["action"]),
            ppe_required=[str(value) for value in item["ppe"]],  # type: ignore[union-attr]
        )
        hazards.append(hazard)

    observed = ["Safety helmets", "High-visibility vests", "Safety boots"]
    missing: list[str] = []
    if "ppe" in categories:
        missing = rng.sample(["Safety helmets", "High-visibility vests", "Eye protection"], k=2)
    elif rng.random() < 0.35:
        missing = ["Eye protection"]
    observed = [item for item in observed if item not in missing]
    ppe_score = _clamp(100 - len(missing) * 24 - (0 if stats else 8), 20, 100)
    overall = (
        "compliant"
        if ppe_score >= 90
        else "partial"
        if ppe_score >= 55
        else "non_compliant"
    )

    base = 8 + sum(
        SEVERITY_WEIGHT[h.severity] * 0.55 + LIKELIHOOD_WEIGHT[h.likelihood] for h in hazards
    )
    if stats is not None and stats.brightness < 55:
        base += 7
    risk_score = int(_clamp(base, 15, 96))
    risk_level = (
        "low"
        if risk_score < 30
        else "moderate"
        if risk_score < 55
        else "high"
        if risk_score < 80
        else "critical"
    )

    immediate = [h.corrective_action for h in sorted(hazards, key=lambda x: x.severity, reverse=True)[:3]]
    immediate.append("Hold a toolbox talk covering the identified hazards before work resumes.")
    positive = rng.sample(
        [
            "Access routes were generally identifiable and free of major obstruction.",
            "Emergency exit signage is visible from the main work area.",
            "Materials are mostly stored within designated zones.",
            "The work front appears organised with active supervision visible.",
        ],
        k=2,
    )

    if stats is None:
        summary = (
            f"Text-only review of the {activity.lower()} activity at {location} indicates a "
            f"{risk_level} risk profile with {len(hazards)} priority hazards. Upload a site "
            "photograph for a stronger visual assessment."
        )
        confidence = 0.62
        quality = "not_provided"
    else:
        summary = (
            f"Visual and contextual review of the {activity.lower()} activity at {location} "
            f"identified {len(hazards)} hazards, including {hazards[0].title.lower()}. "
            f"The combined risk is {risk_level}; address the critical controls before the next work shift."
        )
        quality = (
            "good" if stats.edge_density > 0.03 and stats.brightness > 65 else "fair" if stats.brightness > 40 else "poor"
        )
        confidence = round(_clamp(0.68 + stats.edge_density, 0.68, 0.9), 2)

    return SafetyResult(
        risk_score=risk_score,
        risk_level=risk_level,  # type: ignore[arg-type]
        summary=summary,
        hazards=hazards,
        ppe=PpeCompliance(
            overall=overall,  # type: ignore[arg-type]
            observed=observed,
            missing=missing,
            score=int(ppe_score),
        ),
        immediate_actions=immediate,
        positive_observations=positive,
        confidence=confidence,
        image_quality=quality,  # type: ignore[arg-type]
        disclaimer=DISCLAIMER_SAFETY,
    )


# ---------------------------------------------------------------------------
# Crack analysis
# ---------------------------------------------------------------------------

CRACK_CAUSES = {
    "hairline": ["Surface shrinkage of plaster or putty", "Minor thermal movement", "Application or curing variation"],
    "structural": ["Overloading or inadequate reinforcement", "Design or construction deficiency", "Progressive structural distress"],
    "settlement": ["Differential foundation settlement", "Variable or poorly compacted subsoil", "Adjacent excavation or water ingress"],
    "shrinkage": ["Plastic or drying shrinkage of concrete", "Rich cement mortar mix", "Rapid surface moisture loss"],
    "thermal": ["Daily temperature cycling", "Lack of movement joints", "Differential expansion of materials"],
    "shear": ["Shear stress near supports", "Insufficient shear reinforcement", "Support movement or overload"],
    "flexural": ["Bending stress exceeding capacity", "Sagging or deflection of the member", "Insufficient flexural reinforcement"],
    "corrosion": ["Carbonation or chloride-induced reinforcement corrosion", "Insufficient cover", "Moisture ingress and spalling"],
    "unknown": ["Cause cannot be confirmed from a single image", "Localised surface defect", "Material or workmanship variation"],
}

CRACK_ACTIONS = {
    "minor": ["Clean and monitor the area; record width and length every 30 days.", "Repair non-structural surface cracks with a suitable polymer-modified filler.", "Confirm curing and drainage are adequate around the affected element."],
    "moderate": ["Engage a structural engineer for a site inspection.", "Install crack monitors and record movement for 2-4 weeks.", "Repair after the cause is confirmed; do not conceal active movement."],
    "severe": ["Restrict access below or around the affected element immediately.", "Arrange urgent structural inspection and temporary propping if required.", "Prepare a repair methodology with a licensed structural engineer."],
    "critical": ["Evacuate and barricade the affected zone immediately.", "Notify the project structural engineer and client without delay.", "Do not load or repair the element until it is declared safe."],
}

TYPE_KEYWORDS = {
    "structural": ["structural", "beam", "column", "load", "wide", "deep", "spalling"],
    "settlement": ["settlement", "foundation", "subsidence", "soil", "diagonal", "door"],
    "shrinkage": ["shrinkage", "plaster", "surface", "plastic", "putty"],
    "thermal": ["thermal", "temperature", "expansion", "movement"],
    "shear": ["shear", "diagonal", "support"],
    "flexural": ["flexural", "sagging", "deflection", "beam"],
    "corrosion": ["corrosion", "rust", "rebar", "cover", "spall"],
    "hairline": ["hairline", "fine", "small", "minor"],
}

ELEMENT_KEYWORDS = {
    "beam": "Beam",
    "column": "Column",
    "slab": "Slab",
    "wall": "Wall",
    "plaster": "Plaster / wall finish",
    "foundation": "Foundation",
    "ceiling": "Ceiling",
    "foundation": "Foundation",
}

WIDTH_BY_TYPE = {
    "hairline": (0.1, 0.4),
    "shrinkage": (0.2, 1.2),
    "thermal": (0.4, 2.2),
    "settlement": (1.0, 6.0),
    "structural": (1.5, 10.0),
    "shear": (1.0, 5.0),
    "flexural": (0.5, 4.0),
    "corrosion": (0.2, 3.0),
    "unknown": (0.2, 2.0),
}


def demo_crack(
    *,
    description: str,
    structure_type: str,
    stats: ImageStats,
) -> CrackResult:
    text = description.lower()
    rng = _rng(description, structure_type, stats.seed)
    requested_type: str | None = None
    for crack_type, keywords in TYPE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            requested_type = crack_type
            break

    detected = stats.edge_density > 0.035 or requested_type is not None
    image_quality = (
        "good"
        if stats.brightness > 60 and stats.edge_density > 0.03
        else "fair"
        if stats.brightness > 35
        else "poor"
    )

    if not detected:
        return CrackResult(
            detected=False,
            crack_type="unknown",
            severity="minor",
            severity_score=12,
            summary=(
                "No clear crack pattern was identified in the uploaded frame. The image may "
                "show sound concrete, or the crack may be too fine or poorly lit for this view."
            ),
            affected_element=structure_type,
            probable_causes=["No visible defect in this view", "Insufficient lighting or resolution", "Crack may be outside the camera frame"],
            measurements=CrackMeasurement(estimated_length_cm=None, estimated_width_mm=None, confidence=0.55),
            recommended_actions=[
                "Take close-up photographs in good daylight, perpendicular to the surface.",
                "Include a ruler or known reference object in the frame for scale.",
                "Inspect nearby joints, corners, and openings for related movement.",
            ],
            urgency="monitor",
            requires_professional_inspection=False,
            confidence=0.58,
            image_quality=image_quality,  # type: ignore[arg-type]
            disclaimer=DISCLAIMER_CRACK,
        )

    crack_type = requested_type or rng.choices(
        ["shrinkage", "thermal", "settlement", "hairline", "corrosion", "structural"],
        weights=[26, 20, 18, 16, 12, 8],
        k=1,
    )[0]

    width_low, width_high = WIDTH_BY_TYPE[crack_type]
    width_mm = round(rng.uniform(width_low, width_high), 2)
    length_cm = round(rng.uniform(25, 280), 1)
    severity_score = int(
        _clamp(
            22 + stats.edge_density * 260 + width_mm * 5 + (12 if requested_type else 0),
            18,
            96,
        )
    )
    severity = (
        "minor"
        if severity_score < 32
        else "moderate"
        if severity_score < 56
        else "severe"
        if severity_score < 80
        else "critical"
    )
    if crack_type in {"structural", "shear"}:
        severity = "severe" if severity in {"minor", "moderate"} else "critical"

    affected = structure_type
    for keyword, element in ELEMENT_KEYWORDS.items():
        if keyword in text:
            affected = element
            break
    if affected == "auto":
        affected = rng.choice(["Wall", "Slab", "Beam", "Column", "Plaster / wall finish"])
    if requested_type and requested_type in {"structural", "shear", "flexural"} and affected in {"Wall", "Plaster / wall finish"}:
        affected = "Load-bearing element (confirm on site)"

    urgency = {
        "minor": "monitor",
        "moderate": "schedule_repair",
        "severe": "urgent",
        "critical": "emergency",
    }[severity]
    requires_inspection = severity in {"severe", "critical"} or crack_type in {
        "structural",
        "shear",
        "settlement",
        "corrosion",
    }

    summary = (
        f"A {crack_type} crack pattern is visible on the {affected.lower()}, with an estimated "
        f"width of {width_mm} mm and length of {length_cm} cm. The condition is classified as "
        f"{severity}; {'restrict access and arrange an urgent structural review.' if requires_inspection else 'monitor movement and repair after confirming the cause.'}"
    )

    return CrackResult(
        detected=True,
        crack_type=crack_type,  # type: ignore[arg-type]
        severity=severity,  # type: ignore[arg-type]
        severity_score=severity_score,
        summary=summary,
        affected_element=affected,
        probable_causes=CRACK_CAUSES[crack_type],
        measurements=CrackMeasurement(
            estimated_length_cm=length_cm,
            estimated_width_mm=width_mm,
            confidence=round(_clamp(0.6 + stats.edge_density, 0.6, 0.88), 2),
        ),
        recommended_actions=CRACK_ACTIONS[severity],
        urgency=urgency,  # type: ignore[arg-type]
        requires_professional_inspection=requires_inspection,
        confidence=round(_clamp(0.62 + stats.edge_density * 1.4, 0.62, 0.9), 2),
        image_quality=image_quality,  # type: ignore[arg-type]
        disclaimer=DISCLAIMER_CRACK,
    )


# ---------------------------------------------------------------------------
# Project planning
# ---------------------------------------------------------------------------

BASE_RATES = {
    "residential": 2200,
    "commercial": 3000,
    "industrial": 1900,
    "infrastructure": 2600,
    "renovation": 1500,
}
QUALITY_MULT = {"economy": 0.75, "standard": 1.0, "premium": 1.35, "luxury": 1.8}
FX_USD = 83.0

ROOM_TEMPLATES: dict[str, list[tuple[str, str, float]]] = {
    "residential": [
        ("Living Room", "living", 24),
        ("Kitchen", "kitchen", 11),
        ("Dining", "dining", 9),
        ("Master Bedroom", "bedroom", 16),
        ("Bedroom 2", "bedroom", 12),
        ("Bedroom 3", "bedroom", 11),
        ("Bathroom 1", "bathroom", 5),
        ("Bathroom 2", "bathroom", 4),
        ("Balcony", "balcony", 5),
        ("Circulation / Stair", "circulation", 10),
    ],
    "commercial": [
        ("Reception", "reception", 10),
        ("Open Workstations", "office", 32),
        ("Cabins", "office", 14),
        ("Meeting Room", "meeting", 10),
        ("Pantry", "pantry", 6),
        ("Washrooms", "bathroom", 8),
        ("Server / Utility", "utility", 5),
        ("Circulation", "circulation", 15),
    ],
    "industrial": [
        ("Production / Warehouse", "industrial", 50),
        ("Office", "office", 12),
        ("Storage", "storage", 12),
        ("Utility", "utility", 8),
        ("Washrooms", "bathroom", 5),
        ("Loading Bay", "loading", 10),
        ("Circulation", "circulation", 7),
    ],
    "infrastructure": [
        ("Control Room", "control", 20),
        ("Office", "office", 18),
        ("Storage", "storage", 20),
        ("Utility", "utility", 12),
        ("Welfare Area", "welfare", 12),
        ("Washrooms", "bathroom", 8),
        ("Circulation", "circulation", 10),
    ],
    "renovation": [],
}
ROOM_TEMPLATES["renovation"] = ROOM_TEMPLATES["residential"]


def _slice_layout(
    weights: list[float],
    names: list[tuple[str, str]],
    width: float,
    length: float,
    x: float = 0.0,
    y: float = 0.0,
) -> list[RoomLayout]:
    if len(weights) == 1:
        name, room_type = names[0]
        return [
            RoomLayout(
                name=name,
                room_type=room_type,
                x_ft=round(x, 2),
                y_ft=round(y, 2),
                width_ft=round(width, 2),
                length_ft=round(length, 2),
                area_sqft=round(width * length, 1),
            )
        ]

    total = sum(weights)
    running = 0.0
    split = 1
    best_delta = math.inf
    for index in range(1, len(weights)):
        running += weights[index - 1]
        delta = abs(running / total - 0.5)
        if delta < best_delta:
            best_delta = delta
            split = index
    left_weight = sum(weights[:split])
    ratio = _clamp(left_weight / total, 0.22, 0.78)

    if width >= length:
        left_w = width * ratio
        return _slice_layout(weights[:split], names[:split], left_w, length, x, y) + _slice_layout(
            weights[split:], names[split:], width - left_w, length, x + left_w, y
        )
    top_h = length * ratio
    return _slice_layout(weights[:split], names[:split], width, top_h, x, y) + _slice_layout(
        weights[split:], names[split:], width, length - top_h, x, y + top_h
    )


def _schedule_tasks(area: float, floors: int, start: date) -> Schedule:
    scale = _clamp(math.sqrt(area / 2000), 0.7, 1.8)
    definitions = [
        ("T01", "Site mobilisation and permits", "Pre-construction", 7, []),
        ("T02", "Excavation and foundation", "Substructure", 14, ["T01"]),
        ("T03", "Structural frame and slabs", "Superstructure", 24 + floors * 5, ["T02"]),
        ("T04", "Masonry and internal plaster", "Superstructure", 20, ["T03"]),
        ("T05", "Electrical and plumbing rough-in", "MEP", 14, ["T03"]),
        ("T06", "Waterproofing", "Finishing", 7, ["T04", "T05"]),
        ("T07", "Flooring and tiling", "Finishing", 14, ["T06"]),
        ("T08", "Painting and finishing", "Finishing", 12, ["T07"]),
        ("T09", "Fixtures and fittings", "Handover", 7, ["T08"]),
        ("T10", "Testing, snagging and handover", "Handover", 5, ["T09"]),
    ]
    durations = {
        task_id: max(3, round(duration * scale))
        for task_id, _, _, duration, _ in definitions
    }
    ends: dict[str, int] = {}
    starts: dict[str, int] = {}
    tasks: list[Task] = []
    for task_id, name, phase, _, deps in definitions:
        start_day = 1 if not deps else max(ends[dep] for dep in deps) + 1
        end_day = start_day + durations[task_id] - 1
        starts[task_id] = start_day
        ends[task_id] = end_day
        tasks.append(
            Task(
                id=task_id,
                name=name,
                phase=phase,
                duration_days=durations[task_id],
                start_day=start_day,
                end_day=end_day,
                start_date=start + timedelta(days=start_day - 1),
                end_date=start + timedelta(days=end_day - 1),
                depends_on=deps,
            )
        )

    best: dict[str, tuple[int, list[str]]] = {}
    for task_id, _, _, _, deps in definitions:
        if not deps:
            best[task_id] = (durations[task_id], [task_id])
        else:
            length, path = max((best[dep] for dep in deps), key=lambda item: item[0])
            best[task_id] = (length + durations[task_id], path + [task_id])
    critical_path = max(best.values(), key=lambda item: item[0])[1]
    total = max(ends.values())
    return Schedule(
        total_duration_days=total,
        start_date=start,
        end_date=start + timedelta(days=total - 1),
        tasks=tasks,
        critical_path=critical_path,
    )


def _concept(req: PlanningRequest, area: float) -> DesignConcept:
    palettes = {
        "economy": [("Warm White", "#F3EFE6"), ("Sandstone", "#C9B69A"), ("Slate Grey", "#4A5568"), ("Terracotta", "#C96F4A")],
        "standard": [("Ivory", "#F4F1EA"), ("Concrete Grey", "#9AA0A6"), ("Teak", "#9B6A3F"), ("Deep Teal", "#0F766E")],
        "premium": [("Pearl", "#F8F7F4"), ("Charcoal", "#2F3437"), ("Brass", "#B08D57"), ("Forest", "#1F4D3A")],
        "luxury": [("Alabaster", "#F7F4EE"), ("Onyx", "#1C1F22"), ("Champagne", "#C8A96A"), ("Emerald", "#14532D")],
    }
    style_by_type = {
        "residential": "Warm contemporary",
        "commercial": "Biophilic corporate modern",
        "industrial": "High-performance industrial",
        "infrastructure": "Civic modern",
        "renovation": "Adaptive-reuse contemporary",
    }
    features = {
        "residential": ["Cross-ventilated living zones", "Efficient kitchen work triangle", "Daylit bedrooms with shaded openings", "Integrated utility and storage"],
        "commercial": ["Column-free collaboration zones", "Flexible cabin module", "Daylight-led perimeter workspaces", "Clear visitor and service separation"],
        "industrial": ["Long-span production bay", "Dedicated goods circulation", "High-bay daylighting", "Separated administration block"],
        "infrastructure": ["Resilient service core", "Clear public and operational flows", "Durable low-maintenance finishes", "Accessible welfare facilities"],
        "renovation": ["Retention of the primary structural frame", "Upgraded envelope and services", "Open-plan reconfiguration", "Adaptive reuse of existing finishes"],
    }[req.project_type]
    description = (
        f"A {style_by_type[req.project_type].lower()} concept for a {req.quality} "
        f"{req.project_type} development of {area:,.0f} sq ft across {req.floors} floor(s) "
        f"in {_title_city(req.location)}. The planning prioritises clear circulation, "
        "daylight, maintainability, and a restrained material palette suited to the local context."
    )
    sustainability = [
        "Orient primary glazing to manage solar heat gain and daylight.",
        "Use AAC blocks and fly-ash-blended cement where structurally permitted.",
        "Provide rainwater harvesting and low-flow fixtures.",
        "Specify low-VOC paints and certified composite wood products.",
    ]
    if req.quality in {"premium", "luxury"}:
        sustainability.append("Reserve roof area and conduits for a future solar PV installation.")
    return DesignConcept(
        style=style_by_type[req.project_type],
        description=description,
        key_features=features,
        color_palette=[ColorSwatch(name=name, hex=value) for name, value in palettes[req.quality]],
        sustainability_notes=sustainability,
    )


def demo_planning(req: PlanningRequest) -> PlanningResult:
    rng = _rng(req.location, req.project_type, req.built_up_area_sqft, req.floors)
    area = req.built_up_area_sqft
    rate = (
        BASE_RATES[req.project_type]
        * QUALITY_MULT[req.quality]
        * _city_factor(req.location)
        * rng.uniform(0.97, 1.03)
    )
    total_inr = area * rate
    parts = {
        "structural": total_inr * 0.32,
        "finishing": total_inr * 0.27,
        "mep": total_inr * 0.18,
        "labor": total_inr * 0.17,
        "permits": total_inr * 0.02,
    }
    parts["contingency"] = total_inr * 0.04
    total_inr = sum(parts.values())
    currency = req.currency
    factor = 1.0 if currency == "INR" else 1.0 / FX_USD
    convert = lambda value: round(value * factor, 2) if currency == "USD" else round(value, 2)

    materials_raw = [
        ("OPC 53 grade cement", area * 0.40, "bags", 420, "50 kg bags; includes wastage allowance"),
        ("TMT reinforcement Fe500D", area * 4.2, "kg", 72, "Structural steel for footings, columns, beams and slabs"),
        ("River sand (zone II)", area * 1.8, "cft", 52, "Verify local availability and quality"),
        ("Coarse aggregate 20 mm", area * 1.35, "cft", 38, "Use crushed stone aggregate"),
        ("AAC blocks", round(area * 8), "nos", 48, "600 x 200 x 100 mm nominal blocks"),
        ("Vitrified floor tiles", area * 0.95, "sqft", 68 * QUALITY_MULT[req.quality], "Includes 5% cutting wastage"),
        ("Emulsion paint", area * 0.12, "litre", 320 * QUALITY_MULT[req.quality], "Two coats plus primer"),
        ("Waterproofing membrane", area * 0.35, "sqft", 55, "Terrace, toilets and wet areas"),
        ("Flush doors", max(2, round(area / 450)), "nos", 8500 * QUALITY_MULT[req.quality], "Includes frames and hardware"),
        ("UPVC windows", area * 0.08, "sqft", 700, "Double-glazed where specified"),
        ("Electrical points", max(8, round(area / 120)), "nos", 1200, "Switches, sockets and conduits"),
    ]
    materials = [
        MaterialItem(
            name=name,
            quantity=round(quantity, 2),
            unit=unit,
            unit_cost=convert(unit_cost),
            estimated_cost=convert(quantity * unit_cost),
            notes=notes,
        )
        for name, quantity, unit, unit_cost, notes in materials_raw
    ]

    schedule = _schedule_tasks(area, req.floors, req.start_date)
    concept = _concept(req, area)

    footprint = area / req.floors
    aspect = 1.6 if req.project_type in {"commercial", "industrial"} else 1.35
    width = round(math.sqrt(footprint * aspect), 1)
    length = round(footprint / width, 1)
    template = ROOM_TEMPLATES[req.project_type]
    rooms_template = template
    if req.project_type in {"residential", "renovation"} and footprint < 700:
        rooms_template = [
            room for room in template if room[0] not in {"Bedroom 3", "Bathroom 2", "Dining"}
        ]
    if req.floors > 1 and req.project_type in {"residential", "renovation", "commercial"}:
        rooms_template = [
            room if room[0] != "Circulation / Stair" else ("Stair and Lift Core", "circulation", 10)
            for room in rooms_template
        ]
    names = [(name, room_type) for name, room_type, _ in rooms_template]
    weights = [weight for _, _, weight in rooms_template]
    layout = _slice_layout(weights, names, width, length)
    floor_plan = FloorPlan(
        total_width_ft=width,
        total_length_ft=length,
        typical_floor_area_sqft=round(footprint, 1),
        rooms=layout,
        notes=[
            f"Conceptual typical-floor layout for floor 1 of {req.floors}.",
            "Not a construction drawing; confirm dimensions, structure, and code compliance with an architect.",
        ],
    )

    month = req.start_date.month
    risks = [
        "Material rates are market-sensitive; obtain three current vendor quotations before procurement.",
        "Structural and MEP designs must be validated by licensed consultants.",
        f"Sequence and handover dates assume {schedule.total_duration_days} working-calendar days and favourable weather.",
    ]
    if month in {5, 6}:
        risks.append("Peak summer may affect concrete placement and curing; plan early-morning pours and heat protection.")
    elif month in {7, 8, 9}:
        risks.append("Monsoon conditions may disrupt excavation and finishing; provide drainage and covered storage.")
    elif month in {11, 12, 1}:
        risks.append("Cooler mornings can delay finishes and curing; protect fresh work and monitor dew conditions.")
    if req.floors > 3:
        risks.append("Tall structure: coordinate lift core, scaffolding, and wind-sensitive lifting operations.")
    if area > 100_000:
        risks.append("Large footprint: phase procurement and workforce deployment to avoid congestion at the work front.")

    recommendations = [
        "Freeze the architectural layout and structural grid before issuing the BOQ.",
        "Use a weekly look-ahead schedule and track the critical path tasks T03-T08.",
        "Set a 4% contingency and review it monthly against approved variations.",
        "Inspect waterproofing and MEP pressure tests before closing finishes.",
    ]
    assumptions = [
        "Built-up area includes all floors and is used for cost estimation.",
        f"Rates are indicative {currency} values for {_title_city(req.location)} as of the planning date.",
        "Foundation is assumed to be conventional isolated or raft footings on competent soil.",
        "Cost excludes land, statutory fees beyond permits, interiors, and specialist systems unless noted.",
        "Schedule uses calendar days and allows normal single-shift working.",
    ]

    return PlanningResult(
        project_type=req.project_type,
        built_up_area_sqft=area,
        floors=req.floors,
        location=_title_city(req.location),
        quality=req.quality,
        currency=currency,
        cost=CostBreakdown(
            structural=convert(parts["structural"]),
            finishing=convert(parts["finishing"]),
            mep=convert(parts["mep"]),
            labor=convert(parts["labor"]),
            permits=convert(parts["permits"]),
            contingency=convert(parts["contingency"]),
            total=convert(total_inr),
            cost_per_sqft=convert(total_inr / area),
        ),
        materials=materials,
        schedule=schedule,
        concept=concept,
        floor_plan=floor_plan,
        assumptions=assumptions,
        risks=risks,
        recommendations=recommendations,
    )


# ---------------------------------------------------------------------------
# Real estate valuation
# ---------------------------------------------------------------------------

TYPE_MULT = {"apartment": 1.0, "villa": 1.25, "plot": 0.80, "commercial": 1.30, "office": 1.25, "retail": 1.35}
CONDITION_MULT = {"poor": 0.80, "fair": 0.91, "good": 1.0, "excellent": 1.08}


def demo_valuation(req: ValuationRequest) -> ValuationResult:
    city_key = req.city.strip().lower()
    base_rate = VALUATION_RATES.get(city_key, 5500)
    quality_mult = {"basic": 0.85, "standard": 1.0, "premium": 1.25, "luxury": 1.5}[req.quality]
    age_dep = max(0.55, 1 - req.age_years * 0.012)
    amenity_bonus = min(0.10, len(req.amenities) * 0.015)
    rate = base_rate * TYPE_MULT[req.property_type] * quality_mult * CONDITION_MULT[req.condition] * age_dep * (1 + amenity_bonus)
    estimated = int(round(req.area_sqft * rate / 1000) * 1000)
    spread = 0.10 if req.locality else 0.13
    low = int(round(estimated * (1 - spread) / 1000) * 1000)
    high = int(round(estimated * (1 + spread) / 1000) * 1000)
    price_psf = int(round(estimated / req.area_sqft))
    confidence = round(_clamp(0.86 - (0.06 if req.age_years > 20 else 0) - (0.05 if not req.locality else 0), 0.65, 0.9), 2)
    outlook = "growing" if city_key in {"bengaluru", "bangalore", "hyderabad", "pune", "gurugram", "gurgaon", "noida"} else "stable"

    comps = []
    rng = _rng(req.city, req.locality, req.area_sqft, req.property_type)
    for index, delta in enumerate([-0.18, -0.06, 0.12], start=1):
        comp_area = round(req.area_sqft * (1 + delta), 0)
        comp_rate = int(round(rate * rng.uniform(0.92, 1.08)))
        comps.append(
            Comparable(
                description=f"Comparable {index}: {req.property_type} in {req.locality or req.city}, similar specifications",
                area_sqft=comp_area,
                price_per_sqft=comp_rate,
                estimated_value=comp_area * comp_rate,
            )
        )

    factors = [
        ValuationFactor(factor="Location", impact="positive" if base_rate >= 9000 else "neutral", description=f"{_title_city(req.city)} base rate is ₹{base_rate:,}/sq ft for standard residential property."),
        ValuationFactor(factor="Property age", impact="negative" if req.age_years > 10 else "positive", description=f"{req.age_years}-year-old asset with an estimated age depreciation of {round((1 - age_dep) * 100)}%."),
        ValuationFactor(factor="Quality", impact="positive" if req.quality in {"premium", "luxury"} else "neutral", description=f"{req.quality.title()} specification applied to the base rate."),
        ValuationFactor(factor="Condition", impact="positive" if req.condition == "excellent" else "negative" if req.condition == "poor" else "neutral", description=f"The property is reported to be in {req.condition} condition."),
    ]
    if req.amenities:
        factors.append(ValuationFactor(factor="Amenities", impact="positive", description=f"{len(req.amenities)} amenities add an estimated {round(amenity_bonus * 100, 1)}% premium."))

    summary = (
        f"The estimated market value of the {req.area_sqft:,.0f} sq ft {req.property_type} in "
        f"{req.locality or _title_city(req.city)} is approximately ₹{estimated:,.0f}, with a "
        f"plausible range of ₹{low:,.0f} to ₹{high:,.0f}. The local market outlook is {outlook}."
    )
    assumptions = [
        "The property has clear and marketable title with valid approvals.",
        "Built-up area is verified and matches the saleable area convention used in the locality.",
        "No structural defects, encroachments, or litigation affect the asset.",
        "Indicative rates are based on broad city-level benchmarks, not a physical inspection.",
    ]
    return ValuationResult(
        property_type=req.property_type,
        city=_title_city(req.city),
        locality=req.locality,
        area_sqft=req.area_sqft,
        currency="INR",
        estimated_value=estimated,
        value_range_low=low,
        value_range_high=high,
        price_per_sqft=price_psf,
        confidence=confidence,
        market_outlook=outlook,  # type: ignore[arg-type]
        summary=summary,
        comparable_sales=comps,
        valuation_factors=factors,
        recommendations=[
            "Obtain a formal valuation from a registered valuer before a transaction or loan.",
            "Verify title, encumbrance certificate, occupancy certificate, and approved plans.",
            "Compare at least three recent registered transactions in the same micro-market.",
            "Account for maintenance dues, transfer charges, and applicable stamp duty separately.",
        ],
        assumptions=assumptions,
        disclaimer=DISCLAIMER_VALUATION,
    )


# ---------------------------------------------------------------------------
# Knowledge base + assistant
# ---------------------------------------------------------------------------

KNOWLEDGE_BASE = [
    {
        "slug": "concrete-curing",
        "topic": "concrete",
        "title": "Concrete curing and early-age protection",
        "keywords": ["curing", "concrete", "ponding", "strength", "hydration", "hot weather"],
        "summary": "Concrete must retain moisture during early hydration. Moist-cure structural concrete for at least 7 days, and continue to 14 days for critical elements, hot weather, or blended cements.",
        "key_points": [
            "Start curing as soon as the surface can resist damage, typically within 12-24 hours.",
            "Keep surfaces continuously moist using ponding, wet hessian, or curing compounds.",
            "Protect fresh concrete from rapid drying, wind, and direct sun.",
            "Test cubes at 7 and 28 days and maintain a curing register.",
        ],
        "tips": ["In hot weather, schedule pours early and use evaporation retarders.", "Do not finish surfaces while bleed water is present."],
        "references": [("IS 456:2000 — Plain and reinforced concrete", "Bureau of Indian Standards"), ("Concrete curing best practices", "Indian Concrete Institute")],
        "related": ["Concrete testing and acceptance", "Hot-weather concreting", "Water-cement ratio"],
    },
    {
        "slug": "concrete-testing",
        "topic": "quality",
        "title": "Concrete testing and acceptance",
        "keywords": ["slump", "cube", "test", "nd", "quality", "strength", "acceptance"],
        "summary": "Use slump tests for workability and cube tests for compressive strength. Sample at the point of placement, cure the cubes under standard conditions, and evaluate results against the specified grade.",
        "key_points": [
            "Take samples as per IS 1199 and test cubes at 7 and 28 days.",
            "Maintain a sampling plan covering each pour and each concrete grade.",
            "Check slump against the approved workability range; do not add water to correct slump.",
            "Use NDT such as rebound hammer or UPV only as supporting evidence.",
        ],
        "tips": ["Label cubes with location, grade, date, and pour reference.", "Store cubes in a curing tank, not on site rubble."],
        "references": [("IS 516 — Methods of tests for strength of concrete", "Bureau of Indian Standards"), ("IS 1199 — Sampling and analysis of concrete", "Bureau of Indian Standards")],
        "related": ["Concrete curing", "Mix design", "Quality control plan"],
    },
    {
        "slug": "rebar",
        "topic": "steel",
        "title": "Reinforcement cover, laps, and corrosion",
        "keywords": ["rebar", "steel", "cover", "lap", "reinforcement", "corrosion", "spalling"],
        "summary": "Reinforcement performance depends on correct grade, spacing, cover, and laps. Maintain specified cover with chairs and spacers, and never field-bend bars without engineer approval.",
        "key_points": [
            "Verify bar diameter, grade, and spacing against the approved bar-bending schedule.",
            "Maintain cover using certified spacers and check before every pour.",
            "Use the specified lap length and stagger laps; avoid congestion at beam-column joints.",
            "Clean loose rust and remove formwork debris before concreting.",
        ],
        "tips": ["Photograph reinforcement and cover checks before concrete placement.", "Store rebar clear of the ground and protect it from moisture."],
        "references": [("IS 456:2000 — Durability and cover requirements", "Bureau of Indian Standards"), ("IS 2502 — Bending and fixing of bars", "Bureau of Indian Standards")],
        "related": ["Corrosion of reinforcement", "Structural inspection", "Quality control plan"],
    },
    {
        "slug": "scaffolding",
        "topic": "safety",
        "title": "Scaffolding safety and inspection",
        "keywords": ["scaffold", "scaffolding", "platform", "guardrail", "harness", "fall", "inspection"],
        "summary": "Scaffolds must be designed for the intended load, erected by trained workers, and inspected before use and after any modification, adverse weather, or impact.",
        "key_points": [
            "Provide base plates, sole boards, bracing, and adequate ties to the structure.",
            "Use guardrails, mid-rails, toe boards, and complete working platforms.",
            "Tag scaffolds clearly as safe, incomplete, or awaiting inspection.",
            "Deny access to incomplete scaffolds and enforce fall arrest where required.",
        ],
        "tips": ["Inspect after rain or high wind before allowing access.", "Keep scaffold access clear and use internal stairs or ladders."],
        "references": [("IS 3696 — Safety code for scaffolds and ladders", "Bureau of Indian Standards"), ("OSHA 1926 Subpart L — Scaffolds", "US Department of Labor")],
        "related": ["Fall protection", "Site safety inductions", "Working at height"],
    },
    {
        "slug": "excavation",
        "topic": "excavation",
        "title": "Excavation safety and shoring",
        "keywords": ["excavation", "trench", "shoring", "soil", "slope", "collapse", "pit"],
        "summary": "Excavations are high-risk confined spaces. Assess soil, locate underground services, provide shoring or safe slopes, and control access around the perimeter.",
        "key_points": [
            "Obtain utility clearances and use a cable locator before digging.",
            "Provide shoring, trench shields, or benching for unstable soil.",
            "Barricade edges, provide toe boards, and install safe ladder access.",
            "Inspect after rain, vehicle loading, or any ground movement.",
        ],
        "tips": ["Keep spoil and plant at least 1 m from the excavation edge.", "Never allow workers to enter an unprotected trench."],
        "references": [("IS 3764 — Excavation work safety code", "Bureau of Indian Standards"), ("OSHA 1926 Subpart P — Excavations", "US Department of Labor")],
        "related": ["Underground utility detection", "Confined space entry", "Foundation inspection"],
    },
    {
        "slug": "waterproofing",
        "topic": "waterproofing",
        "title": "Waterproofing: substrate, membrane, and testing",
        "keywords": ["waterproofing", "leak", "membrane", "terrace", "toilet", "damp", "ponding"],
        "summary": "Successful waterproofing depends on a sound, clean substrate, correct detailing at junctions, continuous membrane application, and a proof test before finishes are closed.",
        "key_points": [
            "Cure and dry the substrate; remove loose material and honeycombing.",
            "Use fillets at wall-floor junctions and reinforce all penetrations.",
            "Apply the specified number of coats with adequate intercoat drying.",
            "Conduct a 24-48 hour ponding test and document the result.",
        ],
        "tips": ["Protect the membrane from punctures during subsequent works.", "Slope terraces to drains before applying the membrane."],
        "references": [("IS 3067 — Waterproofing of roofs", "Bureau of Indian Standards"), ("Manufacturer application guidelines", "Approved system supplier")],
        "related": ["Wet-area detailing", "Quality control plan", "Leak investigation"],
    },
    {
        "slug": "scheduling",
        "topic": "scheduling",
        "title": "Project scheduling with critical path method",
        "keywords": ["schedule", "delay", "critical path", "cpm", "timeline", "duration", "milestone", "float"],
        "summary": "A reliable schedule starts with a work breakdown structure, clear dependencies, realistic durations, and an identified critical path. Track progress weekly against the baseline.",
        "key_points": [
            "Break work into deliverable-based activities with accountable owners.",
            "Identify predecessors and lag; validate the network before baselining.",
            "Track the critical path and near-critical float every week.",
            "Recover delay with resequencing, added shifts, or scope decisions—not by compressing safety.",
        ],
        "tips": ["Add weather and approval buffers explicitly.", "Use a 3-week look-ahead and update the master schedule monthly."],
        "references": [("PMBOK Guide — Schedule management", "Project Management Institute"), ("CPM scheduling fundamentals", "Construction Industry Institute")],
        "related": ["Delay analysis", "Procurement lead times", "Progress reporting"],
    },
    {
        "slug": "costing",
        "topic": "costing",
        "title": "Construction cost estimation and contingency",
        "keywords": ["cost", "estimate", "budget", "boq", "rate", "contingency", "variation"],
        "summary": "Build estimates from measured quantities, rate analysis, and current vendor quotations. Keep contingency separate from the base estimate and control it through an approval process.",
        "key_points": [
            "Use a measured BOQ linked to drawings and specifications.",
            "Carry 3-5% design contingency and 2-3% construction contingency for typical buildings.",
            "Separate escalation, taxes, and statutory charges from construction cost.",
            "Review actual versus budget monthly against the cost code structure.",
        ],
        "tips": ["Get three quotations for major packages.", "Record assumptions and exclusions in the estimate basis."],
        "references": [("IS 1200 — Measurement of building works", "Bureau of Indian Standards"), ("RICS New Rules of Measurement", "Royal Institution of Chartered Surveyors")],
        "related": ["Procurement planning", "Variation management", "Cash-flow forecasting"],
    },
    {
        "slug": "procurement",
        "topic": "procurement",
        "title": "Procurement planning and material storage",
        "keywords": ["procurement", "vendor", "material", "delivery", "storage", "lead time", "cement"],
        "summary": "Procurement must follow the construction sequence. Map lead times, approve vendors, inspect deliveries, and store materials to prevent deterioration.",
        "key_points": [
            "Create a procurement schedule with lead times and float for critical items.",
            "Evaluate vendors on quality, capacity, and past performance—not price alone.",
            "Inspect and record quantities and condition at delivery.",
            "Store cement on raised platforms, rebar clear of ground, and aggregates on hardstand.",
        ],
        "tips": ["Use first-in, first-out storage.", "Track reusable formwork and scaffolding as assets."],
        "references": [("Procurement good practice guides", "Chartered Institute of Building"), ("IS 4082 — Storage of construction materials", "Bureau of Indian Standards")],
        "related": ["Cost estimation", "Schedule management", "Quality control"],
    },
    {
        "slug": "green-building",
        "topic": "green_building",
        "title": "Green building measures for Indian projects",
        "keywords": ["green", "sustainability", "energy", "water", "igbc", "griha", "solar", "waste"],
        "summary": "Low-cost sustainability starts with orientation, envelope performance, water efficiency, and construction waste reduction. Certification can follow after basic performance is designed in.",
        "key_points": [
            "Optimise orientation and shading before sizing mechanical systems.",
            "Use low-flow fixtures and rainwater harvesting for water efficiency.",
            "Specify fly-ash blends, AAC blocks, and recycled content where permissible.",
            "Segregate construction waste and track diversion from landfill.",
        ],
        "tips": ["Keep a material register with certifications.", "Commission building systems before occupancy."],
        "references": [("IGBC Green Building Rating System", "Indian Green Building Council"), ("GRIHA rating system", "TERI")],
        "related": ["Energy modelling", "Waterproofing", "Sustainable procurement"],
    },
    {
        "slug": "fall-protection",
        "topic": "safety",
        "title": "Fall protection and working at height",
        "keywords": ["fall", "height", "harness", "guardrail", "opening", "ladder", "anchor"],
        "summary": "Eliminate work at height where possible; otherwise provide guardrails and covers as the primary control, then use fall-arrest systems with trained users and verified anchors.",
        "key_points": [
            "Cover floor openings with secured, load-rated covers marked clearly.",
            "Use guardrails with top rail, mid-rail, and toe board at exposed edges.",
            "Inspect harnesses before use and provide a rescue plan.",
            "Never anchor fall arrest to non-structural elements.",
        ],
        "tips": ["Conduct a toolbox talk before each height activity.", "Stop work in high wind or poor visibility."],
        "references": [("OSHA 1926 Subpart M — Fall protection", "US Department of Labor"), ("IS 3521 — Industrial safety belts and harnesses", "Bureau of Indian Standards")],
        "related": ["Scaffolding safety", "Site induction", "Rescue planning"],
    },
    {
        "slug": "quality-plan",
        "topic": "quality",
        "title": "Building a construction quality control plan",
        "keywords": ["quality", "inspection", "checklist", "itp", "hold point", "acceptance", "snag"],
        "summary": "A quality control plan defines what is inspected, by whom, at which hold points, and against what acceptance criteria. It must be traceable to drawings, specifications, and test records.",
        "key_points": [
            "Create inspection and test plans for every major work package.",
            "Define hold points that cannot be released without documented inspection.",
            "Record materials, test results, and non-conformities with photo evidence.",
            "Close snags before handover and archive as-built records.",
        ],
        "tips": ["Use a mobile checklist to capture evidence at the work face.", "Review recurring defects at weekly quality meetings."],
        "references": [("ISO 9001 — Quality management systems", "International Organization for Standardization"), ("Project specifications and approved drawings", "Contract documents")],
        "related": ["Concrete testing", "Waterproofing", "Snagging and handover"],
    },
]

KNOWLEDGE_BY_SLUG = {entry["slug"]: entry for entry in KNOWLEDGE_BASE}


def find_knowledge(question: str, topic: str = "general", limit: int = 2) -> list[dict]:
    text = question.lower()
    scored: list[tuple[int, dict]] = []
    for entry in KNOWLEDGE_BASE:
        score = 0
        if topic != "general" and entry["topic"] == topic:
            score += 6
        for keyword in entry["keywords"]:
            if keyword in text:
                score += 2
        if entry["title"].lower() in text:
            score += 3
        if score:
            scored.append((score, entry))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [entry for _, entry in scored[:limit]]


def demo_knowledge(req: KnowledgeRequest) -> KnowledgeResult:
    matches = find_knowledge(req.question, req.topic, limit=2)
    entry = matches[0] if matches else KNOWLEDGE_BASE[0]
    related = [value for value in entry["related"] if value]
    topic = req.topic if req.topic != "general" else entry["topic"]
    answer = entry["summary"]
    if len(matches) > 1:
        answer += " " + matches[1]["summary"]
    answer += (
        f" For a {req.experience_level} audience, apply these principles to the project "
        "specification and verify the latest code requirements before execution."
    )
    return KnowledgeResult(
        topic=topic,  # type: ignore[arg-type]
        answer=answer,
        key_points=entry["key_points"],
        practical_tips=entry["tips"],
        references=[KnowledgeReference(title=title, source=source) for title, source in entry["references"]],
        related_topics=related,
        confidence=round(0.74 if matches else 0.55, 2),
        disclaimer=DISCLAIMER_KNOWLEDGE,
    )


def demo_assistant(req: AssistantRequest) -> AssistantResult:
    text = req.message.lower()
    ctx = req.project_context
    stage = ctx.stage.replace("_", " ")
    place = ctx.location or "the project site"
    matches = find_knowledge(req.message, limit=1)
    entry = matches[0] if matches else None

    intents = {
        "safety": ["safety", "ppe", "hazard", "accident", "helmet", "harness", "scaffold"],
        "delay": ["delay", "schedule", "late", "timeline", "duration", "critical path"],
        "cost": ["cost", "budget", "estimate", "rate", "boq", "variation"],
        "quality": ["quality", "crack", "test", "inspection", "defect", "leak"],
        "procurement": ["material", "procure", "vendor", "delivery", "cement", "steel"],
        "concrete": ["concrete", "curing", "pour", "slump", "mix"],
        "documentation": ["document", "drawing", "rfi", "approval", "checklist", "report"],
        "weather": ["rain", "weather", "heat", "wind", "monsoon"],
    }
    intent = "general"
    for key, keywords in intents.items():
        if any(keyword in text for keyword in keywords):
            intent = key
            break

    answers = {
        "safety": (
            f"For the {stage} stage at {place}, treat safety as a control-verification task. "
            "Walk the work front, confirm edge protection and PPE, and close out open actions before the next shift. "
            + (entry["summary"] if entry else "Focus first on falls, electrical exposure, and housekeeping.")
        ),
        "delay": (
            f"To recover schedule at the {stage} stage, first quantify the delay against the baseline and identify "
            "whether it sits on the critical path. Resequence non-critical work, add resources only where the work front "
            "can absorb them, and record any client or approval delay as an extension-of-time event."
        ),
        "cost": (
            f"Control cost at {place} by reconciling committed spend against the approved BOQ, separating approved "
            "variations from the base budget, and reviewing the contingency burn weekly. Obtain competitive quotations "
            "before releasing major packages."
        ),
        "quality": (
            f"Raise a quality observation for the {stage} stage, photograph the defect with a scale reference, and "
            "assign a corrective action with a due date. For cracks or leaks, confirm the cause before covering the work."
        ),
        "procurement": (
            f"At the {stage} stage, release procurement against the look-ahead schedule rather than the master schedule. "
            "Confirm vendor capacity, inspection requirements, and storage arrangements before delivery."
        ),
        "concrete": (
            f"Before the next pour at {place}, confirm reinforcement cover, formwork tightness, and the approved mix. "
            "Plan curing immediately after finishing and retain cube samples for 7- and 28-day testing."
        ),
        "documentation": (
            "Maintain a single document register with revision status, approval dates, and distribution. Log every "
            "RFI with a due date and link it to the affected drawing and schedule activity."
        ),
        "weather": (
            f"Check the local forecast before opening work fronts at {place}. Protect excavation, fresh concrete, and "
            "electrical installations; move finishing work under cover during rain."
        ),
        "general": (
            f"For the {stage} stage at {place}, convert the request into a verifiable next action: define the owner, "
            "the acceptance criteria, and the evidence needed to close it. Review the action in the next daily "
            "coordination meeting. " + (entry["summary"] if entry else "Break the problem into scope, sequence, cost, and safety impacts.")
        ),
    }

    action_map = {
        "safety": ["Issue the observation to the area supervisor today.", "Verify corrective action at the next shift briefing."],
        "delay": ["Update the schedule and mark the critical path.", "Assign owners to recovery actions with daily tracking."],
        "cost": ["Reconcile the latest committed cost report.", "Escalate any unapproved variation above the threshold."],
        "quality": ["Photograph the defect with a scale reference.", "Raise a non-conformance and assign a closure date."],
        "procurement": ["Confirm delivery dates with the top three material vendors.", "Inspect storage and curing arrangements."],
        "concrete": ["Check cover and formwork before the pour.", "Set up curing and cube sampling."],
        "documentation": ["Update the drawing register and RFI log.", "Distribute the latest approved revision."],
        "weather": ["Review the 48-hour forecast with the planning team.", "Cover and secure exposed materials."],
        "general": ["Define the owner and due date for the next action.", "Record the decision in the daily site report."],
    }
    actions = list(action_map.get(intent, action_map["general"]))
    actions.append(f"Review the {stage} work front with the site team at the next coordination meeting.")

    safety_alerts = [
        "Confirm PPE use and edge protection before allowing work to proceed.",
        "Keep access and egress routes clear for the full shift.",
    ]
    if intent == "safety":
        safety_alerts.insert(0, "Stop work immediately if a fall, electrical, or excavation hazard is uncontrolled.")

    followups = [
        "Do you want a checklist for this activity?",
        "Should I map this to the project schedule?",
        "Do you need a material or cost estimate?",
    ]
    references = [f"{title} — {source}" for title, source in entry["references"]] if entry else []
    return AssistantResult(
        answer=answers[intent],
        action_items=actions,
        safety_alerts=safety_alerts,
        follow_up_questions=followups,
        references=references,
        confidence=0.76 if entry else 0.68,
        disclaimer=(
            "Demo assistant output for demonstration. Verify decisions against approved drawings, "
            "contracts, and applicable safety regulations."
        ),
    )


# ---------------------------------------------------------------------------
# Weather
# ---------------------------------------------------------------------------

WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    71: "Slight snow",
    73: "Moderate snow",
    75: "Heavy snow",
    80: "Rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    95: "Thunderstorm",
    96: "Thunderstorm with hail",
    99: "Severe thunderstorm with hail",
}


def weather_condition(code: int) -> str:
    return WEATHER_CODES.get(code, "Mixed conditions")


def demo_weather(query: str, latitude: float | None = None, longitude: float | None = None) -> WeatherResult:
    seed = _rng(query, latitude, longitude, date.today().isoformat())
    today = date.today()
    month = today.month
    base_temp = 29 + (5 if month in {4, 5, 6} else -4 if month in {12, 1} else 0) + seed.uniform(-2, 2)
    location_name = _title_city(query) if query else f"{latitude:.2f}, {longitude:.2f}"
    lat = latitude if latitude is not None else 19.076 + seed.uniform(-4, 4)
    lon = longitude if longitude is not None else 72.877 + seed.uniform(-4, 4)
    forecast: list[ForecastDay] = []
    for offset in range(7):
        day = today + timedelta(days=offset)
        rain_chance = seed.randint(5, 78)
        rain = rain_chance > 55
        code = seed.choice([0, 1, 2, 3, 61, 63, 80, 95]) if rain else seed.choice([0, 1, 2, 3])
        max_temp = base_temp + seed.uniform(-1, 4)
        forecast.append(
            ForecastDay(
                date=day,
                min_c=round(max_temp - seed.uniform(5, 9), 1),
                max_c=round(max_temp, 1),
                precipitation_probability_pct=rain_chance,
                precipitation_mm=round(seed.uniform(1, 22), 1) if rain else 0.0,
                wind_max_kmh=round(seed.uniform(6, 34), 1),
                condition=weather_condition(code),
            )
        )
    first = forecast[0]
    current = CurrentWeather(
        temperature_c=round(first.max_c - 1.5, 1),
        feels_like_c=round(first.max_c + (1.5 if first.precipitation_mm == 0 else 2.5), 1),
        humidity_pct=seed.randint(48, 92),
        wind_speed_kmh=round(first.wind_max_kmh * 0.6, 1),
        precipitation_mm=first.precipitation_mm,
        weather_code=0 if first.precipitation_mm == 0 else 61,
        condition=first.condition,
        is_day=True,
    )
    advisories: list[WeatherAdvisory] = []
    if first.precipitation_probability_pct >= 55:
        advisories.append(WeatherAdvisory(severity="high", activity="Concrete placement", advice="Rain is likely. Postpone exposed pours or provide full weather protection and monitor surface damage."))
        advisories.append(WeatherAdvisory(severity="medium", activity="Excavation", advice="Inspect slopes and shoring before entry; keep pumps and edge drainage ready."))
    if first.max_c >= 36:
        advisories.append(WeatherAdvisory(severity="high", activity="Concrete and rebar work", advice="High heat increases evaporation and heat stress. Schedule work earlier, provide shade and fluids, and cure promptly."))
    if first.wind_max_kmh >= 28:
        advisories.append(WeatherAdvisory(severity="high", activity="Lifting operations", advice="Wind speed may exceed safe lifting limits. Suspend crane lifts above the manufacturer threshold."))
    if not advisories:
        advisories.append(WeatherAdvisory(severity="low", activity="General site work", advice="Conditions are broadly workable. Maintain normal safety and curing controls."))
    advisories.append(WeatherAdvisory(severity="low", activity="Daily planning", advice="Review the forecast again before the next shift and brief the crew on changing conditions."))

    windows = []
    for day in forecast[:5]:
        if day.precipitation_probability_pct >= 65:
            suitability, reason = "poor", "High rain probability; prioritise covered work."
        elif day.max_c >= 37:
            suitability, reason = "caution", "Heat stress risk; use early-morning shifts."
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

    summary = (
        f"{location_name} is currently {current.condition.lower()} at {current.temperature_c:.0f}°C "
        f"with {current.humidity_pct}% humidity. Over the next 7 days, expect highs around "
        f"{min(day.max_c for day in forecast):.0f}-{max(day.max_c for day in forecast):.0f}°C; "
        f"the highest rain probability is {max(day.precipitation_probability_pct for day in forecast)}%."
    )
    return WeatherResult(
        location=WeatherLocation(
            name=location_name,
            region=None,
            country=None,
            latitude=round(lat, 4),
            longitude=round(lon, 4),
            timezone="Asia/Kolkata",
        ),
        current=current,
        forecast=forecast,
        advisories=advisories,
        work_windows=windows,
        summary=summary,
        data_source="demo",
        disclaimer=(
            "Demo weather data for interface preview only. Use an official weather service for "
            "operational go/no-go decisions."
        ),
    )
