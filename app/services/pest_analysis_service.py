"""
app/services/pest_analysis_service.py

Intelligent pest / stress analysis for registered fields.
Uses satellite NDVI simulation + environmental conditions to:
  1. Predict stress cause (water, heat, fungal, pest, nutrient)
  2. Classify severity (healthy / moderate / critical) + urgency
  3. Perform zone-based analysis (% affected area)
  4. Generate actionable, farmer-friendly recommendations
  5. Detect NDVI trend (simulated historical comparison)
  6. Support Hindi translation
"""
import random
import hashlib
from typing import Any
from bson import ObjectId  # type: ignore[import-untyped]

from app.database import get_db  # type: ignore
from app.services.satellite_service import (  # type: ignore
    simulate_ndvi_for_corridor,
    simulate_environmental_conditions,
)
from app.services.season_service import detect_season  # type: ignore


# ── Stress cause inference rules ─────────────────────────────────────────────

def _infer_stress_cause(
    ndvi: float, moisture: float, temp: float, humidity: float
) -> dict[str, Any]:
    """
    Determine the most probable stress cause from combined indicators.
    Returns a dict with cause key, label (EN + HI), explanation, and confidence.
    """
    causes: list[dict[str, Any]] = []

    # Water / drought stress
    if ndvi < 0.5 and moisture < 25:
        conf = min(95, 60 + int((25 - moisture) * 1.4))
        causes.append({
            "key": "water_stress",
            "label": "Water Stress",
            "label_hi": "पानी की कमी (जल तनाव)",
            "explanation": (
                "Low vegetation health combined with dry soil indicates the crop "
                "is not receiving enough water. Leaves may appear wilted or curled."
            ),
            "explanation_hi": (
                "कम वनस्पति स्वास्थ्य और सूखी मिट्टी बताती है कि फसल को पर्याप्त "
                "पानी नहीं मिल रहा है। पत्तियाँ मुरझाई या मुड़ी हुई दिख सकती हैं।"
            ),
            "confidence": conf,
        })

    # Fungal disease risk
    if ndvi < 0.55 and humidity > 75:
        conf = min(92, 55 + int((humidity - 75) * 1.5))
        causes.append({
            "key": "fungal_disease",
            "label": "Fungal Disease Risk",
            "label_hi": "फफूंद रोग का खतरा",
            "explanation": (
                "High humidity creates favorable conditions for fungal diseases like "
                "blight, powdery mildew, and rust. Look for spots or discoloration on leaves."
            ),
            "explanation_hi": (
                "अधिक नमी फफूंद रोग जैसे झुलसा, चूर्णिल आसिता और रतुआ के लिए "
                "अनुकूल परिस्थितियाँ बनाती है। पत्तियों पर धब्बे या रंग बदलना देखें।"
            ),
            "confidence": conf,
        })

    # Heat stress
    if ndvi < 0.5 and temp > 36:
        conf = min(90, 50 + int((temp - 36) * 5))
        causes.append({
            "key": "heat_stress",
            "label": "Heat Stress",
            "label_hi": "गर्मी का तनाव",
            "explanation": (
                "High temperature is causing plant stress. Crops may show leaf "
                "scorching, wilting during midday, and reduced growth."
            ),
            "explanation_hi": (
                "अधिक तापमान से पौधों में तनाव हो रहा है। फसलों में पत्ती जलना, "
                "दोपहर में मुरझाना और विकास में कमी दिख सकती है।"
            ),
            "confidence": conf,
        })

    # Pest activity
    if 0.25 < ndvi < 0.55 and moisture > 20 and temp < 38 and humidity < 80:
        conf = random.randint(60, 78)  # type: ignore
        causes.append({
            "key": "pest_activity",
            "label": "Possible Pest Activity",
            "label_hi": "कीट गतिविधि की संभावना",
            "explanation": (
                "Moderate vegetation decline with otherwise normal conditions suggests "
                "early pest activity. Check leaf undersides for aphids, whiteflies, or borers."
            ),
            "explanation_hi": (
                "सामान्य परिस्थितियों के बावजूद वनस्पति में गिरावट प्रारंभिक कीट "
                "गतिविधि का संकेत देती है। पत्तियों के नीचे एफिड्स, सफेद मक्खी या बोरर की जाँच करें।"
            ),
            "confidence": conf,
        })

    # Nutrient deficiency
    if 0.3 < ndvi < 0.5 and moisture > 25 and temp < 36:
        conf = random.randint(55, 72)  # type: ignore
        causes.append({
            "key": "nutrient_deficiency",
            "label": "Nutrient Deficiency",
            "label_hi": "पोषक तत्वों की कमी",
            "explanation": (
                "Vegetation appears pale or yellowing despite adequate water and temperature. "
                "This often indicates nitrogen, phosphorus, or potassium deficiency."
            ),
            "explanation_hi": (
                "पर्याप्त पानी और तापमान के बावजूद वनस्पति पीली दिख रही है। "
                "यह अक्सर नाइट्रोजन, फॉस्फोरस या पोटेशियम की कमी का संकेत है।"
            ),
            "confidence": conf,
        })

    # Healthy — no stress
    if not causes:
        causes.append({
            "key": "healthy",
            "label": "No Stress Detected",
            "label_hi": "कोई तनाव नहीं पाया गया",
            "explanation": (
                "Vegetation is healthy and environmental conditions are within "
                "normal range. No immediate action required."
            ),
            "explanation_hi": (
                "वनस्पति स्वस्थ है और पर्यावरणीय स्थितियाँ सामान्य सीमा में हैं। "
                "तुरंत कोई कार्रवाई आवश्यक नहीं है।"
            ),
            "confidence": 90,
        })

    # Sort by confidence descending → primary cause is first
    causes.sort(key=lambda c: c["confidence"], reverse=True)
    return {"primary": causes[0], "all_causes": causes}


# ── Severity + urgency classification ────────────────────────────────────────

def _classify_severity(
    ndvi: float, moisture: float, temp: float, stressed_pct: float
) -> dict[str, Any]:
    """Classify into severity level + urgency."""
    if ndvi < 0.25 or (moisture < 15 and temp > 38) or stressed_pct > 60:
        return {
            "level": "critical",
            "level_label": "Critical",
            "level_label_hi": "गंभीर",
            "urgency": "high",
            "urgency_label": "Immediate Action Required",
            "urgency_label_hi": "तुरंत कार्रवाई आवश्यक",
            "color": "red",
        }
    elif ndvi < 0.5 or stressed_pct > 30:
        return {
            "level": "moderate",
            "level_label": "Moderate",
            "level_label_hi": "मध्यम",
            "urgency": "medium",
            "urgency_label": "Action Needed Within 2-3 Days",
            "urgency_label_hi": "2-3 दिनों में कार्रवाई करें",
            "color": "yellow",
        }
    else:
        return {
            "level": "healthy",
            "level_label": "Healthy",
            "level_label_hi": "स्वस्थ",
            "urgency": "low",
            "urgency_label": "Routine Monitoring",
            "urgency_label_hi": "नियमित निगरानी जारी रखें",
            "color": "green",
        }


# ── Zone-based analysis ──────────────────────────────────────────────────────

def _analyze_zones(ndvi_grid: list[dict[str, Any]]) -> dict[str, Any]:
    """Analyze individual grid zones and produce summary."""
    total = len(ndvi_grid)
    stressed = [z for z in ndvi_grid if z["ndvi"] < 0.3]
    moderate = [z for z in ndvi_grid if 0.3 <= z["ndvi"] < 0.6]
    healthy  = [z for z in ndvi_grid if z["ndvi"] >= 0.6]

    stressed_pct = round((len(stressed) / total) * 100, 1) if total else 0  # type: ignore
    moderate_pct = round((len(moderate) / total) * 100, 1) if total else 0  # type: ignore
    healthy_pct  = round((len(healthy) / total) * 100, 1) if total else 0   # type: ignore

    # Determine which region has most stress
    if stressed:
        rows = [z["row"] for z in stressed]
        avg_row = sum(rows) / len(rows)
        if avg_row < 1.5:
            region = "northern"
            region_hi = "उत्तरी"
        elif avg_row > 3.5:
            region = "southern"
            region_hi = "दक्षिणी"
        else:
            region = "central"
            region_hi = "मध्य"
    else:
        region = "none"
        region_hi = "कोई नहीं"

    # Build summary
    if stressed_pct > 0:
        summary = (
            f"{stressed_pct}% of the field is under stress, "
            f"mainly in the {region} region. "
            f"{moderate_pct}% shows moderate health, "
            f"and {healthy_pct}% is healthy."
        )
        summary_hi = (
            f"खेत का {stressed_pct}% हिस्सा तनाव में है, "
            f"मुख्य रूप से {region_hi} क्षेत्र में। "
            f"{moderate_pct}% मध्यम स्वास्थ्य दिखाता है, "
            f"और {healthy_pct}% स्वस्थ है।"
        )
    else:
        summary = f"All zones appear healthy. {healthy_pct}% healthy, {moderate_pct}% moderate."
        summary_hi = f"सभी क्षेत्र स्वस्थ दिखते हैं। {healthy_pct}% स्वस्थ, {moderate_pct}% मध्यम।"

    return {
        "total_zones": total,
        "stressed_zones": len(stressed),
        "moderate_zones": len(moderate),
        "healthy_zones": len(healthy),
        "stressed_pct": stressed_pct,
        "moderate_pct": moderate_pct,
        "healthy_pct": healthy_pct,
        "affected_region": region,
        "affected_region_hi": region_hi,
        "summary": summary,
        "summary_hi": summary_hi,
    }


# ── Actionable recommendations (enhanced) ────────────────────────────────────

def _generate_recommendations(
    cause_key: str,
    severity_level: str,
    zones: dict[str, Any],
) -> dict[str, Any]:
    """
    Generate structured, priority-based, context-aware recommendations.
    Returns high / medium / monitoring actions, timeline, risk, next check.
    """

    # ── Action banks per cause ────────────────────────────────────────────────
    ACTION_BANK: dict[str, dict[str, list[dict[str, str]]]] = {
        "water_stress": {
            "high": [
                {"action": "Irrigate the affected area immediately — apply 25-30 mm of water per hectare",
                 "action_hi": "प्रभावित क्षेत्र में तुरंत सिंचाई करें — प्रति हेक्टेयर 25-30 mm पानी दें",
                 "icon": "💧"},
            ],
            "medium": [
                {"action": "Apply organic mulch (straw or dry leaves) around the crop base to hold moisture in the soil",
                 "action_hi": "मिट्टी में नमी बनाए रखने के लिए फसल के चारों ओर जैविक मल्च (भूसा या सूखी पत्तियाँ) बिछाएँ",
                 "icon": "🌿"},
                {"action": "If possible, switch to drip irrigation — it saves 40-60% water compared to flood irrigation",
                 "action_hi": "यदि संभव हो तो ड्रिप सिंचाई अपनाएँ — यह बाढ़ सिंचाई की तुलना में 40-60% पानी बचाता है",
                 "icon": "⚙️"},
            ],
            "monitoring": [
                {"action": "Check soil moisture daily by inserting a finger 2 inches into the soil — if dry, irrigate",
                 "action_hi": "रोज़ मिट्टी में 2 इंच उंगली डालकर नमी जाँचें — सूखी हो तो सिंचाई करें",
                 "icon": "🔍"},
            ],
        },
        "fungal_disease": {
            "high": [
                {"action": "Spray copper-based fungicide (Copper Oxychloride 50% WP at 2.5 g/litre of water) on affected plants",
                 "action_hi": "प्रभावित पौधों पर कॉपर फफूंदनाशक (कॉपर ऑक्सीक्लोराइड 50% WP, 2.5 ग्राम/लीटर पानी) का छिड़काव करें",
                 "icon": "💊"},
                {"action": "Remove and burn infected leaves immediately — do not leave them in the field or compost",
                 "action_hi": "संक्रमित पत्तियों को तुरंत हटाकर जलाएँ — खेत में न छोड़ें और न खाद बनाएँ",
                 "icon": "🔥"},
            ],
            "medium": [
                {"action": "Stop overhead watering — water only at the base of plants, preferably in early morning",
                 "action_hi": "ऊपर से पानी देना बंद करें — सिर्फ़ पौधे के नीचे, सुबह जल्दी पानी दें",
                 "icon": "🚿"},
                {"action": "Improve air flow between plants by thinning dense growth areas",
                 "action_hi": "घने क्षेत्रों को छाँटकर पौधों के बीच हवा का प्रवाह बढ़ाएँ",
                 "icon": "💨"},
            ],
            "monitoring": [
                {"action": "Check leaves daily for new spots, white powder, or brown patches — report if spreading",
                 "action_hi": "रोज़ पत्तियों की जाँच करें — नए धब्बे, सफ़ेद पाउडर, या भूरे निशान दिखें तो रिपोर्ट करें",
                 "icon": "👀"},
            ],
        },
        "heat_stress": {
            "high": [
                {"action": "Water the field in early morning (before 7 AM) and again in the evening (after 5 PM)",
                 "action_hi": "सुबह 7 बजे से पहले और शाम 5 बजे के बाद खेत में पानी दें",
                 "icon": "☀️"},
            ],
            "medium": [
                {"action": "Spread a 5 cm layer of straw mulch to keep the soil cool and reduce evaporation",
                 "action_hi": "मिट्टी को ठंडा रखने के लिए 5 cm भूसा मल्च की परत बिछाएँ",
                 "icon": "🌿"},
                {"action": "Install temporary shade nets (50% shade) over sensitive or young crops",
                 "action_hi": "संवेदनशील या छोटी फसलों पर अस्थायी शेड नेट (50% छाया) लगाएँ",
                 "icon": "🏗️"},
            ],
            "monitoring": [
                {"action": "Watch for leaf wilting during midday — if plants don't recover by evening, increase water",
                 "action_hi": "दोपहर में पत्ती मुरझाने पर ध्यान दें — शाम तक ठीक न हों तो पानी बढ़ाएँ",
                 "icon": "🌡️"},
            ],
        },
        "pest_activity": {
            "high": [
                {"action": "Spray neem oil solution (5 ml per litre of water) on the affected zones every 5 days",
                 "action_hi": "प्रभावित क्षेत्रों पर हर 5 दिन नीम तेल (5 ml/लीटर पानी) का छिड़काव करें",
                 "icon": "🌱"},
                {"action": "Inspect leaf undersides for aphids, whiteflies, and borers — crush or remove them by hand",
                 "action_hi": "पत्तियों के नीचे एफिड्स, सफेद मक्खी और बोरर खोजें — हाथ से कुचलें या हटाएँ",
                 "icon": "🔍"},
            ],
            "medium": [
                {"action": "Set up 20 yellow sticky traps per hectare to catch flying pests and monitor population",
                 "action_hi": "उड़ने वाले कीटों को पकड़ने के लिए प्रति हेक्टेयर 20 पीले चिपचिपे जाल लगाएँ",
                 "icon": "🪤"},
                {"action": "Encourage natural pest enemies — avoid broad-spectrum pesticides that kill ladybugs and spiders",
                 "action_hi": "प्राकृतिक कीट शत्रुओं को बढ़ावा दें — व्यापक स्पेक्ट्रम कीटनाशक न डालें",
                 "icon": "🐞"},
            ],
            "monitoring": [
                {"action": "Check 10 random plants daily — if more than 3 have pests, re-apply neem oil spray",
                 "action_hi": "रोज़ 10 पौधों की जाँच करें — 3 से ज़्यादा में कीट मिलें तो नीम तेल दोबारा लगाएँ",
                 "icon": "📊"},
            ],
        },
        "nutrient_deficiency": {
            "high": [
                {"action": "Apply NPK fertilizer (10:26:26) at 50 kg per hectare — mix into soil near the roots",
                 "action_hi": "NPK उर्वरक (10:26:26) 50 kg/हेक्टेयर लगाएँ — जड़ों के पास मिट्टी में मिलाएँ",
                 "icon": "🧪"},
            ],
            "medium": [
                {"action": "Do a foliar spray of 2% urea solution for quick nitrogen boost (20 g urea per litre)",
                 "action_hi": "तेज़ नाइट्रोजन के लिए 2% यूरिया घोल (20 ग्राम/लीटर) का पत्तियों पर छिड़काव करें",
                 "icon": "💨"},
                {"action": "Get soil tested at the nearest Krishi Vigyan Kendra or agricultural lab",
                 "action_hi": "निकटतम कृषि विज्ञान केंद्र या कृषि प्रयोगशाला में मिट्टी जाँच कराएँ",
                 "icon": "📋"},
            ],
            "monitoring": [
                {"action": "Watch for yellowing leaves or stunted growth — these indicate the deficiency is continuing",
                 "action_hi": "पीली पत्तियाँ या बौनापन देखें — ये पोषक कमी जारी होने का संकेत हैं",
                 "icon": "🌾"},
            ],
        },
        "healthy": {
            "high": [],
            "medium": [],
            "monitoring": [
                {"action": "Everything looks good! Continue current practices and check again in 7-10 days",
                 "action_hi": "सब ठीक दिख रहा है! वर्तमान प्रबंधन जारी रखें और 7-10 दिन में फिर जाँचें",
                 "icon": "✅"},
                {"action": "Keep a steady irrigation schedule to maintain soil moisture and prevent future stress",
                 "action_hi": "मिट्टी की नमी बनाए रखने के लिए नियमित सिंचाई कार्यक्रम जारी रखें",
                 "icon": "💧"},
            ],
        },
    }

    bank = ACTION_BANK.get(cause_key, ACTION_BANK["healthy"])

    # If critical, prepend an urgent field visit action
    if severity_level == "critical" and cause_key != "healthy":
        bank["high"] = [
            {"action": "⚡ Visit the field TODAY for an immediate physical inspection of affected zones",
             "action_hi": "⚡ प्रभावित क्षेत्रों के तत्काल भौतिक निरीक्षण के लिए आज ही खेत पर जाएँ",
             "icon": "🚨"},
        ] + bank["high"]

    # ── Timeline ──────────────────────────────────────────────────────────────
    TIMELINES: dict[str, list[dict[str, str]]] = {
        "water_stress": [
            {"day": "Day 1", "task": "Irrigate affected area with 25-30 mm water",
             "task_hi": "प्रभावित क्षेत्र में 25-30 mm पानी से सिंचाई करें"},
            {"day": "Day 2", "task": "Apply mulch around crop base to retain moisture",
             "task_hi": "नमी बनाए रखने के लिए फसल के चारों ओर मल्च बिछाएँ"},
            {"day": "Day 3", "task": "Check soil moisture — re-irrigate if still dry",
             "task_hi": "मिट्टी की नमी जाँचें — अभी भी सूखी हो तो दोबारा सिंचाई करें"},
            {"day": "Day 7", "task": "Run analysis again to compare NDVI improvement",
             "task_hi": "NDVI सुधार की तुलना के लिए फिर से विश्लेषण चलाएँ"},
        ],
        "fungal_disease": [
            {"day": "Day 1", "task": "Spray copper fungicide on infected areas",
             "task_hi": "संक्रमित क्षेत्रों पर कॉपर फफूंदनाशक छिड़कें"},
            {"day": "Day 1", "task": "Remove and destroy infected leaves",
             "task_hi": "संक्रमित पत्तियों को हटाकर नष्ट करें"},
            {"day": "Day 3", "task": "Inspect for new infection spots",
             "task_hi": "नए संक्रमण धब्बों की जाँच करें"},
            {"day": "Day 5", "task": "Re-apply fungicide if infection persists",
             "task_hi": "संक्रमण बना रहे तो फफूंदनाशक दोबारा लगाएँ"},
            {"day": "Day 10", "task": "Run analysis again to verify recovery",
             "task_hi": "सुधार सत्यापित करने के लिए दोबारा विश्लेषण करें"},
        ],
        "heat_stress": [
            {"day": "Day 1", "task": "Start morning + evening watering schedule",
             "task_hi": "सुबह + शाम सिंचाई शुरू करें"},
            {"day": "Day 2", "task": "Spread straw mulch (5 cm layer) on exposed soil",
             "task_hi": "खुली मिट्टी पर भूसा मल्च (5 cm) बिछाएँ"},
            {"day": "Day 3", "task": "Install shade nets if available",
             "task_hi": "उपलब्ध हो तो शेड नेट लगाएँ"},
            {"day": "Day 5", "task": "Check if wilting has reduced — adjust water if needed",
             "task_hi": "मुरझाने में कमी जाँचें — ज़रूरत हो तो पानी बढ़ाएँ"},
        ],
        "pest_activity": [
            {"day": "Day 1", "task": "Spray neem oil on affected zones",
             "task_hi": "प्रभावित क्षेत्रों पर नीम तेल छिड़कें"},
            {"day": "Day 2", "task": "Install sticky traps and inspect 10 random plants",
             "task_hi": "चिपचिपे जाल लगाएँ और 10 पौधों की जाँच करें"},
            {"day": "Day 5", "task": "Re-apply neem oil if pests still present",
             "task_hi": "कीट अभी भी मौजूद हों तो नीम तेल दोबारा लगाएँ"},
            {"day": "Day 7", "task": "Count pests on traps — if increasing, consider stronger bio-pesticide",
             "task_hi": "जालों पर कीट गिनें — बढ़ रहे हों तो मज़बूत जैव-कीटनाशक विचार करें"},
            {"day": "Day 10", "task": "Run analysis again to verify improvement",
             "task_hi": "सुधार सत्यापित करने के लिए दोबारा विश्लेषण चलाएँ"},
        ],
        "nutrient_deficiency": [
            {"day": "Day 1", "task": "Apply NPK fertilizer near root zone",
             "task_hi": "जड़ क्षेत्र के पास NPK उर्वरक लगाएँ"},
            {"day": "Day 3", "task": "Foliar spray of urea (2%) for quick nitrogen uptake",
             "task_hi": "तेज़ नाइट्रोजन के लिए यूरिया (2%) का पत्तियों पर छिड़काव"},
            {"day": "Day 5", "task": "Check for colour improvement in leaves",
             "task_hi": "पत्तियों के रंग में सुधार जाँचें"},
            {"day": "Day 10", "task": "Get soil test done and run analysis again",
             "task_hi": "मिट्टी जाँच कराएँ और दोबारा विश्लेषण करें"},
        ],
        "healthy": [
            {"day": "Day 7-10", "task": "Schedule next routine monitoring",
             "task_hi": "अगली नियमित निगरानी शेड्यूल करें"},
        ],
    }

    timeline = TIMELINES.get(cause_key, TIMELINES["healthy"])

    # ── Risk explanation ──────────────────────────────────────────────────────
    RISK_WARNINGS: dict[str, dict[str, str]] = {
        "water_stress": {
            "warning": "If not watered within 48 hours, crop yield could drop by 15-25%. Prolonged drought causes permanent damage to roots.",
            "warning_hi": "अगर 48 घंटे में पानी नहीं दिया तो पैदावार 15-25% तक गिर सकती है। लंबा सूखा जड़ों को स्थायी नुकसान पहुँचाता है।",
        },
        "fungal_disease": {
            "warning": "Fungal diseases can spread rapidly in humid conditions, potentially destroying 30-50% of the crop within 7-10 days if untreated.",
            "warning_hi": "फफूंद रोग नमी में तेज़ी से फैल सकता है, इलाज न करने पर 7-10 दिनों में 30-50% फसल नष्ट हो सकती है।",
        },
        "heat_stress": {
            "warning": "Continued heat exposure without protection can reduce yield by 20-30%. Flowering and grain-filling stages are especially vulnerable.",
            "warning_hi": "बिना सुरक्षा के लगातार गर्मी 20-30% उपज कम कर सकती है। फूल और दाना भरने की अवस्था विशेष रूप से संवेदनशील है।",
        },
        "pest_activity": {
            "warning": "If pest population grows unchecked, yield loss can reach 20-40%. Early action prevents colony establishment.",
            "warning_hi": "कीट जनसंख्या बेरोकटोक बढ़ने पर पैदावार 20-40% तक गिर सकती है। जल्दी कार्रवाई कॉलोनी बनने से रोकती है।",
        },
        "nutrient_deficiency": {
            "warning": "Ongoing nutrient shortage leads to small, pale grains and 15-25% yield reduction. Soil testing prevents recurring deficiency.",
            "warning_hi": "लगातार पोषक कमी से छोटे, पीले दाने और 15-25% पैदावार में कमी होती है। मिट्टी जाँच बार-बार की कमी को रोकती है।",
        },
        "healthy": {
            "warning": "No immediate risk. Regular monitoring helps catch any emerging issues early.",
            "warning_hi": "कोई तत्काल जोखिम नहीं। नियमित निगरानी से कोई भी उभरती समस्या जल्दी पकड़ी जा सकती है।",
        },
    }

    risk = RISK_WARNINGS.get(cause_key, RISK_WARNINGS["healthy"])

    # ── Next check schedule ───────────────────────────────────────────────────
    if severity_level == "critical":
        next_check = "Tomorrow (within 24 hours)"
        next_check_hi = "कल (24 घंटे के भीतर)"
    elif severity_level == "moderate":
        next_check = "In 3 days"
        next_check_hi = "3 दिन में"
    else:
        next_check = "In 7-10 days (routine)"
        next_check_hi = "7-10 दिन में (नियमित)"

    # ── Affected area context ─────────────────────────────────────────────────
    affected_area = {
        "affected_pct": zones["stressed_pct"],
        "affected_region": zones["affected_region"],
        "affected_region_hi": zones["affected_region_hi"],
        "note": (
            f"{zones['stressed_pct']}% of your field is affected, "
            f"concentrated in the {zones['affected_region']} part. "
            f"Focus your actions on that area first."
        ) if zones["stressed_pct"] > 0 else "No specific area is under stress.",
        "note_hi": (
            f"आपके खेत का {zones['stressed_pct']}% प्रभावित है, "
            f"मुख्य रूप से {zones['affected_region_hi']} हिस्से में। "
            f"पहले उस क्षेत्र पर ध्यान दें।"
        ) if zones["stressed_pct"] > 0 else "कोई विशेष क्षेत्र तनाव में नहीं है।",
    }

    return {
        "priority_actions": {
            "high": bank.get("high", []),
            "medium": bank.get("medium", []),
            "monitoring": bank.get("monitoring", []),
        },
        "timeline": timeline,
        "risk_warning": risk,
        "affected_area": affected_area,
        "next_check": next_check,
        "next_check_hi": next_check_hi,
        # Flat list for backward compatibility
        "flat_list": bank.get("high", []) + bank.get("medium", []) + bank.get("monitoring", []),
    }


# ── Trend detection (simulated) ──────────────────────────────────────────────

def _detect_trend(field_id: str, current_ndvi: float) -> dict[str, Any]:
    """
    Simulate historical NDVI comparison.
    In production, this would query stored NDVI history from the database.
    """
    # Simulate previous NDVI based on field_id hash
    seed = int(hashlib.md5(field_id.encode()).hexdigest(), 16) % 1000
    rng = random.Random(seed)  # type: ignore
    previous_ndvi = round(current_ndvi + rng.uniform(-0.15, 0.10), 3)  # type: ignore
    previous_ndvi = max(0.05, min(0.95, previous_ndvi))  # type: ignore

    change = round(current_ndvi - previous_ndvi, 3)  # type: ignore
    change_pct = round((change / previous_ndvi) * 100, 1) if previous_ndvi > 0 else 0  # type: ignore

    if change < -0.1:
        trend = "rapid_decline"
        trend_label = "⚠️ Rapid Decline"
        trend_label_hi = "⚠️ तेज़ गिरावट"
        trend_note = f"NDVI dropped by {abs(change_pct)}% since last observation. Immediate attention recommended."
        trend_note_hi = f"NDVI पिछले अवलोकन से {abs(change_pct)}% गिरा है। तुरंत ध्यान देने की सिफारिश।"
    elif change < -0.03:
        trend = "declining"
        trend_label = "📉 Declining"
        trend_label_hi = "📉 गिरावट"
        trend_note = f"NDVI decreased by {abs(change_pct)}%. Monitor closely over the next few days."
        trend_note_hi = f"NDVI {abs(change_pct)}% कम हुआ है। अगले कुछ दिनों में बारीकी से निगरानी करें।"
    elif change > 0.03:
        trend = "improving"
        trend_label = "📈 Improving"
        trend_label_hi = "📈 सुधार"
        trend_note = f"NDVI improved by {change_pct}%. Current management practices are working well."
        trend_note_hi = f"NDVI {change_pct}% बढ़ा है। वर्तमान प्रबंधन अच्छा काम कर रहा है।"
    else:
        trend = "stable"
        trend_label = "➡️ Stable"
        trend_label_hi = "➡️ स्थिर"
        trend_note = "NDVI is stable with minimal change since last observation."
        trend_note_hi = "पिछले अवलोकन से NDVI में न्यूनतम बदलाव है।"

    return {
        "previous_ndvi": previous_ndvi,
        "current_ndvi": current_ndvi,
        "change": change,
        "change_pct": change_pct,
        "trend": trend,
        "trend_label": trend_label,
        "trend_label_hi": trend_label_hi,
        "trend_note": trend_note,
        "trend_note_hi": trend_note_hi,
    }


# ══════════════════════════════════════════════════════════════════════════════
# MAIN ANALYSIS FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

async def run_pest_analysis(field_id: str, lang: str = "en") -> dict[str, Any]:
    """
    Run intelligent pest/stress analysis for a field.
    Returns structured, farmer-friendly results with:
      - NDVI stats + trend
      - Stress cause prediction
      - Severity & urgency
      - Zone-based breakdown
      - Actionable recommendations
    """
    db = get_db()
    field = await db["fields"].find_one({"_id": ObjectId(field_id)})
    if not field:
        return {"error": "Field not found"}

    lat = field.get("location", {}).get("lat", 25.4)
    lng = field.get("location", {}).get("lng", 81.8)
    crop = field.get("recommended_crop", "wheat")
    area = field.get("area", 1.0)

    # ── 1. Simulate NDVI per zone (5×5 grid) ─────────────────────────────────
    ndvi_grid: list[dict[str, Any]] = []
    for row in range(5):
        for col in range(5):
            grid_pos = f"{field_id}_{row}_{col}"
            ndvi_val = simulate_ndvi_for_corridor(grid_pos)
            ndvi_grid.append({
                "row": row,
                "col": col,
                "grid_position": grid_pos,
                "ndvi": ndvi_val,
                "health": "healthy" if ndvi_val > 0.6 else "moderate" if ndvi_val >= 0.3 else "stress",
            })

    all_ndvi = [z["ndvi"] for z in ndvi_grid]
    ndvi_avg = round(sum(all_ndvi) / len(all_ndvi), 3)  # type: ignore
    ndvi_min = round(min(all_ndvi), 3)  # type: ignore
    ndvi_max = round(max(all_ndvi), 3)  # type: ignore

    # ── 2. Simulate environmental conditions ──────────────────────────────────
    season = detect_season()
    env: dict[str, Any] = simulate_environmental_conditions(lat, lng, season)
    temperature = env["temperature"]
    humidity = env["humidity"]
    soil_moisture = env["soil_moisture"]
    rainfall_prob = env["rainfall_probability"]

    # ── 3. Zone-based analysis ────────────────────────────────────────────────
    zones = _analyze_zones(ndvi_grid)

    # ── 4. Stress cause prediction ────────────────────────────────────────────
    causes = _infer_stress_cause(ndvi_avg, soil_moisture, temperature, humidity)
    primary_cause = causes["primary"]

    # ── 5. Severity + urgency ─────────────────────────────────────────────────
    severity = _classify_severity(ndvi_avg, soil_moisture, temperature, zones["stressed_pct"])

    # ── 6. Actionable recommendations ─────────────────────────────────────────
    recommendations = _generate_recommendations(primary_cause["key"], severity["level"], zones)

    # ── 7. Trend detection ────────────────────────────────────────────────────
    trend = _detect_trend(field_id, ndvi_avg)

    # ── 7b. Pest possibility warning ─────────────────────────────────────────
    # When NDVI is critically low OR more than 30% of zones are stressed,
    # append a pest infestation warning to the primary cause explanation.
    # Condition: ndvi_avg < 0.35 OR stressed_pct > 30
    # Rule: only for non-healthy causes (no false alarm on healthy crops)
    _pest_warning = (
        " There is also a possibility of pest infestation in high-risk areas."
    )
    _pest_warning_hi = (
        " उच्च-जोखिम वाले क्षेत्रों में कीट संक्रमण की भी संभावना है।"
    )
    _high_risk = (ndvi_avg < 0.35) or (zones["stressed_pct"] > 30)

    if _high_risk and primary_cause["key"] != "healthy":
        primary_cause["explanation"]    += _pest_warning
        primary_cause["explanation_hi"] += _pest_warning_hi


    # ── 8. Build farmer-friendly summary ──────────────────────────────────────
    is_hi = lang.startswith("hi")

    if is_hi:
        main_summary = (
            f"आपके खेत ({crop or 'फसल'}, {area} हेक्टेयर) का विश्लेषण पूरा हुआ। "
            f"NDVI: {ndvi_avg}। स्थिति: {severity['level_label_hi']}। "
            f"संभावित कारण: {primary_cause['label_hi']}। "
            f"{zones['summary_hi']}"
        )
    else:
        main_summary = (
            f"Analysis complete for your field ({crop or 'crop'}, {area} ha). "
            f"NDVI: {ndvi_avg}. Status: {severity['level_label']}. "
            f"Likely cause: {primary_cause['label']}. "
            f"{zones['summary']}"
        )

    # ── Response ──────────────────────────────────────────────────────────────
    return {
        "field_id": field_id,
        "crop": crop or "Unknown",
        "area_ha": area,
        "season": season,

        # NDVI
        "ndvi": ndvi_avg,
        "ndvi_min": ndvi_min,
        "ndvi_max": ndvi_max,

        # Status (keep backward-compatible keys)
        "status": severity["level_label"],
        "status_hi": severity["level_label_hi"],
        "status_key": severity["level"],
        "icon": "✅" if severity["level"] == "healthy" else "⚠️" if severity["level"] == "moderate" else "🔴",

        # Severity & urgency
        "severity": severity,

        # Likely cause
        "likely_cause": {
            "label": primary_cause["label"],
            "label_hi": primary_cause["label_hi"],
            "explanation": primary_cause["explanation"],
            "explanation_hi": primary_cause["explanation_hi"],
            "confidence": primary_cause["confidence"],
        },
        "all_causes": [
            {"label": c["label"], "label_hi": c["label_hi"], "confidence": c["confidence"]}
            for c in causes["all_causes"]
        ],

        # Zone analysis
        "zone_analysis": zones,

        # Recommendations
        "recommendations": recommendations,

        # Trend
        "trend": trend,

        # Environmental conditions
        "environmental_conditions": {
            "temperature": temperature,
            "humidity": humidity,
            "soil_moisture": soil_moisture,
            "rainfall_probability": rainfall_prob,
        },

        # Human summary
        "summary": main_summary,

        # Legacy fields for backward compatibility
        "analysis": primary_cause["explanation"],
        "recommendation": recommendations["flat_list"][0]["action"] if recommendations.get("flat_list") else "",
        "risks": [
            {
                "label": c["label"],
                "description": c["explanation"],
                "action": "",
            }
            for c in causes["all_causes"]
            if c["key"] != "healthy"
        ],
    }
