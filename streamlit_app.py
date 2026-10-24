"""ConstructIQ — Streamlit deployment (demo mode, no backend required)."""
from __future__ import annotations

import hashlib
import math
import random
from datetime import date, timedelta
from typing import Any

import streamlit as st

st.set_page_config(
    page_title="ConstructIQ — Construction Intelligence",
    page_icon="🏗️",
    layout="wide",
)

# ---------------------------------------------------------------------------
# Deterministic offline engine (same logic as backend demo.py)
# ---------------------------------------------------------------------------

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
    "mumbai": 1.35, "delhi": 1.20, "new delhi": 1.20, "bengaluru": 1.25, "bangalore": 1.25,
    "hyderabad": 1.15, "chennai": 1.12, "pune": 1.15, "kolkata": 1.00, "ahmedabad": 0.95,
    "jaipur": 0.90, "lucknow": 0.88, "noida": 1.10, "gurugram": 1.20, "gurgaon": 1.20,
    "chandigarh": 1.00, "kochi": 0.98, "indore": 0.88, "surat": 0.92, "nagpur": 0.86,
    "bhopal": 0.85, "patna": 0.82, "coimbatore": 0.90,
}

VALUATION_RATES = {
    "mumbai": 24000, "delhi": 15000, "new delhi": 15000, "bengaluru": 12000, "bangalore": 12000,
    "hyderabad": 9000, "chennai": 9500, "pune": 10000, "kolkata": 7500, "ahmedabad": 6500,
    "jaipur": 5500, "lucknow": 5000, "noida": 8500, "gurugram": 9500, "gurgaon": 9500,
    "chandigarh": 6000, "kochi": 6500, "indore": 5000, "surat": 5200, "nagpur": 4800,
    "bhopal": 4600, "patna": 4500, "coimbatore": 5500,
}


def _rng(*parts: object) -> random.Random:
    raw = "|".join(str(part) for part in parts).encode("utf-8")
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

HAZARD_LIBRARY = {
    "fall": {"title": "Fall from height / unprotected edge",
             "description": "Workers are exposed near an unguarded slab edge or opening with no continuous guardrail or personal fall-arrest system.",
             "action": "Erect double-rail guardrails and toe boards, cover openings with load-rated covers, and enforce full-body harness use with anchor points.",
             "ppe": ["Full-body harness", "Safety helmet", "Safety boots"]},
    "ppe": {"title": "PPE non-compliance",
            "description": "One or more workers appear to be missing task-critical personal protective equipment for the activity being performed.",
            "action": "Stop the task, issue the missing PPE, brief the crew, and record the violation in the daily safety register.",
            "ppe": ["Safety helmet", "High-visibility vest", "Safety boots"]},
    "electrical": {"title": "Exposed temporary electrical hazard",
                   "description": "Temporary cables, distribution boards, or connections show signs of poor guarding, damage, or contact with water.",
                   "action": "Isolate the circuit, use RCD-protected distribution boards, route cables overhead, and have a licensed electrician inspect the installation.",
                   "ppe": ["Electrical gloves", "Safety boots", "Arc-rated clothing"]},
    "housekeeping": {"title": "Poor housekeeping and trip hazards",
                     "description": "Loose materials, debris, and stored items are obstructing access routes and emergency exits on the working level.",
                     "action": "Clear access routes, designate material storage zones, and schedule end-of-shift housekeeping with assigned accountability.",
                     "ppe": ["Safety boots", "Gloves"]},
    "scaffolding": {"title": "Incomplete or untagged scaffolding",
                    "description": "Scaffold sections lack complete platforms, guardrails, base plates, or a current inspection tag.",
                    "action": "Tag and isolate the scaffold, complete missing components, and release it only after a competent person's inspection.",
                    "ppe": ["Full-body harness", "Safety helmet", "Safety boots"]},
    "fire": {"title": "Hot-work and fire risk",
             "description": "Welding, grinding, or other hot work is occurring near combustible material without adequate fire watch controls.",
             "action": "Issue a hot-work permit, remove combustibles, provide fire extinguishers, and maintain a trained fire watch for 60 minutes after work.",
             "ppe": ["Welding shield", "Flame-resistant clothing", "Safety boots"]},
    "lifting": {"title": "Uncontrolled lifting operation",
                "description": "A lifting zone is active with personnel, rigging, or load path conditions that are not fully controlled.",
                "action": "Establish an exclusion zone, verify rigging and lift plans, use a banksman, and stop the lift in high wind or poor visibility.",
                "ppe": ["Safety helmet", "High-visibility vest", "Safety boots"]},
    "excavation": {"title": "Excavation instability and edge protection",
                   "description": "The excavation shows inadequate shoring, sloped banks, edge barriers, or safe access for the soil conditions.",
                   "action": "Reassess soil conditions, install shoring or safe batter, barricade the perimeter, and provide a secured ladder within 7.5 m of the work face.",
                   "ppe": ["Safety helmet", "Safety boots", "High-visibility vest"]},
    "chemical": {"title": "Chemical and dust exposure",
                 "description": "Workers may be exposed to silica dust, solvent vapours, or cementitious materials without suitable respiratory and skin protection.",
                 "action": "Use dust suppression or extraction, provide correct respirators and gloves, and make safety data sheets available at the point of use.",
                 "ppe": ["Respirator", "Safety goggles", "Chemical gloves"]},
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
    "North facade, Level 2", "Main access ramp", "Material storage yard", "Level 1 slab edge",
    "Temporary power distribution area", "Scaffold access stair", "Excavation perimeter",
    "Lifting zone near tower crane", "Ground floor work front",
]

SEVERITY_WEIGHT = {"low": 6, "medium": 13, "high": 22, "critical": 32}
LIKELIHOOD_WEIGHT = {"rare": 0, "unlikely": 1, "possible": 3, "likely": 5, "almost_certain": 7}


def demo_safety(description: str, project_type: str, location: str, activity: str):
    text = description.lower()
    rng = _rng(description, project_type, location, activity)
    categories = []
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
    categories.append("ppe")
    categories = list(dict.fromkeys(categories))[:6]
    if len(categories) < 3:
        for extra in ["ppe", "housekeeping", "fall"]:
            if extra not in categories:
                categories.append(extra)
            if len(categories) >= 3:
                break

    hazards = []
    urgent = any(word in text for word in ["critical", "severe", "urgent", "danger", "collapse"])
    for index, category in enumerate(categories, start=1):
        item = HAZARD_LIBRARY.get(category, HAZARD_LIBRARY["housekeeping"])
        severity = rng.choices(["medium", "high", "critical"], weights=[55, 33, 12] if not urgent else [30, 42, 28], k=1)[0]
        if category == "ppe":
            severity = "high" if severity != "critical" else "critical"
        likelihood = rng.choices(["possible", "likely", "almost_certain"], weights=[38, 42, 20], k=1)[0]
        hazards.append({
            "id": f"H-{index:02d}",
            "title": item["title"],
            "category": category,
            "severity": severity,
            "likelihood": likelihood,
            "location": rng.choice(HAZARD_LOCATIONS),
            "description": item["description"],
            "corrective_action": item["action"],
            "ppe_required": item["ppe"],
        })

    observed = ["Safety helmets", "High-visibility vests", "Safety boots"]
    missing = rng.sample(["Safety helmets", "High-visibility vests", "Eye protection"], k=2) if "ppe" in categories else (["Eye protection"] if rng.random() < 0.35 else [])
    observed = [item for item in observed if item not in missing]
    ppe_score = _clamp(100 - len(missing) * 24 - 8, 20, 100)
    overall = "compliant" if ppe_score >= 90 else "partial" if ppe_score >= 55 else "non_compliant"

    base = 8 + sum(SEVERITY_WEIGHT[h["severity"]] * 0.55 + LIKELIHOOD_WEIGHT[h["likelihood"]] for h in hazards)
    risk_score = int(_clamp(base, 15, 96))
    risk_level = "low" if risk_score < 30 else "moderate" if risk_score < 55 else "high" if risk_score < 80 else "critical"

    immediate = [h["corrective_action"] for h in sorted(hazards, key=lambda x: x["severity"], reverse=True)[:3]]
    immediate.append("Hold a toolbox talk covering the identified hazards before work resumes.")

    summary = (
        f"Visual and contextual review of the {activity.lower()} activity at {location} "
        f"identified {len(hazards)} hazards, including {hazards[0]['title'].lower()}. "
        f"The combined risk is {risk_level}; address the critical controls before the next work shift."
    )
    quality = "good"
    confidence = 0.72

    return {
        "risk_score": risk_score, "risk_level": risk_level, "summary": summary,
        "hazards": hazards, "ppe": {"overall": overall, "observed": observed, "missing": missing, "score": int(ppe_score)},
        "immediate_actions": immediate,
        "positive_observations": ["Access routes were generally identifiable and free of major obstruction.", "Materials are mostly stored within designated zones."],
        "confidence": confidence, "image_quality": quality, "disclaimer": DISCLAIMER_SAFETY,
    }


# ---------------------------------------------------------------------------
# Crack
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

ELEMENT_KEYWORDS = {"beam": "Beam", "column": "Column", "slab": "Slab", "wall": "Wall", "plaster": "Plaster / wall finish", "foundation": "Foundation", "ceiling": "Ceiling"}
WIDTH_BY_TYPE = {"hairline": (0.1, 0.4), "shrinkage": (0.2, 1.2), "thermal": (0.4, 2.2), "settlement": (1.0, 6.0),
                 "structural": (1.5, 10.0), "shear": (1.0, 5.0), "flexural": (0.5, 4.0), "corrosion": (0.2, 3.0), "unknown": (0.2, 2.0)}


def demo_crack(description: str, structure_type: str, brightness: float, edge_density: float):
    text = description.lower()
    rng = _rng(description, structure_type, brightness, edge_density)
    requested_type = None
    for crack_type, keywords in TYPE_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            requested_type = crack_type
            break

    detected = edge_density > 0.035 or requested_type is not None
    image_quality = "good" if brightness > 60 and edge_density > 0.03 else "fair" if brightness > 35 else "poor"

    if not detected:
        return {
            "detected": False, "crack_type": "unknown", "severity": "minor", "severity_score": 12,
            "summary": "No clear crack pattern was identified in the uploaded frame.",
            "affected_element": structure_type, "probable_causes": ["No visible defect in this view", "Insufficient lighting or resolution"],
            "measurements": {"estimated_length_cm": None, "estimated_width_mm": None, "confidence": 0.55},
            "recommended_actions": ["Take close-up photographs in good daylight, perpendicular to the surface.", "Include a ruler or known reference object in the frame for scale."],
            "urgency": "monitor", "requires_professional_inspection": False, "confidence": 0.58,
            "image_quality": image_quality, "disclaimer": DISCLAIMER_CRACK,
        }

    crack_type = requested_type or rng.choices(["shrinkage", "thermal", "settlement", "hairline", "corrosion", "structural"], weights=[26, 20, 18, 16, 12, 8], k=1)[0]
    width_low, width_high = WIDTH_BY_TYPE[crack_type]
    width_mm = round(rng.uniform(width_low, width_high), 2)
    length_cm = round(rng.uniform(25, 280), 1)
    severity_score = int(_clamp(22 + edge_density * 260 + width_mm * 5 + (12 if requested_type else 0), 18, 96))
    severity = "minor" if severity_score < 32 else "moderate" if severity_score < 56 else "severe" if severity_score < 80 else "critical"
    if crack_type in {"structural", "shear"}:
        severity = "severe" if severity in {"minor", "moderate"} else "critical"

    affected = structure_type
    for keyword, element in ELEMENT_KEYWORDS.items():
        if keyword in text:
            affected = element
            break
    if affected == "auto":
        affected = rng.choice(["Wall", "Slab", "Beam", "Column", "Plaster / wall finish"])

    urgency = {"minor": "monitor", "moderate": "schedule_repair", "severe": "urgent", "critical": "emergency"}[severity]
    requires_inspection = severity in {"severe", "critical"} or crack_type in {"structural", "shear", "settlement", "corrosion"}

    summary = (
        f"A {crack_type} crack pattern is visible on the {affected.lower()}, with an estimated "
        f"width of {width_mm} mm and length of {length_cm} cm. The condition is classified as "
        f"{severity}; {'restrict access and arrange an urgent structural review.' if requires_inspection else 'monitor movement and repair after confirming the cause.'}"
    )
    return {
        "detected": True, "crack_type": crack_type, "severity": severity, "severity_score": severity_score,
        "summary": summary, "affected_element": affected, "probable_causes": CRACK_CAUSES[crack_type],
        "measurements": {"estimated_length_cm": length_cm, "estimated_width_mm": width_mm, "confidence": round(_clamp(0.6 + edge_density, 0.6, 0.88), 2)},
        "recommended_actions": CRACK_ACTIONS[severity], "urgency": urgency,
        "requires_professional_inspection": requires_inspection, "confidence": round(_clamp(0.62 + edge_density * 1.4, 0.62, 0.9), 2),
        "image_quality": image_quality, "disclaimer": DISCLAIMER_CRACK,
    }


# ---------------------------------------------------------------------------
# Planning
# ---------------------------------------------------------------------------

BASE_RATES = {"residential": 2200, "commercial": 3000, "industrial": 1900, "infrastructure": 2600, "renovation": 1500}
QUALITY_MULT = {"economy": 0.75, "standard": 1.0, "premium": 1.35, "luxury": 1.8}


def _schedule_tasks(area: float, floors: int, start: date):
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
    durations = {tid: max(3, round(d * scale)) for tid, _, _, d, _ in definitions}
    ends, starts = {}, {}
    tasks = []
    for tid, name, phase, _, deps in definitions:
        sd = 1 if not deps else max(ends[d] for d in deps) + 1
        ed = sd + durations[tid] - 1
        starts[tid] = sd
        ends[tid] = ed
        tasks.append({"id": tid, "name": name, "phase": phase, "duration_days": durations[tid],
                      "start_day": sd, "end_day": ed, "start_date": start + timedelta(days=sd - 1),
                      "end_date": start + timedelta(days=ed - 1), "depends_on": deps})
    best = {}
    for tid, _, _, _, deps in definitions:
        if not deps:
            best[tid] = (durations[tid], [tid])
        else:
            length, path = max((best[d] for d in deps), key=lambda item: item[0])
            best[tid] = (length + durations[tid], path + [tid])
    critical_path = max(best.values(), key=lambda item: item[0])[1]
    total = max(ends.values())
    return {"total_duration_days": total, "start_date": start, "end_date": start + timedelta(days=total - 1),
            "tasks": tasks, "critical_path": critical_path}


def demo_planning(project_type: str, area: float, floors: int, location: str, quality: str, start_date: date, currency: str):
    rng = _rng(location, project_type, area, floors)
    rate = BASE_RATES[project_type] * QUALITY_MULT[quality] * _city_factor(location) * rng.uniform(0.97, 1.03)
    total_inr = area * rate
    parts = {"structural": total_inr * 0.32, "finishing": total_inr * 0.27, "mep": total_inr * 0.18,
             "labor": total_inr * 0.17, "permits": total_inr * 0.02}
    parts["contingency"] = total_inr * 0.04
    total_inr = sum(parts.values())
    factor = 1.0 if currency == "INR" else 1.0 / 83.0
    convert = lambda v: round(v * factor, 2) if currency == "USD" else round(v, 2)

    materials_raw = [
        ("OPC 53 grade cement", area * 0.40, "bags", 420, "50 kg bags"),
        ("TMT reinforcement Fe500D", area * 4.2, "kg", 72, "Structural steel"),
        ("River sand (zone II)", area * 1.8, "cft", 52, "Verify local availability"),
        ("Coarse aggregate 20 mm", area * 1.35, "cft", 38, "Crushed stone aggregate"),
        ("AAC blocks", round(area * 8), "nos", 48, "600 x 200 x 100 mm nominal blocks"),
        ("Vitrified floor tiles", area * 0.95, "sqft", 68 * QUALITY_MULT[quality], "Includes 5% wastage"),
        ("Emulsion paint", area * 0.12, "litre", 320 * QUALITY_MULT[quality], "Two coats plus primer"),
        ("Waterproofing membrane", area * 0.35, "sqft", 55, "Terrace, toilets and wet areas"),
        ("Flush doors", max(2, round(area / 450)), "nos", 8500 * QUALITY_MULT[quality], "Includes frames"),
        ("UPVC windows", area * 0.08, "sqft", 700, "Double-glazed where specified"),
        ("Electrical points", max(8, round(area / 120)), "nos", 1200, "Switches, sockets and conduits"),
    ]
    materials = [{"name": n, "quantity": round(q, 2), "unit": u, "unit_cost": convert(uc),
                  "estimated_cost": convert(q * uc), "notes": nt} for n, q, u, uc, nt in materials_raw]

    schedule = _schedule_tasks(area, floors, start_date)
    concept = {
        "style": {"residential": "Warm contemporary", "commercial": "Biophilic corporate modern",
                  "industrial": "High-performance industrial", "infrastructure": "Civic modern",
                  "renovation": "Adaptive-reuse contemporary"}[project_type],
        "description": f"A {project_type} development of {area:,.0f} sq ft across {floors} floor(s) in {_title_city(location)}.",
        "key_features": ["Clear circulation", "Daylight", "Maintainability", "Restrained material palette"],
        "color_palette": [{"name": "Ivory", "hex": "#F4F1EA"}, {"name": "Concrete Grey", "hex": "#9AA0A6"},
                          {"name": "Teak", "hex": "#9B6A3F"}, {"name": "Deep Teal", "hex": "#0F766E"}],
        "sustainability_notes": ["Orient glazing to manage solar heat gain.", "Use AAC blocks and fly-ash-blended cement.",
                                 "Provide rainwater harvesting and low-flow fixtures."],
    }
    footprint = area / floors
    aspect = 1.6 if project_type in {"commercial", "industrial"} else 1.35
    width = round(math.sqrt(footprint * aspect), 1)
    length = round(footprint / width, 1)
    floor_plan = {"total_width_ft": width, "total_length_ft": length, "typical_floor_area_sqft": round(footprint, 1),
                  "rooms": [{"name": "Living Room", "room_type": "living", "x_ft": 0, "y_ft": 0, "width_ft": width, "length_ft": length, "area_sqft": round(footprint, 1)}],
                  "notes": ["Conceptual typical-floor layout.", "Not a construction drawing."]}

    month = start_date.month
    risks = ["Material rates are market-sensitive; obtain three current vendor quotations before procurement.",
             f"Sequence and handover dates assume {schedule['total_duration_days']} days and favourable weather."]
    if month in {5, 6}:
        risks.append("Peak summer may affect concrete placement; plan early-morning pours.")
    elif month in {7, 8, 9}:
        risks.append("Monsoon conditions may disrupt excavation; provide drainage and covered storage.")
    if floors > 3:
        risks.append("Tall structure: coordinate lift core, scaffolding, and wind-sensitive lifting operations.")

    return {
        "project_type": project_type, "built_up_area_sqft": area, "floors": floors, "location": _title_city(location),
        "quality": quality, "currency": currency,
        "cost": {"structural": convert(parts["structural"]), "finishing": convert(parts["finishing"]),
                 "mep": convert(parts["mep"]), "labor": convert(parts["labor"]), "permits": convert(parts["permits"]),
                 "contingency": convert(parts["contingency"]), "total": convert(total_inr),
                 "cost_per_sqft": convert(total_inr / area)},
        "materials": materials, "schedule": schedule, "concept": concept, "floor_plan": floor_plan,
        "assumptions": ["Built-up area includes all floors.", f"Rates are indicative {currency} values for {_title_city(location)}.",
                        "Foundation is assumed conventional on competent soil."],
        "risks": risks,
        "recommendations": ["Freeze architectural layout before issuing BOQ.", "Use a weekly look-ahead schedule.",
                            "Set a 4% contingency and review monthly."],
    }


# ---------------------------------------------------------------------------
# Valuation
# ---------------------------------------------------------------------------

TYPE_MULT = {"apartment": 1.0, "villa": 1.25, "plot": 0.80, "commercial": 1.30, "office": 1.25, "retail": 1.35}
CONDITION_MULT = {"poor": 0.80, "fair": 0.91, "good": 1.0, "excellent": 1.08}


def demo_valuation(property_type: str, city: str, locality: str | None, area_sqft: float, age_years: int,
                   bedrooms: int, quality: str, condition: str, amenities: list[str]):
    city_key = city.strip().lower()
    base_rate = VALUATION_RATES.get(city_key, 5500)
    quality_mult = {"basic": 0.85, "standard": 1.0, "premium": 1.25, "luxury": 1.5}[quality]
    age_dep = max(0.55, 1 - age_years * 0.012)
    amenity_bonus = min(0.10, len(amenities) * 0.015)
    rate = base_rate * TYPE_MULT[property_type] * quality_mult * CONDITION_MULT[condition] * age_dep * (1 + amenity_bonus)
    estimated = int(round(area_sqft * rate / 1000) * 1000)
    spread = 0.10 if locality else 0.13
    low = int(round(estimated * (1 - spread) / 1000) * 1000)
    high = int(round(estimated * (1 + spread) / 1000) * 1000)
    price_psf = int(round(estimated / area_sqft))
    confidence = round(_clamp(0.86 - (0.06 if age_years > 20 else 0) - (0.05 if not locality else 0), 0.65, 0.9), 2)
    outlook = "growing" if city_key in {"bengaluru", "bangalore", "hyderabad", "pune", "gurugram", "gurgaon", "noida"} else "stable"

    comps = []
    rng = _rng(city, locality, area_sqft, property_type)
    for index, delta in enumerate([-0.18, -0.06, 0.12], start=1):
        comp_area = round(area_sqft * (1 + delta), 0)
        comp_rate = int(round(rate * rng.uniform(0.92, 1.08)))
        comps.append({"description": f"Comparable {index}", "area_sqft": comp_area, "price_per_sqft": comp_rate, "estimated_value": comp_area * comp_rate})

    factors = [
        {"factor": "Location", "impact": "positive" if base_rate >= 9000 else "neutral", "description": f"{_title_city(city)} base rate is ₹{base_rate:,}/sq ft."},
        {"factor": "Property age", "impact": "negative" if age_years > 10 else "positive", "description": f"{age_years}-year-old asset."},
        {"factor": "Quality", "impact": "positive" if quality in {"premium", "luxury"} else "neutral", "description": f"{quality.title()} specification."},
        {"factor": "Condition", "impact": "positive" if condition == "excellent" else "negative" if condition == "poor" else "neutral", "description": f"Property is in {condition} condition."},
    ]
    if amenities:
        factors.append({"factor": "Amenities", "impact": "positive", "description": f"{len(amenities)} amenities add ~{round(amenity_bonus * 100, 1)}% premium."})

    summary = (f"The estimated market value of the {area_sqft:,.0f} sq ft {property_type} in "
               f"{locality or _title_city(city)} is approximately ₹{estimated:,.0f}, with a plausible range of ₹{low:,.0f} to ₹{high:,.0f}.")
    assumptions = ["Clear and marketable title with valid approvals.", "Built-up area verified.",
                   "No structural defects or litigation affect the asset.",
                   "Indicative rates based on city-level benchmarks, not physical inspection."]
    return {
        "property_type": property_type, "city": _title_city(city), "locality": locality, "area_sqft": area_sqft,
        "currency": "INR", "estimated_value": estimated, "value_range_low": low, "value_range_high": high,
        "price_per_sqft": price_psf, "confidence": confidence, "market_outlook": outlook, "summary": summary,
        "comparable_sales": comps, "valuation_factors": factors,
        "recommendations": ["Obtain formal valuation from a registered valuer.", "Verify title and encumbrance certificate.",
                            "Compare at least three recent registered transactions."],
        "assumptions": assumptions, "disclaimer": DISCLAIMER_VALUATION,
    }


# ---------------------------------------------------------------------------
# Knowledge
# ---------------------------------------------------------------------------

KNOWLEDGE_BASE = [
    {"slug": "concrete-curing", "topic": "concrete", "title": "Concrete curing and early-age protection",
     "keywords": ["curing", "concrete", "ponding", "strength", "hydration", "hot weather"],
     "summary": "Concrete must retain moisture during early hydration. Moist-cure structural concrete for at least 7 days.",
     "key_points": ["Start curing within 12-24 hours.", "Keep surfaces continuously moist.", "Test cubes at 7 and 28 days."],
     "tips": ["Schedule pours early in hot weather.", "Do not finish surfaces while bleed water is present."],
     "references": [("IS 456:2000", "Bureau of Indian Standards")], "related": ["Concrete testing", "Hot-weather concreting"]},
    {"slug": "rebar", "topic": "steel", "title": "Reinforcement cover, laps, and corrosion",
     "keywords": ["rebar", "steel", "cover", "lap", "reinforcement", "corrosion"],
     "summary": "Reinforcement performance depends on correct grade, spacing, cover, and laps.",
     "key_points": ["Verify bar diameter, grade, and spacing.", "Maintain cover using certified spacers.", "Use specified lap length."],
     "tips": ["Photograph reinforcement before concrete placement.", "Store rebar clear of the ground."],
     "references": [("IS 456:2000", "Bureau of Indian Standards")], "related": ["Structural inspection", "Quality control"]},
    {"slug": "scaffolding", "topic": "safety", "title": "Scaffolding safety and inspection",
     "keywords": ["scaffold", "scaffolding", "platform", "guardrail", "harness", "fall"],
     "summary": "Scaffolds must be designed for the intended load and inspected before use.",
     "key_points": ["Provide base plates, sole boards, bracing, and adequate ties.", "Use guardrails and complete working platforms."],
     "tips": ["Inspect after rain or high wind.", "Keep scaffold access clear."],
     "references": [("IS 3696", "Bureau of Indian Standards")], "related": ["Fall protection", "Working at height"]},
    {"slug": "waterproofing", "topic": "waterproofing", "title": "Waterproofing: substrate, membrane, and testing",
     "keywords": ["waterproofing", "leak", "membrane", "terrace", "toilet", "damp"],
     "summary": "Successful waterproofing depends on a sound substrate and continuous membrane application.",
     "key_points": ["Cure and dry the substrate.", "Use fillets at wall-floor junctions.", "Conduct a 24-48 hour ponding test."],
     "tips": ["Protect the membrane from punctures.", "Slope terraces to drains before applying membrane."],
     "references": [("IS 3067", "Bureau of Indian Standards")], "related": ["Wet-area detailing", "Leak investigation"]},
]


def find_knowledge(question: str, topic: str = "general", limit: int = 2):
    text = question.lower()
    scored = []
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


def demo_knowledge(question: str, topic: str, experience_level: str):
    matches = find_knowledge(question, topic, limit=2)
    entry = matches[0] if matches else KNOWLEDGE_BASE[0]
    answer = entry["summary"]
    if len(matches) > 1:
        answer += " " + matches[1]["summary"]
    answer += f" For a {experience_level} audience, verify the latest code requirements before execution."
    return {
        "topic": topic if topic != "general" else entry["topic"], "answer": answer,
        "key_points": entry["key_points"], "practical_tips": entry["tips"],
        "references": [{"title": t, "source": s} for t, s in entry["references"]],
        "related_topics": entry["related"], "confidence": 0.74 if matches else 0.55,
        "disclaimer": DISCLAIMER_KNOWLEDGE,
    }


# ---------------------------------------------------------------------------
# Assistant
# ---------------------------------------------------------------------------

INTENTS = {
    "safety": ["safety", "ppe", "hazard", "accident", "helmet", "harness", "scaffold"],
    "delay": ["delay", "schedule", "late", "timeline", "duration", "critical path"],
    "cost": ["cost", "budget", "estimate", "rate", "boq", "variation"],
    "quality": ["quality", "crack", "test", "inspection", "defect", "leak"],
    "procurement": ["material", "procure", "vendor", "delivery", "cement", "steel"],
    "concrete": ["concrete", "curing", "pour", "slump", "mix"],
    "documentation": ["document", "drawing", "rfi", "approval", "checklist", "report"],
    "weather": ["rain", "weather", "heat", "wind", "monsoon"],
}

ANSWERS = {
    "safety": "Treat safety as a control-verification task. Walk the work front, confirm edge protection and PPE, and close out open actions before the next shift.",
    "delay": "Quantify the delay against the baseline and identify whether it sits on the critical path. Resequence non-critical work.",
    "cost": "Reconcile committed spend against the approved BOQ and review the contingency burn weekly.",
    "quality": "Raise a quality observation, photograph the defect with a scale reference, and assign a corrective action with a due date.",
    "procurement": "Release procurement against the look-ahead schedule. Confirm vendor capacity and storage before delivery.",
    "concrete": "Confirm reinforcement cover, formwork tightness, and the approved mix before the pour. Plan curing immediately.",
    "documentation": "Maintain a single document register with revision status and approval dates.",
    "weather": "Check the local forecast before opening work fronts. Protect excavation and fresh concrete.",
    "general": "Convert the request into a verifiable next action: define the owner, acceptance criteria, and evidence needed.",
}

ACTIONS = {
    "safety": ["Issue the observation to the area supervisor today.", "Verify corrective action at the next shift briefing."],
    "delay": ["Update the schedule and mark the critical path.", "Assign owners to recovery actions."],
    "cost": ["Reconcile the latest committed cost report.", "Escalate any unapproved variation above the threshold."],
    "quality": ["Photograph the defect with a scale reference.", "Raise a non-conformance and assign a closure date."],
    "procurement": ["Confirm delivery dates with vendors.", "Inspect storage arrangements."],
    "concrete": ["Check cover and formwork before the pour.", "Set up curing and cube sampling."],
    "documentation": ["Update the drawing register and RFI log.", "Distribute the latest approved revision."],
    "weather": ["Review the 48-hour forecast.", "Cover and secure exposed materials."],
    "general": ["Define the owner and due date for the next action.", "Record the decision in the daily site report."],
}


def demo_assistant(message: str, project_type: str, stage: str, location: str):
    text = message.lower()
    intent = "general"
    for key, keywords in INTENTS.items():
        if any(k in text for k in keywords):
            intent = key
            break
    place = location or "the project site"
    answer = f"For the {stage.replace('_', ' ')} stage at {place}, {ANSWERS[intent]}"
    action_list = list(ACTIONS.get(intent, ACTIONS["general"]))
    action_list.append(f"Review the {stage} work front with the site team at the next coordination meeting.")
    alerts = ["Confirm PPE use and edge protection before allowing work to proceed.", "Keep access and egress routes clear."]
    if intent == "safety":
        alerts.insert(0, "Stop work immediately if a fall, electrical, or excavation hazard is uncontrolled.")
    return {
        "answer": answer, "action_items": action_list, "safety_alerts": alerts,
        "follow_up_questions": ["Do you want a checklist for this activity?", "Should I map this to the project schedule?"],
        "references": [], "confidence": 0.76,
        "disclaimer": "Demo assistant output. Verify decisions against approved drawings and regulations.",
    }


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------

st.markdown(
    """
    <style>
    .main .block-container { padding-top: 1rem; max-width: 1200px; }
    .hero { background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); padding: 2rem; border-radius: 16px; color: white; margin-bottom: 1.5rem; }
    .hero h1 { margin: 0 0 0.5rem; font-size: 2rem; }
    .badge { display: inline-block; padding: 0.25rem 0.6rem; border-radius: 999px; font-size: 0.75rem; font-weight: 700; margin-right: 0.5rem; }
    .badge-demo { background: #fbbf24; color: #713f12; }
    .card { border: 1px solid #e2e8f0; border-radius: 12px; padding: 1.25rem; background: #ffffff; margin-bottom: 1rem; }
    .stButton > button { width: 100%; border-radius: 8px; font-weight: 600; }
    .risk-critical { color: #dc2626; font-weight: 700; }
    .risk-high { color: #ea580c; font-weight: 700; }
    .risk-moderate { color: #d97706; font-weight: 700; }
    .risk-low { color: #16a34a; font-weight: 700; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <h1>🏗️ ConstructIQ</h1>
        <p style="margin:0; opacity:0.9;">AI-powered multimodal construction intelligence — safety, cracks, planning, valuation, site assistant, weather, and knowledge.</p>
        <span class="badge badge-demo">Demo Mode</span>
        <span class="badge badge-demo">No API key required</span>
    </div>
    """,
    unsafe_allow_html=True,
)

st.sidebar.title("Navigation")
module = st.sidebar.radio(
    "Choose a module",
    ["Dashboard", "Site Safety", "Crack Analysis", "Project Planner", "Real Estate Valuation",
     "Site Assistant", "Weather Advisory", "Knowledge Hub"],
)

if module == "Dashboard":
    st.subheader("Intelligence Modules")
    cols = st.columns(4)
    modules = [
        ("🦺", "Site Safety", "Image-led hazard detection, PPE compliance, risk scoring."),
        ("🧱", "Crack Analysis", "Crack type, severity, measurements, inspection urgency."),
        ("📐", "Project Planner", "Cost breakdown, CPM schedule, design concept, floor plan."),
        ("💰", "Real Estate Valuation", "Indicative value range, price per sq ft, comparables."),
        ("💬", "Site Assistant", "Field-ready answers with action items and safety alerts."),
        ("🌤️", "Weather Advisory", "Live forecast translated into work windows and warnings."),
        ("📚", "Knowledge Hub", "Construction guidance with standards references."),
        ("⚙️", "Platform", "Strict JSON contracts · FastAPI + React · Streamlit demo."),
    ]
    for i, (icon, title, desc) in enumerate(modules):
        with cols[i % 4]:
            st.markdown(f"<div class='card'><div style='font-size:1.5rem'>{icon}</div><h4>{title}</h4><p style='color:#64748b;font-size:0.85rem'>{desc}</p></div>", unsafe_allow_html=True)

elif module == "Site Safety":
    st.subheader("🦺 Site Safety Monitor")
    with st.form("safety_form"):
        description = st.text_area("Observation notes", "Crew working near Level 2 slab edge. One worker not wearing helmet. Temporary cables across wet route.",
                                   height=120)
        col1, col2, col3 = st.columns(3)
        project_type = col1.selectbox("Project type", ["residential", "commercial", "industrial", "infrastructure", "renovation"])
        location = col2.text_input("Location", "North tower, Level 2")
        activity = col3.text_input("Work activity", "Slab and reinforcement work")
        submitted = st.form_submit_button("Run safety analysis")
    if submitted:
        res = demo_safety(description, project_type, location, activity)
        st.markdown(f"<div class='card'><h3>Site safety assessment</h3><p>{res['summary']}</p></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Risk score", res["risk_score"], res["risk_level"])
        c2.metric("PPE compliance", res["ppe"]["overall"].replace("_", " ").title(), f"{res['ppe']['score']}%")
        c3.metric("Confidence", f"{int(res['confidence']*100)}%", res["image_quality"])
        st.markdown("### Hazard register")
        for h in res["hazards"]:
            sev_class = f"risk-{h['severity']}"
            with st.expander(f"{h['id']} · {h['title']} · <span class='{sev_class}'>{h['severity']}</span>", unsafe_allow_html=True):
                st.write(f"**Category:** {h['category']}  |  **Likelihood:** {h['likelihood']}  |  **Location:** {h['location']}")
                st.write(f"**Description:** {h['description']}")
                st.write(f"**Corrective action:** {h['corrective_action']}")
                st.write(f"**PPE required:** {', '.join(h['ppe_required'])}")
        st.markdown("**Immediate actions:**")
        for a in res["immediate_actions"]:
            st.write(f"• {a}")
        st.info(res["disclaimer"])

elif module == "Crack Analysis":
    st.subheader("🧱 Crack Analysis")
    st.caption("Upload a close-up photograph (image analysis simulated in demo mode).")
    with st.form("crack_form"):
        description = st.text_input("Inspector notes", "Diagonal crack near beam-column joint")
        structure_type = st.selectbox("Structure element", ["auto", "wall", "beam", "column", "slab", "foundation", "ceiling", "plaster"])
        brightness = st.slider("Image brightness (simulated)", 0, 255, 120)
        edge_density = st.slider("Image edge density (simulated)", 0.0, 0.5, 0.08, 0.01)
        submitted = st.form_submit_button("Analyze crack")
    if submitted:
        res = demo_crack(description, structure_type, brightness, edge_density)
        st.markdown(f"<div class='card'><h3>{res['affected_element']}</h3><p>{res['summary']}</p></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Severity score", res["severity_score"], res["severity"])
        c2.metric("Estimated width", f"{res['measurements']['estimated_width_mm']} mm" if res['measurements']['estimated_width_mm'] else "—")
        c3.metric("Estimated length", f"{res['measurements']['estimated_length_cm']} cm" if res['measurements']['estimated_length_cm'] else "—")
        if res["requires_professional_inspection"]:
            st.error("⚠️ Professional inspection required — restrict access and consult a structural engineer.")
        st.markdown("**Probable causes:**")
        for c in res["probable_causes"]:
            st.write(f"• {c}")
        st.markdown("**Recommended actions:**")
        for a in res["recommended_actions"]:
            st.write(f"• {a}")
        st.info(res["disclaimer"])

elif module == "Project Planner":
    st.subheader("📐 Project Planner")
    with st.form("planning_form"):
        col1, col2 = st.columns(2)
        project_type = col1.selectbox("Project type", ["residential", "commercial", "industrial", "infrastructure", "renovation"])
        quality = col2.selectbox("Quality level", ["economy", "standard", "premium", "luxury"])
        col3, col4 = st.columns(2)
        area = col3.number_input("Built-up area (sq ft)", min_value=200, value=2500, step=50)
        floors = col4.number_input("Floors", min_value=1, max_value=60, value=2)
        col5, col6 = st.columns(2)
        location = col5.text_input("Location", "Pune")
        currency = col6.selectbox("Currency", ["INR", "USD"])
        start_date = st.date_input("Planned start", value=date.today())
        submitted = st.form_submit_button("Generate project plan")
    if submitted:
        res = demo_planning(project_type, area, floors, location, quality, start_date, currency)
        st.markdown(f"<div class='card'><h3>Project plan — {res['location']}</h3><p>{res['concept']['description']}</p></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Estimated cost", f"{res['currency']} {res['cost']['total']:,.0f}", f"{res['cost']['cost_per_sqft']:,.0f} / sq ft")
        c2.metric("Duration", f"{res['schedule']['total_duration_days']} days")
        c3.metric("Typical floor", f"{res['floor_plan']['typical_floor_area_sqft']:,.0f} sq ft")
        st.markdown("### Cost breakdown")
        cost = res["cost"]
        for label, key, color in [("Structural", "structural", "#f97316"), ("Finishing", "finishing", "#a78bfa"),
                                  ("MEP", "mep", "#60a5fa"), ("Labor", "labor", "#2dd4bf"),
                                  ("Permits", "permits", "#f4a62a"), ("Contingency", "contingency", "#94a3b8")]:
            st.progress(cost[key] / cost["total"] if cost["total"] else 0)
            st.caption(f"{label}: {currency} {cost[key]:,.0f} ({cost[key]/cost['total']*100:.0f}%)")
        st.markdown("### Schedule")
        for t in res["schedule"]["tasks"]:
            crit = "🔴" if t["id"] in res["schedule"]["critical_path"] else ""
            st.write(f"{crit} **{t['id']}** {t['name']} · {t['phase']} · {t['duration_days']} days · {t['start_date']} → {t['end_date']}")
        st.info("Costs, quantities, schedule, and floor layout are deterministic estimates, not quotations.")

elif module == "Real Estate Valuation":
    st.subheader("💰 Real Estate Valuation")
    with st.form("valuation_form"):
        col1, col2 = st.columns(2)
        property_type = col1.selectbox("Property type", ["apartment", "villa", "plot", "commercial", "office", "retail"])
        condition = col2.selectbox("Condition", ["poor", "fair", "good", "excellent"])
        col3, col4 = st.columns(2)
        city = col3.text_input("City", "Pune")
        locality = col4.text_input("Locality (optional)", "Baner")
        col5, col6 = st.columns(2)
        area = col5.number_input("Area (sq ft)", min_value=100, value=1200, step=10)
        age = col6.number_input("Age (years)", min_value=0, max_value=100, value=5)
        col7, col8 = st.columns(2)
        bedrooms = col7.number_input("Bedrooms", min_value=0, max_value=20, value=2)
        quality = col8.selectbox("Specification", ["basic", "standard", "premium", "luxury"])
        amenities = st.multiselect("Amenities", ["parking", "gym", "pool", "security", "power_backup", "lift", "garden", "clubhouse"],
                                   default=["parking", "lift", "security"])
        submitted = st.form_submit_button("Estimate property value")
    if submitted:
        res = demo_valuation(property_type, city, locality or None, area, age, bedrooms, quality, condition, amenities)
        st.markdown(f"<div class='card'><h2>₹{res['estimated_value']:,.0f}</h2><p>Likely range: ₹{res['value_range_low']:,.0f} – ₹{res['value_range_high']:,.0f}</p></div>", unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        c1.metric("Price per sq ft", f"₹{res['price_per_sqft']:,.0f}")
        c2.metric("Confidence", f"{int(res['confidence']*100)}%")
        c3.metric("Market outlook", res["market_outlook"].title())
        st.markdown("### Value drivers")
        for f in res["valuation_factors"]:
            st.write(f"• **{f['factor']}** ({f['impact']}): {f['description']}")
        st.info(res["disclaimer"])

elif module == "Site Assistant":
    st.subheader("💬 Site Assistant")
    col1, col2, col3 = st.columns(3)
    project_type = col1.selectbox("Project type", ["residential", "commercial", "industrial", "infrastructure", "renovation"])
    stage = col2.selectbox("Current stage", ["planning", "procurement", "foundation", "structure", "finishing", "handover", "maintenance"])
    location = col3.text_input("Site location", "Pune")
    message = st.text_area("Ask the site assistant", "How do I recover a two-week schedule delay?", height=100)
    if st.button("Send"):
        res = demo_assistant(message, project_type, stage, location)
        st.markdown(f"<div class='card'><p>{res['answer']}</p></div>", unsafe_allow_html=True)
        if res["action_items"]:
            st.markdown("**Action items:**")
            for a in res["action_items"]:
                st.write(f"• {a}")
        if res["safety_alerts"]:
            st.markdown("**Safety alerts:**")
            for a in res["safety_alerts"]:
                st.error(f"⚠️ {a}")
        st.caption(f"Confidence: {int(res['confidence']*100)}% · {res['disclaimer']}")

elif module == "Weather Advisory":
    st.subheader("🌤️ Weather Advisory")
    city = st.text_input("City", "Pune")
    if st.button("Get forecast"):
        import datetime
        today = date.today()
        rng = _rng(city, today.isoformat())
        base_temp = 29 + (5 if today.month in {4, 5, 6} else -4 if today.month in {12, 1} else 0) + rng.uniform(-2, 2)
        st.markdown(f"<div class='card'><h3>{city} — Current: {base_temp:.1f}°C</h3><p>Conditions broadly workable. Recheck forecast before next shift.</p></div>", unsafe_allow_html=True)
        st.markdown("### 7-day forecast")
        for i in range(7):
            d = today + timedelta(days=i)
            max_t = base_temp + rng.uniform(-1, 4)
            rain = rng.randint(5, 78)
            st.write(f"{d.strftime('%a %d %b')}: {max_t:.1f}°C · Rain {rain}% · {'Good' if rain < 65 else 'Poor'} for site work")

elif module == "Knowledge Hub":
    st.subheader("📚 Knowledge Hub")
    with st.form("knowledge_form"):
        question = st.text_input("Question", "What is the required concrete curing period?")
        topic = st.selectbox("Topic", ["general", "concrete", "steel", "safety", "quality", "scheduling", "costing", "procurement", "excavation", "waterproofing", "green_building", "contracts"])
        level = st.selectbox("Experience level", ["beginner", "intermediate", "expert"])
        submitted = st.form_submit_button("Get answer")
    if submitted:
        res = demo_knowledge(question, topic, level)
        st.markdown(f"<div class='card'><h3>{res['topic'].title()}</h3><p>{res['answer']}</p></div>", unsafe_allow_html=True)
        st.markdown("**Key points:**")
        for p in res["key_points"]:
            st.write(f"• {p}")
        if res["practical_tips"]:
            st.markdown("**Practical tips:**")
            for t in res["practical_tips"]:
                st.write(f"• {t}")
        if res["references"]:
            st.markdown("**References:**")
            for r in res["references"]:
                st.write(f"• {r['title']} — {r['source']}")
        st.info(res["disclaimer"])
