import React, { useState, useRef, useCallback } from 'react'
import { Upload, Bug, Loader, CheckCircle, AlertTriangle, X, RefreshCw, Microscope, ShieldCheck, Leaf } from 'lucide-react'
import { useTranslation } from 'react-i18next'
import Sidebar from '../components/Sidebar'
import { useAuth } from '../context/AuthContext'
import api from '../services/api'

// ── Severity config ────────────────────────────────────────────────────────────
const SEV = {
  low:      { label: 'Low',      color: 'text-emerald-400', bg: 'bg-emerald-900/20', border: 'border-emerald-700/40', bar: 'bg-emerald-500', dot: 'bg-emerald-400' },
  moderate: { label: 'Moderate', color: 'text-amber-400',   bg: 'bg-amber-900/20',   border: 'border-amber-700/40',   bar: 'bg-amber-500',   dot: 'bg-amber-400'   },
  high:     { label: 'High',     color: 'text-red-400',     bg: 'bg-red-900/20',     border: 'border-red-700/40',     bar: 'bg-red-500',     dot: 'bg-red-400'     },
}

// ── Tips list ──────────────────────────────────────────────────────────────────
const TIPS = [
  'Take close-up photos of affected leaves',
  'Ensure good lighting — avoid shadows',
  'Capture both sides of the leaf',
  'Include the stem if stem rot is suspected',
]

export default function ImagePestDetectionPage() {
  const { user }   = useAuth()
  const { t }      = useTranslation()
  const role       = user?.role || 'farmer'
  const fileRef    = useRef(null)
  const dropRef    = useRef(null)

  const [image,    setImage]    = useState(null)    // File object
  const [preview,  setPreview]  = useState(null)    // data URL
  const [loading,  setLoading]  = useState(false)
  const [result,   setResult]   = useState(null)
  const [error,    setError]    = useState(null)
  const [dragging, setDragging] = useState(false)

  // ── File selection ─────────────────────────────────────────────────────────
  const handleFile = useCallback((file) => {
    if (!file || !file.type.startsWith('image/')) return
    setImage(file)
    setResult(null)
    setError(null)
    const reader = new FileReader()
    reader.onload = (e) => setPreview(e.target.result)
    reader.readAsDataURL(file)
  }, [])

  const onInputChange = (e) => handleFile(e.target.files?.[0])

  // ── Drag & Drop ────────────────────────────────────────────────────────────
  const onDragOver  = (e) => { e.preventDefault(); setDragging(true)  }
  const onDragLeave = ()  => setDragging(false)
  const onDrop      = (e) => {
    e.preventDefault()
    setDragging(false)
    handleFile(e.dataTransfer.files?.[0])
  }

  // ── Clear ──────────────────────────────────────────────────────────────────
  const clearImage = () => {
    setImage(null); setPreview(null); setResult(null); setError(null)
    if (fileRef.current) fileRef.current.value = ''
  }

  // ── Analyze ───────────────────────────────────────────────────────────────
  const handleAnalyze = async () => {
    if (!image) return
    setLoading(true); setResult(null); setError(null)
    try {
      const form = new FormData()
      form.append('image', image)
      const res = await api.post('/pest-detection/analyze', form, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      setResult(res.data)
    } catch (err) {
      setError(err?.response?.data?.detail || 'Detection failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const sev = result ? (SEV[result.severity] || SEV.low) : null
  const isHealthy = result?.disease === 'Healthy Crop'

  return (
    <div className="flex min-h-screen bg-earth-950">
      <Sidebar role={role} />
      <main className="flex-1 ml-0 lg:ml-60 p-4 lg:p-8 pt-16 lg:pt-8">

        {/* ── Header ────────────────────────────────────────────────────── */}
        <div className="mb-6">
          <p className="text-earth-500 text-sm mb-1 flex items-center gap-2">
            <Microscope size={14} /> AI-Powered Image Analysis
          </p>
          <h1 className="font-display text-3xl font-bold text-earth-50">Pest Detection</h1>
          <p className="text-earth-500 text-sm mt-1">
            Upload a crop or leaf photo — our AI model identifies pests and diseases instantly.
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

          {/* ══════════════  LEFT — Upload Panel  ═══════════════════ */}
          <div className="space-y-4">

            {/* Drop zone / preview */}
            <div className="glass-card rounded-2xl p-5">
              <p className="text-earth-400 text-xs font-medium uppercase tracking-wider mb-3">
                Upload Crop Image
              </p>

              {/* Preview mode */}
              {preview ? (
                <div className="relative rounded-xl overflow-hidden border border-earth-700">
                  <img src={preview} alt="preview"
                    className="w-full object-cover max-h-72" />
                  <button onClick={clearImage}
                    className="absolute top-2 right-2 w-8 h-8 bg-earth-950/80 rounded-full flex items-center justify-center text-earth-400 hover:text-red-400 transition-colors border border-earth-700">
                    <X size={14} />
                  </button>
                  <div className="absolute bottom-2 left-2 px-2 py-1 bg-earth-950/80 rounded-lg text-[10px] text-earth-400 font-mono truncate max-w-[80%]">
                    {image?.name}
                  </div>
                </div>
              ) : (
                /* Drop zone */
                <div
                  ref={dropRef}
                  onDragOver={onDragOver}
                  onDragLeave={onDragLeave}
                  onDrop={onDrop}
                  onClick={() => fileRef.current?.click()}
                  className={`relative border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center cursor-pointer transition-all
                    ${dragging
                      ? 'border-amber-500 bg-amber-900/10'
                      : 'border-earth-700 hover:border-earth-500 bg-earth-900/20 hover:bg-earth-900/40'
                    }`}
                >
                  <div className="w-14 h-14 bg-earth-800 rounded-2xl flex items-center justify-center mb-4">
                    <Upload size={24} className="text-earth-500" />
                  </div>
                  <p className="text-earth-300 text-sm font-medium mb-1">
                    {dragging ? 'Drop it here!' : 'Drop image here or click to browse'}
                  </p>
                  <p className="text-earth-600 text-xs">Supports JPG, PNG, WEBP — max 10 MB</p>
                  <input ref={fileRef} type="file" accept="image/*"
                    className="hidden" onChange={onInputChange} />
                </div>
              )}
            </div>

            {/* Analyze button */}
            <button
              id="analyze-pest-btn"
              onClick={handleAnalyze}
              disabled={!image || loading}
              className={`w-full py-4 rounded-2xl font-body font-semibold flex items-center justify-center gap-3 text-base transition-all ${
                image && !loading
                  ? 'bg-gradient-to-r from-amber-600 to-orange-600 hover:from-amber-500 hover:to-orange-500 text-white shadow-lg shadow-amber-900/30 hover:shadow-amber-900/50'
                  : 'bg-earth-800 text-earth-600 cursor-not-allowed'
              }`}
            >
              {loading
                ? <><Loader size={20} className="animate-spin" /> Analyzing Image…</>
                : <><Bug size={20} /> Detect Pests &amp; Diseases</>
              }
            </button>

            {/* Tips card */}
            <div className="glass-card rounded-2xl p-5">
              <h3 className="text-earth-300 text-sm font-semibold mb-3 flex items-center gap-2">
                <Leaf size={14} className="text-crop-400" /> Tips for Better Results
              </h3>
              <ul className="space-y-2">
                {TIPS.map((tip, i) => (
                  <li key={i} className="flex items-start gap-2.5 text-earth-500 text-xs">
                    <span className="w-1.5 h-1.5 rounded-full bg-amber-500 flex-shrink-0 mt-1.5" />
                    {tip}
                  </li>
                ))}
              </ul>
            </div>
          </div>

          {/* ══════════════  RIGHT — Results Panel  ══════════════════ */}
          <div className="space-y-4">

            {/* Empty state */}
            {!result && !loading && !error && (
              <div className="glass-card rounded-2xl flex flex-col items-center justify-center p-12 text-center min-h-[420px]">
                <div className="w-20 h-20 rounded-full bg-earth-800/60 flex items-center justify-center mb-5">
                  <Bug size={36} className="text-earth-600" />
                </div>
                <h3 className="font-display text-xl font-semibold text-earth-500 mb-2">
                  Detection Results
                </h3>
                <p className="text-earth-600 text-sm max-w-xs">
                  Upload a crop image and click "Detect" to get AI-powered pest and disease analysis.
                </p>
              </div>
            )}

            {/* Loading state */}
            {loading && (
              <div className="glass-card rounded-2xl flex flex-col items-center justify-center p-12 text-center min-h-[420px]">
                <div className="w-20 h-20 border-2 border-amber-500/30 border-t-amber-500 rounded-full animate-spin mb-6" />
                <h3 className="font-display text-xl font-semibold text-earth-300 mb-2">Analyzing…</h3>
                <p className="text-earth-500 text-sm">AI model is examining your crop image</p>
              </div>
            )}

            {/* Error state */}
            {error && !loading && (
              <div className="glass-card rounded-2xl p-8 text-center min-h-[320px] flex flex-col items-center justify-center">
                <AlertTriangle size={40} className="text-red-500 mb-4" />
                <h3 className="font-display text-lg font-semibold text-red-400 mb-2">Detection Failed</h3>
                <p className="text-earth-500 text-sm mb-4">{error}</p>
                <button onClick={handleAnalyze}
                  className="px-5 py-2 rounded-xl bg-earth-800 hover:bg-earth-700 text-earth-300 text-sm border border-earth-700 transition-colors">
                  Try Again
                </button>
              </div>
            )}

            {/* ── Results ──────────────────────────────────────────────── */}
            {result && !loading && (
              <>
                {/* Disease header */}
                <div className={`${sev.bg} border ${sev.border} rounded-2xl p-5 shadow-lg`}>
                  <div className="flex items-center justify-between mb-2">
                    <span className={`text-xs font-mono uppercase tracking-wider ${sev.color}`}>
                      {isHealthy ? '✅ No Disease Detected' : '🔬 Disease Identified'}
                    </span>
                    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold border ${sev.border} ${sev.color} bg-earth-950/40`}>
                      <span className={`w-1.5 h-1.5 rounded-full ${sev.dot}`} />
                      {sev.label} Severity
                    </span>
                  </div>
                  <h2 className="font-display text-2xl font-bold text-earth-100 mb-3">
                    {result.disease}
                  </h2>

                  {/* Confidence bar */}
                  <div className="mb-1 flex items-center justify-between text-xs">
                    <span className="text-earth-500">Confidence</span>
                    <span className={`font-mono font-semibold ${sev.color}`}>{result.confidence}%</span>
                  </div>
                  <div className="w-full bg-earth-800 rounded-full h-2 overflow-hidden">
                    <div className={`h-full rounded-full transition-all duration-700 ${sev.bar}`}
                      style={{ width: `${result.confidence}%` }} />
                  </div>
                </div>

                {/* Recommendation */}
                <div className="glass-card rounded-2xl p-5">
                  <h3 className="text-earth-200 text-sm font-semibold mb-2 flex items-center gap-2">
                    <ShieldCheck size={14} className="text-crop-400" /> Recommendation
                  </h3>
                  <p className="text-earth-400 text-sm leading-relaxed">{result.recommendation}</p>
                </div>

                {/* Treatments */}
                {result.treatments?.length > 0 && (
                  <div className="glass-card rounded-2xl p-5">
                    <h3 className="text-earth-200 text-sm font-semibold mb-3 flex items-center gap-2">
                      🧪 Recommended Treatments
                    </h3>
                    <ul className="space-y-2">
                      {result.treatments.map((t, i) => (
                        <li key={i} className="flex items-start gap-2.5 bg-earth-900/40 rounded-xl px-3 py-2.5 border border-earth-800/60">
                          <CheckCircle size={14} className="text-amber-400 flex-shrink-0 mt-0.5" />
                          <span className="text-earth-300 text-sm">{t}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Prevention */}
                {result.prevention && (
                  <div className="glass-card rounded-2xl p-5 border border-crop-800/30 bg-crop-950/10">
                    <h3 className="text-earth-200 text-sm font-semibold mb-2 flex items-center gap-2">
                      🌿 Prevention
                    </h3>
                    <p className="text-earth-400 text-sm leading-relaxed">{result.prevention}</p>
                  </div>
                )}

                {/* Re-analyze */}
                <button onClick={clearImage}
                  className="w-full py-3 rounded-xl bg-earth-800 hover:bg-earth-700 text-earth-300 text-sm font-medium transition-colors border border-earth-700 flex items-center justify-center gap-2">
                  <RefreshCw size={14} /> Analyze Another Image
                </button>
              </>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
