"""
app/services/translation_service.py

Hybrid translation engine:
  1. Dictionary-based translation (crop names, agriculture terms, templates)
  2. LibreTranslate API fallback for dynamic AI-generated text
  3. In-memory cache to avoid repeated API calls
"""
import re
from typing import Any
import httpx  # type: ignore[import-untyped]
from functools import lru_cache

# ══════════════════════════════════════════════════════════════════════════════
# DICTIONARIES
# ══════════════════════════════════════════════════════════════════════════════

# ── Crop Names ────────────────────────────────────────────────────────────────
CROP_NAMES_HI = {
    "wheat": "गेहूं",
    "rice": "धान",
    "paddy": "धान",
    "maize": "मक्का",
    "corn": "मक्का",
    "cotton": "कपास",
    "sugarcane": "गन्ना",
    "soybean": "सोयाबीन",
    "mustard": "सरसों",
    "barley": "जौ",
    "gram": "चना",
    "peas": "मटर",
    "lentil": "मसूर",
    "potato": "आलू",
    "watermelon": "तरबूज",
    "muskmelon": "खरबूजा",
    "cucumber": "खीरा",
    "sunflower": "सूरजमुखी",
    "moong": "मूंग",
    "urad": "उड़द",
    "bajra": "बाजरा",
    "jowar": "ज्वार",
    "groundnut": "मूंगफली",
    "cowpea": "लोबिया",
    "fodder": "चारा",
    "radish": "मूली",
    "spinach": "पालक",
    "coriander": "धनिया",
    "tomato": "टमाटर",
    "onion": "प्याज",
    "garlic": "लहसुन",
    "chilli": "मिर्च",
    "turmeric": "हल्दी",
    "ginger": "अदरक",
}

# ── Agriculture & Science Terms ───────────────────────────────────────────────
AGRI_TERMS_HI = {
    # soil
    "soil": "मिट्टी",
    "soil type": "मिट्टी का प्रकार",
    "soil moisture": "मिट्टी की नमी",
    "soil ph": "मिट्टी का पी.एच",
    "alluvial": "जलोढ़",
    "black soil": "काली मिट्टी",
    "red soil": "लाल मिट्टी",
    "clay soil": "चिकनी मिट्टी",
    "sandy soil": "बलुई मिट्टी",
    "loamy soil": "दोमट मिट्टी",
    "laterite": "लैटेराइट",
    "water retention": "जल धारण क्षमता",
    "drainage": "जल निकासी",
    "well-drained": "अच्छी जल निकासी वाली",

    # nutrients
    "nitrogen": "नाइट्रोजन",
    "phosphorus": "फास्फोरस",
    "potassium": "पोटैशियम",
    "npk": "एन.पी.के",
    "fertilizer": "उर्वरक",
    "organic matter": "जैविक पदार्थ",
    "farmyard manure": "गोबर की खाद",
    "fym": "गोबर की खाद",
    "urea": "यूरिया",
    "compost": "कम्पोस्ट",
    "micronutrients": "सूक्ष्म पोषक तत्व",
    "zinc": "जस्ता",
    "zinc sulphate": "जिंक सल्फेट",

    # water & climate
    "irrigation": "सिंचाई",
    "rainfall": "वर्षा",
    "humidity": "आर्द्रता",
    "temperature": "तापमान",
    "drip irrigation": "ड्रिप सिंचाई",
    "flood irrigation": "बाढ़ सिंचाई",
    "sprinkler": "स्प्रिंकलर",
    "monsoon": "मानसून",
    "drought": "सूखा",
    "waterlogging": "जलभराव",

    # crop & cultivation
    "crop": "फसल",
    "sowing": "बुवाई",
    "sowing window": "बुवाई का समय",
    "sowing time": "बुवाई का समय",
    "harvest": "कटाई",
    "harvest time": "कटाई का समय",
    "yield": "उपज",
    "expected yield": "अपेक्षित उपज",
    "seed": "बीज",
    "seed rate": "बीज दर",
    "seed treatment": "बीज उपचार",
    "seed varieties": "बीज किस्में",
    "germination": "अंकुरण",
    "tillering": "फुटाव",
    "flowering": "फूल आना",
    "fruiting": "फल बनना",
    "maturity": "परिपक्वता",
    "transplanting": "रोपाई",
    "ploughing": "जुताई",
    "land preparation": "भूमि तैयारी",
    "nursery": "नर्सरी",
    "weeding": "निराई",
    "mulching": "मल्चिंग",
    "pruning": "छंटाई",
    "spacing": "दूरी",
    "intercropping": "अंतरफसल",
    "crop rotation": "फसल चक्र",

    # pest & disease
    "pest": "कीट",
    "pest management": "कीट प्रबंधन",
    "disease": "रोग",
    "fungal": "फफूंद",
    "insect": "कीट",
    "spray": "छिड़काव",
    "pesticide": "कीटनाशक",
    "herbicide": "खरपतवारनाशी",
    "fungicide": "फफूंदनाशी",
    "integrated pest management": "समन्वित कीट प्रबंधन",

    # season
    "season": "मौसम",
    "kharif": "खरीफ",
    "rabi": "रबी",
    "zaid": "जायद",
    "summer": "गर्मी",
    "winter": "सर्दी",
    "spring": "बसंत",

    # stage
    "early": "प्रारंभिक",
    "mid": "मध्य",
    "end": "अंतिम",
    "stage": "चरण",

    # analysis
    "ndvi": "एन.डी.वी.आई",
    "vegetation index": "वनस्पति सूचकांक",
    "healthy": "स्वस्थ",
    "moderate": "मध्यम",
    "stress": "तनाव",
    "crop stress": "फसल तनाव",
    "heat stress": "गर्मी का तनाव",
    "drought risk": "सूखे का खतरा",
    "low": "कम",
    "high": "अधिक",
    "medium": "मध्यम",
    "confidence": "विश्वसनीयता",
    "analysis": "विश्लेषण",
    "recommendation": "सिफारिश",
    "alternative": "विकल्प",
    "suitable": "उपयुक्त",
    "not suitable": "उपयुक्त नहीं",
    "allowed": "अनुमत",
    "not allowed": "अनुमत नहीं",

    # general
    "field": "खेत",
    "farmer": "किसान",
    "hectare": "हेक्टेयर",
    "quintal": "क्विंटल",
    "kg/ha": "किलो/हेक्टेयर",
    "days": "दिन",
    "month": "महीना",
    "year": "साल",
    "per": "प्रति",
    "total": "कुल",
    "current": "वर्तमान",
    "next": "अगला",
    "optimal": "अनुकूल",
    "ideal": "आदर्श",
    "critical": "महत्वपूर्ण",
    "recommended": "अनुशंसित",
    "apply": "लगाएं",
    "use": "उपयोग करें",
    "maintain": "बनाए रखें",
    "monitor": "निगरानी करें",
    "prepare": "तैयारी करें",
    "plant": "बोएं",
    "grow": "उगाएं",
    "avoid": "बचें",
    "warning": "चेतावनी",
    "alert": "सूचना",
}

# ── Month Names ───────────────────────────────────────────────────────────────
MONTH_NAMES_HI = {
    "January": "जनवरी", "February": "फरवरी", "March": "मार्च",
    "April": "अप्रैल", "May": "मई", "June": "जून",
    "July": "जुलाई", "August": "अगस्त", "September": "सितंबर",
    "October": "अक्टूबर", "November": "नवंबर", "December": "दिसंबर",
}

# ── Common Phrases ────────────────────────────────────────────────────────────
PHRASES_HI = {
    "sowing allowed": "बुवाई अनुमत",
    "sowing not allowed": "बुवाई अनुमत नहीं",
    "not the right time": "सही समय नहीं है",
    "sowing window has passed": "बुवाई का समय बीत चुका है",
    "not yet started": "अभी शुरू नहीं हुआ",
    "can be sown now": "अभी बुवाई की जा सकती है",
    "alternative crops": "वैकल्पिक फसलें",
    "next season plan": "अगले मौसम की योजना",
    "planning guidance": "योजना मार्गदर्शन",
    "complete farming guide": "संपूर्ण कृषि मार्गदर्शिका",
    "no analysis data": "कोई विश्लेषण डेटा नहीं",
    "run analysis": "विश्लेषण चलाएं",
    "confidence score": "विश्वसनीयता स्कोर",
    "also suitable": "यह भी उपयुक्त",
    "soil moisture critically low": "मिट्टी की नमी गंभीर रूप से कम",
    "immediate irrigation required": "तुरंत सिंचाई आवश्यक",
    "high yield expected": "अधिक उपज की उम्मीद",
    "moderate yield expected": "मध्यम उपज की उम्मीद",
    "low yield expected": "कम उपज की उम्मीद",
    "season is ending": "मौसम समाप्त हो रहा है",
    "start preparing": "तैयारी शुरू करें",
    "focus on harvesting": "कटाई पर ध्यान दें",
    "prepare land": "भूमि तैयार करें",
    "arrange seeds": "बीज की व्यवस्था करें",
    "plan irrigation": "सिंचाई की योजना बनाएं",
    "apply npk": "एन.पी.के. लगाएं",
    "install drip irrigation": "ड्रिप सिंचाई स्थापित करें",
    "use shade nets": "शेड नेट का उपयोग करें",
    "monitor for fungal disease": "फफूंद रोग की निगरानी करें",
}

# ── Season Labels ─────────────────────────────────────────────────────────────
SEASON_LABELS_HI = {
    "Kharif (Monsoon)": "खरीफ (मानसून)",
    "Rabi (Winter)": "रबी (सर्दी)",
    "Zaid (Summer)": "जायद (गर्मी)",
    "Early Kharif (Monsoon)": "प्रारंभिक खरीफ (मानसून)",
    "Mid Kharif (Monsoon)": "मध्य खरीफ (मानसून)",
    "End Kharif (Monsoon)": "अंतिम खरीफ (मानसून)",
    "Early Rabi (Winter)": "प्रारंभिक रबी (सर्दी)",
    "Mid Rabi (Winter)": "मध्य रबी (सर्दी)",
    "End Rabi (Winter)": "अंतिम रबी (सर्दी)",
    "Early Zaid (Summer)": "प्रारंभिक जायद (गर्मी)",
    "Mid Zaid (Summer)": "मध्य जायद (गर्मी)",
    "End Zaid (Summer)": "अंतिम जायद (गर्मी)",
    "June – October": "जून – अक्टूबर",
    "October – March": "अक्टूबर – मार्च",
    "March – June": "मार्च – जून",
}

# Merge all direct-lookup dictionaries into one for fast phrase matching
_ALL_PHRASES_HI = {}
_ALL_PHRASES_HI.update({k.lower(): v for k, v in PHRASES_HI.items()})
_ALL_PHRASES_HI.update({k.lower(): v for k, v in SEASON_LABELS_HI.items()})


# ══════════════════════════════════════════════════════════════════════════════
# TRANSLATION CACHE
# ══════════════════════════════════════════════════════════════════════════════
_translation_cache: dict[str, str] = {}


# ══════════════════════════════════════════════════════════════════════════════
# GOOGLE TRANSLATE FALLBACK (via deep-translator, free)
# ══════════════════════════════════════════════════════════════════════════════

def translate_with_api(text: str, source: str = "en", target: str = "hi") -> str:
    """
    Fallback: call Google Translate via deep-translator for dynamic text.
    Returns original text if translation fails (graceful degradation).
    """
    if not text or len(text.strip()) < 3:
        return text

    # Check cache first
    cache_key = f"{target}:{text}"
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]

    try:
        from deep_translator import GoogleTranslator  # type: ignore
        translator = GoogleTranslator(source=source, target=target)
        translated = translator.translate(text)
        if translated:
            _translation_cache[cache_key] = translated
            return translated
    except Exception as e:
        print(f"[translation] Google Translate failed: {e}")

    return text  # fallback to original


# ══════════════════════════════════════════════════════════════════════════════
# CORE TRANSLATION FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def contains_english(text: str) -> bool:
    """Check if text still contains English alphabetic words (a-z)."""
    if not text:
        return False
    # Remove numbers, units, common codes/abbreviations that are acceptable in Hindi text
    cleaned = re.sub(r'\b[A-Z]{1,5}[-]?\d+\b', '', text)  # variety codes like HD-2967
    cleaned = re.sub(r'\b\d+[\.\d]*\s*(%|°C|mm|kg|ha|L|cm|g|ml|EC|SL|WP|SC|SG)\b', '', cleaned)
    cleaned = re.sub(r'\b(NPK|NDVI|pH|N|P|K|FYM|SRI|IPM|CRI|BPH|HQPM|Bt)\b', '', cleaned)
    cleaned = re.sub(r'[^\w\s]', '', cleaned)  # remove punctuation
    # Check if remaining text has English letters
    english_words = re.findall(r'\b[a-zA-Z]{3,}\b', cleaned)
    return len(english_words) > 2  # allow 1-2 stray codes


def translate_crop_name(crop: str, lang: str = "en") -> str:
    """Translate a crop name consistently."""
    if lang == "en" or not crop:
        return crop
    return CROP_NAMES_HI.get(crop.lower(), crop.capitalize())


def _dictionary_translate(text: str) -> str:
    """
    Apply dictionary-based translation to a string.
    Replaces known crop names, agriculture terms, months, and phrases.
    """
    if not text or not isinstance(text, str):
        return text

    result = text

    # 1. Replace exact phrase matches (longest first to avoid partial matches)
    for eng, hi in sorted(_ALL_PHRASES_HI.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(re.escape(eng), re.IGNORECASE)
        result = pattern.sub(hi, result)

    # 2. Replace season labels
    for eng, hi in sorted(SEASON_LABELS_HI.items(), key=lambda x: len(x[0]), reverse=True):
        result = result.replace(eng, hi)

    # 3. Replace month names
    for eng, hi in MONTH_NAMES_HI.items():
        result = result.replace(eng, hi)

    # 4. Replace crop names (case-insensitive, word boundary)
    for eng, hi in sorted(CROP_NAMES_HI.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(r'\b' + re.escape(eng) + r'\b', re.IGNORECASE)
        result = pattern.sub(hi, result)

    # 5. Replace agriculture terms (case-insensitive, word boundary)
    for eng, hi in sorted(AGRI_TERMS_HI.items(), key=lambda x: len(x[0]), reverse=True):
        pattern = re.compile(r'\b' + re.escape(eng) + r'\b', re.IGNORECASE)
        result = pattern.sub(hi, result)

    return result


def translate_text(text: str, lang: str = "en") -> str:
    """
    Translate a text string to the target language.
    Uses hybrid approach: dictionary first, then LibreTranslate fallback.
    """
    if lang == "en" or not text or not isinstance(text, str):
        return text

    # Check full-text cache
    cache_key = f"{lang}:{text}"
    if cache_key in _translation_cache:
        return _translation_cache[cache_key]

    # Step 1: Dictionary-based translation
    translated = _dictionary_translate(text)

    # Step 2: If still contains significant English, call API
    if contains_english(translated):
        api_result = translate_with_api(text, "en", lang)
        if api_result and api_result != text:
            translated = api_result

    _translation_cache[cache_key] = translated
    return translated


# ── Keys to skip translating (preserve as-is) ────────────────────────────────
_SKIP_KEYS = {
    "id", "_id", "field_id", "farmer_id", "corridor_id", "user_id",
    "created_at", "updated_at", "analyzed_at",
    "coordinates", "boundary", "grid_position", "location", "center",
    "email", "password", "token", "analysis_status",
    # numeric-like keys we want to preserve
    "ndvi", "ndvi_avg", "n", "p", "k", "ph",
    "temperature", "humidity", "rainfall", "soil_moisture",
    "land_surface_temp", "rainfall_probability",
    "crop_confidence", "confidence", "area",
    "healthy_count", "stress_count", "total_corridors",
    "current_month", "lat", "lng",
    "sowing_allowed", "can_start_long_crops",
    "sowing_months",
}


def translate_response(data: Any, lang: str = "en") -> Any:
    """
    Recursively translate all user-facing string values in a response.
    Preserves numeric values, booleans, and structural keys.
    """
    if lang == "en":
        return data

    if isinstance(data, str):
        return translate_text(data, lang)

    if isinstance(data, list):
        return [translate_response(item, lang) for item in data]

    if isinstance(data, dict):
        result: dict[str, Any] = {}
        for key, value in data.items():
            # Skip keys that should not be translated
            if key in _SKIP_KEYS:
                result[key] = value
            elif isinstance(value, (int, float, bool)) or value is None:
                result[key] = value
            elif isinstance(value, str):
                # Translate the "crop" key using crop name dictionary for consistency
                if key == "crop" or key == "crop_name" or key == "recommended_crop" or key == "predicted_crop":
                    result[key] = translate_crop_name(value, lang)
                else:
                    result[key] = translate_text(value, lang)
            elif isinstance(value, (dict, list)):
                result[key] = translate_response(value, lang)
            else:
                result[key] = value
        return result

    return data
