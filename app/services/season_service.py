"""
app/services/season_service.py

Season detection with stage awareness (early/mid/end),
next-season planning, and crop calendar for Indian agriculture.
"""
from datetime import datetime
from typing import Any, Optional
import calendar


# ── Season Definitions ────────────────────────────────────────────────────────
SEASONS: dict[str, Any] = {
    "kharif": {
        "label": "Kharif (Monsoon)",
        "period": "June – October",
        "months": (6, 7, 8, 9, 10),
        "stages": {
            "early": (6, 7),    # June-July
            "mid":   (8, 9),    # August-September
            "end":   (10,),     # October
        },
        "typical_temp": (25, 35),
        "typical_humidity": (70, 90),
        "typical_rainfall": (200, 500),
        "crops": {
            "normal": [
                {"crop": "rice",       "duration": "120-150 days", "type": "long"},
                {"crop": "maize",      "duration": "90-120 days",  "type": "medium"},
                {"crop": "cotton",     "duration": "150-180 days", "type": "long"},
                {"crop": "soybean",    "duration": "85-120 days",  "type": "medium"},
                {"crop": "sugarcane",  "duration": "300-365 days", "type": "long"},
                {"crop": "groundnut",  "duration": "100-130 days", "type": "medium"},
                {"crop": "bajra",      "duration": "75-90 days",   "type": "short"},
                {"crop": "jowar",      "duration": "90-110 days",  "type": "medium"},
            ],
            "short_duration": [
                {"crop": "bajra",      "duration": "75-90 days",   "type": "short"},
                {"crop": "moong",      "duration": "60-75 days",   "type": "short"},
                {"crop": "urad",       "duration": "70-90 days",   "type": "short"},
                {"crop": "cowpea",     "duration": "60-90 days",   "type": "short"},
                {"crop": "maize",      "duration": "90 days (short var.)", "type": "short"},
            ],
        },
    },
    "rabi": {
        "label": "Rabi (Winter)",
        "period": "October – March",
        "months": (10, 11, 12, 1, 2, 3),
        "stages": {
            "early": (10, 11),   # October-November
            "mid":   (12, 1),    # December-January
            "end":   (2, 3),     # February-March
        },
        "typical_temp": (10, 25),
        "typical_humidity": (40, 65),
        "typical_rainfall": (20, 100),
        "crops": {
            "normal": [
                {"crop": "wheat",    "duration": "120-150 days", "type": "long"},
                {"crop": "mustard",  "duration": "110-140 days", "type": "medium"},
                {"crop": "barley",   "duration": "120-140 days", "type": "long"},
                {"crop": "gram",     "duration": "95-120 days",  "type": "medium"},
                {"crop": "peas",     "duration": "90-120 days",  "type": "medium"},
                {"crop": "lentil",   "duration": "100-130 days", "type": "medium"},
                {"crop": "potato",   "duration": "80-120 days",  "type": "medium"},
            ],
            "short_duration": [
                {"crop": "potato",    "duration": "80-90 days (early var.)", "type": "short"},
                {"crop": "peas",      "duration": "60-75 days (early var.)", "type": "short"},
                {"crop": "radish",    "duration": "30-45 days",              "type": "short"},
                {"crop": "spinach",   "duration": "40-50 days",              "type": "short"},
                {"crop": "coriander", "duration": "40-60 days",              "type": "short"},
            ],
        },
    },
    "zaid": {
        "label": "Zaid (Summer)",
        "period": "March – June",
        "months": (3, 4, 5, 6),
        "stages": {
            "early": (3, 4),   # March-April
            "mid":   (5,),     # May
            "end":   (6,),     # June
        },
        "typical_temp": (30, 42),
        "typical_humidity": (30, 55),
        "typical_rainfall": (10, 60),
        "crops": {
            "normal": [
                {"crop": "watermelon",  "duration": "80-100 days",  "type": "medium"},
                {"crop": "muskmelon",   "duration": "70-90 days",   "type": "short"},
                {"crop": "cucumber",    "duration": "45-70 days",   "type": "short"},
                {"crop": "moong",       "duration": "60-75 days",   "type": "short"},
                {"crop": "sunflower",   "duration": "80-100 days",  "type": "medium"},
                {"crop": "fodder",      "duration": "45-60 days",   "type": "short"},
                {"crop": "maize",       "duration": "90-100 days",  "type": "medium"},
            ],
            "short_duration": [
                {"crop": "cucumber",    "duration": "45-55 days",   "type": "short"},
                {"crop": "muskmelon",   "duration": "70-80 days",   "type": "short"},
                {"crop": "fodder",      "duration": "45-60 days",   "type": "short"},
                {"crop": "moong",       "duration": "60-65 days",   "type": "short"},
            ],
        },
    },
}

SEASON_ORDER = ["kharif", "rabi", "zaid"]
MONTH_NAMES  = {i: calendar.month_name[i] for i in range(1, 13)}


# ── Core Detection Functions ─────────────────────────────────────────────────

def detect_season(dt: Optional[datetime] = None) -> str:
    """Return current farming season: 'kharif', 'rabi', or 'zaid'."""
    if dt is None:
        dt = datetime.now()
    month = dt.month

    if month in (6, 7, 8, 9):
        return "kharif"
    elif month in (11, 12, 1, 2):
        return "rabi"
    elif month in (4, 5):
        return "zaid"
    elif month == 10:
        return "kharif"   # late kharif / transitional
    elif month == 3:
        return "rabi"     # late rabi / transitional
    return "rabi"


def detect_season_stage(dt: Optional[datetime] = None) -> str:
    """Return season stage: 'early', 'mid', or 'end'."""
    if dt is None:
        dt = datetime.now()
    month  = dt.month
    season = detect_season(dt)
    stages: dict[str, Any] = SEASONS[season]["stages"]

    for stage_name, months in stages.items():
        if month in months:
            return stage_name
    return "mid"  # fallback


def get_next_season(current: str) -> str:
    """Return the next season after the current one."""
    idx = SEASON_ORDER.index(current) if current in SEASON_ORDER else 0
    return SEASON_ORDER[(idx + 1) % len(SEASON_ORDER)]


def get_season_analysis(dt: Optional[datetime] = None) -> dict:
    """
    Complete season analysis with month, season, stage, and crop planning.
    This is the main function called by land_analysis_service.
    """
    if dt is None:
        dt = datetime.now()

    month        = dt.month
    month_name   = MONTH_NAMES[month]
    season       = detect_season(dt)
    stage        = detect_season_stage(dt)
    season_data: dict[str, Any]  = SEASONS[season]
    next_season  = get_next_season(season)
    next_data: dict[str, Any]    = SEASONS[next_season]

    # ── Stage-aware crop recommendations ──────────────────────────────────
    if stage == "early":
        recommended_crops   = season_data["crops"]["normal"]
        sowing_advice       = f"This is the ideal time to sow {season_data['label']} crops. All normal and long-duration varieties can be planted."
        can_start_long      = True
        future_plan         = None
    elif stage == "mid":
        recommended_crops   = season_data["crops"]["short_duration"]
        sowing_advice       = (
            f"Mid-{season_data['label']} season. It is too late for long-duration crops. "
            f"Only short-duration varieties (60-90 days) should be planted now."
        )
        can_start_long      = False
        future_plan         = None
    else:  # end
        recommended_crops   = season_data["crops"]["short_duration"][:2]  # very few options
        sowing_advice       = (
            f"The {season_data['label']} season is ending. It is not ideal to start new crops now. "
            f"Focus on harvesting existing crops and preparing land for the upcoming "
            f"{next_data['label']} season."
        )
        can_start_long      = False
        future_plan         = {
            "next_season":       next_season,
            "next_season_label": next_data["label"],
            "next_season_period": next_data["period"],
            "recommended_crops": next_data["crops"]["normal"],
            "preparation_advice": (
                f"Start preparing for {next_data['label']} ({next_data['period']}). "
                f"Begin soil preparation, arrange seeds, and plan irrigation. "
                f"Recommended crops for next season: "
                + ", ".join(c["crop"].capitalize() for c in next_data["crops"]["normal"][:5])
                + "."
            ),
        }

    return {
        "current_month":      month,
        "current_month_name": month_name,
        "season":             season,
        "season_label":       season_data["label"],
        "season_period":      season_data["period"],
        "season_stage":       stage,
        "season_stage_label": f"{stage.capitalize()} {season_data['label']}",
        "sowing_advice":      sowing_advice,
        "can_start_long_crops": can_start_long,
        "recommended_crops":  recommended_crops,
        "future_plan":        future_plan,
        "typical_temp_range": season_data["typical_temp"],
        "typical_humidity_range": season_data["typical_humidity"],
        "typical_rainfall_range": season_data["typical_rainfall"],
    }


# ── Helper functions used by land_analysis_service ────────────────────────────

def get_season_info(season: Optional[str] = None) -> dict:
    """Get detailed info about a season (backward compatible)."""
    if season is None:
        season = detect_season()
    info: dict[str, Any] = SEASONS[season] if season in SEASONS else SEASONS["rabi"]
    return {
        "season": season,
        "label": info["label"],
        "period": info["period"],
        "preferred_crops": [c["crop"] for c in info["crops"]["normal"]],
        "typical_temp_range": info["typical_temp"],
        "typical_humidity_range": info["typical_humidity"],
        "typical_rainfall_range": info["typical_rainfall"],
    }


def get_season_crop_boost(crop: str, season: Optional[str] = None, stage: Optional[str] = None) -> float:
    """
    Returns a multiplier indicating how well a crop fits
    the current season AND stage.

    In-season crops:  1.0 – 1.3 (boosted)
    Out-of-season:    0.05 – 0.15 (heavily penalised)
    """
    if season is None:
        season = detect_season()
    if stage is None:
        stage = detect_season_stage()

    info: dict[str, Any] = SEASONS[season] if season in SEASONS else SEASONS["rabi"]
    normal_crops = [c["crop"].lower() for c in info["crops"]["normal"]]
    short_crops  = [c["crop"].lower() for c in info["crops"]["short_duration"]]
    all_season_crops = set(normal_crops + short_crops)

    crop_lower = crop.lower()
    is_in_season = crop_lower in all_season_crops

    if not is_in_season:
        # Crop does NOT belong to the current season at all → heavy penalty
        if stage == "early":
            return 0.15
        elif stage == "mid":
            return 0.10
        else:  # end
            return 0.05

    # Crop IS in the current season
    if stage == "early":
        if crop_lower in normal_crops:
            return 1.30
        return 1.15  # short-duration crop in early stage
    elif stage == "mid":
        if crop_lower in short_crops:
            return 1.20
        elif crop_lower in normal_crops:
            for c in info["crops"]["normal"]:
                if c["crop"].lower() == crop_lower and c["type"] == "long":
                    return 0.5  # long-duration in mid → risky
            return 0.8
        return 0.6
    else:  # end
        if crop_lower in short_crops:
            return 0.7
        return 0.3


# ══════════════════════════════════════════════════════════════════════════════
# CROP CALENDAR — sowing windows for each crop
# ══════════════════════════════════════════════════════════════════════════════

CROP_CALENDAR = {
    # ── Kharif crops ──
    "rice":       {"sowing_months": [6, 7],       "sowing_window": "June – July",       "season": "kharif", "duration": "120-150 days",  "next_window": "June – July (next Kharif)"},
    "cotton":     {"sowing_months": [4, 5, 6],    "sowing_window": "April – June",      "season": "kharif", "duration": "150-180 days",  "next_window": "April – June (next year)"},
    "soybean":    {"sowing_months": [6, 7],       "sowing_window": "June – July",       "season": "kharif", "duration": "85-120 days",   "next_window": "June – July (next Kharif)"},
    "groundnut":  {"sowing_months": [6, 7],       "sowing_window": "June – July",       "season": "kharif", "duration": "100-130 days",  "next_window": "June – July (next Kharif)"},
    "bajra":      {"sowing_months": [6, 7],       "sowing_window": "June – July",       "season": "kharif", "duration": "75-90 days",    "next_window": "June – July (next Kharif)"},
    "jowar":      {"sowing_months": [6, 7, 8],    "sowing_window": "June – August",     "season": "kharif", "duration": "90-110 days",   "next_window": "June – August (next Kharif)"},
    "urad":       {"sowing_months": [6, 7],       "sowing_window": "June – July",       "season": "kharif", "duration": "70-90 days",    "next_window": "June – July (next Kharif)"},
    "cowpea":     {"sowing_months": [6, 7],       "sowing_window": "June – July",       "season": "kharif", "duration": "60-90 days",    "next_window": "June – July (next Kharif)"},

    # ── Rabi crops ──
    "wheat":      {"sowing_months": [10, 11],     "sowing_window": "October – November","season": "rabi",   "duration": "120-150 days",  "next_window": "October – November (next Rabi)"},
    "mustard":    {"sowing_months": [10, 11],     "sowing_window": "October – November","season": "rabi",   "duration": "110-140 days",  "next_window": "October – November (next Rabi)"},
    "barley":     {"sowing_months": [10, 11],     "sowing_window": "October – November","season": "rabi",   "duration": "120-140 days",  "next_window": "October – November (next Rabi)"},
    "gram":       {"sowing_months": [10, 11],     "sowing_window": "October – November","season": "rabi",   "duration": "95-120 days",   "next_window": "October – November (next Rabi)"},
    "peas":       {"sowing_months": [10, 11],     "sowing_window": "October – November","season": "rabi",   "duration": "90-120 days",   "next_window": "October – November (next Rabi)"},
    "lentil":     {"sowing_months": [10, 11],     "sowing_window": "October – November","season": "rabi",   "duration": "100-130 days",  "next_window": "October – November (next Rabi)"},
    "potato":     {"sowing_months": [10, 11],     "sowing_window": "October – November","season": "rabi",   "duration": "80-120 days",   "next_window": "October – November (next Rabi)"},

    # ── Zaid crops ──
    "watermelon": {"sowing_months": [2, 3, 4],    "sowing_window": "February – April",  "season": "zaid",   "duration": "80-100 days",   "next_window": "February – April (next year)"},
    "muskmelon":  {"sowing_months": [2, 3, 4],    "sowing_window": "February – April",  "season": "zaid",   "duration": "70-90 days",    "next_window": "February – April (next year)"},
    "cucumber":   {"sowing_months": [2, 3, 4, 5], "sowing_window": "February – May",    "season": "zaid",   "duration": "45-70 days",    "next_window": "February – May (next year)"},
    "fodder":     {"sowing_months": [3, 4],       "sowing_window": "March – April",     "season": "zaid",   "duration": "45-60 days",    "next_window": "March – April (next year)"},
    "sunflower":  {"sowing_months": [1, 2, 6, 7], "sowing_window": "Jan–Feb / Jun–Jul", "season": "zaid/kharif", "duration": "80-100 days", "next_window": "January – February or June – July"},

    # ── Multi-season crops ──
    "maize":      {"sowing_months": [3, 4, 6, 7], "sowing_window": "Mar–Apr / Jun–Jul", "season": "zaid/kharif", "duration": "90-120 days", "next_window": "March – April (Zaid) or June – July (Kharif)"},
    "moong":      {"sowing_months": [3, 4, 6, 7], "sowing_window": "Mar–Apr / Jun–Jul", "season": "zaid/kharif", "duration": "60-75 days",  "next_window": "March – April (Zaid) or June – July (Kharif)"},
    "sugarcane":  {"sowing_months": [2, 3, 10],   "sowing_window": "Feb–Mar / October", "season": "multi",  "duration": "300-365 days",  "next_window": "February – March (Spring) or October (Autumn)"},
}


def validate_sowing_window(crop: str, month: Optional[int] = None, dt: Optional[datetime] = None) -> dict:
    """
    Validate whether a crop can be sown in the given month.

    Returns:
        {
            "crop": str,
            "sowing_allowed": bool,
            "sowing_window": str,
            "current_month": int,
            "current_month_name": str,
            "warning": str or None,
            "reason": str,
            "next_sowing_window": str,
            "alternative_crops": list,
        }
    """
    if dt is None:
        dt = datetime.now()
    if month is None:
        month = dt.month

    month_name = MONTH_NAMES[month]
    crop_lower = crop.lower()

    # Look up in crop calendar
    cal = CROP_CALENDAR.get(crop_lower)

    if not cal:
        # Unknown crop — allow by default
        return {
            "crop": crop,
            "sowing_allowed": True,
            "sowing_window": "Not specified",
            "current_month": month,
            "current_month_name": month_name,
            "warning": None,
            "reason": f"No calendar data available for {crop}. Sowing allowed by default.",
            "next_sowing_window": None,
            "alternative_crops": get_sowable_crops_for_month(month),
        }

    allowed = month in cal["sowing_months"]  # type: ignore

    if allowed:
        return {
            "crop": crop,
            "sowing_allowed": True,
            "sowing_window": cal["sowing_window"],
            "current_month": month,
            "current_month_name": month_name,
            "warning": None,
            "reason": (
                f"{crop.capitalize()} can be sown now. Current month ({month_name}) "
                f"falls within the sowing window ({cal['sowing_window']}). "
                f"Crop duration: {cal['duration']}."
            ),
            "next_sowing_window": cal["next_window"],
            "alternative_crops": [],
        }
    else:
        alternatives = get_sowable_crops_for_month(month)
        return {
            "crop": crop,
            "sowing_allowed": False,
            "sowing_window": cal["sowing_window"],
            "current_month": month,
            "current_month_name": month_name,
            "warning": (
                f"It is not the right time to start {crop.capitalize()} cultivation. "
                f"The sowing window for {crop.capitalize()} is {cal['sowing_window']}."
            ),
            "reason": (
                f"Current month ({month_name}) is outside the sowing window "
                f"for {crop.capitalize()} ({cal['sowing_window']}). "
                f"The sowing window has {'passed' if _window_passed(month, cal['sowing_months']) else 'not yet started'}."  # type: ignore
            ),
            "next_sowing_window": cal["next_window"],
            "alternative_crops": alternatives,
        }


def _window_passed(current_month: int, sowing_months: list) -> bool:
    """Check if the sowing window has already passed this year."""
    max_sow = max(sowing_months)
    if max_sow < current_month:
        return True
    return False


def get_sowable_crops_for_month(month: int) -> list:
    """Return all crops whose sowing window includes the given month."""
    result = []
    for crop_name, cal in CROP_CALENDAR.items():
        sow_months: list = cal.get("sowing_months") or []  # type: ignore
        if month in sow_months:
            result.append({
                "crop": crop_name,
                "sowing_window": cal["sowing_window"],
                "duration": cal["duration"],
                "season": cal["season"],
            })
    return result

