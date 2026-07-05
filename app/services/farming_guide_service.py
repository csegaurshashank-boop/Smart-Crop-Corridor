"""
app/services/farming_guide_service.py

Detailed crop-specific farming guides with cultivation instructions.
Supports English (default) and Hindi.
"""
from typing import Optional

from app.services.farming_guide_hi import CROP_GUIDES_HI  # type: ignore


# ── Comprehensive Farming Knowledge Base ──────────────────────────────────────
CROP_GUIDES = {
    "wheat": {
        "crop_name": "Wheat",
        "why_suitable": "Wheat thrives in cool, dry climates with moderate rainfall. It requires well-drained loamy or alluvial soil with pH 6.0-7.5. The current soil moisture and temperature conditions on your field are ideal for wheat cultivation during the Rabi season.",
        "land_preparation": [
            "Plough the field 2-3 times to a depth of 20-25 cm to achieve fine tilth",
            "Apply 10-15 tonnes of well-decomposed farmyard manure (FYM) per hectare during last ploughing",
            "Level the field using a laser land leveler for uniform irrigation",
            "Create proper irrigation channels and field bunds",
            "Ensure adequate soil moisture at the time of sowing (field capacity)",
        ],
        "seed_varieties": {
            "irrigated": ["HD-2967", "WH-1105", "PBW-343", "DBW-17", "HD-3086"],
            "rainfed": ["C-306", "K-65", "Lok-1", "HW-2004"],
            "late_sowing": ["HD-2985", "PBW-373", "WH-1080", "DBW-16"],
        },
        "seed_rate": "100-125 kg/ha for normal sowing, 125-150 kg/ha for late sowing",
        "sowing_time": {
            "north_india": "Late October to November (optimal: 1st-25th November)",
            "central_india": "November to early December",
            "late_sowing": "After 25th December (use late sowing varieties)",
        },
        "sowing_depth": "5-6 cm in moist soil, 7-8 cm in dry conditions",
        "spacing": "Row-to-row: 20-22.5 cm, Plant-to-plant: 5-8 cm",
        "fertilizer_plan": {
            "basal": "NPK 60:30:30 kg/ha at sowing time",
            "first_top_dress": "Nitrogen 30 kg/ha at first irrigation (21 days)",
            "second_top_dress": "Nitrogen 30 kg/ha at tillering stage (45 days)",
            "micronutrients": "Zinc Sulphate 25 kg/ha if zinc deficient",
            "total_npk": "N: 120 kg/ha, P: 60 kg/ha, K: 40 kg/ha",
        },
        "irrigation": {
            "total_irrigations": "4-6 irrigations depending on soil and weather",
            "critical_stages": [
                "Crown root initiation (CRI) — 21 days after sowing (MOST CRITICAL)",
                "Tillering stage — 40-45 days after sowing",
                "Late jointing — 60-65 days after sowing",
                "Flowering — 80-85 days after sowing",
                "Milking stage — 100-105 days after sowing",
                "Dough stage — 115-120 days after sowing",
            ],
            "water_requirement": "350-450 mm total water requirement",
        },
        "pest_management": [
            {"pest": "Aphids", "symptoms": "Yellowish colonies on leaves, honeydew secretion", "control": "Spray Imidacloprid 17.8% SL @ 0.3 ml/L or Dimethoate 30 EC @ 1.5 ml/L"},
            {"pest": "Termites", "symptoms": "Wilting and drying of plants in patches", "control": "Seed treatment with Chlorpyriphos 20 EC @ 5 ml/kg seed; soil drench with Chlorpyriphos"},
            {"pest": "Rust (Yellow/Brown)", "symptoms": "Orange-yellow pustules on leaves", "control": "Spray Propiconazole 25 EC @ 1 ml/L or Tebuconazole 25.9% EC @ 1 ml/L"},
            {"pest": "Karnal Bunt", "symptoms": "Black powdery mass in grains", "control": "Use resistant varieties, seed treatment with Thiram @ 2.5 g/kg"},
            {"pest": "Powdery Mildew", "symptoms": "White cottony growth on leaves", "control": "Spray Sulphur 80 WP @ 2.5 g/L water"},
        ],
        "expected_yield": {
            "irrigated": "45-55 quintals/ha with improved varieties",
            "rainfed": "20-30 quintals/ha",
            "potential": "Up to 65 quintals/ha with optimal management",
        },
        "harvest_time": "120-150 days after sowing; when grain moisture is 12-14%",
    },

    "rice": {
        "crop_name": "Rice (Paddy)",
        "why_suitable": "Rice requires warm, humid conditions with temperatures between 22-35°C and high rainfall (150-400 mm). Your field's soil moisture levels and temperature profile are well-suited for paddy cultivation during the Kharif season.",
        "land_preparation": [
            "Plough the field 2-3 times when soil is moist (puddling)",
            "Apply 10-12 tonnes FYM per hectare before last puddling",
            "Level the field and create bunds for water retention",
            "Maintain 2-5 cm standing water during puddling",
            "Prepare nursery beds: 1/10th of main field area, raised 10-15 cm",
        ],
        "seed_varieties": {
            "high_yield": ["Pusa Basmati-1121", "IR-64", "Samba Mahsuri", "Swarna"],
            "aromatic": ["Pusa Basmati-1509", "Pusa-1121", "Taraori Basmati"],
            "short_duration": ["PR-126", "Pusa-44", "Sahbhagi Dhan"],
        },
        "seed_rate": "20-25 kg/ha for transplanting (nursery), 80-100 kg/ha for direct seeding",
        "sowing_time": {
            "nursery": "May-June (3-4 weeks before transplanting)",
            "transplanting": "June-July (when seedlings are 21-25 days old)",
            "direct_seeding": "June (with onset of monsoon)",
        },
        "sowing_depth": "2-3 cm in nursery; transplant seedlings at 3-4 cm depth",
        "spacing": "Row-to-row: 20 cm, Plant-to-plant: 15 cm (2-3 seedlings/hill)",
        "fertilizer_plan": {
            "basal": "NPK 40:30:20 kg/ha at transplanting",
            "first_top_dress": "Nitrogen 40 kg/ha at tillering (21 days after transplanting)",
            "second_top_dress": "Nitrogen 40 kg/ha at panicle initiation (42 days)",
            "micronutrients": "Zinc Sulphate 25 kg/ha in zinc-deficient soils",
            "total_npk": "N: 120 kg/ha, P: 60 kg/ha, K: 40 kg/ha",
        },
        "irrigation": {
            "total_irrigations": "Continuous flooding or alternate wetting-drying",
            "critical_stages": [
                "Transplanting — maintain 2-3 cm standing water",
                "Tillering — 15-20 days, maintain 5 cm water",
                "Panicle initiation — CRITICAL, 5-7 cm water",
                "Flowering — 5-7 cm standing water (most sensitive to drought)",
                "Grain filling — gradual reduction of water",
            ],
            "water_requirement": "1200-1400 mm total (highest among cereals)",
        },
        "pest_management": [
            {"pest": "Brown Plant Hopper (BPH)", "symptoms": "Hopperburn, circular patches of dried plants", "control": "Avoid excess nitrogen, spray Buprofezin 25 SC @ 2 ml/L"},
            {"pest": "Stem Borer", "symptoms": "Dead hearts in vegetative stage, white earheads", "control": "Install pheromone traps, spray Cartap Hydrochloride 4G @ 25 kg/ha"},
            {"pest": "Blast", "symptoms": "Diamond-shaped lesions on leaves", "control": "Spray Tricyclazole 75 WP @ 0.6 g/L or Isoprothiolane 40 EC @ 1.5 ml/L"},
            {"pest": "Sheath Blight", "symptoms": "Irregular greenish-grey lesions on sheath", "control": "Spray Hexaconazole 5 EC @ 2 ml/L"},
        ],
        "expected_yield": {
            "irrigated": "50-65 quintals/ha with HYV",
            "rainfed": "25-35 quintals/ha",
            "potential": "Up to 80 quintals/ha with SRI method",
        },
        "harvest_time": "110-150 days after transplanting; when 80% grains turn golden",
    },

    "maize": {
        "crop_name": "Maize (Corn)",
        "why_suitable": "Maize is versatile and adapts to various conditions. It requires well-drained loamy soil and moderate temperatures (18-32°C). Your field conditions support excellent maize growth.",
        "land_preparation": [
            "Deep ploughing to 25-30 cm depth",
            "Apply 8-10 tonnes FYM per hectare",
            "Create ridges and furrows for drainage",
            "Ensure well-pulverized seedbed",
        ],
        "seed_varieties": {
            "hybrid": ["HQPM-1", "PEHM-2", "Vivek-27", "DHM-117"],
            "composite": ["Navjot", "Prabhat", "Kisan", "Jawahar"],
        },
        "seed_rate": "18-20 kg/ha for hybrid, 20-25 kg/ha for composite varieties",
        "sowing_time": {
            "kharif": "June-July with onset of monsoon",
            "rabi": "October-November (winter maize)",
            "spring": "January-February in irrigated areas",
        },
        "sowing_depth": "5-7 cm",
        "spacing": "Row-to-row: 60-75 cm, Plant-to-plant: 20-25 cm",
        "fertilizer_plan": {
            "basal": "NPK 40:40:20 kg/ha at sowing",
            "first_top_dress": "Nitrogen 40 kg/ha at knee-high stage (25-30 days)",
            "second_top_dress": "Nitrogen 40 kg/ha at tasseling (45-50 days)",
            "total_npk": "N: 120 kg/ha, P: 60 kg/ha, K: 40 kg/ha",
        },
        "irrigation": {
            "total_irrigations": "5-6 irrigations",
            "critical_stages": [
                "Knee-high stage — 25-30 days",
                "Tasseling — 45-50 days (MOST CRITICAL)",
                "Silking and pollination — 55-60 days",
                "Grain filling — 70-80 days",
            ],
            "water_requirement": "500-600 mm total water",
        },
        "pest_management": [
            {"pest": "Fall Armyworm", "symptoms": "Window-pane damage on leaves, frass in whorl", "control": "Spray Emamectin Benzoate 5 SG @ 0.4 g/L + Neem oil 1%"},
            {"pest": "Stem Borer", "symptoms": "Dead hearts, bore holes in stem", "control": "Apply Carbofuran 3G granules in whorl @ 8-10 kg/ha"},
            {"pest": "Turcicum Leaf Blight", "symptoms": "Long elliptical grey-green lesions", "control": "Spray Mancozeb 75 WP @ 2.5 g/L"},
        ],
        "expected_yield": {
            "irrigated": "50-70 quintals/ha with hybrid varieties",
            "rainfed": "30-40 quintals/ha",
            "potential": "Up to 90 quintals/ha with optimal management",
        },
        "harvest_time": "90-120 days; when husk turns brown and grain is hard",
    },

    "cotton": {
        "crop_name": "Cotton",
        "why_suitable": "Cotton requires warm climate (25-35°C) and moderate rainfall. Black or alluvial soil with good drainage is ideal. Your field conditions support cotton cultivation.",
        "land_preparation": [
            "Deep ploughing during summer for moisture conservation",
            "Apply 10 tonnes FYM per hectare",
            "Form ridges and furrows at 90-100 cm spacing",
            "Pre-sowing irrigation (rauni) for uniform germination",
        ],
        "seed_varieties": {
            "bt_hybrid": ["Bollgard-II", "RCH-2", "MRC-7351", "JKCH-1947"],
            "non_bt": ["Suraj", "Khandwa-2", "JK-4"],
        },
        "seed_rate": "2.5-3.0 kg/ha for Bt hybrid (450g/packet)",
        "sowing_time": {"kharif": "April-May (irrigated), June-July (rainfed)"},
        "sowing_depth": "3-5 cm",
        "spacing": "Row-to-row: 90-100 cm, Plant-to-plant: 45-60 cm",
        "fertilizer_plan": {
            "basal": "NPK 30:20:10 kg/ha at sowing",
            "top_dress_1": "Nitrogen 30 kg/ha at squaring (40-45 days)",
            "top_dress_2": "Nitrogen 20 kg/ha at flowering (60-65 days)",
            "total_npk": "N: 80 kg/ha, P: 40 kg/ha, K: 20 kg/ha",
        },
        "irrigation": {
            "total_irrigations": "6-8 irrigations",
            "critical_stages": [
                "Squaring stage (40-45 days)",
                "Flowering (60-70 days) — CRITICAL",
                "Boll development (80-100 days)",
            ],
            "water_requirement": "700-800 mm",
        },
        "pest_management": [
            {"pest": "Pink Bollworm", "symptoms": "Rosetted flowers, damaged bolls", "control": "Pheromone traps + Quinalphos 25 EC @ 2 ml/L"},
            {"pest": "Whitefly", "symptoms": "Leaf yellowing, sooty mold", "control": "Spray Diafenthiuron 50 WP @ 1.2 g/L"},
            {"pest": "Jassids", "symptoms": "Leaf reddening, curling", "control": "Neem oil spray + Imidacloprid 17.8 SL @ 0.3 ml/L"},
        ],
        "expected_yield": {
            "irrigated": "20-25 quintals lint/ha with Bt hybrid",
            "rainfed": "8-12 quintals lint/ha",
            "potential": "Up to 30 quintals lint/ha",
        },
        "harvest_time": "150-180 days; pick bolls when they burst open fully",
    },

    "sugarcane": {
        "crop_name": "Sugarcane",
        "why_suitable": "Sugarcane thrives in hot, humid conditions with rich alluvial or loamy soil. It requires high rainfall and long growing period. Your field conditions are suitable.",
        "land_preparation": [
            "Deep ploughing 30-40 cm, cross ploughing twice",
            "Apply 15-20 tonnes FYM/ha, mix thoroughly",
            "Create furrows 75-90 cm apart, 20 cm deep",
            "Apply pre-emergent herbicide after planting",
        ],
        "seed_varieties": {
            "early": ["CoJ-64", "CoS-767", "BO-91"],
            "mid_late": ["CoS-8436", "CoSe-95422", "UP-0097"],
        },
        "seed_rate": "6-8 tonnes setts/ha (3-budded setts)",
        "sowing_time": {"spring": "February-March", "autumn": "October-November"},
        "sowing_depth": "7-10 cm in furrows",
        "spacing": "Row-to-row: 75-90 cm",
        "fertilizer_plan": {
            "basal": "NPK 50:60:40 kg/ha in furrows",
            "top_dress_1": "Nitrogen 75 kg/ha at tillering (45-60 days)",
            "top_dress_2": "Nitrogen 75 kg/ha at grand growth (90 days)",
            "total_npk": "N: 200-250 kg/ha, P: 60 kg/ha, K: 60 kg/ha",
        },
        "irrigation": {
            "total_irrigations": "8-12 irrigations",
            "critical_stages": [
                "Germination (1-30 days)",
                "Tillering (45-120 days) — CRITICAL",
                "Grand growth phase (120-270 days) — HEAVY irrigation needed",
            ],
            "water_requirement": "1800-2200 mm (very high)",
        },
        "pest_management": [
            {"pest": "Early Shoot Borer", "symptoms": "Dead hearts in young shoots", "control": "Apply Carbofuran 3G @ 30 kg/ha in soil around roots"},
            {"pest": "Top Borer", "symptoms": "Dead heart with side shoots (bunchy top)", "control": "Remove infested shoots, spray Monocrotophos 36 SL"},
            {"pest": "Red Rot", "symptoms": "Yellowing of leaves, red internal tissue", "control": "Use resistant varieties, hot water treatment of setts at 50°C for 2 hrs"},
        ],
        "expected_yield": {
            "irrigated": "800-1000 quintals/ha (cane yield)",
            "rainfed": "400-600 quintals/ha",
            "potential": "Up to 1500 quintals/ha with optimal management",
        },
        "harvest_time": "10-14 months; when Brix reading is 18-20%",
    },

    "soybean": {
        "crop_name": "Soybean",
        "why_suitable": "Soybean adapts well to warm, moist conditions. It fixes atmospheric nitrogen and improves soil health. Ideal for well-drained loamy or clay-loam soils with pH 6.0-7.5.",
        "land_preparation": [
            "Plough field 2-3 times to create fine tilth",
            "Apply 5 tonnes FYM/ha before last ploughing",
            "Seed treatment with Rhizobium culture (200g/10 kg seed)",
            "Treat seeds with Thiram @ 2g/kg + Carbendazim 1g/kg before sowing",
        ],
        "seed_varieties": {
            "high_yield": ["JS-9560", "JS-335", "NRC-86", "MAUS-71"],
            "early_maturing": ["JS-9752", "NRC-37", "MACS-450"],
        },
        "seed_rate": "60-75 kg/ha",
        "sowing_time": {"kharif": "June 20 – July 10 (with onset of monsoon)"},
        "sowing_depth": "3-4 cm",
        "spacing": "Row-to-row: 30-45 cm, Plant-to-plant: 5-7 cm",
        "fertilizer_plan": {
            "basal": "NPK 20:60:20 kg/ha at sowing (low N due to nitrogen fixation)",
            "total_npk": "N: 20 kg/ha, P: 60 kg/ha, K: 20 kg/ha",
        },
        "irrigation": {
            "total_irrigations": "1-2 irrigations if monsoon gaps",
            "critical_stages": [
                "Flowering (35-40 days) — CRITICAL for pod setting",
                "Pod development (50-60 days)",
            ],
            "water_requirement": "350-500 mm (mostly rainfed)",
        },
        "pest_management": [
            {"pest": "Girdle Beetle", "symptoms": "Girdles on stem and petioles", "control": "Spray Triazophos 40 EC @ 1.5 ml/L at 20-25 DAS"},
            {"pest": "Leaf Defoliators", "symptoms": "Feeding on leaves, skeletonization", "control": "Spray Quinalphos 25 EC @ 2 ml/L"},
            {"pest": "Yellow Mosaic Virus", "symptoms": "Yellow mottling on leaves", "control": "Use resistant varieties, control whitefly vector"},
        ],
        "expected_yield": {
            "irrigated": "20-25 quintals/ha",
            "rainfed": "12-18 quintals/ha",
            "potential": "Up to 30 quintals/ha",
        },
        "harvest_time": "85-120 days; when 95% pods turn brown and leaves shed",
    },

    "mustard": {
        "crop_name": "Mustard (Sarson)",
        "why_suitable": "Mustard is a premier Rabi oilseed crop that grows well in cool, dry climates (15–25°C). It tolerates moderate drought and thrives in well-drained loamy or sandy-loam soils.",
        "land_preparation": [
            "Plough field 2-3 times to fine tilth after kharif harvest",
            "Apply 8-10 tonnes FYM per hectare before last ploughing",
            "Level field and create proper drainage channels",
            "Ensure soil moisture is adequate at sowing (pre-sowing irrigation if needed)",
        ],
        "seed_varieties": {
            "high_yield": ["Pusa Bold", "RH-30", "Varuna", "Pusa Agrani"],
            "early_maturing": ["Kranti", "Maya", "Pusa Mustard-25"],
        },
        "seed_rate": "4-5 kg/ha (line sowing); 3-4 kg/ha with seed drill",
        "sowing_time": {
            "north_india": "October 1–15 (optimal); late sowing after Oct 25 reduces yield",
            "central_india": "October 15 – November 5",
        },
        "sowing_depth": "2-3 cm",
        "spacing": "Row-to-row: 30–45 cm, Plant-to-plant: 10–15 cm",
        "fertilizer_plan": {
            "basal": "NPK 40:20:0 kg/ha at sowing",
            "top_dress": "Nitrogen 40 kg/ha at first irrigation (25-30 DAS)",
            "sulphur": "Gypsum 200 kg/ha or Elemental Sulphur 20 kg/ha for better oil content",
            "total_npk": "N: 80 kg/ha, P: 40 kg/ha, S: 20 kg/ha",
        },
        "irrigation": {
            "total_irrigations": "2-3 irrigations",
            "critical_stages": [
                "First: 25-30 DAS — rosette stage (MOST CRITICAL)",
                "Second: 55-60 DAS — flowering stage",
                "Third: 80-85 DAS — pod filling stage",
            ],
            "water_requirement": "250-350 mm",
        },
        "pest_management": [
            {"pest": "Aphids", "symptoms": "Black colonies on stem/pods, leaf curling", "control": "Spray Dimethoate 30 EC @ 1.5 ml/L or Imidacloprid 0.3 ml/L at first sign"},
            {"pest": "Sawfly", "symptoms": "Caterpillars feeding on leaves causing skeletonization", "control": "Spray Quinalphos 25 EC @ 2 ml/L"},
            {"pest": "White Rust / Alternaria Blight", "symptoms": "White pustules or dark brown spots on leaves", "control": "Spray Mancozeb 75 WP @ 2.5 g/L"},
        ],
        "expected_yield": {
            "irrigated": "18-22 quintals/ha with improved varieties",
            "rainfed": "8-12 quintals/ha",
            "potential": "Up to 28 quintals/ha",
        },
        "harvest_time": "110-140 days; when 75% pods turn yellow-brown. Harvest early morning to avoid pod shattering.",
    },

    "gram": {
        "crop_name": "Gram (Chickpea / Chana)",
        "why_suitable": "Gram is India's most important Rabi pulse. It fixes atmospheric nitrogen, improving soil health. It requires cool weather (10–25°C) and well-drained loamy or sandy-loam soil with pH 6.0–8.0.",
        "land_preparation": [
            "Plough field 2-3 times to fine tilth after kharif",
            "Apply 4-5 tonnes FYM per hectare (avoid excess nitrogen)",
            "Seed treatment with Rhizobium culture @ 200 g/10 kg seed is ESSENTIAL",
            "Treat with Thiram 2 g/kg + Carbendazim 1 g/kg for fungal protection",
        ],
        "seed_varieties": {
            "desi": ["JG-16", "JG-74", "Pusa-256", "JAKI-9218"],
            "kabuli": ["Pusa-1003", "KWR-108", "HK-94-134"],
        },
        "seed_rate": "60-80 kg/ha (desi); 100-120 kg/ha (kabuli varieties)",
        "sowing_time": {
            "north_india": "Late October – mid November",
            "central_india": "October 25 – November 15",
        },
        "sowing_depth": "7-10 cm",
        "spacing": "Row-to-row: 30 cm, Plant-to-plant: 10 cm",
        "fertilizer_plan": {
            "basal": "NPK 20:40:20 kg/ha at sowing",
            "note": "Do NOT apply excess Nitrogen — inhibits natural N-fixation by Rhizobium",
            "sulphur": "Sulphur 20 kg/ha on deficient soils",
            "total_npk": "N: 20 kg/ha, P: 40 kg/ha, K: 20 kg/ha",
        },
        "irrigation": {
            "total_irrigations": "1-2 (rainfed crop; irrigate only at critical stages)",
            "critical_stages": [
                "30-35 DAS: Pre-flowering (if dry spell occurs)",
                "70-75 DAS: Pod filling stage (CRITICAL if no rainfall)",
            ],
            "water_requirement": "250-400 mm",
        },
        "pest_management": [
            {"pest": "Gram Pod Borer (Helicoverpa)", "symptoms": "Circular holes in pods; caterpillars feed on developing seeds", "control": "Spray Emamectin Benzoate 5 SG @ 0.4 g/L or Indoxacarb @ 0.7 ml/L"},
            {"pest": "Wilt (Fusarium)", "symptoms": "Sudden wilting; browning of vascular tissue", "control": "Use resistant varieties; Trichoderma viride seed treatment"},
            {"pest": "Ascochyta Blight", "symptoms": "Circular lesions on leaves and pods", "control": "Spray Mancozeb 75 WP @ 2.5 g/L at 10-day intervals"},
        ],
        "expected_yield": {
            "irrigated": "18-25 quintals/ha",
            "rainfed": "10-15 quintals/ha",
            "potential": "Up to 35 quintals/ha with kabuli varieties",
        },
        "harvest_time": "90-110 days (desi); 110-130 days (kabuli). Harvest when 75% pods turn brown.",
    },

    "groundnut": {
        "crop_name": "Groundnut (Peanut / Moongphali)",
        "why_suitable": "Groundnut is South India's premier oilseed crop. It fixes nitrogen, thrives in red sandy-loam soils, and performs best in warm conditions (24–35°C) during the Rabi/summer seasons.",
        "land_preparation": [
            "Deep ploughing 20-25 cm to loosen soil for pod development underground",
            "Apply 5-8 tonnes FYM per hectare and mix thoroughly",
            "Form ridges or raised beds for drainage management",
            "Apply Gypsum 500 kg/ha at pegging stage for better pod filling",
        ],
        "seed_varieties": {
            "bunch_type": ["TAG-24", "ICGS-44", "GG-2", "TG-37A"],
            "spreading_type": ["TMV-2", "CO-1", "JL-24", "DH-86"],
        },
        "seed_rate": "80-100 kg/ha (shelled kernel)",
        "sowing_time": {
            "rabi_south": "October – November (main season in South India)",
            "kharif": "June – July with monsoon onset",
            "summer": "January – February in irrigated areas",
        },
        "sowing_depth": "5-7 cm",
        "spacing": "Row-to-row: 30 cm, Plant-to-plant: 10 cm",
        "fertilizer_plan": {
            "basal": "NPK 20:40:20 kg/ha at sowing",
            "gypsum": "Gypsum 500 kg/ha at pegging (30-35 DAS) — ESSENTIAL for pod filling",
            "boron": "Borax 10 kg/ha soil application for pod quality",
            "total_npk": "N: 20 kg/ha, P: 40 kg/ha, K: 20 kg/ha",
        },
        "irrigation": {
            "total_irrigations": "6-8 irrigations",
            "critical_stages": [
                "Germination (0-10 DAS) — light irrigation",
                "Flowering (25-35 DAS) — CRITICAL",
                "Pegging (35-45 DAS) — CRITICAL",
                "Pod development (50-80 DAS) — consistent moisture",
                "Withhold irrigation 2 weeks before harvest",
            ],
            "water_requirement": "400-500 mm",
        },
        "pest_management": [
            {"pest": "Leaf Miner", "symptoms": "Serpentine mines on leaves", "control": "Spray Dimethoate 30 EC @ 1.5 ml/L at 15-day intervals"},
            {"pest": "Tikka Disease (Cercospora)", "symptoms": "Brown circular leaf spots with yellow halo", "control": "Spray Mancozeb 75 WP @ 2.5 g/L from 30 DAS at 15-day intervals"},
            {"pest": "White Grub", "symptoms": "Plants wilting in patches; pod damage", "control": "Soil drench with Chlorpyrifos 20 EC @ 4 ml/L"},
        ],
        "expected_yield": {
            "irrigated": "25-35 quintals/ha pods",
            "rainfed": "12-18 quintals/ha",
            "potential": "Up to 45 quintals/ha",
        },
        "harvest_time": "120-130 days (bunch type); 140-160 days (spreading). Harvest when 70% pods show dark veins on inner surface.",
    },

    "watermelon": {
        "crop_name": "Watermelon (Tarbuj)",
        "why_suitable": "Watermelon is the ideal Zaid crop, thriving in hot, sunny conditions (28–40°C) with low humidity. It requires well-drained sandy-loam soil and produces high market returns in the summer season.",
        "land_preparation": [
            "Deep plough 30 cm; prepare raised beds 60 cm wide or dig ring pits (60×45 cm)",
            "Apply 20-25 tonnes FYM per hectare; mix thoroughly in bed/pit soil",
            "Mulching with black polyethylene film reduces weeds and conserves moisture",
            "Ensure excellent drainage — waterlogging is fatal to watermelon",
        ],
        "seed_varieties": {
            "hybrid": ["Shugarbaby", "Arka Manik", "NS-295", "Asahi Yamato"],
            "open_pollinated": ["Durgapura Kesar", "Pusa Bedana", "Arka Jyoti"],
        },
        "seed_rate": "3-4 kg/ha (open pollinated); 500 g/ha (hybrid)",
        "sowing_time": {"zaid": "February – March (plains); harvest May–June"},
        "sowing_depth": "2-3 cm; 2 seeds per pit, thin to 1 after germination",
        "spacing": "Row-to-row: 2.0–2.5 m, Pit-to-pit: 0.5–0.75 m",
        "fertilizer_plan": {
            "basal": "NPK 30:30:30 kg/ha + FYM in pits at sowing",
            "top_dress_1": "Nitrogen 30 kg/ha at runner stage (20-25 DAS)",
            "top_dress_2": "Potassium 30 kg/ha at fruit set — improves sweetness",
            "total_npk": "N: 80 kg/ha, P: 40 kg/ha, K: 60 kg/ha",
        },
        "irrigation": {
            "total_irrigations": "8-10 irrigations (drip preferred)",
            "critical_stages": [
                "Germination (light daily irrigation for 7-10 days)",
                "Vine development (20-30 DAS)",
                "Flowering (35-45 DAS) — CRITICAL",
                "Fruit set and filling (50-70 DAS) — CRITICAL",
                "Stop irrigation 10 days before harvest for maximum sweetness",
            ],
            "water_requirement": "400-600 mm",
        },
        "pest_management": [
            {"pest": "Red Pumpkin Beetle", "symptoms": "Holes in cotyledon and young leaves", "control": "Spray Carbaryl 50 WP @ 2 g/L; hand-pick beetles early morning"},
            {"pest": "Aphids & Whitefly", "symptoms": "Leaf curling, virus transmission", "control": "Spray Imidacloprid 17.8 SL @ 0.3 ml/L; yellow sticky traps"},
            {"pest": "Fruit Fly", "symptoms": "Maggots inside fruit, rotting and premature drop", "control": "Malathion bait traps; bag young fruits with paper"},
            {"pest": "Downy Mildew", "symptoms": "Yellow angular spots on upper leaf surface", "control": "Spray Mancozeb 75 WP @ 2.5 g/L preventively"},
        ],
        "expected_yield": {
            "open_pollinated": "200-350 quintals/ha",
            "hybrid": "350-500 quintals/ha",
            "potential": "Up to 600 quintals/ha with drip + hybrid",
        },
        "harvest_time": "70-90 days from sowing. Ready when tendril near fruit dries, fruit bottom turns creamy yellow, and hollow sound on tapping.",
    },

    "cucumber": {
        "crop_name": "Cucumber (Kheera)",
        "why_suitable": "Cucumber is a quick-return Zaid vegetable that thrives in warm summers (25–38°C). It is ideal for well-drained sandy-loam soil and generates excellent market returns in the summer season.",
        "land_preparation": [
            "Plough 2-3 times to fine tilth; prepare raised beds 60 cm wide",
            "Apply 15-20 tonnes FYM per hectare and mix thoroughly",
            "Ensure soil pH of 6.0–7.0 for optimal nutrient uptake",
            "Create proper drainage channels to prevent waterlogging",
        ],
        "seed_varieties": {
            "hybrid": ["Pusa Uday", "KH-2", "Malini", "Sheetal"],
            "open_pollinated": ["Pusa Sanyog", "Himangi", "Straight Eight", "Poinsett-76"],
        },
        "seed_rate": "2-3 kg/ha",
        "sowing_time": {"summer_zaid": "February – March (harvest April–May)", "rainy": "June – July"},
        "sowing_depth": "2-3 cm; 2-3 seeds per hill, thin to 1-2 plants",
        "spacing": "Row-to-row: 1.5 m, Hill-to-hill: 60 cm",
        "fertilizer_plan": {
            "basal": "NPK 40:30:30 kg/ha mixed in soil before sowing",
            "top_dress_1": "Nitrogen 20 kg/ha at vine initiation (15-20 DAS)",
            "top_dress_2": "Nitrogen 20 kg/ha at fruiting (35-40 DAS)",
            "total_npk": "N: 80 kg/ha, P: 30 kg/ha, K: 30 kg/ha",
        },
        "irrigation": {
            "total_irrigations": "8-10 irrigations",
            "critical_stages": [
                "Germination (light irrigation daily for 5-7 days)",
                "Vine initiation (15-20 DAS)",
                "Flowering (30-35 DAS) — CRITICAL",
                "Fruit development (40-55 DAS) — maintain consistent moisture",
            ],
            "water_requirement": "300-450 mm",
        },
        "pest_management": [
            {"pest": "Red Pumpkin Beetle", "symptoms": "Holes in leaves and cotyledons", "control": "Spray Carbaryl 50 WP @ 2 g/L; hand-pick beetles"},
            {"pest": "Aphids", "symptoms": "Leaf curling, honeydew, mosaic virus spread", "control": "Spray Dimethoate 30 EC @ 1.5 ml/L"},
            {"pest": "Powdery Mildew", "symptoms": "White powdery growth on leaves", "control": "Spray Sulphur 80 WP @ 2.5 g/L"},
            {"pest": "Downy Mildew", "symptoms": "Yellow spots on upper leaf surface", "control": "Spray Metalaxyl + Mancozeb @ 2 g/L"},
        ],
        "expected_yield": {
            "open_pollinated": "150-200 quintals/ha",
            "hybrid": "200-300 quintals/ha",
            "potential": "Up to 350 quintals/ha with trellis + drip",
        },
        "harvest_time": "50-65 days from sowing. Harvest every 2-3 days when fruits are dark green, firm, and 8-12 cm long.",
    },

    "muskmelon": {
        "crop_name": "Muskmelon (Kharbooja)",
        "why_suitable": "Muskmelon is a premium summer fruit that demands hot, dry Zaid conditions (28–40°C) with low humidity. It produces excellent yields in well-drained sandy-loam or alluvial soils with high solar radiation.",
        "land_preparation": [
            "Deep plough 30 cm; prepare raised beds 60–90 cm wide or ring pits (60×45 cm)",
            "Apply 20-25 tonnes FYM per hectare — critical for fruit quality and sweetness",
            "Mulch with silver-black polyfilm to conserve moisture and reduce weeds",
            "Ensure excellent drainage — root rot in waterlogged conditions",
        ],
        "seed_varieties": {
            "hybrid": ["Pusa Sharbati", "MH-10", "NS-910", "Punjab Sunehri"],
            "open_pollinated": ["Hara Madhu", "Durgapura Madhu", "Punjab Hybrid-1"],
        },
        "seed_rate": "2-3 kg/ha",
        "sowing_time": {"zaid": "February – March; harvest May – June"},
        "sowing_depth": "2-3 cm; 2 seeds per pit",
        "spacing": "Row-to-row: 2.0–2.5 m, Pit-to-pit: 60–75 cm",
        "fertilizer_plan": {
            "basal": "NPK 30:30:30 kg/ha + FYM in pits at sowing",
            "top_dress_1": "Nitrogen 30 kg/ha at runner stage (20-25 DAS)",
            "top_dress_2": "Potassium 30 kg/ha at fruit set — boosts sugar content",
            "total_npk": "N: 60 kg/ha, P: 30 kg/ha, K: 60 kg/ha",
        },
        "irrigation": {
            "total_irrigations": "8-12 irrigations (drip preferred)",
            "critical_stages": [
                "Germination to vine stage (light daily irrigation)",
                "Flowering (30-40 DAS) — CRITICAL",
                "Fruit set and development (45-65 DAS) — CRITICAL",
                "Stop irrigation 10-15 days before harvest — maximises Brix/sweetness",
            ],
            "water_requirement": "350-500 mm",
        },
        "pest_management": [
            {"pest": "Red Pumpkin Beetle", "symptoms": "Holes in young leaves", "control": "Spray Carbaryl 50 WP @ 2 g/L"},
            {"pest": "Fruit Fly", "symptoms": "Maggots inside fruit, rotting", "control": "Malathion bait traps; paper bag young fruits"},
            {"pest": "Powdery Mildew", "symptoms": "White powder coating on leaves", "control": "Spray Sulphur 80 WP @ 2.5 g/L preventively"},
        ],
        "expected_yield": {
            "open_pollinated": "150-250 quintals/ha",
            "hybrid": "250-350 quintals/ha",
            "potential": "Up to 400 quintals/ha",
        },
        "harvest_time": "80-100 days from sowing. Harvest when netting fully develops, stem slips from fruit easily, and sweet aroma is detected.",
    },
}



def get_farming_guide(crop: str, season: Optional[str] = None, soil_type: Optional[str] = None, area: Optional[float] = None, lang: str = "en") -> dict:
    """
    Get detailed farming guide for a crop.
    Returns complete cultivation instructions in the requested language.
    """
    crop_lower = crop.lower()

    # Pick the right language guide source
    if lang == "hi" and crop_lower in CROP_GUIDES_HI:
        guide = CROP_GUIDES_HI.get(crop_lower)
    else:
        guide = CROP_GUIDES.get(crop_lower)

    if not guide:
        # generic fallback
        if lang == "hi":
            return {
                "crop_name": crop.capitalize(),
                "why_suitable": f"{crop.capitalize()} आपके खेत की मिट्टी, जलवायु और NDVI विश्लेषण के आधार पर अनुशंसित है।",
                "land_preparation": [
                    "बारीक भुरभुरी बीज शैय्या के लिए 2-3 बार जुताई करें",
                    "8-10 टन गोबर की खाद प्रति हेक्टेयर डालें",
                    "समान सिंचाई के लिए खेत समतल करें",
                    "उचित जल निकासी नालियां बनाएं",
                ],
                "seed_rate": "सही बीज दर के लिए स्थानीय कृषि विस्तार कार्यालय से संपर्क करें",
                "sowing_time": {"अनुशंसित": f"{'वर्तमान' if not season else season} मौसम में बुवाई करें"},
                "fertilizer_plan": {"सिफारिश": "सही उर्वरक खुराक के लिए मिट्टी परीक्षण कराएं"},
                "pest_management": [{"pest": "सामान्य", "symptoms": "नियमित निगरानी करें", "control": "समन्वित कीट प्रबंधन (IPM) अपनाएं"}],
                "expected_yield": {"सामान्य": "किस्म और प्रबंधन पर निर्भर"},
                "harvest_time": "फसल परिपक्वता पर कटाई करें",
            }
        return {
            "crop_name": crop.capitalize(),
            "why_suitable": f"{crop.capitalize()} is recommended based on your field's soil conditions, climate, and NDVI analysis.",
            "land_preparation": [
                "Plough the field 2-3 times to achieve fine tilth",
                "Apply 8-10 tonnes farmyard manure per hectare",
                "Level the field for uniform irrigation",
                "Create proper drainage channels",
            ],
            "seed_rate": "Consult local agricultural extension office for exact seed rate",
            "sowing_time": {"recommended": f"Sow during the {'current' if not season else season} season"},
            "sowing_depth": "3-5 cm depending on soil moisture",
            "fertilizer_plan": {"recommendation": "Get soil tested for precise fertilizer dosage"},
            "pest_management": [{"pest": "General", "symptoms": "Monitor regularly", "control": "Use integrated pest management (IPM) practices"}],
            "expected_yield": {"general": "Depends on variety and management practices"},
            "harvest_time": "Harvest when crop reaches physiological maturity",
        }

    result = dict(guide)  # copy

    # Add context
    if season:
        result["current_season"] = season
    if soil_type:
        result["field_soil_type"] = soil_type
    if area:
        result["field_area_ha"] = area  # type: ignore
        # Calculate seed and fertilizer for actual area
        sr: str = str(guide.get("seed_rate", ""))
        if "kg/ha" in sr or "किलो/हेक्टेयर" in sr:
            try:
                base = float(sr.split("-")[0].strip())
                if lang == "hi":
                    result["seed_quantity_for_field"] = f"{area} हेक्टेयर के लिए {round(base * area, 1)} किलो"  # type: ignore
                else:
                    result["seed_quantity_for_field"] = f"{round(base * area, 1)} kg for {area} ha"  # type: ignore
            except Exception:
                pass

    return result

