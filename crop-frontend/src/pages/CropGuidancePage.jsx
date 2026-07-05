import React, { useEffect, useState, useCallback } from 'react'
import { MapContainer, TileLayer, Polygon, Tooltip, useMap } from 'react-leaflet'
import { Bell, Lightbulb, ChevronDown, RefreshCw, Layers, Play, CheckCircle2, AlertCircle,
         Droplets, Sun, Leaf, BookOpen, AlertTriangle } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import Sidebar from '../components/Sidebar'
import { listFields, getGeoJSON, getAlerts, getRecommendations, reanalyzeField,
         getFarmingGuide, getIrrigationAlert } from '../services/api'
import { useAuth } from '../context/AuthContext'
import 'leaflet/dist/leaflet.css'
import { getCurrentSeasonInfo, withLiveSeason } from '../utils/seasonUtils'


// Smoothly fly the map to a new center without destroying the map instance
function FlyController({ center }) {
  const map = useMap()
  useEffect(() => {
    if (center) map.flyTo(center, map.getZoom(), { duration: 1 })
  }, [center, map])
  return null
}

const ndviColor = (ndvi) => {
  if (!ndvi || ndvi === 0) return '#57534e'
  if (ndvi > 0.6)  return '#22c55e'
  if (ndvi >= 0.3) return '#eab308'
  return '#ef4444'
}

const StatusBadge = ({ status }) => {
  const map = {
    pending:   { label: 'Pending',   cls: 'bg-earth-800 text-earth-400',      icon: '⏳' },
    running:   { label: 'Analysing', cls: 'bg-yellow-900/40 text-yellow-400', icon: '⚙️' },
    completed: { label: 'Completed', cls: 'bg-crop-900/40 text-crop-400',     icon: '✓' },
    failed:    { label: 'Failed',    cls: 'bg-red-900/40 text-red-400',        icon: '✗' },
  }
  const s = map[status] || map.pending
  return <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-medium ${s.cls}`}>{s.icon} {s.label}</span>
}

const SeasonBadge = ({ season, label }) => {
  const colors = {
    kharif: 'bg-green-900/40 text-green-400 border-green-800/50',
    rabi:   'bg-blue-900/40 text-blue-400 border-blue-800/50',
    zaid:   'bg-orange-900/40 text-orange-400 border-orange-800/50',
  }
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium border ${colors[season] || colors.rabi}`}>
      <Sun size={12} /> {label || season}
    </span>
  )
}

const Gauge = ({ label, value, max, unit, color }) => {
  const pct = Math.min(100, (value / max) * 100)
  return (
    <div>
      <div className="flex justify-between text-xs text-earth-500 mb-1">
        <span>{label}</span><span className={color}>{value}{unit}</span>
      </div>
      <div className="w-full bg-earth-800 rounded-full h-1.5">
        <div className={`h-1.5 rounded-full ${color.replace('text-','bg-')}`} style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}

export default function CropGuidancePage() {
  const { user } = useAuth()
  const { t }    = useTranslation()
  const role     = user?.role || 'farmer'
  const isManager = role === 'manager' || role === 'admin' || role === 'super_admin'

  const [fields, setFields]                   = useState([])
  const [selectedField, setSelectedField]      = useState(null)
  const [corridors, setCorridors]              = useState([])
  const [alerts, setAlerts]                    = useState([])
  const [recommendations, setRecommendations]  = useState([])
  const [guide, setGuide]                      = useState(null)
  const [irrigation, setIrrigation]            = useState(null)
  const [loading, setLoading]                  = useState(false)
  const [analysing, setAnalysing]              = useState(false)
  const [analysisMsg, setAnalysisMsg]          = useState(null)
  const [mapCenter, setMapCenter]              = useState([25.43, 81.84])
  const [activeTab, setActiveTab]              = useState('monitoring') // monitoring | guide | irrigation

  // ── load fields ──────────────────────────────────────────────────────────────
  useEffect(() => {
    listFields().then(r => {
      const list = Array.isArray(r.data) ? r.data : r.data?.fields || []
      setFields(list)
      if (list.length > 0) setSelectedField(list[0])
    }).catch(() => {})
  }, [])

  // ── load data when field changes ─────────────────────────────────────────────
  const loadFieldData = useCallback(async (field) => {
    if (!field) return
    setLoading(true)
    setCorridors([]); setAlerts([]); setRecommendations([]); setGuide(null); setIrrigation(null)

    const farmerId = field.farmer_id || user?.user_id

    const [geoRes, alertRes, recRes, guideRes, irrRes] = await Promise.allSettled([
      getGeoJSON(field.id),
      getAlerts(farmerId),
      getRecommendations(field.id),
      getFarmingGuide(field.id),
      getIrrigationAlert(field.id),
    ])

    if (geoRes.status === 'fulfilled') {
      const features = geoRes.value.data?.features || []
      setCorridors(features.map(f => ({
        grid_position: f.properties.grid_position,
        ndvi: f.properties.ndvi,
        health_status: f.properties.health_status,
        coordinates: f.geometry.coordinates[0].map(([lng, lat]) => [lat, lng]),
      })))
    }
    if (alertRes.status === 'fulfilled') {
      const all = Array.isArray(alertRes.value.data) ? alertRes.value.data : []
      setAlerts(all.filter(a => !a.field_id || a.field_id === field.id))
    }
    if (recRes.status === 'fulfilled') setRecommendations(Array.isArray(recRes.value.data) ? recRes.value.data : [])
    if (guideRes.status === 'fulfilled') setGuide(guideRes.value.data)
    if (irrRes.status === 'fulfilled') setIrrigation(irrRes.value.data)

    const loc = field.location || field.center
    if (loc?.lat && loc?.lng) setMapCenter([loc.lat, loc.lng])
    setLoading(false)
  }, [user])

  useEffect(() => { loadFieldData(selectedField) }, [selectedField, loadFieldData])

  // ── re-fetch when language toggles (i18n) ─────────────────────────────────
  const { i18n } = useTranslation()
  useEffect(() => {
    const handleLangChange = () => {
      if (selectedField) loadFieldData(selectedField)
    }
    i18n.on('languageChanged', handleLangChange)
    return () => i18n.off('languageChanged', handleLangChange)
  }, [i18n, selectedField, loadFieldData])

  // ── run analysis (manager) ───────────────────────────────────────────────────
  const runAnalysis = async () => {
    if (!selectedField) return
    setAnalysing(true); setAnalysisMsg(null)
    try {
      await reanalyzeField(selectedField.id)
      setAnalysisMsg({ type: 'success', text: 'Analysis completed! Refreshing…' })
      setFields(prev => prev.map(f => f.id === selectedField.id ? { ...f, analysis_status: 'completed' } : f))
      setSelectedField(prev => ({ ...prev, analysis_status: 'completed' }))
      setTimeout(() => loadFieldData(selectedField), 1200)
      setTimeout(() => setAnalysisMsg(null), 5000)
    } catch (err) {
      setAnalysisMsg({ type: 'error', text: err?.response?.data?.detail || 'Analysis failed.' })
      setTimeout(() => setAnalysisMsg(null), 6000)
    } finally { setAnalysing(false) }
  }

  const hasData = corridors.some(c => c.ndvi > 0)
  const ndviAvg = hasData ? (corridors.reduce((s, c) => s + (c.ndvi || 0), 0) / corridors.length).toFixed(3) : null
  const storedAnalysis = selectedField?.land_analysis || {}
  // Always use live season info so the displayed month/season is current
  const liveSeason = getCurrentSeasonInfo()
  const analysis = {
    ...storedAnalysis,
    current_month: liveSeason.current_month,
    current_month_name: liveSeason.current_month_name,
    season: liveSeason.season,
    season_label: liveSeason.season_label,
    season_period: liveSeason.season_period,
    season_stage: liveSeason.season_stage,
    season_stage_label: liveSeason.season_stage_label,
    sowing_advice: liveSeason.sowing_advice,
    season_crops: liveSeason.season_crops,
    future_plan: liveSeason.future_plan,
  }

  return (
    <div className="flex min-h-screen bg-earth-950">
      <Sidebar role={role} />
      <main className="flex-1 ml-0 lg:ml-60 p-4 lg:p-8 pt-16 lg:pt-8">

        {/* header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <p className="text-earth-500 text-sm mb-1">{t('cropGuidance.monitoring')}</p>
            <h1 className="font-display text-3xl font-bold text-earth-50">{t('cropGuidance.title')}</h1>
          </div>
          <div className="flex items-center gap-3">
            <SeasonBadge season={liveSeason.season} label={liveSeason.season_label} />
            {loading && <div className="flex items-center gap-2 text-earth-500 text-sm"><RefreshCw size={14} className="animate-spin" /> Loading…</div>}
          </div>
        </div>

        {/* selector bar */}
        <div className="glass-card rounded-xl p-3 lg:p-4 mb-6 flex items-center gap-2 lg:gap-3 flex-wrap">
          <Layers size={16} className="text-earth-500" />
          <label className="text-earth-400 text-sm">{t('cropGuidance.selectField')}:</label>
          <div className="relative">
            <select value={selectedField?.id || ''} onChange={e => setSelectedField(fields.find(f => f.id === e.target.value))}
              className="bg-earth-900 border border-earth-700 text-earth-200 rounded-lg px-3 py-2 text-sm appearance-none pr-8 focus:outline-none focus:border-crop-500">
              <option value="">{t('cropGuidance.selectFieldPlaceholder')}</option>
              {fields.map(f => (
                <option key={f.id} value={f.id}>
                  {f.recommended_crop ? `${f.recommended_crop} Field` : 'Field'} — {f.area} ha
                </option>
              ))}
            </select>
            <ChevronDown size={14} className="absolute right-2 top-1/2 -translate-y-1/2 text-earth-500 pointer-events-none" />
          </div>

          {selectedField && <StatusBadge status={selectedField.analysis_status || 'pending'} />}

          {isManager && selectedField && (
            <button onClick={runAnalysis} disabled={analysing}
              className="flex items-center gap-2 px-4 py-2 bg-crop-700 hover:bg-crop-600 disabled:opacity-60
                         text-white text-sm font-semibold rounded-lg transition shadow-md">
              {analysing ? <><RefreshCw size={14} className="animate-spin" /> Analysing…</> : <><Play size={14} /> Run Analysis</>}
            </button>
          )}

          {analysisMsg && (
            <div className={`flex items-center gap-2 text-xs px-3 py-2 rounded-lg ${
              analysisMsg.type === 'success' ? 'bg-crop-900/40 border border-crop-800/50 text-crop-300'
                : 'bg-red-900/40 border border-red-800/50 text-red-300'}`}>
              {analysisMsg.type === 'success' ? <CheckCircle2 size={13} /> : <AlertCircle size={13} />}
              {analysisMsg.text}
            </div>
          )}

          {/* legend */}
          <div className="flex items-center gap-3 ml-auto flex-wrap">
            {[['bg-crop-500','Healthy'],['bg-yellow-500','Moderate'],['bg-red-500','Stress'],['bg-earth-600','No Data']].map(([c,l]) => (
              <div key={l} className="flex items-center gap-1.5">
                <div className={`w-3 h-3 rounded-sm ${c}`} /><span className="text-earth-500 text-xs">{l}</span>
              </div>
            ))}
          </div>
        </div>

        {/* no-data banner */}
        {selectedField && !hasData && !loading && (
          <div className="mb-6 flex items-center gap-3 px-5 py-4 bg-yellow-950/40 border border-yellow-900/60 rounded-xl">
            <AlertCircle size={18} className="text-yellow-400 flex-shrink-0" />
            <div className="flex-1">
              <p className="text-yellow-300 text-sm font-semibold">No analysis data yet</p>
              <p className="text-yellow-600 text-xs mt-0.5">
                {isManager ? 'Click "Run Analysis" to generate data.' : 'The manager will run analysis. Check back shortly.'}
              </p>
            </div>
            {isManager && (
              <button onClick={runAnalysis} disabled={analysing}
                className="flex items-center gap-2 px-4 py-2 bg-yellow-700 hover:bg-yellow-600 text-white text-sm font-semibold rounded-lg transition disabled:opacity-60">
                {analysing ? <RefreshCw size={14} className="animate-spin" /> : <Play size={14} />}
                {analysing ? 'Analysing…' : 'Run Now'}
              </button>
            )}
          </div>
        )}

        {/* ── tab bar ── */}
        <div className="flex gap-1 mb-6 bg-earth-900/50 rounded-xl p-1 w-fit">
          {[
            { key: 'monitoring', label: '🛰 Monitoring', icon: <Leaf size={14} /> },
            { key: 'guide',      label: '📖 Farming Guide', icon: <BookOpen size={14} /> },
            { key: 'irrigation', label: '💧 Irrigation', icon: <Droplets size={14} /> },
          ].map(tab => (
            <button key={tab.key} onClick={() => setActiveTab(tab.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition ${
                activeTab === tab.key
                  ? 'bg-crop-800/50 text-crop-300 shadow-sm'
                  : 'text-earth-500 hover:text-earth-300 hover:bg-earth-800/50'
              }`}>
              {tab.icon} {tab.label}
            </button>
          ))}
        </div>

        {/* ═══ TAB: MONITORING ═══ */}
        {activeTab === 'monitoring' && (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 lg:gap-6">
            <div className="lg:col-span-2 space-y-4">
              <div className="glass-card rounded-2xl overflow-hidden" style={{ height: 'clamp(260px, 40vw, 420px)' }}>
                <MapContainer center={mapCenter} zoom={14} style={{ height: '100%', width: '100%' }}>
                  <FlyController center={mapCenter} />
                  <TileLayer url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                    attribution="© Esri" maxZoom={21} />
                  {corridors.map((c, i) => (
                    <Polygon key={i} positions={c.coordinates}
                      pathOptions={{ color: ndviColor(c.ndvi), fillColor: ndviColor(c.ndvi), fillOpacity: 0.45, weight: 1.5 }}>
                      <Tooltip>
                        <div className="text-xs"><strong>{c.grid_position}</strong><br />NDVI: {c.ndvi > 0 ? c.ndvi.toFixed(3) : 'N/A'}<br />{c.health_status}</div>
                      </Tooltip>
                    </Polygon>
                  ))}
                </MapContainer>
              </div>

              {ndviAvg && (
                <div className="grid grid-cols-3 gap-2 lg:gap-3">
                  {[
                    { label: 'Avg NDVI', value: ndviAvg, color: 'text-crop-400' },
                    { label: 'Healthy', value: corridors.filter(c => c.ndvi > 0.6).length, color: 'text-green-400' },
                    { label: 'Stress', value: corridors.filter(c => c.ndvi > 0 && c.ndvi < 0.3).length, color: 'text-red-400' },
                  ].map(s => (
                    <div key={s.label} className="glass-card rounded-xl px-4 py-3 text-center">
                      <div className={`font-display text-xl font-bold ${s.color}`}>{s.value}</div>
                      <div className="text-earth-500 text-xs mt-0.5">{s.label}</div>
                    </div>
                  ))}
                </div>
              )}

              {corridors.length > 0 && (
                <div className="glass-card rounded-2xl p-4">
                  <h3 className="text-earth-400 text-xs font-medium uppercase tracking-wider mb-3">{t('cropGuidance.corridorGrid')}</h3>
                  <div className="grid grid-cols-3 sm:grid-cols-5 gap-1.5">
                    {corridors.map((c, i) => (
                      <div key={i} className="rounded-md p-1.5 text-center"
                        style={{ backgroundColor: ndviColor(c.ndvi) + '22', border: `1px solid ${ndviColor(c.ndvi)}55` }}>
                        <div className="text-xs font-mono font-medium" style={{ color: ndviColor(c.ndvi) }}>{c.grid_position}</div>
                        <div className="text-xs font-mono text-earth-500">{c.ndvi > 0 ? c.ndvi.toFixed(2) : '—'}</div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* sidebar */}
            <div className="space-y-4">
              {/* recommended crop */}
              {selectedField?.recommended_crop && (
                <div className="glass-card rounded-2xl p-5 border border-crop-800/40 bg-crop-950/20">
                  <p className="text-earth-500 text-xs mb-1">AI Recommended Crop</p>
                  <p className="text-crop-300 font-display text-2xl font-bold capitalize">{selectedField.recommended_crop}</p>
                  {selectedField.crop_confidence && (
                    <div className="mt-3">
                      <div className="flex justify-between text-xs text-earth-500 mb-1">
                        <span>Confidence</span><span className="text-crop-400">{selectedField.crop_confidence}%</span>
                      </div>
                      <div className="w-full bg-earth-800 rounded-full h-1.5">
                        <div className="h-1.5 rounded-full bg-gradient-to-r from-crop-700 to-crop-400"
                          style={{ width: `${Math.min(100, selectedField.crop_confidence)}%` }} />
                      </div>
                    </div>
                  )}
                  {selectedField.alternative_crops?.length > 0 && (
                    <div className="mt-3 flex gap-1.5 flex-wrap">
                      <span className="text-xs text-earth-500">Also suitable:</span>
                      {selectedField.alternative_crops.map(c => (
                        <span key={c} className="px-2 py-0.5 bg-earth-800 rounded-full text-xs text-earth-400 capitalize">{c}</span>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* ── Season Analysis Card ── */}
              {liveSeason.season && (
                <div className="glass-card rounded-2xl p-5 space-y-3">
                  <h3 className="text-earth-400 text-xs font-medium uppercase tracking-wider flex items-center gap-2">
                    <Sun size={14} className="text-yellow-400" /> Season Analysis
                  </h3>

                  {/* month / season / stage grid */}
                  <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="bg-earth-900/50 rounded-lg py-2 px-1">
                      <p className="text-earth-200 text-sm font-bold">{analysis.current_month_name}</p>
                      <p className="text-earth-600 text-[10px]">Month</p>
                    </div>
                    <div className="bg-earth-900/50 rounded-lg py-2 px-1">
                      <p className="text-earth-200 text-sm font-bold capitalize">{analysis.season}</p>
                      <p className="text-earth-600 text-[10px]">Season</p>
                    </div>
                    <div className={`rounded-lg py-2 px-1 ${
                      analysis.season_stage === 'end' ? 'bg-red-900/30' :
                      analysis.season_stage === 'mid' ? 'bg-yellow-900/30' :
                      'bg-crop-900/30'
                    }`}>
                      <p className={`text-sm font-bold capitalize ${
                        analysis.season_stage === 'end' ? 'text-red-400' :
                        analysis.season_stage === 'mid' ? 'text-yellow-400' :
                        'text-crop-400'
                      }`}>{analysis.season_stage}</p>
                      <p className="text-earth-600 text-[10px]">Stage</p>
                    </div>
                  </div>

                  {/* sowing advice */}
                  {analysis.sowing_advice && (
                    <div className={`rounded-xl p-3 border text-xs leading-relaxed ${
                      analysis.season_stage === 'end' ? 'bg-red-900/10 border-red-800/30 text-red-300' :
                      analysis.season_stage === 'mid' ? 'bg-yellow-900/10 border-yellow-800/30 text-yellow-300' :
                      'bg-crop-900/10 border-crop-800/30 text-crop-300'
                    }`}>
                      {analysis.sowing_advice}
                    </div>
                  )}

                  {/* season crops */}
                  {analysis.season_crops?.length > 0 && (
                    <div>
                      <p className="text-earth-500 text-[10px] uppercase mb-1.5 tracking-wider">Season Crops</p>
                      <div className="flex gap-1.5 flex-wrap">
                        {analysis.season_crops.map(c => (
                          <span key={c.crop} className="px-2 py-0.5 bg-earth-800 rounded-full text-[10px] text-earth-400 capitalize"
                            title={`${c.duration} (${c.type})`}>
                            {c.crop} <span className="text-earth-600">· {c.type}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* future plan */}
                  {analysis.future_plan && (
                    <div className="bg-yellow-900/15 border border-yellow-800/30 rounded-xl p-3">
                      <p className="text-yellow-400 text-xs font-semibold mb-1.5">
                        🔄 Upcoming: {analysis.future_plan.next_season_label}
                      </p>
                      <p className="text-earth-400 text-[11px] mb-2 leading-relaxed">
                        {analysis.future_plan.preparation_advice}
                      </p>
                      <div className="flex gap-1 flex-wrap">
                        {analysis.future_plan.recommended_crops?.slice(0, 5).map(c => (
                          <span key={c.crop} className="px-2 py-0.5 bg-yellow-900/25 border border-yellow-800/25 rounded-full text-[10px] text-yellow-300 capitalize">
                            {c.crop}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* field analysis summary */}
              {analysis.soil_type && (
                <div className="glass-card rounded-2xl p-5 space-y-3">
                  <h3 className="text-earth-400 text-xs font-medium uppercase tracking-wider">Field Analysis</h3>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                    {[
                      ['Soil', analysis.soil_type],
                      ['pH', analysis.ph],
                      ['Temp', `${analysis.temperature}°C`],
                      ['Moisture', `${analysis.soil_moisture}%`],
                      ['Humidity', `${analysis.humidity}%`],
                      ['Rainfall', `${analysis.rainfall} mm`],
                    ].map(([k, v]) => (
                      <div key={k} className="bg-earth-900/50 rounded-lg px-2.5 py-2">
                        <span className="text-earth-500">{k}:</span>{' '}
                        <span className="text-earth-200 font-medium capitalize">{v}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* alerts */}
              <div className="glass-card rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Bell size={15} className="text-red-400" />
                  <h3 className="font-display text-base font-semibold text-earth-100">{t('cropGuidance.alerts')}</h3>
                  {alerts.filter(a => !a.is_read).length > 0 && (
                    <span className="ml-auto bg-red-900/50 text-red-400 border border-red-800/50 text-xs px-2 py-0.5 rounded-full">
                      {alerts.filter(a => !a.is_read).length} new
                    </span>
                  )}
                </div>
                {alerts.length === 0
                  ? <p className="text-earth-600 text-xs">{t('cropGuidance.noAlerts')}</p>
                  : <div className="space-y-2 max-h-48 overflow-y-auto">
                      {alerts.slice(0, 6).map((a, i) => (
                        <div key={a.id || i} className={`p-3 rounded-xl border text-xs ${
                          a.alert_type === 'irrigation' ? 'bg-blue-900/20 border-blue-800/40 text-blue-300' :
                          a.alert_type === 'crop_stress' ? 'bg-red-900/20 border-red-800/40 text-red-300' :
                          a.alert_type === 'heat_stress' ? 'bg-orange-900/20 border-orange-800/40 text-orange-300' :
                          'bg-yellow-900/20 border-yellow-800/40 text-yellow-300'}`}>
                          <div className="font-medium mb-0.5 capitalize">{a.alert_type?.replace('_',' ')}</div>
                          <div className="opacity-80">{a.message}</div>
                        </div>
                      ))}
                    </div>
                }
              </div>

              {/* recommendations */}
              <div className="glass-card rounded-2xl p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Lightbulb size={15} className="text-yellow-400" />
                  <h3 className="font-display text-base font-semibold text-earth-100">{t('cropGuidance.recommendations')}</h3>
                </div>
                {recommendations.length === 0
                  ? <p className="text-earth-600 text-xs">{isManager ? 'Run analysis to generate recommendations.' : 'No recommendations yet.'}</p>
                  : <div className="space-y-3 max-h-64 overflow-y-auto">
                      {recommendations.slice(0, 2).map((r, i) => (
                        <div key={i} className="bg-earth-900/40 border border-earth-800/30 rounded-xl p-3">
                          {r.predicted_crop && <div className="text-crop-400 text-xs font-mono mb-2">🌱 {r.predicted_crop} ({r.confidence || '—'}%)</div>}
                          {r.reason && <p className="text-earth-400 text-xs mb-2 leading-relaxed">{r.reason.substring(0, 150)}…</p>}
                          <ul className="space-y-1">
                            {(r.suggestions || []).slice(0, 4).map((s, j) => (
                              <li key={j} className="text-earth-400 text-xs flex items-start gap-1.5">
                                <span className="text-crop-500 flex-shrink-0">•</span> {s}
                              </li>
                            ))}
                          </ul>
                          {r.expected_yield && <div className="text-earth-500 text-xs mt-2 pt-2 border-t border-earth-800/30">📊 {r.expected_yield}</div>}
                        </div>
                      ))}
                    </div>
                }
              </div>
            </div>
          </div>
        )}

        {/* ═══ TAB: FARMING GUIDE ═══ */}
        {activeTab === 'guide' && (
          <div className="max-w-4xl">
            {!guide ? (
              <div className="glass-card rounded-2xl p-8 text-center">
                <BookOpen size={40} className="text-earth-600 mx-auto mb-4" />
                <p className="text-earth-500 text-sm">No farming guide available. {isManager ? 'Run analysis first.' : 'Analysis needs to complete.'}</p>
              </div>
            ) : guide.sowing_allowed === false ? (
              /* ── Sowing NOT allowed — planning only ── */
              <div className="space-y-4">
                <div className="glass-card rounded-2xl p-6 border border-red-800/40 bg-red-950/10">
                  <div className="flex items-center gap-4 mb-4">
                    <div className="w-14 h-14 bg-red-900/40 rounded-2xl flex items-center justify-center">
                      <AlertCircle size={28} className="text-red-400" />
                    </div>
                    <div>
                      <p className="text-red-400 text-xs font-semibold uppercase tracking-wide">Sowing Not Allowed</p>
                      <h2 className="text-red-300 font-display text-2xl font-bold capitalize">{guide.recommended_crop || guide.crop_name}</h2>
                    </div>
                    {guide.crop_confidence && (
                      <div className="ml-auto text-right">
                        <span className="text-earth-500 text-2xl font-bold">{guide.crop_confidence}%</span>
                        <p className="text-earth-600 text-xs">Confidence</p>
                      </div>
                    )}
                  </div>
                  <div className="bg-red-900/15 border border-red-800/30 rounded-xl p-4">
                    <p className="text-red-300 text-sm leading-relaxed">
                      ⚠️ {guide.sowing_warning || guide.why_not_suitable || `It is not the right time to start ${guide.recommended_crop || guide.crop_name} cultivation.`}
                    </p>
                    <p className="text-earth-500 text-xs mt-2">Sowing window: {guide.sowing_window}</p>
                    {guide.next_sowing_window && (
                      <p className="text-yellow-400 text-xs mt-1">📅 Next opportunity: {guide.next_sowing_window}</p>
                    )}
                  </div>
                </div>

                {guide.planning_guidance && (
                  <div className="glass-card rounded-2xl p-5 border border-yellow-800/30 bg-yellow-950/5">
                    <h3 className="text-yellow-300 text-sm font-semibold mb-2">📋 Planning Guidance</h3>
                    <p className="text-earth-400 text-sm leading-relaxed">{guide.planning_guidance}</p>
                  </div>
                )}

                {guide.alternative_crops?.length > 0 && (
                  <div className="glass-card rounded-2xl p-5">
                    <h3 className="text-crop-300 text-sm font-semibold mb-3">🌱 Crops You Can Sow Now ({guide.current_month_name})</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {guide.alternative_crops.map(c => (
                        <div key={c.crop} className="bg-crop-900/15 border border-crop-800/30 rounded-xl p-3 flex items-center gap-3">
                          <div className="w-8 h-8 bg-crop-900/40 rounded-lg flex items-center justify-center">
                            <Leaf size={16} className="text-crop-400" />
                          </div>
                          <div>
                            <p className="text-crop-300 text-sm font-semibold capitalize">{c.crop}</p>
                            <p className="text-earth-500 text-[10px]">{c.duration} · {c.season}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {guide.sowing_reason && (
                  <div className="glass-card rounded-2xl p-5">
                    <h3 className="text-earth-400 text-xs uppercase tracking-wider mb-2">Details</h3>
                    <p className="text-earth-500 text-sm leading-relaxed">{guide.sowing_reason}</p>
                  </div>
                )}
              </div>
            ) : (
              /* ── Sowing ALLOWED — full guide ── */
              <div className="space-y-4">
                {/* header */}
                <div className="glass-card rounded-2xl p-6 border border-crop-800/40 bg-crop-950/10">
                  <div className="flex items-center gap-4">
                    <div className="w-14 h-14 bg-crop-900/50 rounded-2xl flex items-center justify-center">
                      <Leaf size={28} className="text-crop-400" />
                    </div>
                    <div>
                      <p className="text-crop-400 text-xs font-semibold">✅ Sowing Allowed — Complete Farming Guide</p>
                      <h2 className="text-crop-300 font-display text-2xl font-bold capitalize">{guide.crop_name}</h2>
                    </div>
                    {guide.crop_confidence && (
                      <div className="ml-auto text-right">
                        <span className="text-crop-400 text-2xl font-bold">{guide.crop_confidence}%</span>
                        <p className="text-earth-500 text-xs">Confidence</p>
                      </div>
                    )}
                  </div>
                  {guide.why_suitable && (
                    <p className="text-earth-400 text-sm mt-4 leading-relaxed">{guide.why_suitable}</p>
                  )}
                </div>

                {/* all guide sections */}
                {[
                  { key: 'land_preparation', title: '🌱 Land Preparation', type: 'list' },
                  { key: 'seed_varieties',    title: '🌾 Seed Varieties',   type: 'obj' },
                  { key: 'seed_rate',         title: '📏 Seed Rate',        type: 'text' },
                  { key: 'sowing_time',       title: '📅 Sowing Time',      type: 'obj' },
                  { key: 'sowing_depth',      title: '📐 Sowing Depth',     type: 'text' },
                  { key: 'spacing',           title: '↔️ Spacing',          type: 'text' },
                  { key: 'fertilizer_plan',   title: '🧪 Fertilizer Plan',  type: 'obj' },
                  { key: 'irrigation',        title: '💧 Irrigation Guide',  type: 'obj' },
                  { key: 'expected_yield',    title: '📊 Expected Yield',   type: 'obj' },
                  { key: 'harvest_time',      title: '🏆 Harvest Time',     type: 'text' },
                ].filter(s => guide[s.key]).map(section => (
                  <div key={section.key} className="glass-card rounded-2xl p-5">
                    <h3 className="text-earth-200 text-sm font-semibold mb-3">{section.title}</h3>
                    {section.type === 'list' && Array.isArray(guide[section.key]) ? (
                      <ol className="space-y-2">
                        {guide[section.key].map((item, j) => (
                          <li key={j} className="flex items-start gap-3 text-earth-400 text-sm">
                            <span className="w-6 h-6 rounded-full bg-crop-900/40 text-crop-400 text-xs flex items-center justify-center flex-shrink-0 font-bold">
                              {j + 1}
                            </span>
                            {typeof item === 'string' ? item : `${item.pest}: ${item.control}`}
                          </li>
                        ))}
                      </ol>
                    ) : section.type === 'obj' && typeof guide[section.key] === 'object' ? (
                      <div className="space-y-2">
                        {Object.entries(guide[section.key]).map(([k, v]) => (
                          <div key={k} className="flex items-start gap-2 text-sm">
                            <span className="text-earth-500 capitalize font-medium min-w-[120px]">{k.replace(/_/g, ' ')}:</span>
                            <span className="text-earth-300">{Array.isArray(v) ? v.join(', ') : String(v)}</span>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-earth-400 text-sm">{String(guide[section.key])}</p>
                    )}
                  </div>
                ))}

                {/* pest management special section */}
                {guide.pest_management?.length > 0 && (
                  <div className="glass-card rounded-2xl p-5">
                    <h3 className="text-earth-200 text-sm font-semibold mb-3">🐛 Pest & Disease Management</h3>
                    <div className="space-y-3">
                      {guide.pest_management.map((p, j) => (
                        <div key={j} className="bg-earth-900/40 border border-earth-800/30 rounded-xl p-4">
                          <p className="text-red-400 font-semibold text-sm mb-1">{p.pest}</p>
                          <p className="text-earth-500 text-xs"><strong>Symptoms:</strong> {p.symptoms}</p>
                          <p className="text-earth-300 text-xs mt-1"><strong>Control:</strong> {p.control}</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ═══ TAB: IRRIGATION ═══ */}
        {activeTab === 'irrigation' && (
          <div className="max-w-3xl">
            {!irrigation ? (
              <div className="glass-card rounded-2xl p-8 text-center">
                <Droplets size={40} className="text-earth-600 mx-auto mb-4" />
                <p className="text-earth-500 text-sm">No irrigation data. {isManager ? 'Run analysis first.' : 'Waiting for analysis.'}</p>
              </div>
            ) : (
              <div className="space-y-4">
                {/* status header */}
                <div className={`glass-card rounded-2xl p-6 border ${
                  irrigation.urgency === 'high' ? 'border-red-800/50 bg-red-950/10' :
                  irrigation.urgency === 'medium' ? 'border-yellow-800/50 bg-yellow-950/10' :
                  'border-crop-800/50 bg-crop-950/10'
                }`}>
                  <div className="flex items-center gap-3 mb-3">
                    {irrigation.needs_irrigation
                      ? <AlertTriangle size={24} className={irrigation.urgency === 'high' ? 'text-red-400' : 'text-yellow-400'} />
                      : <CheckCircle2 size={24} className="text-crop-400" />}
                    <div>
                      <h2 className={`font-display text-xl font-bold ${
                        irrigation.needs_irrigation ? (irrigation.urgency === 'high' ? 'text-red-300' : 'text-yellow-300') : 'text-crop-300'
                      }`}>
                        {irrigation.needs_irrigation ? 'Irrigation Required' : 'No Irrigation Needed'}
                      </h2>
                      <p className="text-earth-400 text-sm mt-1">{irrigation.message}</p>
                    </div>
                  </div>
                </div>

                {/* gauges */}
                <div className="glass-card rounded-2xl p-6 space-y-4">
                  <h3 className="text-earth-400 text-xs font-medium uppercase tracking-wider">Current Conditions</h3>
                  <Gauge label="Soil Moisture" value={irrigation.soil_moisture} max={100} unit="%" color="text-blue-400" />
                  <Gauge label="Rainfall Probability" value={irrigation.rainfall_probability} max={100} unit="%" color="text-indigo-400" />
                  <Gauge label="Growth Stage" value={irrigation.growth_stage?.stage_pct || 0} max={100} unit="%" color="text-crop-400" />
                  <div className="flex items-center gap-2 bg-earth-900/50 rounded-xl p-3">
                    <Leaf size={16} className="text-crop-400" />
                    <span className="text-earth-300 text-sm font-medium">{irrigation.growth_stage?.stage}</span>
                  </div>
                </div>

                {/* schedule */}
                {irrigation.needs_irrigation && (
                  <div className="glass-card rounded-2xl p-6">
                    <h3 className="text-earth-400 text-xs font-medium uppercase tracking-wider mb-4">Irrigation Schedule</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 lg:gap-4">
                      <div className="bg-earth-900/50 rounded-xl p-4 text-center">
                        <Droplets size={24} className="text-blue-400 mx-auto mb-2" />
                        <p className="text-earth-200 font-display text-lg font-bold">{irrigation.water_quantity_liters?.toLocaleString()} L</p>
                        <p className="text-earth-500 text-xs">Water Quantity</p>
                      </div>
                      <div className="bg-earth-900/50 rounded-xl p-4 text-center">
                        <Sun size={24} className="text-yellow-400 mx-auto mb-2" />
                        <p className="text-earth-200 font-display text-sm font-bold">{irrigation.timing?.best_time}</p>
                        <p className="text-earth-500 text-xs">Best Time</p>
                      </div>
                      <div className="bg-earth-900/50 rounded-xl p-4 text-center">
                        <Bell size={24} className="text-orange-400 mx-auto mb-2" />
                        <p className="text-earth-200 font-display text-sm font-bold">
                          {new Date(irrigation.next_irrigation).toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })}
                        </p>
                        <p className="text-earth-500 text-xs">Next Date</p>
                      </div>
                    </div>
                    {irrigation.timing?.reason && (
                      <p className="text-earth-400 text-xs mt-4 leading-relaxed">💡 {irrigation.timing.reason}</p>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        )}

      </main>
    </div>
  )
}