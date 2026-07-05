// ── Live season detection (client-side) ────────────────────────────────────────
// Mirrors backend season_service.py so the UI always shows the real current
// month / season / stage regardless of when the last server-side analysis ran.

const SEASONS_DATA = {
  kharif: {
    label: 'Kharif (Monsoon)', period: 'June – October',
    months: [6,7,8,9,10],
    stages: { early: [6,7], mid: [8,9], end: [10] },
    crops: {
      normal: [
        { crop: 'rice', duration: '120-150 days', type: 'long' },
        { crop: 'maize', duration: '90-120 days', type: 'medium' },
        { crop: 'cotton', duration: '150-180 days', type: 'long' },
        { crop: 'soybean', duration: '85-120 days', type: 'medium' },
        { crop: 'sugarcane', duration: '300-365 days', type: 'long' },
        { crop: 'groundnut', duration: '100-130 days', type: 'medium' },
        { crop: 'bajra', duration: '75-90 days', type: 'short' },
        { crop: 'jowar', duration: '90-110 days', type: 'medium' },
      ],
      short_duration: [
        { crop: 'bajra', duration: '75-90 days', type: 'short' },
        { crop: 'moong', duration: '60-75 days', type: 'short' },
        { crop: 'urad', duration: '70-90 days', type: 'short' },
        { crop: 'cowpea', duration: '60-90 days', type: 'short' },
        { crop: 'maize', duration: '90 days (short var.)', type: 'short' },
      ],
    },
  },
  rabi: {
    label: 'Rabi (Winter)', period: 'October – March',
    months: [10,11,12,1,2,3],
    stages: { early: [10,11], mid: [12,1], end: [2,3] },
    crops: {
      normal: [
        { crop: 'wheat', duration: '120-150 days', type: 'long' },
        { crop: 'mustard', duration: '110-140 days', type: 'medium' },
        { crop: 'barley', duration: '120-140 days', type: 'long' },
        { crop: 'gram', duration: '95-120 days', type: 'medium' },
        { crop: 'peas', duration: '90-120 days', type: 'medium' },
        { crop: 'lentil', duration: '100-130 days', type: 'medium' },
        { crop: 'potato', duration: '80-120 days', type: 'medium' },
      ],
      short_duration: [
        { crop: 'potato', duration: '80-90 days (early var.)', type: 'short' },
        { crop: 'peas', duration: '60-75 days (early var.)', type: 'short' },
        { crop: 'radish', duration: '30-45 days', type: 'short' },
        { crop: 'spinach', duration: '40-50 days', type: 'short' },
        { crop: 'coriander', duration: '40-60 days', type: 'short' },
      ],
    },
  },
  zaid: {
    label: 'Zaid (Summer)', period: 'March – June',
    months: [3,4,5,6],
    stages: { early: [3,4], mid: [5], end: [6] },
    crops: {
      normal: [
        { crop: 'watermelon', duration: '80-100 days', type: 'medium' },
        { crop: 'muskmelon', duration: '70-90 days', type: 'short' },
        { crop: 'cucumber', duration: '45-70 days', type: 'short' },
        { crop: 'moong', duration: '60-75 days', type: 'short' },
        { crop: 'sunflower', duration: '80-100 days', type: 'medium' },
        { crop: 'fodder', duration: '45-60 days', type: 'short' },
        { crop: 'maize', duration: '90-100 days', type: 'medium' },
      ],
      short_duration: [
        { crop: 'cucumber', duration: '45-55 days', type: 'short' },
        { crop: 'muskmelon', duration: '70-80 days', type: 'short' },
        { crop: 'fodder', duration: '45-60 days', type: 'short' },
        { crop: 'moong', duration: '60-65 days', type: 'short' },
      ],
    },
  },
}

const SEASON_ORDER = ['kharif', 'rabi', 'zaid']
const MONTH_NAMES = ['', 'January','February','March','April','May','June','July','August','September','October','November','December']

export function getCurrentSeasonInfo() {
  const now = new Date()
  const month = now.getMonth() + 1 // 1-12
  const monthName = MONTH_NAMES[month]

  // Detect season
  let season
  if ([6,7,8,9].includes(month))       season = 'kharif'
  else if ([11,12,1,2].includes(month)) season = 'rabi'
  else if ([4,5].includes(month))       season = 'zaid'
  else if (month === 10)                season = 'kharif'
  else if (month === 3)                 season = 'rabi'
  else                                  season = 'rabi'

  const data = SEASONS_DATA[season]

  // Detect stage
  let stage = 'mid'
  for (const [stageName, months] of Object.entries(data.stages)) {
    if (months.includes(month)) { stage = stageName; break }
  }

  // Next season
  const idx = SEASON_ORDER.indexOf(season)
  const nextSeason = SEASON_ORDER[(idx + 1) % SEASON_ORDER.length]
  const nextData = SEASONS_DATA[nextSeason]

  // Sowing advice & crops
  let sowingAdvice, recommendedCrops, futurePlan = null
  if (stage === 'early') {
    recommendedCrops = data.crops.normal
    sowingAdvice = `This is the ideal time to sow ${data.label} crops. All normal and long-duration varieties can be planted.`
  } else if (stage === 'mid') {
    recommendedCrops = data.crops.short_duration
    sowingAdvice = `Mid-${data.label} season. It is too late for long-duration crops. Only short-duration varieties (60-90 days) should be planted now.`
  } else {
    recommendedCrops = data.crops.short_duration.slice(0, 2)
    sowingAdvice = `The ${data.label} season is ending. It is not ideal to start new crops now. Focus on harvesting existing crops and preparing land for the upcoming ${nextData.label} season.`
    futurePlan = {
      next_season: nextSeason,
      next_season_label: nextData.label,
      next_season_period: nextData.period,
      recommended_crops: nextData.crops.normal,
      preparation_advice: `Start preparing for ${nextData.label} (${nextData.period}). Begin soil preparation, arrange seeds, and plan irrigation. Recommended crops: ${nextData.crops.normal.slice(0, 5).map(c => c.crop.charAt(0).toUpperCase() + c.crop.slice(1)).join(', ')}.`,
    }
  }

  return {
    current_month: month,
    current_month_name: monthName,
    season,
    season_label: data.label,
    season_period: data.period,
    season_stage: stage,
    season_stage_label: `${stage.charAt(0).toUpperCase() + stage.slice(1)} ${data.label}`,
    sowing_advice: sowingAdvice,
    season_crops: recommendedCrops,
    future_plan: futurePlan,
  }
}

/**
 * Merge live season info into a stored analysis object,
 * overriding all season-related fields with current values.
 */
export function withLiveSeason(storedAnalysis = {}) {
  const live = getCurrentSeasonInfo()
  return {
    ...storedAnalysis,
    current_month: live.current_month,
    current_month_name: live.current_month_name,
    season: live.season,
    season_label: live.season_label,
    season_period: live.season_period,
    season_stage: live.season_stage,
    season_stage_label: live.season_stage_label,
    sowing_advice: live.sowing_advice,
    season_crops: live.season_crops,
    future_plan: live.future_plan,
  }
}
