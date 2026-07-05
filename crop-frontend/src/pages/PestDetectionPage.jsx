import React, { useEffect, useState, useCallback } from 'react'
import { MapContainer, TileLayer, Polygon, Tooltip } from 'react-leaflet'
import { Bug, Loader, ChevronDown, Activity, Thermometer, Droplets, CloudRain,
         Leaf, Shield, AlertTriangle, TrendingDown, TrendingUp, Minus, Target, Zap, Languages } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import Sidebar from '../components/Sidebar'
import { useAuth } from '../context/AuthContext'
import { listFields, getGeoJSON, runPestAnalysis } from '../services/api'
import 'leaflet/dist/leaflet.css'


const ndviColor = (ndvi) => {
  if (!ndvi || ndvi === 0) return '#57534e'
  if (ndvi > 0.6)  return '#22c55e'
  if (ndvi >= 0.3) return '#eab308'
  return '#ef4444'
}

const statusConfig = {
  healthy:  { color: 'text-emerald-400', bg: 'bg-emerald-900/25', border: 'border-emerald-700/40', bar: 'bg-emerald-500', glow: 'shadow-emerald-500/10' },
  moderate: { color: 'text-amber-400',   bg: 'bg-amber-900/25',   border: 'border-amber-700/40',   bar: 'bg-amber-500',   glow: 'shadow-amber-500/10' },
  critical: { color: 'text-red-400',     bg: 'bg-red-900/25',     border: 'border-red-700/40',     bar: 'bg-red-500',     glow: 'shadow-red-500/10' },
}

const urgencyBadge = {
  low:    'bg-emerald-900/40 text-emerald-400 border-emerald-800/50',
  medium: 'bg-amber-900/40 text-amber-400 border-amber-800/50',
  high:   'bg-red-900/40 text-red-400 border-red-800/50',
}

const TrendIcon = ({ trend }) => {
  if (trend === 'improving') return <TrendingUp size={14} className="text-emerald-400" />
  if (trend === 'declining' || trend === 'rapid_decline') return <TrendingDown size={14} className="text-red-400" />
  return <Minus size={14} className="text-earth-500" />
}


export default function PestDetectionPage() {
  const { user } = useAuth()
  const { t } = useTranslation()
  const role = user?.role || 'farmer'

  const [fields, setFields]              = useState([])
  const [selectedField, setSelectedField] = useState(null)
  const [corridors, setCorridors]         = useState([])
  const [mapCenter, setMapCenter]         = useState([25.43, 81.84])
  const [dropOpen, setDropOpen]           = useState(false)
  const [loading, setLoading]             = useState(false)
  const [result, setResult]               = useState(null)
  const [lang, setLang]                   = useState('en')   // 'en' | 'hi'

  // helper: pick Hindi value if available and lang === 'hi'
  const L = (obj, key) => {
    if (lang === 'hi' && obj?.[key + '_hi']) return obj[key + '_hi']
    return obj?.[key] ?? ''
  }

  // ── load fields on mount ──────────────────────────────────────────────────
  useEffect(() => {
    listFields().then(r => {
      const list = Array.isArray(r.data) ? r.data : r.data?.fields || []
      setFields(list)
      if (list.length > 0) setSelectedField(list[0])
    }).catch(() => {})
  }, [])

  // ── load corridors for map when field changes ─────────────────────────────
  const loadFieldMap = useCallback(async (field) => {
    if (!field) return
    setResult(null)
    setCorridors([])
    try {
      const geoRes = await getGeoJSON(field.id)
      const features = geoRes.data?.features || []
      setCorridors(features.map(f => ({
        grid_position: f.properties.grid_position,
        ndvi: f.properties.ndvi,
        health_status: f.properties.health_status,
        coordinates: f.geometry.coordinates[0].map(([lng, lat]) => [lat, lng]),
      })))
    } catch {}
    const loc = field.location || field.center
    if (loc?.lat && loc?.lng) setMapCenter([loc.lat, loc.lng])
  }, [])

  useEffect(() => { loadFieldMap(selectedField) }, [selectedField, loadFieldMap])

  // ── run analysis ──────────────────────────────────────────────────────────
  const handleRunAnalysis = async () => {
    if (!selectedField) return
    setLoading(true)
    setResult(null)
    try {
      const res = await runPestAnalysis(selectedField.id, lang)
      setResult(res.data)
    } catch (err) {
      setResult({ error: err?.response?.data?.detail || 'Analysis failed. Try again.' })
    } finally {
      setLoading(false)
    }
  }

  const cfg = result?.status_key ? (statusConfig[result.status_key] || statusConfig.moderate) : null
  const sev = result?.severity
  const cause = result?.likely_cause
  const zones = result?.zone_analysis
  const trend = result?.trend
  const recs = result?.recommendations

  return (
    <div className="flex min-h-screen bg-earth-950">
      <Sidebar role={role} />
      <main className="flex-1 ml-0 lg:ml-60 p-4 lg:p-8 pt-16 lg:pt-8">

        {/* ── Header ──────────────────────────────────────────────────── */}
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-6">
          <div>
            <p className="text-earth-500 text-sm mb-1">{lang === 'hi' ? 'AI-संचालित उपग्रह विश्लेषण' : 'AI-Powered Satellite Analysis'}</p>
            <h1 className="font-display text-3xl font-bold text-earth-50">
              {lang === 'hi' ? 'तनाव पहचान' : 'Stress Detection'}
            </h1>
          </div>
          <button
            onClick={() => {
              setLang(prev => {
                const next = prev === 'en' ? 'hi' : 'en'
                // Re-run analysis with new language if results exist
                if (result && !result.error && selectedField) {
                  setLoading(true)
                  setResult(null)
                  runPestAnalysis(selectedField.id, next)
                    .then(res => setResult(res.data))
                    .catch(err => setResult({ error: err?.response?.data?.detail || 'Translation failed.' }))
                    .finally(() => setLoading(false))
                }
                return next
              })
            }}
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-earth-800 hover:bg-earth-700 border border-earth-700 text-earth-300 text-sm font-medium transition-colors"
          >
            <Languages size={16} />
            {lang === 'en' ? 'हिन्दी' : 'English'}
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* ════════════════════  LEFT PANEL  ════════════════════════ */}
          <div className="space-y-4">

            {/* Map — rendered first so dropdown never overlaps it */}
            <div className="glass-card rounded-2xl overflow-hidden mb-4" style={{ height: 'clamp(240px, 35vw, 340px)', position: 'relative', zIndex: 1 }}>
              <MapContainer
                key={`${mapCenter[0]}-${mapCenter[1]}`}
                center={mapCenter}
                zoom={16}
                scrollWheelZoom={true}
                style={{ height: '100%', width: '100%' }}
              >
                <TileLayer
                  url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
                  attribution="Esri Satellite"
                />
                {corridors.map((c, i) => (
                  <Polygon
                    key={i}
                    positions={c.coordinates}
                    pathOptions={{
                      color: ndviColor(c.ndvi),
                      weight: 1,
                      fillColor: ndviColor(c.ndvi),
                      fillOpacity: 0.45,
                    }}
                  >
                    <Tooltip sticky>
                      <span className="text-xs font-mono">
                        {c.grid_position} — NDVI: {c.ndvi?.toFixed(3) || 'N/A'}
                      </span>
                    </Tooltip>
                  </Polygon>
                ))}
              </MapContainer>
            </div>

            {/* Run Analysis Button */}
            <button
              id="run-pest-analysis-btn"
              onClick={handleRunAnalysis}
              disabled={!selectedField || loading}
              className={`w-full mt-4 mb-4 py-4 rounded-2xl font-body font-semibold flex items-center justify-center gap-3 text-base transition-all ${
                selectedField && !loading
                  ? 'bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white shadow-lg shadow-amber-900/30 hover:shadow-amber-900/50'
                  : 'bg-earth-800 text-earth-600 cursor-not-allowed'
              }`}
            >
              {loading
                ? <><Loader size={20} className="animate-spin" /> Analyzing Field…</>
                : <><Activity size={20} /> Run Analysis</>
              }
            </button>

            {/* Field Selector — rendered last (below map) so dropdown list never overlaps Leaflet */}
            <div className="glass-card rounded-2xl p-5" style={{ overflow: 'visible' }}>
              <label className="block text-earth-400 text-xs font-medium uppercase tracking-wider mb-2">
                Select Field
              </label>
              <div className="relative">
                <button
                  onClick={() => setDropOpen(!dropOpen)}
                  className="w-full flex items-center justify-between bg-earth-900/60 border border-earth-700 rounded-xl px-4 py-3 text-earth-100 text-sm hover:border-earth-600 transition-colors"
                >
                  <span>
                    {selectedField
                      ? `📍 ${selectedField.location?.lat?.toFixed(4)}, ${selectedField.location?.lng?.toFixed(4)} — ${selectedField.area || '?'} ha`
                      : 'No fields found'}
                  </span>
                  <ChevronDown size={16} className={`text-earth-500 transition-transform ${dropOpen ? 'rotate-180' : ''}`} />
                </button>
                {dropOpen && (
                  <div
                    className="absolute top-full left-0 right-0 mt-1 bg-earth-900 border border-earth-700 rounded-xl shadow-2xl w-full"
                    style={{ zIndex: 9999, maxHeight: '128px', overflowY: 'auto' }}
                  >
                    {fields.map((f, i) => (
                      <button key={f.id || i}
                        onClick={() => { setSelectedField(f); setDropOpen(false) }}
                        className={`w-full text-left px-4 py-3 text-sm hover:bg-earth-800 transition-colors border-b border-earth-800/50 last:border-0 ${
                          selectedField?.id === f.id ? 'bg-earth-800 text-amber-400' : 'text-earth-300'
                        }`}
                      >
                        📍 {f.location?.lat?.toFixed(4)}, {f.location?.lng?.toFixed(4)} — {f.area || '?'} ha
                        {f.recommended_crop && <span className="ml-2 text-earth-500">({f.recommended_crop})</span>}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* ════════════════════  RIGHT PANEL  ═══════════════════════ */}
          <div className="space-y-4">

            {/* Empty state */}
            {!result && !loading && (
              <div className="glass-card rounded-2xl h-full flex flex-col items-center justify-center p-12 text-center min-h-[540px]">
                <div className="w-20 h-20 rounded-full bg-earth-800/60 flex items-center justify-center mb-5">
                  <Bug size={36} className="text-earth-600" />
                </div>
                <h3 className="font-display text-xl font-semibold text-earth-500 mb-2">
                  Analysis Results
                </h3>
                <p className="text-earth-600 text-sm max-w-xs">
                  Select a field and click "Run Analysis" to get automated pest & stress detection results from satellite data.
                </p>
              </div>
            )}

            {/* Loading state */}
            {loading && (
              <div className="glass-card rounded-2xl h-full flex flex-col items-center justify-center p-12 text-center min-h-[540px]">
                <div className="w-20 h-20 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin mb-6" />
                <h3 className="font-display text-xl font-semibold text-earth-300 mb-2">
                  Analyzing Satellite Data…
                </h3>
                <p className="text-earth-500 text-sm">
                  Fetching NDVI imagery, processing vegetation indices, and detecting stress patterns.
                </p>
              </div>
            )}

            {/* Error state */}
            {result?.error && !loading && (
              <div className="glass-card rounded-2xl p-8 text-center min-h-[540px] flex flex-col items-center justify-center">
                <AlertTriangle size={40} className="text-red-500 mb-4" />
                <h3 className="font-display text-lg font-semibold text-red-400 mb-2">Analysis Failed</h3>
                <p className="text-earth-500 text-sm">{result.error}</p>
              </div>
            )}

            {/* ═══════════ Results ═══════════ */}
            {result && !result.error && !loading && (
              <>
                {/* Status + Urgency badge */}
                <div className={`${cfg.bg} border ${cfg.border} rounded-2xl p-5 shadow-lg ${cfg.glow}`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-xs font-mono uppercase tracking-wider ${cfg.color}`}>
                      {lang === 'hi' ? result.status_hi : result.status}
                    </span>
                    {sev && (
                      <span className={`inline-flex items-center gap-1 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${urgencyBadge[sev.urgency] || urgencyBadge.low}`}>
                        <Zap size={10} /> {L(sev, 'urgency_label')}
                      </span>
                    )}
                  </div>
                  <h2 className="font-display text-2xl font-bold text-earth-100 mb-1">
                    {result.icon} {lang === 'hi' ? result.status_hi : result.status}
                  </h2>
                  {result.summary && (
                    <p className="text-earth-400 text-sm leading-relaxed mt-2">{result.summary}</p>
                  )}
                </div>

                {/* Likely Cause */}
                {cause && cause.label !== 'No Stress Detected' && (
                  <div className="glass-card rounded-2xl p-5">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="text-earth-200 text-sm font-semibold flex items-center gap-2">
                        <Target size={14} className="text-amber-400" /> {lang === 'hi' ? 'संभावित कारण' : 'Likely Cause'}
                      </h3>
                      <span className="text-xs font-mono text-earth-500">{cause.confidence}% confidence</span>
                    </div>
                    <div className="text-amber-400 font-display font-bold text-lg mb-1">{L(cause, 'label')}</div>
                    <p className="text-earth-400 text-sm leading-relaxed">{L(cause, 'explanation')}</p>
                    {/* Confidence bar */}
                    <div className="mt-3 w-full bg-earth-800 rounded-full h-1.5">
                      <div className="h-full rounded-full bg-amber-500 transition-all duration-700"
                        style={{ width: `${cause.confidence}%` }} />
                    </div>
                    {/* Other possible causes */}
                    {result.all_causes && result.all_causes.length > 1 && (
                      <div className="mt-3 flex flex-wrap gap-2">
                        {result.all_causes.slice(1).map((c, i) => (
                          <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-earth-800 text-earth-500 border border-earth-700">
                            {lang === 'hi' ? c.label_hi : c.label} ({c.confidence}%)
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                )}

                {/* Zone Analysis */}
                {zones && (
                  <div className="glass-card rounded-2xl p-5">
                    <h3 className="text-earth-200 text-sm font-semibold mb-3 flex items-center gap-2">
                      <Activity size={14} className="text-crop-400" /> {lang === 'hi' ? 'क्षेत्र विश्लेषण' : 'Zone Analysis'}
                    </h3>
                    {/* Bar chart */}
                    <div className="space-y-2 mb-3">
                      <div className="flex items-center gap-3">
                        <span className="text-[11px] text-earth-500 w-16">Stressed</span>
                        <div className="flex-1 bg-earth-800 rounded-full h-2 overflow-hidden">
                          <div className="h-full rounded-full bg-red-500 transition-all duration-700"
                            style={{ width: `${zones.stressed_pct}%` }} />
                        </div>
                        <span className="text-xs font-mono text-red-400 w-12 text-right">{zones.stressed_pct}%</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-[11px] text-earth-500 w-16">Moderate</span>
                        <div className="flex-1 bg-earth-800 rounded-full h-2 overflow-hidden">
                          <div className="h-full rounded-full bg-amber-500 transition-all duration-700"
                            style={{ width: `${zones.moderate_pct}%` }} />
                        </div>
                        <span className="text-xs font-mono text-amber-400 w-12 text-right">{zones.moderate_pct}%</span>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className="text-[11px] text-earth-500 w-16">Healthy</span>
                        <div className="flex-1 bg-earth-800 rounded-full h-2 overflow-hidden">
                          <div className="h-full rounded-full bg-emerald-500 transition-all duration-700"
                            style={{ width: `${zones.healthy_pct}%` }} />
                        </div>
                        <span className="text-xs font-mono text-emerald-400 w-12 text-right">{zones.healthy_pct}%</span>
                      </div>
                    </div>
                    <p className="text-earth-500 text-xs leading-relaxed">{L(zones, 'summary')}</p>
                    <div className="mt-2 flex gap-4 text-[11px] text-earth-600">
                      <span>Total: {zones.total_zones} zones</span>
                      {zones.affected_region !== 'none' && <span>Region: {zones.affected_region}</span>}
                    </div>
                  </div>
                )}

                {/* NDVI + Trend */}
                <div className="glass-card rounded-2xl p-5">
                  <div className="flex items-center gap-2 mb-3">
                    <Leaf size={16} className="text-crop-400" />
                    <h3 className="text-earth-200 text-sm font-semibold">{lang === 'hi' ? 'वनस्पति सूचकांक (NDVI)' : 'Vegetation Index (NDVI)'}</h3>
                  </div>
                  <div className="flex items-end justify-between mb-3">
                    <div>
                      <span className={`text-4xl font-display font-bold ${cfg.color}`}>{result.ndvi}</span>
                      <span className="text-earth-500 text-xs ml-3">
                        Range: {result.ndvi_min} – {result.ndvi_max}
                      </span>
                    </div>
                    {trend && (
                      <div className="flex items-center gap-1.5 text-xs">
                        <TrendIcon trend={trend.trend} />
                        <span className={trend.trend === 'improving' ? 'text-emerald-400' : trend.trend.includes('declin') ? 'text-red-400' : 'text-earth-500'}>
                          {trend.change > 0 ? '+' : ''}{trend.change_pct}%
                        </span>
                      </div>
                    )}
                  </div>
                  <div className="w-full bg-earth-800 rounded-full h-2 overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-700 ${cfg.bar}`}
                      style={{ width: `${Math.min(100, Math.max(5, result.ndvi * 100))}%` }} />
                  </div>
                  <div className="flex justify-between text-[10px] text-earth-600 mt-1">
                    <span>0 (Bare)</span><span>0.3</span><span>0.6</span><span>1.0 (Dense)</span>
                  </div>
                  {trend && (
                    <div className="mt-3 bg-earth-900/50 rounded-xl p-3 border border-earth-800/60">
                      <div className="flex items-center gap-2 mb-1">
                        <TrendIcon trend={trend.trend} />
                        <span className="text-earth-300 text-xs font-medium">{L(trend, 'trend_label')}</span>
                      </div>
                      <p className="text-earth-500 text-[11px] leading-relaxed">{L(trend, 'trend_note')}</p>
                    </div>
                  )}
                </div>

                {/* Environmental conditions */}
                {result.environmental_conditions && (
                  <div className="glass-card rounded-2xl p-5">
                    <h3 className="text-earth-200 text-sm font-semibold mb-3">📡 {lang === 'hi' ? 'पर्यावरणीय स्थितियाँ' : 'Environmental Conditions'}</h3>
                    <div className="grid grid-cols-2 gap-3">
                      {[
                        { icon: <Thermometer size={14} />, label: 'Temperature', value: `${result.environmental_conditions.temperature}°C`, color: result.environmental_conditions.temperature > 35 ? 'text-red-400' : 'text-earth-300' },
                        { icon: <Droplets size={14} />, label: 'Humidity', value: `${result.environmental_conditions.humidity}%`, color: result.environmental_conditions.humidity > 80 ? 'text-amber-400' : 'text-earth-300' },
                        { icon: <CloudRain size={14} />, label: 'Soil Moisture', value: `${result.environmental_conditions.soil_moisture}%`, color: result.environmental_conditions.soil_moisture < 20 ? 'text-red-400' : 'text-earth-300' },
                        { icon: <CloudRain size={14} />, label: 'Rain Probability', value: `${result.environmental_conditions.rainfall_probability}%`, color: 'text-earth-300' },
                      ].map((item, i) => (
                        <div key={i} className="bg-earth-900/40 rounded-xl p-3 border border-earth-800/60">
                          <div className="flex items-center gap-1.5 text-earth-500 text-[11px] mb-1">
                            {item.icon} {item.label}
                          </div>
                          <span className={`text-lg font-semibold ${item.color}`}>{item.value}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* ── Structured Recommendations ── */}
                {recs && (
                  <div className="space-y-4">

                    {/* Affected Area callout */}
                    {recs.affected_area && recs.affected_area.affected_pct > 0 && (
                      <div className="glass-card rounded-2xl p-4 border border-amber-800/30 bg-amber-900/10">
                        <div className="flex items-center gap-2 mb-1">
                          <Target size={14} className="text-amber-400" />
                          <span className="text-amber-400 text-xs font-semibold uppercase tracking-wider">Affected Area</span>
                        </div>
                        <p className="text-earth-300 text-sm leading-relaxed">{L(recs.affected_area, 'note')}</p>
                      </div>
                    )}

                    {/* Priority Actions */}
                    <div className="glass-card rounded-2xl p-5">
                      <h3 className="text-earth-200 text-sm font-semibold mb-4 flex items-center gap-2">
                        <Shield size={14} className="text-crop-400" /> {lang === 'hi' ? 'अनुशंसित कार्रवाई' : 'Recommended Actions'}
                      </h3>

                      {/* High Priority */}
                      {recs.priority_actions?.high?.length > 0 && (
                        <div className="mb-4">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="w-2 h-2 rounded-full bg-red-500" />
                            <span className="text-red-400 text-[11px] font-semibold uppercase tracking-wider">{lang === 'hi' ? 'उच्च प्राथमिकता — 24-48 घंटे में' : 'High Priority — Within 24-48 Hours'}</span>
                          </div>
                          <div className="space-y-2">
                            {recs.priority_actions.high.map((rec, i) => (
                              <div key={`h${i}`} className="flex items-start gap-3 bg-red-900/10 rounded-xl p-3 border border-red-800/30">
                                <span className="text-base flex-shrink-0 mt-0.5">{rec.icon}</span>
                                <p className="text-earth-200 text-sm leading-relaxed">{lang === 'hi' ? rec.action_hi : rec.action}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Medium Priority */}
                      {recs.priority_actions?.medium?.length > 0 && (
                        <div className="mb-4">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="w-2 h-2 rounded-full bg-amber-500" />
                            <span className="text-amber-400 text-[11px] font-semibold uppercase tracking-wider">{lang === 'hi' ? 'मध्यम प्राथमिकता — कुछ दिनों में' : 'Medium Priority — Within a Few Days'}</span>
                          </div>
                          <div className="space-y-2">
                            {recs.priority_actions.medium.map((rec, i) => (
                              <div key={`m${i}`} className="flex items-start gap-3 bg-amber-900/10 rounded-xl p-3 border border-amber-800/30">
                                <span className="text-base flex-shrink-0 mt-0.5">{rec.icon}</span>
                                <p className="text-earth-300 text-sm leading-relaxed">{lang === 'hi' ? rec.action_hi : rec.action}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Monitoring */}
                      {recs.priority_actions?.monitoring?.length > 0 && (
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <span className="w-2 h-2 rounded-full bg-emerald-500" />
                            <span className="text-emerald-400 text-[11px] font-semibold uppercase tracking-wider">{lang === 'hi' ? 'निगरानी — दैनिक जाँच' : 'Monitoring — Daily Checks'}</span>
                          </div>
                          <div className="space-y-2">
                            {recs.priority_actions.monitoring.map((rec, i) => (
                              <div key={`o${i}`} className="flex items-start gap-3 bg-earth-900/30 rounded-xl p-3 border border-earth-800/50">
                                <span className="text-base flex-shrink-0 mt-0.5">{rec.icon}</span>
                                <p className="text-earth-400 text-sm leading-relaxed">{lang === 'hi' ? rec.action_hi : rec.action}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Action Timeline */}
                    {recs.timeline && recs.timeline.length > 0 && (
                      <div className="glass-card rounded-2xl p-5">
                        <h3 className="text-earth-200 text-sm font-semibold mb-3 flex items-center gap-2">
                          📅 {lang === 'hi' ? 'कार्य योजना' : 'Action Timeline'}
                        </h3>
                        <div className="relative pl-4 border-l-2 border-earth-800 space-y-3">
                          {recs.timeline.map((step, i) => (
                            <div key={i} className="relative">
                              <div className="absolute -left-[21px] top-1 w-3 h-3 rounded-full bg-earth-700 border-2 border-earth-600" />
                              <div className="flex items-start gap-3">
                                <span className="text-xs font-mono text-amber-400 min-w-[52px] pt-0.5">{step.day}</span>
                                <p className="text-earth-300 text-sm leading-relaxed">{lang === 'hi' ? step.task_hi : step.task}</p>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Risk Warning */}
                    {recs.risk_warning && recs.risk_warning.warning && (
                      <div className="glass-card rounded-2xl p-4 border border-red-900/30 bg-red-950/20">
                        <div className="flex items-center gap-2 mb-1.5">
                          <AlertTriangle size={14} className="text-red-400" />
                          <span className="text-red-400 text-xs font-semibold uppercase tracking-wider">{lang === 'hi' ? 'कार्रवाई न करने पर जोखिम' : 'Risk if No Action Taken'}</span>
                        </div>
                        <p className="text-earth-400 text-sm leading-relaxed">{L(recs.risk_warning, 'warning')}</p>
                      </div>
                    )}

                    {/* Next Check */}
                    {recs.next_check && (
                      <div className="glass-card rounded-2xl p-4 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-base">🔔</span>
                          <span className="text-earth-400 text-sm">{lang === 'hi' ? 'अगली जाँच' : 'Next Check Recommended'}</span>
                        </div>
                        <span className={`text-sm font-semibold ${
                          sev?.urgency === 'high' ? 'text-red-400' : sev?.urgency === 'medium' ? 'text-amber-400' : 'text-emerald-400'
                        }`}>{L(recs, 'next_check')}</span>
                      </div>
                    )}
                  </div>
                )}

                {/* Re-run button */}
                <button onClick={handleRunAnalysis}
                  className="w-full py-3 rounded-xl bg-earth-800 hover:bg-earth-700 text-earth-300 text-sm font-medium transition-colors border border-earth-700">
                  🔄 {lang === 'hi' ? 'दोबारा विश्लेषण करें' : 'Run Analysis Again'}
                </button>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}